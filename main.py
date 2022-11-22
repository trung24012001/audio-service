import traceback
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS, cross_origin
import audio_service as AudioService
import random
import uuid
from database import db
import json
import utils

app = Flask(__name__)
cors = CORS(app)

SERVICE_NAME = "PYTHON_AUDIO_SERVICE"
MAX_OFFSET_SAMPLE = 0.3 * AudioService.SAMPLE_RATE
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
        answer_cards = AudioService.get_random_cards(n_cards)
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
        traceback.print_exc()
        return f"{e}", 500


@app.route(r"/problem-data", methods=["PUT"])
@cross_origin()
def updateProblemData():
    try:
        payload = request.get_json()
        n_cards = payload["n_cards"]
        question_uuid = payload["question_uuid"]
        if n_cards < MIN_CARD or n_cards > MAX_CARD:
            n_cards = random.randint(MIN_CARD, MAX_CARD)
        answer_cards = AudioService.get_random_cards(n_cards)

        question = utils.get_question(question_uuid)
        if not question:
            return jsonify(message="Question not found"), 404
        question["answer_data"] = answer_cards
        db.set(question_uuid, json.dumps(question))

        return (
            jsonify(
                {
                    "question_uuid": question_uuid,
                    "n_cards": n_cards,
                    "service_type": SERVICE_NAME,
                }
            ),
            200,
        )
    except Exception as e:
        return f"{e}", 500
#### TUNG ADDED ######
def doCreateDividedData(question):
    #question = utils.get_question(question_uuid)
    n_parts = question.get('n_parts')
    if n_parts is None:
        question.n_parts = 2
        n_parts = 2

    if n_parts < 2 or n_parts > 5:
        raise Exception("Number of divided data require >= 2 and <= 5")

    problem_audio = utils.overlap_cards(question['answer_data'])

    max_dur = len(problem_audio)
    i = n_parts - 1
    cur_dur = 0
    segments = []
    while i >= 0:
        dur = (
            max_dur - cur_dur
            if i == 0
            else random.randint(
                MIN_DIVIDED_TIME, max_dur - cur_dur - MIN_DIVIDED_TIME * i
            )
        )
        segments.append({
            "index": i, "duration": dur
        })
        cur_dur += dur
        i -= 1
    question['divided_data'] = segments
    db.set(question["question_uuid"], json.dumps(question))
    return segments, problem_audio

@app.route(r"/divided-data", methods=["POST"])
@cross_origin()
def createDividedData():
    try:
        payload = request.get_json()
        team_id = payload["team_id"]
        question_uuid = payload["question_uuid"]
        n_divided = int(payload["n_divided"]) or 0
        if n_divided < 2 or n_divided > 5:
            raise Exception("Number of divided data required >= 2 and <= 5")

        question = utils.get_question(question_uuid)
        problem_audio = utils.overlap_cards(question["answer_data"])
        max_dur = len(problem_audio)
        i = n_divided - 1
        cur_dur = 0
        segments = []
        while i >= 0:
            dur = (
                max_dur - cur_dur
                if i == 0
                else random.randint(
                    MIN_DIVIDED_TIME, max_dur - cur_dur - MIN_DIVIDED_TIME * i
                )
            )
            segments.append({"index": i, "duration": dur})
            cur_dur += dur
            i -= 1

        answer = utils.get_answer(question_uuid + str(team_id))
        if not answer.get("divided_data"):
            answer["divided_data"] = segments
            db.set(answer["answer_uuid"], json.dumps(answer))
        elif len(answer["divided_data"]) >= len(segments):
            segments = answer["divided_data"]

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
        answer = utils.change_score(team_cards, team_id, question_uuid)

        return jsonify(answer), 200
    except Exception as e:
        return f"{e}", 500


@app.route(r"/audio", methods=["GET"])
def get_audio_data():
    try:
        type = request.args.get("type")
        audio_data = None
        if type == "answer":
            answer = utils.get_answer(request.args.get("answer_uuid"))
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
            audio_data = utils.overlap_cards(question.get("answer_data"))

        elif type == "divided":
            '''
            index = int(request.args.get("index"))
            team_id = request.args.get("team_id")
            question_uuid = request.args.get("question_uuid")
            answer = utils.get_answer(question_uuid + str(team_id))
            question = utils.get_question(question_uuid)
            sound = utils.overlap_cards(question.get("answer_data"))
            segments = AudioService.seperate_audio(
                sound, [item["duration"] for item in answer["divided_data"]]
            )
            audio_data = segments[index]
            '''
            team_id = request.args.get("team_id")
            question_uuid = request.args.get('question_uuid')
            question = utils.get_question(question_uuid)
            answer_uuid = question_uuid + str(team_id)
            answer = utils.get_answer(answer_uuid)
            received_ids = answer.get('received_ids') or []
            segments = question.get("divided_data")
            problem_audio = None

            if segments is None:
                segments, problem_audio = doCreateDividedData(question)
            else:
                problem_audio = utils.overlap_cards(question.get("answer_data"))

            segments.sort(key=lambda s: s['index'])
            valid_segments = list(
                filter(lambda uid: uid["index"] not in received_ids, segments)
            )
            n_left = len(valid_segments)
            if n_left == 0:
                return jsonify("All divided data segments sent"), 404

            selected_index = random.randint(0, n_left)
            selected_index = segments[selected_index]['index']
            audio_segments = AudioService.seperate_audio(
                problem_audio, [item["duration"] for item in answer["divided_data"]]
            )
            audio_data = audio_segments[selected_index]
            received_ids.append(selected_index)
            answer['received_ids'] = received_ids
            db.set(answer_uuid, json.dumps(answer))


        if not audio_data:
            return jsonify("No data"), 404

        return send_file(
            audio_data.export(format="wav"),
            attachment_filename="audio.wav",
            mimetype="audio/wav",
            as_attachment=False,
        )

    except Exception as e:
        return f"{e}", 500


@app.route(r"/download/resource", methods=["GET"])
def download_resource():
    try:

        return send_from_directory(
            directory="./resource",
            path="procon_audio.zip",
            attachment_filename="resource.zip",
            as_attachment=True,
        )

    except Exception as e:
        return f"{e}", 500


@app.route(r"/download/resource/<path:filename>", methods=["GET"])
def download_file(filename):
    try:
        return send_from_directory(
            directory=AudioService.RESOURCE_PATH,
            path=filename,
            as_attachment=False,
        )
    except Exception as e:
        return f"{e}", 500


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
