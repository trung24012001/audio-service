from pydub import AudioSegment

RESOURCE_PATH = "resource/procon_audio/JKspeech"
OUTPUT_PATH = "output/audio"


def get_audio_file(file_name):
    sound = AudioSegment.from_wav(
        "{}/{}.wav".format(RESOURCE_PATH, file_name))
    return sound


def export_audio(sound, file_name):
    sound.export(
        "{}/{}".format(OUTPUT_PATH, file_name), format="wav")
    return True


def format_audio(path):
    sound = AudioSegment.from_file(path, format="wav")
    # sampling 48kHz
    sound = sound.set_frame_rate(48000)
    # quantization 2 bytes ~ 16 bit rate
    sound = sound.set_sample_width(2)
    # monaural
    sound = sound.set_channels(1)
    return sound


def seperate_audio(sound, durations):
    segments = []
    start, end = 0, 0
    for dur in durations:
        start = end
        end = start + dur
        segment = sound[start:end]
        segments.append(segment)

    return segments


def overlap_audio(sounds):
    problem = AudioSegment.empty()
    for sound in sounds:
        audio = sound["audio"]
        offset = sound["offset"]
        audio = audio[offset:]
        if len(problem) > len(audio) or len(problem) == 0:
            problem = audio.overlay(problem)
        else:
            problem = problem.overlay(audio)

    return problem
