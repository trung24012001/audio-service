from pydub import AudioSegment
import base64

RESOURCE_PATH = "resource/procon_audio/JKspeech"
SAMPLE_RATE = 48000


def get_audio(file_name, dir="resource"):
    if dir == "resource":
        path = RESOURCE_PATH
    else:
        path = dir

    return AudioSegment.from_wav("{}/{}.wav".format(path, file_name))


def export_audio(sound, path, format):
    sound.export(path, format=format)
    return path


def format_audio(path):
    sound = AudioSegment.from_file(path, format="wav")
    # sampling 48kHz
    sound = sound.set_frame_rate(SAMPLE_RATE)
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
        offset = sound["offset"] / SAMPLE_RATE
        audio = audio[offset:]
        problem = (
            audio.overlay(problem)
            if len(problem) > len(audio) or len(problem) == 0
            else problem.overlay(audio)
        )

    return problem


def to_base64(sound):
    return base64.b64encode(sound.raw_data).decode("utf-8")
