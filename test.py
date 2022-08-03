import audio_service as service
from pydub import AudioSegment
import pickledb


def test_format():
    sound = service.format_audio("resource/source_file.wav")
    print(sound.sample_width, sound.frame_rate, sound.channels)
    sound.export("output/source_file.wav", format="wav")
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
    {"path": "resource/procon_audio/JKspeech/J01.wav", "offset": 4800},
    {"path": "resource/procon_audio/JKspeech/E02.wav", "offset": 9600},
    {"path": "resource/procon_audio/JKspeech/J03.wav", "offset": 4800},
    {"path": "resource/procon_audio/JKspeech/E04.wav", "offset": 9600},
    {"path": "resource/procon_audio/JKspeech/J05.wav", "offset": 4800},
]


def test_problem_data():
    sounds = []
    for item in data:
        sounds.append(
            {"audio": service.get_audio_file(
                item["path"]), "offset": item["offset"]}
        )
    problem = service.overlap_audio(sounds)
    problem.export("output/problem_file.wav", format="wav")
    print("Problem data test successfully")


def testDb():
    db = pickledb.load('db/database.db', True)
    db.set('lala', 'agag')


testDb()

# test_format()
# test_divided_data()
# test_problem_data()
# test()
