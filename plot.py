import matplotlib.pyplot as plt
import numpy as np
import wave
import audio_service as AudioService
import scipy.io.wavfile as wavfile
import scipy.fftpack

files = [
    {"path": "output/problem_file.wav", "color": "blue"},
    {"path": AudioService.RESOURCE_PATH + "/E01.wav", "color": "green"},
    {"path": AudioService.RESOURCE_PATH + "/E02.wav", "color": "orange"},
    {"path": AudioService.RESOURCE_PATH + "/E03.wav", "color": "red"},
]
# plt.figure(1)
fig, axs = plt.subplots(4, 2)


def plot_signal(path, color, i, j):
    spf = wave.open(path, "r")
    signal = spf.readframes(-1)
    signal = np.frombuffer(signal, dtype=np.int16)
    fs = spf.getframerate()
    time = np.linspace(0, len(signal) / fs, num=len(signal))
    axs[i, j].plot(time, signal, color=color)
    # axs[i, j].set_title(path.split("/")[-1])


def plot_freq(path, color, i, j):
    fs_rate, signal = wavfile.read(path)
    N = signal.shape[0]
    secs = N / float(fs_rate)
    Ts = 1.0 / fs_rate
    t = np.arange(0, secs, Ts)
    FFT = np.abs(scipy.fftpack.fft(signal))
    DCT = np.abs(scipy.fftpack.dct(signal))
    freqs = scipy.fftpack.fftfreq(signal.size, Ts)
    axs[i, j].plot(freqs, FFT, color=color)
    # axs[i, j].plot(freqs, DCT, color=color)
    # print(freqs[list(FFT).index(max(list(FFT)))])
    # axs[i, j].set_title("frequence " + path.split("/")[-1])


for file in files:
    plot_signal(file["path"], file["color"], 0, 0)
    plot_freq(file["path"], file["color"], 2, 0)
i = 0
j = 1
for file in files[1:]:
    plot_signal(file["path"], file["color"], i, j)
    plot_freq(file["path"], file["color"], i + 2, j)
    j += 1
    if j >= 2:
        i += 1
        j = 0


# axs[0, i].specgram(signal, NFFT=1024, Fs=AudioService.SAMPLE_RATE, noverlap=900)
# axs[0, i].set_title("Problem Data")

plt.show()
