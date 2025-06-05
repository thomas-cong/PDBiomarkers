import whisper
import numpy as np
import os
import torch
import pandas as pd
model = whisper.load_model("base")
def get_embeddings(audio_path, aggregation = "mean"):
    '''
    Given an audio path, return the Whisper embeddings
    audio_path: path to the audio file
    aggregation: method of aggregation, default is mean
    '''
    # Load and preprocess audio
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)

    # Get the log-mel spectrogram
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # Extract embeddings from the encoder
    with torch.no_grad():
        # Get the encoder output (embeddings)
        embeddings = model.encoder(mel.unsqueeze(0))
        embeddings_np = embeddings.cpu().numpy().squeeze()
    if aggregation == "mean":
        return np.mean(embeddings_np, axis=0)
    elif aggregation == "max":
        return np.max(embeddings_np, axis=0)
    elif aggregation == "min":
        return np.min(embeddings_np, axis=0)
    elif aggregation == "median":
        return np.median(embeddings_np, axis=0)
    else:
        raise ValueError("Invalid aggregation method")
def create_embedding_df(audio_dir, aggregation = "mean"):
    '''
    Given an audio directory, that are preprocessed
    (requires 'preprocessed' in filename), return a dataframe of the Whisper embeddings
    audio_dir: directory of the audio files
    aggregation: method of aggregation, default is mean
    '''
    audio_files = [os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith('.wav') and "preprocessed" in f]
    embeddings = [get_embeddings(audio_file, aggregation) for audio_file in audio_files]
    df = pd.DataFrame(embeddings, columns=[f"embedding_{i}" for i in range(len(embeddings[0]))])
    df['filename'] = [os.path.basename(audio_file) for audio_file in audio_files]
    df['filename'] = df['filename'].str.replace("_preprocessed.wav", "")
    return df
