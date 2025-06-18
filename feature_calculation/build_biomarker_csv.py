
import os
import ssl
import json
import pydub
import pyfoal
import parselmouth
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from praatio import textgrid
from feature_calculation import text_features
from feature_calculation import audio_features
from audio_preprocessing import audio_preprocessing
from feature_calculation import transcription_functions
ssl._create_default_https_context = ssl._create_unverified_context

def calculate_vai(audio_path, text_path):
    snd = parselmouth.Sound(audio_path)
    tg = textgrid.openTextgrid(text_path, False)
    phone_tier  = tg.tiers[0]

    corner_vowels = {'i', 'u', 'æ', 'ɑ'}
    formant_dict = {v:[] for v in corner_vowels}

    for entry in phone_tier.entries:
        label = entry.label.lower()
        if label in corner_vowels:
            start, end = entry.start, entry.end
            mid_time = (start + end) / 2
            formant = snd.to_formant_burg()
            times = np.linspace(start, end, 10)
            f1_vals = [formant.get_value_at_time(1, time) for time in times]
            f2_vals = [formant.get_value_at_time(2, time) for time in times]
            f1 = np.nanmean(f1_vals)
            f2 = np.nanmean(f2_vals)
            formant_dict[label].append((f1, f2))
    avg_formants = {v:np.mean(formant_dict[v], axis=0) if formant_dict[v] else None for v in corner_vowels }
    calculate_vai = True
    VAI = None
    for v in avg_formants:
        if avg_formants[v] is None:
            calculate_vai = False
    if calculate_vai:
        VAI = (avg_formants['i'][1] - avg_formants['ɑ'][0]) / (avg_formants['u'][1] + avg_formants['ɑ'][1] + avg_formants['u'][0] + avg_formants['i'][0])
    return VAI
def build_text_grids(audio_dir, text_dir):
    texts = sorted([text_dir + "/" + x for x in os.listdir(text_dir) if "preprocessed" in x])
    audios = sorted([audio_dir + "/" + x for x in os.listdir(audio_dir) if "preprocessed" in x])
    outputs = []
    os.makedirs(text_dir, exist_ok=True)
    for x in os.listdir(text_dir):
        if "preprocessed" in x:
            outputs.append(text_dir + "/" + x.replace("preprocessed", "alignment").replace(".txt", ".TextGrid"))
    outputs = sorted(outputs)
    texts = [Path(x) for x in texts]
    audios = [Path(x) for x in audios]
    outputs = [Path(x) for x in outputs]
    alignment = pyfoal.from_files_to_files(texts, audios, outputs, aligner='mfa')
    return None

def process_audio_file(audio_path, write_preprocess_dir = None):
    """
    Process a single audio file and extract all metrics
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dictionary containing all metrics for the audio file
    """
    # Get filename without extension for CSV row label
    filename = os.path.basename(audio_path).replace('.wav', '')
    
    # Create a dictionary to store metrics
    metrics = {'filename': filename}
    
    # Preprocess the audio file
    audioSeg = pydub.AudioSegment.from_file(audio_path, format="wav")
    audioSeg = audio_preprocessing.trim_leading_and_lagging_silence(audioSeg)

    if audioSeg.duration_seconds < 0.5:
        print(f"Audio file {filename} is too short, skipping...")
        return None
    # Create a temporary trimmed file path
    if write_preprocess_dir is not None:
        os.makedirs(write_preprocess_dir, exist_ok=True)
        preprocessed_path = os.path.join(write_preprocess_dir, f"{filename}_preprocessed.wav")
        audioSeg.export(preprocessed_path, format="wav")
    else:
        preprocessed_path = os.path.join(os.path.dirname(audio_path), f"{filename}_preprocessed.wav")
        audioSeg.export(preprocessed_path, format="wav")
    text_path = transcription_functions.transcribe_audio(preprocessed_path)    

    # TODO: CHECK THE ALIGNMENT OF FUNCTION INDEXING
    try:
        # Get alignment data
        alignment_path = preprocessed_path.split("/")
        alignment_path[-2] = "Alignment Files"
        alignment_path = "/".join(alignment_path)
        alignment_path = alignment_path.replace(".wav", ".json")
        transcription_functions.align_audio(preprocessed_path)
        
        # Load the alignment data
        with open(alignment_path, "r", encoding="utf-8") as f:
            segments = json.load(f)
        
        # Calculate metrics from transcription_functions
        # Extract formant data and calculate AAVS and hull area
        formant_data = audio_features.generate_formant_data(preprocessed_path)
        hz_data = formant_data[["F1(Hz)", "F2(Hz)"]]
        metrics['aavs'] = audio_features.calculate_aavs(hz_data)
        metrics['hull_area'] = audio_features.calculate_hull_area(hz_data)
        lexical_dict = transcription_functions.adv_speech_metrics(preprocessed_path)
        metrics['speech_rate'] = lexical_dict['speechrate(nsyll / dur)']
        metrics['articulation_rate'] = lexical_dict['articulation_rate(nsyll/phonationtime)']
        metrics['average_syllable_duration'] = lexical_dict['average_syllable_dur(speakingtime/nsyll)']

        text_feats = text_features.calculate_text_features(text_path)
        metrics['avg_word_length'] = text_feats['avg_word_length']
        metrics['content_richness'] = text_feats['content_richness']
        metrics['mattr'] = text_feats['mattr']
        metrics['phrase_patterns'] = text_feats['phrase_patterns']
        metrics['sentence_length'] = text_feats['sentence_length']

        audio_feats = audio_features.calculate_audio_features(preprocessed_path)
        metrics['avg_pause_duration'] = audio_feats['avg_pause_duration']
        metrics['ff_mean'] = audio_feats['fundamental_frequency'][0]
        metrics['ff_median'] = audio_feats['fundamental_frequency'][1]
        metrics['ff_std'] = audio_feats['fundamental_frequency'][2]
        metrics['ff_min'] = audio_feats['fundamental_frequency'][3]
        metrics['ff_max'] = audio_feats['fundamental_frequency'][4]
        metrics['inten_mean'] = audio_feats['intensity'][0]
        metrics['inten_median'] = audio_feats['intensity'][1]
        metrics['inten_std'] = audio_feats['intensity'][2]
        metrics['inten_min'] = audio_feats['intensity'][3]
        metrics['inten_max'] = audio_feats['intensity'][4]
        metrics['harm_mean'] = audio_feats['harmonicity'][0]
        metrics['harm_std'] = audio_feats['harmonicity'][1]
        metrics['harm_min'] = audio_feats['harmonicity'][2]
        metrics['harm_max'] = audio_feats['harmonicity'][3]
        metrics['shimmer_local'] = audio_feats['shimmer'][0]
        metrics['shimmer_local_db'] = audio_feats['shimmer'][1]
        metrics['shimmer_apq3'] = audio_feats['shimmer'][2]
        metrics['shimmer_apq5'] = audio_feats['shimmer'][3]
        metrics['jitter_local'] = audio_feats['jitter'][0]
        metrics['jitter_local_db'] = audio_feats['jitter'][1]
        metrics['jitter_apq3'] = audio_feats['jitter'][2]
        metrics['jitter_apq5'] = audio_feats['jitter'][3]
        metrics['ppe'] = audio_feats['ppe']
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        with open("./feature_list.txt", "r") as f:
            feature_list = f.read().splitlines()
        # Fill missing metrics with None
        for metric in feature_list:
            if metric not in metrics:
                metrics[metric] = None
        
    return metrics

