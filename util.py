import random
import base64
import json
from database import db
import uuid
import audio_service as audioService

BONUS_COEF = 2
SCORE_DEDUCT = 10
SCORE_PLUS = 100
SCORE_THRESHOLD = 0
DEDUCT_THRESHOLD = 100


def get_answer(answer_uuid, question_uuid, team_id):
    uid = answer_uuid
    if not db.get(uid):
        uid = str(uuid.uuid4())
        db.set(
            uid,
            json.dumps(
                {
                    "answer_uuid": uid,
                    "bonus_coef": BONUS_COEF,
                    "question_uuid": question_uuid,
                    "team_id": team_id,
                }
            ),
        )
    return json.loads(db.get(uid))


def get_score(team_answer, question, answer):
    answer_file_list = [obj["file_name"] for obj in question["answer_data"]]
    team_file_list = [*team_answer["picked_cards"],
                      *team_answer["changed_cards"]]
    score, correct = 0, 0

    if len(team_file_list) != len(answer_file_list):
        raise Exception(
            "Number of answer must be equal number of reading cards that generate problem data"
        )

    for file in answer_file_list:
        if file in team_file_list:
            score += answer["bonus_coef"] * SCORE_PLUS
            correct += 1
    deduct = len(team_answer["changed_cards"]) * SCORE_DEDUCT
    score_data = answer.get("score_data")

    if score_data:
        score_data["deduct"] += SCORE_DEDUCT
        if score_data["deduct"] > DEDUCT_THRESHOLD:
            score_data["deduct"] = 100
        deduct = score_data["deduct"]
    score = SCORE_THRESHOLD if (
        score - deduct) < SCORE_THRESHOLD else (score - deduct)

    return {
        "answer_uuid": answer["answer_uuid"],
        "score": score,
        "correct": correct,
        "deduct": deduct,
        "bonus": answer["bonus_coef"],
        "mse": "",
        "problem_audio": "",
        "team_audio": "",
        # "answer_file_list":  audioService.overlap_audio([audioService.get_audio_file(file) for obj in question["answer_data"]]),
        # "team_file_list": audioService.overlap_audio([audioService.get_audio_file(file) for file in team_file_list])
    }


def get_rand_filename(avoids):
    file_name = "E" if random.randint(0, 1) else "J"
    serial = random.randint(1, 44)
    file_name += ("0" + str(serial)) if serial <= 9 else str(serial)
    if file_name in avoids:
        file_name = get_rand_filename(avoids)

    return file_name


def audio_base64(audio):
    return base64.b64encode(audio).decode("utf-8")
