from pydub import AudioSegment
import base64
import random
from os import walk
from sklearn.metrics import mean_squared_error
import numpy as np
import scipy.fftpack
from sklearn import preprocessing

RESOURCE_PATH = "resource/procon_audio/JKspeech"
SAMPLE_RATE = 48000
MAX_OFFSET_SAMPLE = 0.3 * SAMPLE_RATE


def get_card_list():
    filenames = next(walk(RESOURCE_PATH), (None, None, []))[2]
    return [file[:-4] for file in filenames]


AUDIO_CARDS = get_card_list()


def get_random_cards(n_cards):
    cards = random.choices(AUDIO_CARDS, k=n_cards)
    return [
        {"card": card, "offset": random.randint(0, MAX_OFFSET_SAMPLE)} for card in cards
    ]


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


def get_mse(st_audio, nd_audio, dct=False):
    st_sample = st_audio.get_array_of_samples()
    nd_sample = nd_audio.get_array_of_samples()
    st_res, nd_res = None, None
    if dct:
        st_res = np.abs(scipy.fftpack.fft(st_sample))
        nd_res = np.abs(scipy.fftpack.fft(nd_sample))
    else:
        st_res = preprocessing.normalize([st_sample])[0]
        nd_res = preprocessing.normalize([nd_sample])[0]
    min_sample = min(len(st_res), len(nd_res))
    return mean_squared_error(st_res[:min_sample], nd_res[:min_sample]) * 1e6


def to_base64(sound):
    return base64.b64encode(sound.raw_data).decode("utf-8")
