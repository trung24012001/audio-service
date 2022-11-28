import json
from database import db
import audio_service as AudioService
import random


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
    answer["score_data"] = {
        "correct": correct,
        "changed": changed,
        "card_selected": team_cards,
        "mse": AudioService.get_mse(team_audio, problem_audio),
        "parts_needed": len(answer["received_ids"])
    }
#<<<<<<< HEAD
    evaluate(question, score_data)
    answer["score_data"] = score_data
#=======
#    answer["score_data"]["total"] = get_total_score(answer)

#>>>>>>> 77f959de28cdd59d617a3478ff554fde22c90542
    db.set(answer["answer_uuid"], json.dumps(answer))

    return answer


def overlap_cards(cards):
    return AudioService.overlap_audio(
        [
            {"audio": AudioService.get_audio(card["card"]), "offset": card["offset"]} for card in cards or []
        ]
    )


def get_score(team_cards, answer_cards, score_data):
    correct = 0
    changed = [False] * len(answer_cards)
    for card in answer_cards:
        if card in team_cards:
            correct += 1
    if score_data:
        changed = score_data["changed"]
        pre_selected = score_data["card_selected"]
#<<<<<<< HEAD
        for card in team_cards:
            if card not in pre_selected:
                changed += 1
#=======
#
#        for i in range(len(team_cards)):
#            if changed[i] == True:
#                continue
#            if team_cards[i] != pre_selected[i]:
#                changed[i] = True
#>>>>>>> 77f959de28cdd59d617a3478ff554fde22c90542

    return correct, changed


#def get_total_score(answer):
#    total_score = 0
#    score_data = answer.get("score_data")
#    divided_data = answer.get("divided_data")
#    if score_data:
#        n_correct = score_data["correct"]
#        n_changed = 0
#        n_divided = 1
#        for change in score_data["changed"]:
#            if change:
#                n_changed += 1
#
#        if divided_data:
#            n_divided = len(divided_data)
#
#        total_score = (1 / n_divided) * 2 * n_correct * 10 - n_changed * 5
#
#    return total_score


def get_divided_data(problem_audio, n_divided, min_time):
    max_dur = len(problem_audio)
    i = n_divided - 1
    cur_dur = 0
    segments = []
    while i >= 0:
        dur = (
            max_dur - cur_dur
            if i == 0
            else random.randint(min_time, max_dur - cur_dur - min_time * i)
        )
        segments.append({"position": i, "duration": dur})
        cur_dur += dur
        i -= 1
    random.shuffle(segments)
    for i, seg in enumerate(segments):
        seg["index"] = i

    return segments
