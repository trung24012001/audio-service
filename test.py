import audio_service as service
from pydub import AudioSegment
import pickledb


def test_format():
    sound = service.get_audio("E05")
    print(sound.sample_width, sound.frame_rate, sound.channels, len(sound))
    print("Format test successfully")


def test_divided_data():
    problem = AudioSegment.from_wav("output/problem_file.wav")
    segments = service.seperate_audio(
        problem, durations=[24000, 24000, 24000, 24000, 58996]
    )
    for i in range(len(segments)):
        segments[i].export("output/segment_{}.wav".format(i), format="wav")
    print("Divided test successfully")


data = [
    {"card": "J01", "offset": 4800},
    {"card": "E02", "offset": 9600},
    {"card": "J03", "offset": 4800},
    {"card": "E04", "offset": 9600},
    {"card": "J05", "offset": 4800},
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


# def testDb():
#     db = pickledb.load('db/database.db', True)
#     db.set('lala', 'agag')


# testDb()

# test_format()
# test_divided_data()
test_problem_data()
# test()
