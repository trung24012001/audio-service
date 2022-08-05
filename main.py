from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS, cross_origin
import audio_service as AudioService
import random
import uuid
from database import db
import json
import utils
import io

app = Flask(__name__)
cors = CORS(app)

SERVICE_NAME = "PYTHON_AUDIO_SERVICE"
MAX_OFFSET_SAMPLE = 0.25 * AudioService.SAMPLE_RATE
MAX_CARD = 20
MIN_CARD = 3
MIN_DIVIDED_TIME = 500


@app.route(r"/problem-data", methods=["GET"])
@cross_origin()
def createProblemData():
    try:
        n_cards = request.args.get("n_cards", default=0, type=int)
        if n_cards < MIN_CARD or n_cards > MAX_CARD:
            n_cards = random.randint(MIN_CARD, MAX_CARD)
        sounds = []
        answer_cards = []
        selected_cards = []
        i = 0
        while i < n_cards:
            card = utils.get_random_card(selected_cards)
            offset = random.randint(0, MAX_OFFSET_SAMPLE)
            answer_cards.append({"card": card, "offset": offset})
            selected_cards.append(card)
            sounds.append(
                {
                    "audio": AudioService.get_audio(card),
                    "offset": offset,
                }
            )
            i += 1

        uid = str(uuid.uuid4())
        db.set(
            uid,
            json.dumps(
                {
                    "question_uuid": uid,
                    "answer_data": answer_cards,
                }
            ),
        )

        return (
            jsonify(
                {
                    "question_uuid": uid,
                    "n_cards": n_cards,
                    "service_type": SERVICE_NAME,
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
        durations = []
        question = utils.get_question(question_uuid)
        problem_audio = utils.overlap_cards(question["answer_data"])

        max_dur = len(problem_audio)
        i = n_divided - 1
        cur_dur = 0
        while i >= 0:
            dur = (
                max_dur - cur_dur
                if i == 0
                else random.randint(
                    MIN_DIVIDED_TIME, max_dur - cur_dur - MIN_DIVIDED_TIME * i
                )
            )
            durations.append(dur)
            cur_dur += dur
            i -= 1
        segments = [
            AudioService.to_base64(seg)
            for seg in AudioService.seperate_audio(problem_audio, durations)
        ]

        answer = utils.get_answer(question_uuid, team_id)
        answer["n_divided"] = n_divided
        db.set(answer["answer_uuid"], json.dumps(answer))

        return jsonify(segments), 200
    except Exception as e:
        return f"{e}", 500


@app.route(r"/answer-data", methods=["POST"])
@cross_origin()
def createScore():
    try:
        payload = request.get_json()
        team_id = payload["team_id"]
        team_cards = payload["answer_data"]
        question_uuid = payload["question_uuid"]

        score_data = utils.change_score(team_cards, team_id, question_uuid)

        return jsonify(score_data), 200
    except Exception as e:
        return f"{e}", 500


# @app.route(r"/audio/<path:uuid>")
# def get_audio_data(uuid):
#     OUTPUT_PATH = "output/audio"
#     return send_from_directory(OUTPUT_PATH, uuid, as_attachment=False)


@app.route(r"/audio", methods=["GET"])
def get_audio_data():
    try:
        type = request.args.get("type")
        audio_data = None
        if type == "answer":
            answer_uuid = request.args.get("answer_uuid")
            answer = json.loads(db.get(answer_uuid)) if db.get(answer_uuid) else {}
            audio_data = AudioService.overlap_audio(
                [
                    {
                        "audio": AudioService.get_audio(card),
                        "offset": 0,
                    }
                    for card in (answer.get("score_data") or {}).get("card_selected")
                    or []
                ]
            )

        elif type == "question":
            question_uuid = request.args.get("question_uuid")
            question = utils.get_question(question_uuid)
            audio_data = AudioService.overlap_audio(
                [
                    {
                        "audio": AudioService.get_audio(data["card"]),
                        "offset": data["offset"],
                    }
                    for data in question.get("answer_data") or []
                ]
            )
            print(len(audio_data))
            audio_data.export("output/audio.wav", format="wav")

        if not audio_data:
            return jsonify("No data"), 400

        return send_file(
            io.BytesIO(audio_data.raw_data),
            attachment_filename="audio.wav",
            mimetype="audio/wav",
            as_attachment=False,
        )

    except Exception as e:
        return f"{e}", 500


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
