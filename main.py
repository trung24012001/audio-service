from msilib.schema import Error
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS, cross_origin
from audio_service import AudioService
from pydub import AudioSegment
import random
import base64
import uuid
import pickledb
import json

app = Flask(__name__)
cors = CORS(app)
audioService = AudioService()
question_db = pickledb.load("db/question.db", True, False)
answer_db = pickledb.load("db/answer.db", True, False)
BONUS_COEF = 2
SCORE_DEDUCT = 10
SCORE_PLUS = 100
SCORE_THRESHOLD = 0
DEDUCT_THRESHOLD = 100
RESOURCE_PATH = "resource/procon_audio/JKspeech"
OUTPUT_PATH = "output/audio"


@app.route(r"/problem-data", methods=["GET"])
@cross_origin()
def createProblemData():
    try:
        sounds = []
        n_reading_card = random.randint(3, 20)
        answer_list = []
        i = 0
        while i < n_reading_card:
            file_name = rand_file_name(answer_list)
            answer_list.append(file_name)
            sound = AudioSegment.from_wav("{}/{}.wav".format(RESOURCE_PATH, file_name))
            sounds.append(
                {
                    "audio": sound,
                    "offset": random.randint(0, int(len(sound) / 5)),
                }
            )
            i += 1

        problem_data = audioService.gen_problem_data(sounds)
        uid = str(uuid.uuid4())
        file_name = "{}.wav".format(uid)
        problem_data.export("{}/{}".format(OUTPUT_PATH, file_name), format="wav")

        question_db.set(
            uid,
            json.dumps(
                {
                    "question_uuid": uid,
                    "problem_data": file_name,
                    "answer_data": answer_list,
                }
            ),
        )

        return (
            jsonify(
                {
                    "question_uuid": uid,
                    "problem_data": file_name,
                    "card_number": n_reading_card,
                    "service_type": "PYTHON_AUDIO_SERVICE",
                }
            ),
            200,
        )
    except Exception as e:
        return f"{e}", 500


@app.route(r"/divided-data", methods=["POST"])
@cross_origin()
def createDividedData():
    try:
        payload = request.get_json()
        team_id = payload["team_id"]
        n_divided = int(payload["n_divided"])
        question_uuid = payload["question_uuid"]
        durations, result = [], []
        problem_data = AudioSegment.from_wav(
            "{}/{}.wav".format(OUTPUT_PATH, question_uuid)
        )
        len_sound = len(problem_data)
        i = n_divided - 1
        sum = 0
        while i >= 0:
            dur = (
                len_sound - sum
                if i == 0
                else random.randint(500, len_sound - sum - 500 * i)
            )
            durations.append(dur)
            sum += dur
            i -= 1
        segments = audioService.gen_divided_data(problem_data, durations)
        for seg in segments:
            uid = str(uuid.uuid4())
            file_name = "{}.wav".format(uid)
            seg.export("{}/{}".format(OUTPUT_PATH, file_name), format="wav")
            result.append(file_name)

        bonus = BONUS_COEF + (n_divided - 1) * (-0.25)
        answer_uuid = question_uuid + team_id
        if not answer_db.get(answer_uuid):
            answer_db.set(answer_uuid, json.dumps({}))
        answer = json.loads(answer_db.get(answer_uuid))
        answer["bonus_coef"] = bonus
        answer_db.set(answer_uuid, json.dumps(answer))
        return jsonify(result), 200
    except Exception as e:
        return f"{e}", 500


@app.route(r"/answer-data", methods=["POST"])
@cross_origin()
def createScore():
    try:
        payload = request.get_json()
        team_id = payload["team_id"]
        payload_answer = payload["answer_data"]
        question_uuid = payload["question_uuid"]
        question_data = json.loads(question_db.get(question_uuid))
        right_answers = question_data["answer_data"]
        check_answers = payload_answer["picked_cards"] + payload_answer["changed_cards"]
        score, correct = 0, 0

        answer_uuid = question_uuid + team_id
        if not answer_db.get(answer_uuid):
            answer_db.set(answer_uuid, json.dumps({"bonus_coef": BONUS_COEF}))
        answer_data = json.loads(answer_db.get(answer_uuid))

        if len(check_answers) != len(right_answers):
            raise Exception(
                "Number of answer must be equal number of reading cards that generate problem data"
            )
        for answer in check_answers:
            if answer in check_answers:
                score += answer_data["bonus_coef"] * SCORE_PLUS
                correct += 1
        deduct = len(check_answers["changed_cards"]) * SCORE_DEDUCT

        score_data = answer_data.get("score_data")
        if score_data:
            score_data["deduct"] += SCORE_DEDUCT
            if score_data["deduct"] > DEDUCT_THRESHOLD:
                score_data["deduct"] = 100
            deduct = score_data["deduct"]
        score = (
            SCORE_THRESHOLD if (score - deduct) < SCORE_THRESHOLD else (score - deduct)
        )
        score_data = {"score": score, "correct": correct, "deduct": deduct}
        answer_data["score_data"] = score_data
        answer_db.set(answer_uuid, json.dumps(answer_data))
        return jsonify(score_data), 200
    except Exception as e:
        print(e)
        return f"{e}", 500


@app.route(r"/audio/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_PATH, filename, as_attachment=False)


def rand_file_name(avoids):
    file_name = "E" if random.randint(0, 1) else "J"
    serial = random.randint(1, 44)
    file_name += ("0" + str(serial)) if serial <= 9 else str(serial)
    if file_name in avoids:
        file_name = rand_file_name(avoids)

    return file_name


def audio_base64(audio):
    return base64.b64encode(audio).decode("utf-8")


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
