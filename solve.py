import math
import sys
import audio_service as AudioService
import time
import numpy as np
import scipy.sparse
import scipy.sparse.linalg
import scipy.fftpack
from cvxopt import matrix
from cvxopt.glpk import ilp
import itertools
from cvxopt.modeling import op, variable, dot
from sklearn import preprocessing


def combinations(
    array,
    tupple_len,
):

    return list(itertools.combinations(array, tupple_len))


def problem_transform(problem, dct=False):
    problem_sample = problem.get_array_of_samples()
    res = None
    if dct:
        res = scipy.fftpack.dct(np.abs(problem_sample))
    else:
        res = preprocessing.normalize([problem_sample])[0]
    return res


def create_matrix(max_sample, dct=False):
    matrix = []
    for card in AudioService.AUDIO_CARDS:
        audio = AudioService.get_audio(card)
        audio_sample = audio.get_array_of_samples()
        res = None
        if dct:
            res = scipy.fftpack.dct(np.abs(audio_sample))
        else:
            res = preprocessing.normalize([audio_sample])[0]
        matrix.append(res[:max_sample])
    return matrix


def get_problem_data(n_cards):
    answer_cards = AudioService.get_random_cards(n_cards)
    answer_cards = [
        {"card": "E01", "offset": 4800},
        {"card": "E09", "offset": 9600},
        {"card": "E02", "offset": 4800},
        {"card": "J04", "offset": 4800},
    ]
    sounds = [
        {"audio": AudioService.get_audio(item["card"]), "offset": item["offset"]}
        for item in answer_cards
    ]
    return AudioService.overlap_audio(sounds), [item["card"] for item in answer_cards]


def sound_compare_brute_force(mse_min=None, sec_from=0, sec_to=30000):
    mse = sys.maxsize
    n_cards = 4
    problem, answer = get_problem_data(n_cards)
    problem = problem[sec_from:sec_to]
    solve = None
    start = time.time()
    combs = combinations(AudioService.AUDIO_CARDS, n_cards)
    for comb in combs:
        start_loop = time.time()
        sound = AudioService.overlap_audio(
            [{"audio": AudioService.get_audio(card), "offset": 0} for card in comb]
        )
        sound = sound[sec_from:sec_to]
        tmp_mse = AudioService.get_mse(sound, problem)

        if mse > tmp_mse:
            mse = tmp_mse
            solve = comb
            if mse_min and mse < mse_min:
                break
        end_loop = time.time()
        print(
            "solve:",
            comb,
            "mse:",
            tmp_mse,
            "answer",
            answer,
            "time",
            end_loop - start_loop,
        )
    stop = time.time()
    print(
        "solve:",
        solve,
        "mse:",
        mse,
        "total time:",
        stop - start,
        "answer",
        answer,
        "accept",
    )


def sound_compare_matrix():
    n_cards = 4
    max_sample = 88
    problem, answer = get_problem_data(n_cards)
    problem_sample = problem_transform(problem, dct=False)[:max_sample]
    matrix_sample = create_matrix(max_sample, dct=False)
    c = matrix(np.array([sum(row) for row in matrix_sample], dtype=float))
    G = matrix(-np.array(matrix_sample, dtype=float))
    h = matrix(-np.array(problem_sample, dtype=float))
    A = matrix(1.0, (1, max_sample))
    b = matrix(n_cards, tc="d")
    x = variable(max_sample, "x")

    lp = op(
        abs((dot(c, x) - math.fsum(problem_sample))),
        [G * x <= h, sum(x) == n_cards, x >= 0, x <= 1],
    )
    lp.solve()
    print(x.value)
    # (status, x) = ilp(
    #     c,
    #     G,
    #     h,
    #     matrix(1.0, (1, max_sample)),
    #     matrix(n_cards, tc="d"),
    #     B=set(range(len(c))),
    # )
    # print(status, x)
    # if x:
    #     print(
    #         [AudioService.AUDIO_CARDS[i] for i, coef in enumerate(x) if coef >= 1],
    #         answer,
    #     )


def main():
    # sound_compare_brute_force(mse_min=6e-06, sec_from=1000, sec_to=2000)
    sound_compare_matrix()


main()
