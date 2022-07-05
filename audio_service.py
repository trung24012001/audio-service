from pydub import AudioSegment


class AudioService:
    def __init__(self):
        self.audio_forder = []

    def format_audio(self, path):
        sound = AudioSegment.from_file(path, format="wav")
        # sampling 48kHz
        sound = sound.set_frame_rate(48000)
        # quantization 2 bytes ~ 16 bit rate
        sound = sound.set_sample_width(2)
        # monaural
        sound = sound.set_channels(1)
        return sound

    def gen_divided_data(self, sound, durations):
        segments = []
        start, end = 0, 0
        for dur in durations:
            start = end
            end = start + (dur / 48000) * 1000
            segment = sound[start:end]
            segments.append(segment)

        return segments

    def gen_problem_data(self, sounds):
        problem = AudioSegment.empty()
        for sound in sounds:
            audio = sound['audio']
            offset = (sound['offset'] / 48000) * 1000
            audio = audio[offset:]
            if len(problem) > len(audio) or len(problem) == 0:
                problem = audio.overlay(problem)
            else:
                problem = problem.overlay(audio)

        return problem
