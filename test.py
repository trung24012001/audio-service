import audio_service as service
from pydub import AudioSegment
import pickledb


def test_format():
    sound = service.get_audio("E05")
    print(sound.sample_width, sound.frame_rate, sound.channels, len(sound))
    print("Format test successfully")


test_format()


def test_divided_data():
    problem = AudioSegment.from_wav("output/audio.wav")
    segments = service.seperate_audio(
        sound=problem, durations=[24000, 24000, 24000, 24000, 58996]
    )
    for i in range(len(segments)):
        segments[i].export("output/segment_{}.wav".format(i), format="wav")
    print("Divided test successfully")


data = [
    {"card": "E01", "offset": 0},
    {"card": "E02", "offset": 0},
    {"card": "E03", "offset": 0},
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


def testDb():
    db = pickledb.load("db/database.db", True)
    db.set("lala", "agag")
