
import os
import json
import pandas as pd
import transcriptionFunctions
import audioFeatures
import audioPreprocessing
import pydub

def process_audio_file(audio_path):
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
    trimmed_audio = audioPreprocessing.trimLeadingAndLaggingSilence(audioSeg)
    normalized_audio = audioPreprocessing.normalize_audio(trimmed_audio)
    # normalized_audio = trimmed_audio
    # Create a temporary trimmed file path
    preprocessed_path = os.path.join(os.path.dirname(audio_path), f"{filename}_preprocessed.wav")
    normalized_audio.export(preprocessed_path, format="wav")
    print(f"Preprocessed audio saved to {preprocessed_path}")
    
    try:
        # Get alignment data
        alignment_path = os.path.join(os.path.dirname(audio_path), f"{filename}_alignment.json")
        transcriptionFunctions.align_audio(preprocessed_path, output_path=alignment_path)
        
        # Load the alignment data
        with open(alignment_path, "r", encoding="utf-8") as f:
            segments = json.load(f)
        
        # Calculate metrics from transcriptionFunctions
        interword_pauses = transcriptionFunctions.calculate_interword_pauses(segments)
        avg_pause_duration = sum(interword_pauses) / len(interword_pauses) if interword_pauses else 0
        
        metrics['avg_syllable_duration'] = transcriptionFunctions.average_syllable_duration(segments)
        metrics['speech_rate_syllable'] = transcriptionFunctions.speech_rate(segments, by='syllable')
        metrics['speech_rate_word'] = transcriptionFunctions.speech_rate(segments, by='word')
        metrics['avg_pause_duration'] = avg_pause_duration
        ff = audioFeatures.calculateFundamentalFrequency(preprocessed_path)
        metrics['ff_mean'] = ff[0]
        metrics['ff_median'] = ff[1]
        metrics['ff_std'] = ff[2]
        metrics['ff_min'] = ff[3]
        metrics['ff_max'] = ff[4]
        inten = audioFeatures.calculateIntensity(preprocessed_path)
        metrics['inten_mean'] = inten[0]
        metrics['inten_median'] = inten[1]
        metrics['inten_std'] = inten[2]
        metrics['inten_min'] = inten[3]
        metrics['inten_max'] = inten[4]
        # Extract formant data and calculate AAVS and hull area
        formant_data = audioFeatures.generateFormantData(preprocessed_path)
        bark_formant_data = formant_data[["F1(Bark)", "F2(Bark)"]]
        
        metrics['aavs'] = audioFeatures.calculateAAVS(bark_formant_data)
        metrics['hull_area'] = audioFeatures.calculateHullArea(bark_formant_data)
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        feature_list = ['avg_syllable_duration', 'speech_rate_syllable', 'speech_rate_word', 
                      'avg_pause_duration', 'ff_mean', 'ff_median', 'ff_std', 'ff_min', 'ff_max',
                      'aavs', 'hull_area', 'inten_mean', 'inten_median', 'inten_std', 'inten_min', 'inten_max']
        # Fill missing metrics with None
        for metric in feature_list:
            if metric not in metrics:
                metrics[metric] = None
    
    finally:
        pass
        
    return metrics

def metrics_to_csv(csv_path, audio_files=None, audio_dir=None):

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
        metrics = process_audio_file(audio_path)
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

