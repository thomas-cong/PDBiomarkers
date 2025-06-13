

def resample(sound, hz = 16000):
    '''
    sound is a pydub sound
    '''
    return sound.set_frame_rate(hz)

def detect_leading_silence(sound, silence_threshold=-40.0, chunk_size=10):
    '''
    sound is a pydub Sound
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    trim_ms = 0 # ms

    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms

def trim_leading_and_lagging_silence(audioSegment):
    sound = audioSegment

    start_trim = detect_leading_silence(sound)
    end_trim = detect_leading_silence(sound.reverse())
    duration = len(sound)
    trimmed_sound = sound[start_trim: duration-end_trim]
    return trimmed_sound

def match_target_amplitude(audioSegment, target_dBFS):
    sound = audioSegment
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)
