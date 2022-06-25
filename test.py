from audio_service import AudioService

service = AudioService()


def test_format():
    sound = service.format_audio("resource/source_file.wav")
    print(sound.sample_width, sound.frame_rate, sound.channels)
    sound.export("output/source_file.wav", format="wav")
    print("Format test successfully")


def test_problem_data():
    return None


def test_divided_data():
    sound = service.format_audio("resource/source_file.wav")
    numData = 10
    segments = service.gen_divided_data(sound, numData)
    for i in range(len(segments)):
        segments[i].export("output/segment_{}.wav".format(i), format="wav")
    print("Divided test successfully")


def test_problem_data(type):
    sound = service.format_audio("resource/source_file.wav")
    sounds = [sound, sound, sound]
    combined = service.gen_problem_data(sounds, type)
    print(combined.max, sound.max)
    combined.export("output/{}_file.wav".format(type), format="wav")
    print("Problem {} test successfully".format(type))


# test_format()
# test_divided_data()
# test_problem_data('concat')
test_problem_data("overlay")
