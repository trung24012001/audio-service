from pydub import AudioSegment
import base64
import random
from os import walk


RESOURCE_PATH = "resource/procon_audio/JKspeech"
SAMPLE_RATE = 48000


def get_card_list():
    filenames = next(walk(RESOURCE_PATH), (None, None, []))[2]
    return [file[:-4] for file in filenames]


AUDIO_CARDS = get_card_list()


def get_random_card(selected_list):
    card = random.choice(AUDIO_CARDS)
    if card in selected_list:
        card = get_random_card(selected_list)

    return card


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


def get_mse(st_audio, nd_audio):
    st_sample = st_audio.get_array_of_samples()
    nd_sample = nd_audio.get_array_of_samples()
    min_sample = min(len(st_sample), len(nd_sample))
    mse = 0
    for i in range(min_sample):
        mse += (st_sample[i] - nd_sample[i]) ** 2
    return mse / min_sample


def to_base64(sound):
    return base64.b64encode(sound.raw_data).decode("utf-8")
