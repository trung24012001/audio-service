import utils
import sys
import audio_service as AudioService
import time


def combinations(array, tupple_len, prev_array=[]):
    if len(prev_array) == tupple_len:
        return [prev_array]
    combs = []
    for i, val in enumerate(array):
        prev_array_extended = prev_array.copy()
        prev_array_extended.append(val)
        combs += combinations(array[i + 1 :], tupple_len, prev_array_extended)

    return combs


def get_problem_data():
    data = [
        {"card": "E06", "offset": 4800},
        {"card": "J03", "offset": 9600},
        {"card": "E08", "offset": 4800},
        {"card": "J08", "offset": 2800},
        {"card": "E31", "offset": 0},
    ]
    sounds = [
        {"audio": AudioService.get_audio(item["card"]), "offset": item["offset"]}
        for item in data
    ]
    return AudioService.overlap_audio(sounds)


def main():
    mse = sys.maxsize
    problem = get_problem_data()
    problem = problem[1000:2000]
    solve = None
    for comb in combinations(AudioService.AUDIO_CARDS, 5):
        start = time.time()
        sound = AudioService.overlap_audio(
            [{"audio": AudioService.get_audio(file), "offset": 0} for file in comb]
        )
        sound = sound[1000:2000]
        tmp_mse = AudioService.get_mse(sound, problem)

        if mse > tmp_mse:
            mse = tmp_mse
            solve = comb
            if mse < 5000000:
                break
        stop = time.time()
        print("solve:", comb, "mse:", tmp_mse, "duration:", stop - start, "reject")

    print(solve, mse, "accept")


main()
