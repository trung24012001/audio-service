from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from audio_service import AudioService
from pydub import AudioSegment
import random
import base64
import uuid
import pickledb

app = Flask(__name__)
cors = CORS(app)
audioService = AudioService()
db = pickledb.load('db/database.db', True)
SCORE_PLUS = 100


@app.route(r"/api/problem-data", methods=["POST"])
@cross_origin()
def createProblemData():
    try:
        sounds = []
        n_reading_card = random.randint(3, 20)
        path = "resource/procon_audio/JKspeech/{}.wav"
        answer_list = []
        i = 0
        while i < n_reading_card:
            file_name = rand_file_name(answer_list)
            answer_list.append(file_name)
            sound = AudioSegment.from_wav(path.format(file_name))
            sounds.append(
                {"audio": sound, "offset": random.randint(
                    0, len(sound)) / 1000 * 48000}
            )
            i += 1

        problem_data = audioService.gen_problem_data(sounds)

        data = {
            "question_uuid": uuid.uuid4(),
            "problem_data": audio_base64(problem_data.raw_data),
            "n_card": n_reading_card,
            "answer_data": answer_list,
            "service_type": "PYTHON_AUDIO_SERVICE",
        }

        db.set(data['question_uuid'], data)

        return (
            jsonify(data),
            200,
        )
    except Exception as e:
        print(e)
        return jsonify({"error": "Could not create problem data!"}), 500


@app.route(r"/api/divided-data", methods=["POST"])
@cross_origin()
def createDividedData():
    n_divided = request.form["n_divided"]
    problem_file = request.files["problem_file"]
    problem_data = AudioSegment.from_wav(problem_file)
    try:
        n_divided = int(n_divided)
        if n_divided < 2 or n_divided > 5:
            raise Exception("Number of divided data must >= 2 and <= 5")
        durations = []
        len_sound = len(problem_data)
        i = n_divided - 1
        dur = 0
        while i >= 0:
            dur = random.randint(500, len_sound - dur - 500 * i)
            durations.append(dur)
            i -= 1
        segments = audioService.gen_divided_data(problem_data, durations)
        result = []
        for seg in segments:
            result.append(audio_base64(seg.raw_data))
        return jsonify({"divided_data": result}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Could not create divided data!"}), 500


@app.route(r"/api/answer-data", methods=["POST"])
@cross_origin()
def createScore():
    payload = request.get_json()
    team_answer = payload["answer_data"]
    question_id = team_answer["question_uuid"]
    data = db.get(question_id)
    answer_data = data["answer_data"]
    score, correct, deduct = 0, 0, 0
    try:
        cards = [*team_answer["picked_cards"], *team_answer["changed_cards"]]
        for card in cards:
            if card["answer"] in answer_data:
                score += card["coef"] * SCORE_PLUS - card["deduct"]
                deduct += card["deduct"]
                correct += 1
        score_data = {
            "score": score,
            "correct": correct,
            "deduct": deduct
        }
        data["score_data"] = score_data
        db.set(question_id, data)
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


def audio_base64(audio):
    return base64.b64encode(audio).decode("utf-8")


if __name__ == "__main__":
    app.run(host="localhost", port=5555)
