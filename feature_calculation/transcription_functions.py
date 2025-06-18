import os

import whisper
import json
import parselmouth
from parselmouth.praat import call
import math

model = whisper.load_model("base.en")


def transcribe_audio(audio_path):
    """
    Transcribe audio with word timestamps
    """
    transcribed_audio = model.transcribe(audio_path)
    text_dir = audio_path.split("/")
    text_dir[-2] = "Text Files"
    del text_dir[-1]
    text_dir = "/".join(text_dir)
    # Create the Text Files directory if it doesn't exist
    os.makedirs(text_dir, exist_ok=True)
    text_file_folder = text_dir

    # Extract just the filename without path and extension
    filename = os.path.basename(audio_path).replace(".wav", "")

    # Create the text file in the text file folder
    with open(os.path.join(text_file_folder, filename + ".txt"), "w") as f:
        f.write(transcribed_audio["text"])
    return os.path.join(text_file_folder, filename + ".txt")


def align_audio(audio_path):
    """
    Align audio with word timestamps
    """
    # Create the Alignment Files directory if it doesn't exist
    align_dir = audio_path.split("/")
    align_dir[-2] = "Alignment Files"
    del align_dir[-1]
    align_dir = "/".join(align_dir)
    os.makedirs(align_dir, exist_ok=True)
    result = model.transcribe(audio_path, word_timestamps=True)
    segments = result["segments"]
    with open(
        os.path.join(
            align_dir, os.path.basename(audio_path).replace(".wav", "") + ".json"
        ),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)


def calculate_interword_pauses(segments):
    """
    Calculate interword pauses from a list of segments
    """
    pauses = []
    prev_end = None
    for segment in segments:
        for word in segment["words"]:
            if prev_end is not None:
                pause = word["start"] - prev_end
                pauses.append(pause)
            prev_end = word["end"]
    return pauses


def avg_pause_duration(pauses):

    return sum(pauses) / len(pauses) if pauses else 0


def adv_speech_metrics(filename):
    """
       Calculate speech rate, articulation rate, and average syllable duration from an audio file.

       Parameters:
           filename (str): Path to the audio file.

       Returns:
           dict: A dictionary containing the calculated speech metrics.
    from ANNAFAVARO/PARKCELEB

    """

    silencedb = -25
    mindip = 2
    minpause = 0.1
    sound = parselmouth.Sound(filename)
    originaldur = sound.get_total_duration()
    intensity = sound.to_intensity(50)
    start = call(intensity, "Get time from frame number", 1)
    nframes = call(intensity, "Get number of frames")
    end = call(intensity, "Get time from frame number", nframes)
    min_intensity = call(intensity, "Get minimum", 0, 0, "Parabolic")
    max_intensity = call(intensity, "Get maximum", 0, 0, "Parabolic")

    # get .99 quantile to get maximum (without influence of non-speech sound bursts)
    max_99_intensity = call(intensity, "Get quantile", 0, 0, 0.99)

    # estimate Intensity threshold
    threshold = max_99_intensity + silencedb
    threshold2 = max_intensity - max_99_intensity
    threshold3 = silencedb - threshold2
    if threshold < min_intensity:
        threshold = min_intensity

    # get pauses (silences) and speakingtime
    textgrid = call(
        intensity,
        "To TextGrid (silences)",
        threshold3,
        minpause,
        0.1,
        "silent",
        "sounding",
    )
    silencetier = call(textgrid, "Extract tier", 1)
    silencetable = call(silencetier, "Down to TableOfReal", "sounding")
    npauses = call(silencetable, "Get number of rows")
    speakingtot = 0
    for ipause in range(npauses):
        pause = ipause + 1
        beginsound = call(silencetable, "Get value", pause, 1)
        endsound = call(silencetable, "Get value", pause, 2)
        speakingdur = endsound - beginsound
        speakingtot += speakingdur

    intensity_matrix = call(intensity, "Down to Matrix")
    # sndintid = sound_from_intensity_matrix
    sound_from_intensity_matrix = call(intensity_matrix, "To Sound (slice)", 1)
    # use total duration, not end time, to find out duration of intdur (intensity_duration)
    # in order to allow nonzero starting times.
    intensity_duration = call(sound_from_intensity_matrix, "Get total duration")
    intensity_max = call(sound_from_intensity_matrix, "Get maximum", 0, 0, "Parabolic")
    point_process = call(
        sound_from_intensity_matrix,
        "To PointProcess (extrema)",
        "Left",
        "yes",
        "no",
        "Sinc70",
    )
    # estimate peak positions (all peaks)
    numpeaks = call(point_process, "Get number of points")
    t = [call(point_process, "Get time from index", i + 1) for i in range(numpeaks)]

    # fill array with intensity values
    timepeaks = []
    peakcount = 0
    intensities = []
    for i in range(numpeaks):
        value = call(sound_from_intensity_matrix, "Get value at time", t[i], "Cubic")
        if value > threshold:
            peakcount += 1
            intensities.append(value)
            timepeaks.append(t[i])

    # fill array with valid peaks: only intensity values if preceding
    # dip in intensity is greater than mindip
    validpeakcount = 0
    currenttime = timepeaks[0]
    currentint = intensities[0]
    validtime = []

    for p in range(peakcount - 1):
        following = p + 1
        followingtime = timepeaks[p + 1]
        dip = call(intensity, "Get minimum", currenttime, timepeaks[p + 1], "None")
        diffint = abs(currentint - dip)
        if diffint > mindip:
            validpeakcount += 1
            validtime.append(timepeaks[p])
        currenttime = timepeaks[following]
        currentint = call(intensity, "Get value at time", timepeaks[following], "Cubic")

    # Look for only voiced parts
    pitch = sound.to_pitch_ac(0.02, 30, 4, False, 0.03, 0.25, 0.01, 0.35, 0.25, 450)
    voicedcount = 0
    voicedpeak = []

    for time in range(validpeakcount):
        querytime = validtime[time]
        whichinterval = call(textgrid, "Get interval at time", 1, querytime)
        whichlabel = call(textgrid, "Get label of interval", 1, whichinterval)
        value = pitch.get_value_at_time(querytime)
        if not math.isnan(value):
            if whichlabel == "sounding":
                voicedcount += 1
                voicedpeak.append(validtime[time])

    # calculate time correction due to shift in time for Sound object versus
    # intensity object
    timecorrection = originaldur / intensity_duration

    # Insert voiced peaks in TextGrid
    call(textgrid, "Insert point tier", 1, "syllables")
    for i in range(len(voicedpeak)):
        position = voicedpeak[i] * timecorrection
        call(textgrid, "Insert point", 1, position, "")

    # return results
    speakingrate = voicedcount / originaldur
    articulationrate = voicedcount / speakingtot
    npause = npauses - 1
    # asd = speakingtot / voicedcount
    if voicedcount != 0:
        asd = speakingtot / voicedcount
    else:
        # Handle the case when the denominator is zero
        # You can assign a default value or take any other appropriate action
        print("handling 0 voiced count --> check file")
        asd = 0
    speechrate_dictionary = {
        "tot_name": filename,
        "nsyll": voicedcount,
        "npause": npause,
        "dur(s)": originaldur,
        "phonationtime(s)": intensity_duration,
        "speechrate(nsyll / dur)": speakingrate,
        "articulation_rate(nsyll/phonationtime)": articulationrate,
        "average_syllable_dur(speakingtime/nsyll)": asd,
    }
    return speechrate_dictionary


if __name__ == "__main__":
    adv_speech_metrics("Preprocessed 2157/71254-05-01-2025_21_08_45_preprocessed.wav")
