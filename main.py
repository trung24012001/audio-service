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
db = pickledb.load("db/database.db", True, False)
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

        db.set(
            uid,
            json.dumps(
                {
                    "question_uuid": uid,
                    "problem_data": file_name,
                    "answer_data": answer_list,
                    "bonus_coef": BONUS_COEF,
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

        question_data = json.loads(db.get(question_uuid))
        question_data["bonus_coef"] = BONUS_COEF + (n_divided - 1) * (-0.25)
        db.set(question_uuid, json.dumps(question_data))
        return jsonify(result), 200
    except Exception as e:
        return f"{e}", 500


@app.route(r"/answer-data", methods=["POST"])
@cross_origin()
def createScore():
    try:
        payload = request.get_json()
        team_answer = payload["answer_data"]
        question_uuid = payload["question_uuid"]
        question_data = json.loads(db.get(question_uuid))
        real_answer = question_data["answer_data"]
        score, correct = 0, 0
        answers = team_answer["picked_cards"] + team_answer["changed_cards"]
        if len(answers) != len(real_answer):
            raise Exception(
                "Number of answer must be equal number of reading cards that generate problem data"
            )
        for answer in answers:
            if answer in real_answer:
                score += question_data["bonus_coef"] * SCORE_PLUS
                correct += 1
        deduct = len(team_answer["changed_cards"]) * SCORE_DEDUCT
        score_data = question_data["score_data"]
        if score_data:
            score_data["deduct"] += SCORE_DEDUCT
            if score_data["deduct"] > DEDUCT_THRESHOLD:
                score_data["deduct"] = 100
            deduct = score_data["deduct"]
        score = (
            SCORE_THRESHOLD if (score - deduct) < SCORE_THRESHOLD else (score - deduct)
        )
        score_data = {"score": score, "correct": correct, "deduct": deduct}
        question_data["score_data"] = score_data
        db.set(question_uuid, json.dumps(question_data))
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
