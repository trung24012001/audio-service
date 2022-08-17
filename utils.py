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


def change_score(team_cards, team_id, question_uuid):
    question = get_question(question_uuid)
    answer = get_answer(question_uuid + str(team_id))
    answer_cards = [data["card"] for data in question["answer_data"]]
    print("answer", answer_cards)
    for card in team_cards:
        if not card in AudioService.AUDIO_CARDS:
            raise Exception("Card {} not exist in cards list".format(card))
    if len(team_cards) != len(answer_cards):
        raise Exception(
            "Number of cards answer must be equal number of cards that generate problem data"
        )

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
    }

    answer["score_data"] = score_data
    db.set(answer["answer_uuid"], json.dumps(answer))

    return answer


def overlap_cards(cards):
    return AudioService.overlap_audio(
        [
            {"audio": AudioService.get_audio(data["card"]), "offset": data["offset"]}
            for data in cards or []
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

        for i in range(len(team_cards)):
            if i >= len(pre_selected):
                continue
            if team_cards[i] != pre_selected[i]:
                changed += 1

    return correct, changed