def build_csv(csv_path, audio_files=None, audio_dir=None, write_preprocess_dir = None):

    """
    Generate a CSV file with metrics from transcriptionFunctions and formantExtraction
    
    Args:
        csv_path: Path to save the CSV file
        audio_files: List of audio file paths to process (optional)
        audio_dir: Directory containing audio files to process (optional)
        
    If both audio_files and audio_dir are provided, audio_files takes precedence.
    If neither is provided, the function will look for .wav files in the 'Audio Files' directory.
    """
    # Determine which audio files to process
    if audio_files is None:
        if audio_dir is None:
            # Default to 'Audio Files' directory
            audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Audio Files')
        
        # Get all .wav files in the directory
        audio_files = [os.path.join(audio_dir, f) for f in os.listdir(audio_dir) 
                      if f.endswith('.wav') and not f.endswith('_preprocessed.wav') and not f.endswith('_temp_preprocessed.wav')]
    # Process each audio file
    all_metrics = {}
    for audio_path in tqdm(audio_files):
        metrics = process_audio_file(audio_path, write_preprocess_dir)
        if metrics:
            # Always use base filename (no .wav, no _preprocessed)
            base_key = os.path.basename(audio_path).replace('.wav', '').replace('_preprocessed', '')
            all_metrics[base_key] = metrics
    # get text directory
    text_dir = audio_files[0].split("/")
    text_dir[-2] = "Text Files"
    del text_dir[-1]
    text_dir = "/".join(text_dir)
    # build text grids
    build_text_grids(audio_dir, text_dir)
    # calculate textgrid dependent features
    if write_preprocess_dir is None:
        preprocessed_dir = audio_dir
    else:
        preprocessed_dir = write_preprocess_dir
    preprocessed_files = [os.path.join(preprocessed_dir, f) for f in os.listdir(preprocessed_dir) if f.endswith('.wav')]
    for audio_path in tqdm(preprocessed_files):
        if "preprocessed" not in audio_path:
            continue
        tg_path = os.path.join(text_dir, os.path.basename(audio_path).replace('_preprocessed.wav', '_alignment.TextGrid'))
        base_key = os.path.basename(audio_path).replace('.wav', '').replace('_preprocessed', '')
        if base_key in all_metrics:
            all_metrics[base_key]['vai'] = calculate_vai(audio_path, tg_path)
        else:
            print(f"Warning: base_key {base_key} not found in all_metrics for VAI assignment.")

    # Create DataFrame and save to CSV
    print(all_metrics)
    if all_metrics:
        df = pd.DataFrame.from_dict(all_metrics, orient='index').reset_index()
        df = df.rename(columns={'index': 'filename'})
        
        # Check if CSV exists
        if os.path.exists(csv_path):
            # If CSV exists, read it and append new data
            # Remove any rows with filenames that match the new data
            existing_df = existing_df[~existing_df['filename'].astype(str).str.strip().isin(df['filename'].astype(str).str.strip())]

            # Remove duplicate columns if any
            df = df.loc[:, ~df.columns.duplicated()]
            existing_df = existing_df.loc[:, ~existing_df.columns.duplicated()]

            # Align columns to be the same and in the same order
            for col in df.columns:
                if col not in existing_df.columns:
                    existing_df[col] = None
            for col in existing_df.columns:
                if col not in df.columns:
                    df[col] = None
            existing_df = existing_df[df.columns]

            # Append new data
            df = pd.concat([existing_df, df], ignore_index=True)

            # Drop duplicates by filename, keeping the last (newest) entry
            df = df.drop_duplicates(subset=['filename'], keep='last')
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
        print(f"Metrics saved to {csv_path}")
    else:
        print("No audio files were processed.")

if __name__ == "__main__":
    pass
