from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import audio_service as audioService
import random
import uuid
from database import db
import json
import util

app = Flask(__name__)
cors = CORS(app)

BONUS_COEF = 2
OUTPUT_PATH = "output/audio"
AUDIO_PREFIX = "audio/"


@app.route(r"/problem-data", methods=["GET"])
@cross_origin()
def createProblemData():
    try:
        n_cards = request.args.get("n_cards", default=0, type=int)
        if n_cards < 3 or n_cards > 20:
            n_cards = random.randint(3, 20)
        sounds = []
        answer_list = []
        file_name_list = []
        i = 0
        while i < n_cards:
            file_name = util.get_rand_filename(file_name_list)
            offset = random.randint(0, int(len(sound) / 5))
            answer_list.append({
                file_name,
                offset
            })
            file_name_list.append(file_name)
            sound = audioService.get_audio_file(file_name)
            sounds.append(
                {
                    "audio": sound,
                    "offset": offset,
                }
            )
            i += 1

        problem_data = audioService.overlap_audio(sounds)
        uid = str(uuid.uuid4())
        file_name = "{}.wav".format(uid)
        audioService.export_audio(problem_data, file_name)

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
                    "card_number": n_cards,
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
        problem_data = audioService.get_audio_file(question_uuid)

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
        segments = audioService.seperate_audio(problem_data, durations)
        for seg in segments:
            uid = str(uuid.uuid4())
            file_name = "{}.wav".format(uid)
            audioService.export_audio(seg, file_name)
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
        team_id = payload["team_id"]
        team_answer = payload["answer_data"]
        question_uuid = payload["question_uuid"]

        question = json.loads(db.get(question_uuid))
        answer = util.get_answer(question_uuid, team_id)
        score = util.get_score(team_answer, question, answer)
        answer["score_data"] = score
        db.set(answer["answer_uuid"], json.dumps(answer))

        return jsonify(score), 200
    except Exception as e:
        print(e)
        return f"{e}", 500


@app.route(r"/audio/<path:filename>")
def get_audio_file(filename):
    return send_from_directory(OUTPUT_PATH, filename, as_attachment=False)


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
