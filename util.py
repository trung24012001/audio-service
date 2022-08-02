import random
import base64
import json
from database import db

BONUS_COEF = 2
SCORE_DEDUCT = 10
SCORE_PLUS = 100
SCORE_THRESHOLD = 0
DEDUCT_THRESHOLD = 100


def get_answer(question_uuid, team_id):
    answer_uuid = question_uuid + team_id
    if not db.get(answer_uuid):
        db.set(
            answer_uuid,
            json.dumps(
                {
                    "answer_uuid": answer_uuid,
                    "bonus_coef": BONUS_COEF,
                    "question_uuid": question_uuid,
                    "team_id": team_id,
                }
            ),
        )
    return json.loads(db.get(answer_uuid))


def get_score(payload_answer, question_data, answer_data):
    right_answers = question_data["answer_data"]
    check_answers = [*payload_answer["picked_cards"], *payload_answer["changed_cards"]]
    score, correct = 0, 0

    if len(check_answers) != len(right_answers):
        raise Exception(
            "Number of answer must be equal number of reading cards that generate problem data"
        )

    for answer in right_answers:
        if answer in check_answers:
            score += answer_data["bonus_coef"] * SCORE_PLUS
            correct += 1
        deduct = len(payload_answer["changed_cards"]) * SCORE_DEDUCT
    score_data = answer_data.get("score_data")
    if score_data:
        score_data["deduct"] += SCORE_DEDUCT
        if score_data["deduct"] > DEDUCT_THRESHOLD:
            score_data["deduct"] = 100
        deduct = score_data["deduct"]
    score = SCORE_THRESHOLD if (score - deduct) < SCORE_THRESHOLD else (score - deduct)
    score_data = {
        "score": score,
        "correct": correct,
        "deduct": deduct,
        "bonus": answer_data["bonus_coef"],
    }

    return score_data


def get_rand_filename(avoids):
    file_name = "E" if random.randint(0, 1) else "J"
    serial = random.randint(1, 44)
    file_name += ("0" + str(serial)) if serial <= 9 else str(serial)
    if file_name in avoids:
        file_name = get_rand_filename(avoids)

    return file_name


def audio_base64(audio):
    return base64.b64encode(audio).decode("utf-8")
