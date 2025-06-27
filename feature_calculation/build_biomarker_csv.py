import os
import multiprocessing
import functools
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
import warnings

warnings.filterwarnings("ignore")

ssl._create_default_https_context = ssl._create_unverified_context


def calculate_vai(audio_path, grid_path):
    """
    Calculate the Vowel Articulation Index (VAI) from an audio file and its corresponding TextGrid.

    Args:
        audio_path (str): Path to the audio file.
        grid_path (str): Path to the TextGrid file.

    Returns:
        float or None: The VAI value if calculable, otherwise None. The VAI is calculated based on
                       the formant frequencies (F1 and F2) of the corner vowels 'i', 'u', 'æ', and 'ɑ'.
    """
    try:
        snd = parselmouth.Sound(audio_path)
        tg = textgrid.openTextgrid(grid_path, False)
    except:
        print(
            f"Error processing {audio_path} and {grid_path}, maybe the file was excluded?"
        )
        return None
    phone_tier = tg.tiers[0]

    corner_vowels = {"i", "u", "æ", "ɑ"}
    formant_dict = {v: [] for v in corner_vowels}

    for entry in phone_tier.entries:
        label = entry.label.lower()
        if label in corner_vowels:
            start, end = entry.start, entry.end
            mid_time = (start + end) / 2
            formant = snd.to_formant_burg()
            f1 = formant.get_value_at_time(1, mid_time)
            f2 = formant.get_value_at_time(2, mid_time)
            formant_dict[label].append((f1, f2))

    avg_formants = {
        v: np.mean(formant_dict[v], axis=0) if formant_dict[v] else None
        for v in corner_vowels
    }
    calculate_vai = True
    VAI = None
    for v in avg_formants:
        if avg_formants[v] is None:
            calculate_vai = False
    if calculate_vai:
        VAI = (avg_formants["i"][1] - avg_formants["ɑ"][0]) / (
            avg_formants["u"][1]
            + avg_formants["ɑ"][1]
            + avg_formants["u"][0]
            + avg_formants["i"][0]
        )
    return VAI


def build_text_grids(preprocessed_dir, textgrid_dir):
    """
    Generate TextGrid files for aligned audio and text pairs.
    TextGrids are written to the TextGrid subfolder in Results-.
    """
    texts = sorted(
        [
            os.path.join(
                os.path.dirname(preprocessed_dir),
                "Text",
                os.path.basename(x).replace(".wav", ".txt"),
            )
            for x in os.listdir(preprocessed_dir)
            if x.endswith("_preprocessed.wav")
        ]
    )
    audios = sorted(
        [
            os.path.join(preprocessed_dir, x)
            for x in os.listdir(preprocessed_dir)
            if x.endswith("_preprocessed.wav")
        ]
    )
    outputs = sorted(
        [
            os.path.join(
                textgrid_dir,
                os.path.basename(x).replace("_preprocessed.wav", "_alignment.TextGrid"),
            )
            for x in os.listdir(preprocessed_dir)
            if x.endswith(".wav")
        ]
    )
    texts = [Path(x) for x in texts]
    audios = [Path(x) for x in audios]
    outputs = [Path(x) for x in outputs]
    alignment = pyfoal.from_files_to_files(texts, audios, outputs, aligner="mfa")
    return None


