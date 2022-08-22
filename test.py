import audio_service as service
from pydub import AudioSegment
import pickledb


def test_format():
    sound1 = service.get_audio("E05")
    sound2 = service.get_audio("E06")
    print(len(sound1.get_array_of_samples()))
    print("Format test successfully")


def test_divided_data():
    problem = AudioSegment.from_wav("output/audio.wav")
    segments = service.seperate_audio(
        sound=problem, durations=[24000, 24000, 24000, 24000, 58996]
    )
    for i in range(len(segments)):
        segments[i].export("output/segment_{}.wav".format(i), format="wav")
    print("Divided test successfully")


data = [
    {"card": "E01", "offset": 4800},
    {"card": "E02", "offset": 9600},
    {"card": "E03", "offset": 4800},
]


def test_problem_data():
    sounds = []
    for item in data:
        sounds.append(
            {"audio": service.get_audio(item["card"]), "offset": item["offset"]}
        )
    problem = service.overlap_audio(sounds)
    problem.export("output/problem_file.wav", format="wav")
    print("Problem data test successfully")


test_problem_data()


def testDb():
    db = pickledb.load("db/database.db", True)
    db.set("lala", "agag")
