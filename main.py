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
MAX_CARD = 20
MIN_CARD = 3
MIN_DIVIDED = 2
MAX_DIVIDED = 5
MIN_DIVIDED_TIME = 500


@app.route(r"/problem-data", methods=["GET"])
@cross_origin()
def createProblemData():
    try:
        n_cards = request.args.get("n_cards", default=0, type=int)
        n_parts = request.args.get("n_parts", default=2, type=int)
        bonus_factor = request.args.get("bonus_factor", default=1., type=float)
        penalty_per_change = request.args.get("penalty_per_change", default=2., type=float)
        point_per_correct = request.args.get('point_per_correct', default=10, type=int)

        if n_cards < MIN_CARD or n_cards > MAX_CARD:
            n_cards = random.randint(MIN_CARD, MAX_CARD)
        answer_cards = AudioService.get_random_cards(n_cards)
        uid = str(uuid.uuid4())

        question = {
          "question_uuid": uid,
          "answer_data": answer_cards,
          "n_parts": n_parts,
          "bonus_factor": bonus_factor,
          "penalty_per_change": penalty_per_change,
          "point_per_correct": point_per_correct
        }

        db.set(uid, json.dumps(question))
        question['n_cards'] = len(question['answer_data'])
        try:
          del question['answer_data']
          del question['divided_data']
        except:
          pass

        return jsonify(question), 200
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

        n_parts = request.args.get("n_parts") or question.get('n_parts', 2)
        bonus_factor = request.args.get("bonus_factor") or question.get('bonus_factor', 1.0)
        penalty_per_change = request.args.get("penalty_per_change") or question.get('penalty_per_change', 2.0)
        point_per_correct = request.args.get('point_per_correct') or question.get('point_per_correct', 10)

        question["answer_data"] = answer_cards
        question["n_parts"] = n_parts
        question["bonus_factor"] = bonus_factor
        question["penalty_per_change"] = penalty_per_change
        question["point_per_correct"] = point_per_correct
        db.set(question_uuid, json.dumps(question))

        question['n_cards'] = len(question['answer_data'])
        try:
          del question['answer_data']
          del question['divided_data']
        except:
          pass
        return jsonify(question), 200
    except Exception as e:
        traceback.print_exc()
        return f"{e}", 500

#### TUNG ADDED ######
def doCreateDividedData(question):
    #question = utils.get_question(question_uuid)
    print("doCreateDividedData")
    n_parts = question.get('n_parts')
    print("doCreateDividedData", n_parts)
    if n_parts is None:
        question["n_parts"] = 2
        n_parts = 2

    print("doCreateDividedData", n_parts)

    if n_parts < 2 or n_parts > 5:
        raise Exception("Number of divided data require >= 2 and <= 5")

    problem_audio = utils.overlap_cards(question['answer_data'])

    max_dur = len(problem_audio)
    segment_dur = int(max_dur / n_parts)
    if segment_dur < MIN_DIVIDED_TIME:
        raise Exception("Segment duration is less than 0.5 seconds")

    i = n_parts - 1
    cur_dur = 0
    segments = []
    while i >= 0:
        dur = (max_dur - cur_dur) if i == 0 else segment_dur
        
        segments.append({
            "index": i, "duration": dur, "uuid": str(uuid.uuid4())
        })
        cur_dur += dur
        i -= 1

    print(segments)
    question['divided_data'] = segments
    db.set(question["question_uuid"], json.dumps(question))
    return segments, problem_audio

@app.route(r"/reset_answer", methods=["GET"])
@cross_origin()
def reset_answer():
    try:
        team_id = request.args.get("team_id")
        question_uuid = request.args.get("question_uuid")
        answer_uuid = question_uuid + str(team_id)
        db.set(answer_uuid, json.dumps({"answer_uuid": answer_uuid}))
        return "Ok", 200
    except Exception as e:
        traceback.print_exc()
        return f"{e}", 500
########### TUNG Modified ##########
@app.route(r"/divided-data", methods=["POST"])
@cross_origin()
def createDividedData():
    try:
        payload = request.get_json()
        team_id = payload["team_id"]
        question_uuid = payload["question_uuid"]