def process_audio_file(audio_path, results_dir):
    """
    Process a single audio file and extract all metrics.
    All outputs are written into Results- subfolders.
    """
    preprocessed_dir = os.path.join(results_dir, "Preprocessed")
    text_dir = os.path.join(results_dir, "Text")
    align_dir = os.path.join(results_dir, "Alignments")
    for d in [preprocessed_dir, text_dir, align_dir]:
        os.makedirs(d, exist_ok=True)
    filename = os.path.basename(audio_path).replace(".wav", "")
    metrics = {"filename": filename}
    # Preprocess audio
    audioSeg = pydub.AudioSegment.from_file(audio_path, format="wav")
    audioSeg = audio_preprocessing.trim_leading_and_lagging_silence(audioSeg)
    if audioSeg.duration_seconds < 0.5:
        print(f"Audio file {filename} is too short, skipping...")
        return None
    preprocessed_path = os.path.join(preprocessed_dir, f"{filename}_preprocessed.wav")
    audioSeg.export(preprocessed_path, format="wav")
    # Transcribe and align
    text_path = transcription_functions.transcribe_audio(preprocessed_path, text_dir)
    try:
        alignment_path = os.path.join(align_dir, f"{filename}_preprocessed.json")
        transcription_functions.align_audio(preprocessed_path, align_dir)
        with open(alignment_path, "r", encoding="utf-8") as f:
            segments = json.load(f)
        # Calculate metrics
        formant_data = audio_features.generate_formant_data(preprocessed_path)
        hz_data = formant_data[["F1(Hz)", "F2(Hz)"]]
        metrics["AAVS"] = audio_features.calculate_aavs(hz_data)
        metrics["Hull Area (hz^2)"] = audio_features.calculate_hull_area(hz_data)
        lexical_dict = transcription_functions.adv_speech_metrics(preprocessed_path)
        metrics["Speech Rate (syll/s)"] = lexical_dict["speechrate(nsyll / dur)"]
        metrics["Articulation Rate (syll/s)"] = lexical_dict[
            "articulation_rate(nsyll/phonationtime)"
        ]
        metrics["Average Syllable Duration (ms)"] = lexical_dict[
            "average_syllable_dur(speakingtime/nsyll)"
        ]*1000
        text_feats = text_features.calculate_text_features(text_path)
        metrics["Average Word Length (chars)"] = text_feats["avg_word_length"]
        metrics["Content Richness"] = text_feats["content_richness"]
        metrics["MATTR"] = text_feats["mattr"]
        metrics["Phrase Patterns"] = text_feats["phrase_patterns"]
        metrics["Sentence Length"] = text_feats["sentence_length"]
        audio_feats = audio_features.calculate_audio_features(preprocessed_path)
        metrics["Average Pause Duration (ms)"] = audio_feats["avg_pause_duration"]*1000
        metrics["F0 Mean (hz)"] = audio_feats["fundamental_frequency"][0]
        metrics["F0 Median (hz)"] = audio_feats["fundamental_frequency"][1]
        metrics["F0 Std (hz)"] = audio_feats["fundamental_frequency"][2]
        metrics["F0 Min (hz)"] = audio_feats["fundamental_frequency"][3]
        metrics["F0 Max (hz)"] = audio_feats["fundamental_frequency"][4]
        metrics["Intensity Mean (db SPL)"] = audio_feats["intensity"][0]
        metrics["Intensity Median (db SPL)"] = audio_feats["intensity"][1]
        metrics["Intensity Std (db SPL)"] = audio_feats["intensity"][2]
        metrics["Intensity Min (db SPL)"] = audio_feats["intensity"][3]
        metrics["Intensity Max (db SPL)"] = audio_feats["intensity"][4]
        metrics["Harmonicity Mean"] = audio_feats["harmonicity"][0]
        metrics["Harmonicity Std"] = audio_feats["harmonicity"][1]
        metrics["Harmonicity Min"] = audio_feats["harmonicity"][2]
        metrics["Harmonicity Max"] = audio_feats["harmonicity"][3]
        metrics["Shimmer Local"] = audio_feats["shimmer"][0]
        metrics["Shimmer Local (db)"] = audio_feats["shimmer"][1]
        metrics["Shimmer APQ3"] = audio_feats["shimmer"][2]
        metrics["Shimmer APQ5"] = audio_feats["shimmer"][3]
        metrics["Jitter Local"] = audio_feats["jitter"][0]
        metrics["Jitter Local (db)"] = audio_feats["jitter"][1]
        metrics["Jitter APQ3"] = audio_feats["jitter"][2]
        metrics["Jitter APQ5"] = audio_feats["jitter"][3]
        metrics["Pitch Period Entropy"] = audio_feats["ppe"]
        metrics["Cepstral Peak Prominence"] = audio_feats["cpp"]
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        with open("./feature_list.txt", "r") as f:
            feature_list = f.read().splitlines()
        for metric in feature_list:
            if metric not in metrics:
                metrics[metric] = None
    return metrics


def build_csv(csv_path, audio_files=None, audio_dir=None, results_dir=None):
    """
    Generate a CSV file with metrics from transcriptionFunctions and formantExtraction.
    All outputs are written into the Results- folder with subfolders for each type.
    """
    # Set up Results- directory and subfolders
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if results_dir is None:
        results_dir = os.path.join(script_dir, "Results-")
    preprocessed_dir = os.path.join(results_dir, "Preprocessed")
    text_dir = os.path.join(results_dir, "Text")
    align_dir = os.path.join(results_dir, "Alignments")
    textgrid_dir = os.path.join(results_dir, "TextGrid")
    for d in [results_dir, preprocessed_dir, text_dir, align_dir, textgrid_dir]:
        os.makedirs(d, exist_ok=True)

    # Determine which audio files to process
    if audio_files is None:
        if audio_dir is None:
            audio_dir = os.path.join(script_dir, "Audio Files")
        audio_files = [
            os.path.join(audio_dir, f)
            for f in os.listdir(audio_dir)
            if f.endswith(".wav")
            and not f.endswith("_preprocessed.wav")
            and not f.endswith("_temp_preprocessed.wav")
        ]

    if not audio_files:
        print("No .wav files found to process.")
        return

    all_metrics = {}
    # Process each audio file in parallel
    with multiprocessing.Pool() as pool:
        process_file_with_results = functools.partial(
            process_audio_file, results_dir=results_dir
        )
        results = list(
            tqdm(
                pool.imap_unordered(process_file_with_results, audio_files),
                total=len(audio_files),
                desc="Processing audio files",
            )
        )
        for r in results:
            if r:
                all_metrics[r["filename"]] = r

    if all_metrics:
        df = pd.DataFrame.from_dict(all_metrics, orient="index").reset_index()
        df = df.rename(columns={"index": "filename"})
        df.to_csv(csv_path, index=False)
        print(f"Metrics saved to {csv_path}")
    else:
        print("No audio files were processed.")


if __name__ == "__main__":
    pass
