import json
from database import db
import audio_service as AudioService


def get_answer(answer_uuid):
    if not db.get(answer_uuid):
        db.set(
            answer_uuid,
            json.dumps({"answer_uuid": answer_uuid}),
        )
    return json.loads(db.get(answer_uuid))


def get_question(question_uuid):
    question = db.get(question_uuid)
    if not question:
        return None
    return json.loads(question)

#### TUNG ADDED ######
def evaluate(question_data, score_data):
  print(question_data)
  # final_bonus_factor = question_data.get("bonus_factor", 1.) * question_data.get('n_parts', 2)*1.0 / score_data.get("parts_needed")
  final_bonus_factor = round((1.0 - score_data.get("parts_needed")*1.0 / question_data.get('n_parts', 2)) * question_data.get("bonus_factor", 1.), 2)
  penalties = round(question_data.get("penalty_per_change", 2) * score_data.get('changed'))
  raw_score = question_data.get("point_per_correct", 10) * score_data.get('correct')
  final_score = round((raw_score - penalties) * (1.0 + final_bonus_factor), 2)
  max_score = round(question_data.get("point_per_correct", 10)*len(question_data.get("answer_data"))*(1.0 + question_data.get("bonus_factor", 1.)*(1.0 - 1.0/question_data.get("n_parts", 2))), 2)
  score_data["score"] = dict(final_bonus_factor=final_bonus_factor, penalties=penalties, raw_score=raw_score, final_score=final_score, max_score=max_score)

def change_score(team_cards, team_id, question_uuid):
    question = get_question(question_uuid)
    answer = get_answer(question_uuid + str(team_id))
    answer_cards = [data["card"] for data in question["answer_data"]]
    print("answer", answer_cards)
    for card in team_cards:
        if not card in AudioService.AUDIO_CARDS:
            raise Exception("Card {} not exist in cards list".format(card))
    if len(team_cards) != len(answer_cards):
        raise Exception("Number of cards invalid")

    score_data = answer.get("score_data")
    correct, changed = get_score(team_cards, answer_cards, score_data)
    problem_audio = overlap_cards(question["answer_data"])
    team_audio = overlap_cards([{"card": card, "offset": 0} for card in team_cards])
    score_data = {
        "correct": correct,
        "changed": changed,
        "card_selected": team_cards,
        # "card_answer": answer_cards,
        "mse": AudioService.get_mse(team_audio, problem_audio),
        "parts_needed": len(answer["received_ids"])
    }
    evaluate(question, score_data)
    answer["score_data"] = score_data
    db.set(answer["answer_uuid"], json.dumps(answer))

    return answer


def overlap_cards(cards):
    return AudioService.overlap_audio(
        [
            {"audio": AudioService.get_audio(card["card"]), "offset": card["offset"]} for card in cards or []
        ]
    )


def get_score(team_cards, answer_cards, score_data):
    correct, changed = 0, 0
    for card in answer_cards:
        if card in team_cards:
            correct += 1
    if score_data:
        changed = score_data["changed"]
        pre_selected = score_data["card_selected"]
        for card in team_cards:
            if card not in pre_selected:
                changed += 1

    return correct, changed
