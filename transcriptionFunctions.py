import os
# import requests
import whisper
import json


model = whisper.load_model("base")

def transcribe_audio(audio_path):    
    transcribed_audio = model.transcribe(audio_path)
    # Assuming you have a variable for the text file folder
    text_file_folder = "./Text Files"

    # Extract just the filename without path and extension
    filename = os.path.basename(audio_path).replace('.wav', '')

    # Create the text file in the text file folder
    with open(os.path.join(text_file_folder, filename + '.txt'), 'w') as f:
        f.write(transcribed_audio['text'])

def align_audio(audio_path, output_path="alignment.json"):
    result = model.transcribe(audio_path, word_timestamps=True)
    segments = result["segments"]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    print(f"Alignment data saved to {output_path}")

import re

def count_syllables(word):
    # Simple heuristic for English
    word = word.lower()
    word = re.sub(r'[^a-z]', '', word)
    vowels = 'aeiouy'
    syllables = re.findall(r'[aeiouy]+', word)
    count = len(syllables)
    # Adjust for silent 'e'
    if word.endswith('e') and not word.endswith('le') and count > 1:
        count -= 1
    return max(1, count)

def calculate_interword_pauses(segments):
    pauses = []
    prev_end = None
    for segment in segments:
        for word in segment['words']:
            if prev_end is not None:
                pause = word['start'] - prev_end
                pauses.append(pause)
            prev_end = word['end']
    return pauses

def average_syllable_duration(segments):
    total_syllables = 0
    total_duration = 0.0
    for segment in segments:
        for word in segment['words']:
            syllables = count_syllables(word['word'])
            duration = word['end'] - word['start']
            total_syllables += syllables
            total_duration += duration
    return total_duration / total_syllables if total_syllables > 0 else 0

def speech_rate(segments, by='syllable'):
    # by='syllable' or 'word'
    total_syllables = 0
    total_words = 0
    start_time = None
    end_time = None
    for segment in segments:
        for idx, word in enumerate(segment['words']):
            if start_time is None:
                start_time = word['start']
            end_time = word['end']
            total_words += 1
            total_syllables += count_syllables(word['word'])
    total_time = end_time - start_time if start_time is not None and end_time is not None else 0
    if by == 'syllable':
        return total_syllables / total_time if total_time > 0 else 0
    else:
        return total_words / total_time if total_time > 0 else 0