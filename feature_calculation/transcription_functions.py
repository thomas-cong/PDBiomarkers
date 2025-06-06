import os

import whisper
import json

model = whisper.load_model("base.en")

def transcribe_audio(audio_path):    
    '''
    Transcribe audio with word timestamps
    '''
    transcribed_audio = model.transcribe(audio_path)
    text_dir = audio_path.split("/")
    text_dir[-2] = "Text Files"
    del text_dir[-1]
    text_dir = "/".join(text_dir)
# Create the Text Files directory if it doesn't exist
    os.makedirs(text_dir, exist_ok=True)
    text_file_folder = text_dir

    # Extract just the filename without path and extension
    filename = os.path.basename(audio_path).replace('.wav', '')

    # Create the text file in the text file folder
    with open(os.path.join(text_file_folder, filename + '.txt'), 'w') as f:
        f.write(transcribed_audio['text'])
    print(f"Text data saved to {text_file_folder}")
    return os.path.join(text_file_folder, filename + '.txt')

def align_audio(audio_path):
    '''
    Align audio with word timestamps
    '''
    # Create the Alignment Files directory if it doesn't exist
    align_dir = audio_path.split("/")
    align_dir[-2] = "Alignment Files"
    del align_dir[-1]
    align_dir = "/".join(align_dir)
    os.makedirs(align_dir, exist_ok=True)
    result = model.transcribe(audio_path, word_timestamps=True)
    segments = result["segments"]
    with open(os.path.join(align_dir, os.path.basename(audio_path).replace('.wav', '') + '.json'), "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    print(f"Alignment data saved to {align_dir}")

import re

def count_syllables(word):
    '''
    Count syllables in a word grammatically (not sound peaks)
    '''
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
    '''
    Calculate interword pauses from a list of segments
    '''
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
    '''
    Calculate average syllable duration from a list of segments
    '''
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
    '''
    Calculate speech rate from a list of segments
    by='syllable' or 'word'
    '''
    total_syllables = 0
    total_words = 0
    total_speaking_time = 0
    for segment in segments:
        for word in segment['words']:
            total_words += 1
            total_syllables += count_syllables(word['word'])
            total_speaking_time += word['end'] - word['start']
            # total speaking time skips pauses, by just taking the sum of word time lengths
    if by == 'syllable':
        return total_syllables / total_speaking_time if total_speaking_time > 0 else 0
    else:
        return total_words / total_speaking_time if total_speaking_time > 0 else 0