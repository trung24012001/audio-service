from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from audio_service import AudioService
from pydub import AudioSegment
import random
import uuid
from database import db
import json
import util

app = Flask(__name__)
cors = CORS(app)
audioService = AudioService()

BONUS_COEF = 2
RESOURCE_PATH = "resource/procon_audio/JKspeech"
OUTPUT_PATH = "output/audio"
AUDIO_PREFIX = "audio/"


@app.route(r"/problem-data", methods=["GET"])
@cross_origin()
def createProblemData():
    try:
        sounds = []
        n_reading_card = random.randint(3, 20)
        answer_list = []
        i = 0
        while i < n_reading_card:
            file_name = util.get_rand_filename(answer_list)
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
                    "problem_data": AUDIO_PREFIX + file_name,
                    "answer_data": answer_list,
                }
            ),
        )

        return (
            jsonify(
                {
                    "question_uuid": uid,
                    "problem_data": AUDIO_PREFIX + file_name,
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
        team_id = str(payload["team_id"])
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
            result.append(AUDIO_PREFIX + file_name)

        bonus = BONUS_COEF + (n_divided - 1) * (-0.25)
        answer_data = util.get_answer(question_uuid, team_id)
        answer_data["bonus_coef"] = bonus
        db.set(answer_data["answer_uuid"], json.dumps(answer_data))
        return jsonify(result), 200
    except Exception as e:
        return f"{e}", 500


@app.route(r"/answer-data", methods=["POST"])
@cross_origin()
def createScore():
    try:
        payload = request.get_json()
        team_id = str(payload["team_id"])
        payload_answer = payload["answer_data"]
        question_uuid = payload["question_uuid"]

        question_data = json.loads(db.get(question_uuid))
        answer_data = util.get_answer(question_uuid, team_id)
        score_data = util.get_score(payload_answer, question_data, answer_data)

        answer_data["score_data"] = score_data
        db.set(answer_data["answer_uuid"], json.dumps(answer_data))

        return jsonify(score_data), 200
    except Exception as e:
        print(e)
        return f"{e}", 500


@app.route(r"/audio/<path:filename>")
def get_audio_file(filename):
    return send_from_directory(OUTPUT_PATH, filename, as_attachment=False)


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