#<<<<<<< HEAD
        new = payload.get("new") or False

        question = utils.get_question(question_uuid)
        answer_uuid = question_uuid + str(team_id)
        answer = utils.get_answer(answer_uuid)
        received_ids = answer.get('received_ids') or []
        segments = question.get("divided_data")
        if segments is None:
            segments, _ = doCreateDividedData(question)

        valid_segments = list(
            filter(lambda uid: uid["index"] not in received_ids, segments)
        )
        n_left = len(valid_segments)
        if n_left == 0 or not new:
            return jsonify([ segments[i]['uuid'] for i in received_ids ]), 200
            #return jsonify("All divided data segments sent"), 404

        selected_index = random.randint(0, n_left - 1)
        print(selected_index, n_left)
        selected_index = valid_segments[selected_index]['index']
        print(selected_index, segments)
        received_ids.append(selected_index)
        answer['received_ids'] = received_ids
        print("Before save answer")
        print(answer)
        print(json.dumps(answer))

        __res = db.set(answer_uuid, json.dumps(answer))
        print(__res)
        return jsonify([ segments[i]['uuid'] for i in received_ids ]), 200
#=======
#        n_divided = int(payload["n_divided"]) or 0
#        if n_divided < MIN_DIVIDED or n_divided > MAX_DIVIDED:
#            raise Exception(
#                "Number of divided data required >= {} and <= {}".format(
#                    MIN_DIVIDED, MAX_DIVIDED
#                )
#            )
#
#        question = utils.get_question(question_uuid)
#        problem_audio = utils.overlap_cards(question["answer_data"])
#        segments = utils.get_divided_data(problem_audio, n_divided, MIN_DIVIDED_TIME)
#        answer = utils.get_answer(question_uuid + str(team_id))
#        answer["divided_data"] = segments
#        db.set(answer["answer_uuid"], json.dumps(answer))
#
#        return jsonify(len(segments)), 200
#>>>>>>> 77f959de28cdd59d617a3478ff554fde22c90542
    except Exception as e:
        traceback.print_exc();
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
        answer["received_ids"] = len(answer["received_ids"])
        return jsonify(answer), 200
    except Exception as e:
        traceback.print_exc()
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
            durs = sorted(answer["divided_data"], key=lambda x: x["position"])
            segments = AudioService.seperate_audio(
                sound,
                [item["duration"] for item in durs],
            )
            audio_data = segments[index]
            '''
#<<<<<<< HEAD
            team_id = request.args.get("team_id")
            segment_uuid = request.args.get("uuid")
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
            audio_segments = AudioService.seperate_audio(
                problem_audio, [item["duration"] for item in question["divided_data"]]
            )
            
            selected_index = -1
            for idx, segment in enumerate(segments):
                if segment['uuid'] == segment_uuid:
                    selected_index = idx
                    break;

            if selected_index == -1 :
                return jsonify({"error": "wrong segment uuid"}), 404

            print(selected_index)
            print(segments)
            audio_data = audio_segments[selected_index]
#=======
#            for dur in durs:
#                if dur["index"] == index:
#                    audio_data = segments[dur["position"]]
#>>>>>>> 77f959de28cdd59d617a3478ff554fde22c90542

        if not audio_data:
            return jsonify("No data"), 404

        return send_file(
            audio_data.export(format="wav"),
            attachment_filename="audio.wav",
            mimetype="audio/wav",
            as_attachment=False,
        )

    except Exception as e:
        traceback.print_exc()
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

####### TUNG ADDED #########
@app.route(r"/question-template", methods=["GET"])
def question_template():
    try:
        jsonify({
          "n_cards": 3, 
          "n_parts": 2,
          "bonus_factor": 1.0,
          "penalty_per_change": 2,
          "point_per_correct": 10
        }), 200
    except Exception as e:
        traceback.print_exc()
        return f"{e}", 500

if __name__ == "__main__":
    app.run(host="localhost", port=5000)
