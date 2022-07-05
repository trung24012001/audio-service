from audio_service import AudioService
from pydub import AudioSegment

service = AudioService()


def test_format():
    sound = service.format_audio("resource/source_file.wav")
    print(sound.sample_width, sound.frame_rate, sound.channels)
    sound.export("output/source_file.wav", format="wav")
    print("Format test successfully")


def test_divided_data():
    problem = AudioSegment.from_file("output/problem_file.wav", format="wav")
    segments = service.gen_divided_data(
        problem, durations=[24000, 24000, 24000, 24000, 58996])
    for i in range(len(segments)):
        segments[i].export("output/segment_{}.wav".format(i), format="wav")
    print("Divided test successfully")


data = [
    {
        "path": "resource/JKspeech-v_1_0/JKspeech/J01.wav",
        "offset": 4800
    },
    {
        "path": "resource/JKspeech-v_1_0/JKspeech/E02.wav",
        "offset": 9600
    },
    {
        "path": "resource/JKspeech-v_1_0/JKspeech/J03.wav",
        "offset": 4800
    },
    {
        "path": "resource/JKspeech-v_1_0/JKspeech/E04.wav",
        "offset": 9600
    },
    {
        "path": "resource/JKspeech-v_1_0/JKspeech/J05.wav",
        "offset": 4800
    }
]


def test_problem_data():
    sounds = []
    for item in data:
        sounds.append({
            "audio":  AudioSegment.from_file(item['path'], format="wav"),
            "offset": item['offset']
        })
    problem = service.gen_problem_data(sounds)
    problem.export("output/problem_file.wav", format="wav")
    print("Problem data test successfully")


def test():
    problem_file = AudioSegment.from_file(
        "output/problem_file.wav", format="wav")
    test_file = AudioSegment.from_file(
        "resource/sample_Q_202205/sample_Q_202205/sample_Q_M01/sample_Q_M01/problem.wav", format="wav")
    print("test_file", test_file.sample_width,
          test_file.frame_rate, test_file.channels, len(test_file))
    print("problem_file", problem_file.sample_width,
          problem_file.frame_rate, problem_file.channels,  len(problem_file))


# test_format()
test_divided_data()
# test_problem_data()
# test()
