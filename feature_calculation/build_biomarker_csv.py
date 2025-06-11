
import os
import json
import pandas as pd
import pydub
from . import transcription_functions, audio_features, text_features
from audio_preprocessing import audio_preprocessing

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
    audioSeg = audio_preprocessing.resample(audioSeg)
    audioSeg = audio_preprocessing.trim_leading_and_lagging_silence(audioSeg)
    audioSeg = audio_preprocessing.match_target_amplitude(audioSeg, target_dBFS=-20)
    # Create a temporary trimmed file path
    if write_preprocess_dir is not None:
        os.makedirs(write_preprocess_dir, exist_ok=True)
        preprocessed_path = os.path.join(write_preprocess_dir, f"{filename}_preprocessed.wav")
        audioSeg.export(preprocessed_path, format="wav")
    else:
        preprocessed_path = os.path.join(os.path.dirname(audio_path), f"{filename}_preprocessed.wav")
        audioSeg.export(preprocessed_path, format="wav")
    text_path = transcription_functions.transcribe_audio(preprocessed_path)
    print(f"Preprocessed audio saved to {preprocessed_path}")
    
    try:
        # Get alignment data
        alignment_path = preprocessed_path.split("/")
        alignment_path[-2] = "Alignment Files"
        alignment_path = "/".join(alignment_path)
        alignment_path = alignment_path.replace(".wav", ".json")
        print("Alignment_Path: ", alignment_path)
        transcription_functions.align_audio(preprocessed_path)
        
        # Load the alignment data
        with open(alignment_path, "r", encoding="utf-8") as f:
            segments = json.load(f)
        
        # Calculate metrics from transcription_functions
        interword_pauses = transcription_functions.calculate_interword_pauses(segments)
        avg_pause_duration = sum(interword_pauses) / len(interword_pauses) if interword_pauses else 0
        # Extract formant data and calculate AAVS and hull area
        formant_data = audio_features.generate_formant_data(preprocessed_path)
        bark_formant_data = formant_data[["F1(Bark)", "F2(Bark)"]]
        metrics['aavs'] = audio_features.calculate_aavs(bark_formant_data)
        metrics['hull_area'] = audio_features.calculate_hull_area(bark_formant_data)
        lexical_dict = transcription_functions.adv_speech_metrics(preprocessed_path)
        metrics['speech_rate'] = lexical_dict['speechrate(nsyll / dur)']
        metrics['articulation_rate'] = lexical_dict['articulation_rate(nsyll/phonationtime)']
        metrics['average_syllable_duration'] = lexical_dict['average_syllable_dur(speakingtime/nsyll)']
        
        ff = audio_features.calculate_fundamental_frequency(preprocessed_path)
        metrics['ff_mean'] = ff[0]
        metrics['ff_median'] = ff[1]
        metrics['ff_std'] = ff[2]
        metrics['ff_min'] = ff[3]
        metrics['ff_max'] = ff[4]
        inten = audio_features.calculate_intensity(preprocessed_path)
        metrics['inten_mean'] = inten[0]
        metrics['inten_median'] = inten[1]
        metrics['inten_std'] = inten[2]
        metrics['inten_min'] = inten[3]
        metrics['inten_max'] = inten[4]
        harm = audio_features.calculate_harmonicity(preprocessed_path)
        metrics['harm_mean'] = harm[0]
        metrics['harm_std'] = harm[1]
        metrics['harm_min'] = harm[2]
        metrics['harm_max'] = harm[3]

        metrics['avg_word_length'] = text_features.avg_word_length(text_path)
        metrics['avg_syllables_per_word'] = text_features.avg_syllables_per_word(text_path)
        shimmer = audio_features.calculate_shimmer(preprocessed_path)
        metrics['shimmer_local'] = shimmer[0]
        metrics['shimmer_local_db'] = shimmer[1]
        metrics['shimmer_apq3'] = shimmer[2]
        metrics['shimmer_apq5'] = shimmer[3]
        jitter = audio_features.calculate_jitter(preprocessed_path)
        metrics['jitter_local'] = jitter[0]
        metrics['jitter_local_db'] = jitter[1]
        metrics['jitter_apq3'] = jitter[2]
        metrics['jitter_apq5'] = jitter[3]
        number_of_coeffecients = 13
        for x in range(number_of_coeffecients):
            mfcc_calculation = audio_features.calculate_mfcc(preprocessed_path)
            metrics[f'mfcc_{x}_mean'] = mfcc_calculation[0][x]
            metrics[f'mfcc_{x}_std'] = mfcc_calculation[1][x]
            metrics[f'mfcc_{x}_min'] = mfcc_calculation[2][x]
            metrics[f'mfcc_{x}_max'] = mfcc_calculation[3][x]
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        with open("feature_list.txt", "r") as f:
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
    all_metrics = []
    for audio_path in audio_files:
        print(f"Processing {os.path.basename(audio_path)}...")
        metrics = process_audio_file(audio_path, write_preprocess_dir)
        all_metrics.append(metrics)
    
    # Create DataFrame and save to CSV
    if all_metrics:
        df = pd.DataFrame(all_metrics)
        
        # Check if CSV exists
        if os.path.exists(csv_path):
            # If CSV exists, read it and append new data
            existing_df = pd.read_csv(csv_path)
            
            # Remove any rows with filenames that match the new data
            existing_df = existing_df[~existing_df['filename'].isin(df['filename'])]
            
            # Append new data
            df = pd.concat([existing_df, df], ignore_index=True)
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
        print(f"Metrics saved to {csv_path}")
    else:
        print("No audio files were processed.")

