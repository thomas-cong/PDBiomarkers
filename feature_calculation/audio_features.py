import parselmouth
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from scipy.spatial import ConvexHull

'''
Given an audio path, extract formant data using parselmouth
'''
def extract_formants(audio_path, time_step = 0.05, max_number_of_formants = 5):
    try:
        sound = parselmouth.Sound(audio_path)
        formant_contour = sound.to_formant_burg(time_step = time_step, max_number_of_formants = max_number_of_formants)
        return formant_contour
    except Exception as e:
        raise Exception("Failed to extract formants from audio file: " + audio_path)

'''
Given a frequency in Hz, convert it to Bark scale
'''
def bark_transform(hz):
    bark = ((26.81*hz)/(1960+hz)) - 0.53
    if bark < 2.0:
        return bark + 0.15*(2-bark)
    else:
        return bark + 0.22*(bark-20.1)

'''
Given an audio path, generate a dataframe with bark formant data, and hz valued data (removing outliers)
'''
def generate_formant_data(audio_path):
    # Extract formant data into a table
    formant_contour = extract_formants(audio_path, time_step = 0.01)
    times = np.arange(formant_contour.start_time, formant_contour.end_time, formant_contour.time_step)

    data = {
        'Time(s)': times,
        'F1(Hz)': [formant_contour.get_value_at_time(1, t) for t in times],
        'F2(Hz)': [formant_contour.get_value_at_time(2, t) for t in times],
    }
    raw_formant_df = pd.DataFrame(data)
    # get timestamps with full formant data
    full_formant_df = raw_formant_df[(raw_formant_df["F2(Hz)"] > 0) & (raw_formant_df["F1(Hz)"] > 0)]
    bark_transformed_df = full_formant_df.copy()
    bark_transformed_df["F1(Bark)"] = bark_transformed_df["F1(Hz)"].map(bark_transform)
    bark_transformed_df["F2(Bark)"] = bark_transformed_df["F2(Hz)"].map(bark_transform)
    bark_transformed_df.drop(["F1(Hz)", "F2(Hz)"], axis=1, inplace=True)
    bark_transformed_df.reset_index(drop=True, inplace=True)

    gmm = GaussianMixture(n_components=6, covariance_type='full', random_state=42)
    gmm.fit(bark_transformed_df[["F1(Bark)", "F2(Bark)"]])
    log_probs = pd.DataFrame(gmm.score_samples(bark_transformed_df[["F1(Bark)", "F2(Bark)"]]), columns=['log_prob'])
    log_probs["Time(s)"] = bark_transformed_df["Time(s)"]
    iqr = log_probs['log_prob'].quantile(0.75) - log_probs['log_prob'].quantile(0.25)
    q1 = log_probs['log_prob'].quantile(0.25)
    inliers = log_probs[log_probs["log_prob"] > q1 - 1.5 * iqr]
    
    inlying_bark_data = bark_transformed_df[bark_transformed_df["Time(s)"].isin(inliers["Time(s)"])].reset_index(drop=True)
    inlying_hz_data = full_formant_df[full_formant_df["Time(s)"].isin(inliers["Time(s)"])].reset_index(drop=True)

    inlying_data = pd.merge(inlying_bark_data, inlying_hz_data, on='Time(s)', suffixes=('_bark', '_hz'))

    return inlying_data

'''
Given a dataframe with only bark formant data, calculate the AAVS (Standard Deviation of the Covariance Matrix)
'''
def calculate_aavs(data):
    cov_matrix = np.cov(data, rowvar=False)
    det_cov = np.linalg.det(cov_matrix)
    sgv = np.sqrt(det_cov)
    return sgv

'''
Given a dataframe with only bark formant data, calculate the hull area of the clusters
'''
def calculate_hull_area(data):
    kmeans = KMeans(n_clusters = 6, random_state = 0, n_init="auto")
    kmeans.fit(data)
    centers = kmeans.cluster_centers_
    hull = ConvexHull(centers)
    return hull.volume

'''
Given audio files, calculate their fundamental frequency (mean, median, std, min, max)
'''
def calculate_fundamental_frequency(audio_path):
    sound = parselmouth.Sound(audio_path)
    pitch = sound.to_pitch()
    frequencies = pitch.selected_array['frequency']
    voiced_frequencies = frequencies[frequencies > 0]
    return [np.mean(voiced_frequencies), np.median(voiced_frequencies), np.std(voiced_frequencies), np.min(voiced_frequencies), np.max(voiced_frequencies)]

'''
Given audio files, calculate their intensity (mean, median, std, min, max)
'''
def calculate_intensity(audio_path):
    sound = parselmouth.Sound(audio_path)
    intensity = sound.to_intensity()
    return [np.mean(intensity), np.median(intensity), np.std(intensity), np.min(intensity), np.max(intensity)]
