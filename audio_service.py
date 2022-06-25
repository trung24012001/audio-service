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

  def gen_divided_data(self, sound, numData):
    # miliseconds
    duration_len = len(sound)
    segment_len = duration_len / numData
    segments = []
    i = 0
    while i < numData:
      start = i * segment_len
      end = start + segment_len
      segment_sound = sound[start:end]
      segments.append(segment_sound)
      i+=1

    return segments

  def gen_problem_data(self, sounds, type):
    combined = None
    if type == 'overlay':
      combined = sounds[0].overlay(sounds[1])
      for song in sounds[2:]:
        combined = combined.overlay(song)
    elif type== 'concat':
      combined = AudioSegment.empty()
      for song in sounds:
        combined += song

    return combined
