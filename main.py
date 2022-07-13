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
SCORE_DEDUCT = 10
SCORE_PLUS = 100
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
                    "bonus_coef": 1,
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
        print(e)
        return jsonify({"error": "Could not create problem data!"}), 500


@app.route(r"/divided-data", methods=["POST"])
@cross_origin()
def createDividedData():
    payload = request.get_json()
    n_divided = payload["n_divided"]
    question_id = payload["question_uuid"]
    problem_data = AudioSegment.from_wav("{}/{}.wav".format(OUTPUT_PATH, question_id))
    try:
        n_divided = int(n_divided)
        if n_divided < 2 or n_divided > 5:
            raise Exception("Number of divided data must >= 2 and <= 5")
        durations = []
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
        result = []
        for seg in segments:
            uid = str(uuid.uuid4())
            file_name = "{}.wav".format(uid)
            seg.export("{}/{}".format(OUTPUT_PATH, file_name), format="wav")
            result.append(file_name)
        return jsonify(result), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Could not create divided data!"}), 500


@app.route(r"/answer-data", methods=["POST"])
@cross_origin()
def createScore():
    payload = request.get_json()
    team_answer = payload["answer_data"]
    question_uuid = team_answer["question_uuid"]
    data = json.loads(db.get(question_uuid))
    answer_data = data["answer_data"]
    score, correct = 0, 0, 0
    try:
        cards = [*team_answer["picked_cards"], *team_answer["changed_cards"]]
        for card in cards:
            if card in answer_data:
                score += data["bonus_coef"] * SCORE_PLUS
                correct += 1
        deduct = len(team_answer["changed_cards"]) * SCORE_DEDUCT
        score -= deduct
        score_data = {"score": score, "correct": correct, "deduct": deduct}
        data["score_data"] = score_data
        db.set(question_uuid, json.dumps(data))
        return jsonify(score_data), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Could not handle answer data!"}), 500


def rand_file_name(avoids):
    file_name = "E" if random.randint(0, 1) else "J"
    serial = random.randint(1, 44)
    file_name += ("0" + str(serial)) if serial <= 9 else str(serial)
    if file_name in avoids:
        file_name = rand_file_name(avoids)

    return file_name


@app.route(r"/audio/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_PATH, filename, as_attachment=False)


def audio_base64(audio):
    return base64.b64encode(audio).decode("utf-8")


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
