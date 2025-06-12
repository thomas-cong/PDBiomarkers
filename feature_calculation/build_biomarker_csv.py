
import os
import json
import pandas as pd
from feature_calculation import transcription_functions
from feature_calculation import audio_features
from feature_calculation import text_features
import pydub
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
    

    # TODO: CHECK THE ALIGNMENT OF FUNCTION INDEXING
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
        metrics['average_pause_duration'] = avg_pause_duration

        text_feats = text_features.calculate_text_features(text_path)
        metrics['avg_word_length'] = text_feats['avg_word_length']
        metrics['content_richness'] = text_feats['content_richness']
        metrics['mattr'] = text_feats['mattr']
        metrics['phrase_patterns'] = text_feats['phrase_patterns']
        metrics['sentence_length'] = text_feats['sentence_length']

        audio_feats = audio_features.calculate_audio_features(preprocessed_path)
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
        number_of_coeffecients = 13
        for x in range(number_of_coeffecients):
            metrics[f'mfcc_{x}_mean'] = audio_feats['mfcc'][0][x]
            metrics[f'mfcc_{x}_std'] = audio_feats['mfcc'][1][x]
            metrics[f'mfcc_{x}_min'] = audio_feats['mfcc'][2][x]
            metrics[f'mfcc_{x}_max'] = audio_feats['mfcc'][3][x]
        metrics['ppe'] = audio_feats['ppe']
        
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

