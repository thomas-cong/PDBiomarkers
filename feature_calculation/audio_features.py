import parselmouth
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from scipy.spatial import ConvexHull
from parselmouth.praat import call
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.signal import lfilter
import librosa
import warnings


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
    sound = parselmouth.Sound(audio_path)
    formant = sound.to_formant_burg()
    n_frames = formant.get_number_of_frames()
    times = [formant.get_time_from_frame_number(i + 1) for i in range(n_frames)]
    f1 = [formant.get_value_at_time(1, t) for t in times]
    f2 = [formant.get_value_at_time(2, t) for t in times]
    raw_formant_df = pd.DataFrame({"Time(s)": times, "F1(Hz)": f1, "F2(Hz)": f2})
    # get timestamps with full formant data
    full_formant_df = raw_formant_df[(raw_formant_df["F2(Hz)"] > 0) & (raw_formant_df["F1(Hz)"] > 0)]
    bark_transformed_df = full_formant_df.copy()
    bark_transformed_df["F1(Bark)"] = bark_transformed_df["F1(Hz)"].map(bark_transform)
    bark_transformed_df["F2(Bark)"] = bark_transformed_df["F2(Hz)"].map(bark_transform)
    bark_transformed_df.drop(["F1(Hz)", "F2(Hz)"], axis=1, inplace=True)
    bark_transformed_df.reset_index(drop=True, inplace=True)
    gmm = GaussianMixture(n_components=12, covariance_type='full', random_state=42)
    gmm.fit(bark_transformed_df[["F1(Bark)", "F2(Bark)"]])
    log_probs = pd.DataFrame(gmm.score_samples(bark_transformed_df[["F1(Bark)", "F2(Bark)"]]), columns=['log_prob'])
    log_probs["Time(s)"] = bark_transformed_df["Time(s)"]
    iqr = log_probs['log_prob'].quantile(0.75) - log_probs['log_prob'].quantile(0.25)
    q1 = log_probs['log_prob'].quantile(0.25)
    inliers = log_probs[log_probs["log_prob"] > q1 - 1.5 * iqr]
    
    inlying_bark_data = bark_transformed_df[bark_transformed_df["Time(s)"].isin(inliers["Time(s)"])].reset_index(drop=True)
    inlying_hz_data = full_formant_df[full_formant_df["Time(s)"].isin(inliers["Time(s)"])].reset_index(drop=True)

    inlying_data = pd.merge(inlying_bark_data, inlying_hz_data, on='Time(s)', suffixes=('_bark', '_hz'))
    inlying_data.convert_dtypes()
    return inlying_data
'''
Given a dataframe with only formant data, calculate the AAVS (Standard Deviation of the Covariance Matrix)
'''
def calculate_aavs(data):
    cov_matrix = np.cov(data, rowvar=False)
    det_cov = np.linalg.det(cov_matrix)
    sgv = np.sqrt(det_cov)
    return sgv

'''
Given a dataframe with only formant data, calculate the hull area of the clusters
'''
def calculate_hull_area(data):
    kmeans = KMeans(n_clusters = 8, random_state = 0, n_init="auto")
    kmeans.fit(data)
    centers = kmeans.cluster_centers_
    hull = ConvexHull(centers)
    return hull.volume

'''
Given parselmouth Sound, calculate their fundamental frequency (mean, median, std, min, max)
'''
def calculate_fundamental_frequency(sound, return_type = "statistics"):
    pitch = sound.to_pitch()
    frequencies = pitch.selected_array['frequency']
    voiced_frequencies = frequencies[frequencies > 0]
    # average fundamental frequency (estimate of pitch over time)
    if return_type == "statistics":
        return [np.mean(voiced_frequencies), np.median(voiced_frequencies), np.std(voiced_frequencies), np.min(voiced_frequencies), np.max(voiced_frequencies)]
    elif return_type == "frequencies":
        return voiced_frequencies
    else:
        raise ValueError("Invalid return type")

'''
Given parselmouth Sound, calculate their intensity (mean, median, std, min, max)
'''
def calculate_intensity(sound):
    intensity = sound.to_intensity()
    # average intensity (estimate of amplitude over time)
    return [np.mean(intensity), np.median(intensity), np.std(intensity), np.min(intensity), np.max(intensity)]
'''
Given parselmouth Sound, calculate the harmonicity (mean, median, std, min, max)
'''
def calculate_harmonicity(sound):
    harmonicity = call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
    # harmonic (voiced speech) to noise ratio
    mean = call(harmonicity, "Get mean", 0,0)
    std = call(harmonicity, "Get standard deviation", 0,0)
    min_val = call(harmonicity, "Get minimum", 0,0, "parabolic")
    max_val = call(harmonicity, "Get maximum", 0,0, "parabolic")
    return [mean, std, min_val, max_val]

def calculate_shimmer(sound):
    '''
    Given parselmouth Sound, calculate their shimmer
    Shimmer: represents the change in loudness of each period
    Period: duration of one complete cycle of a soundwave
    '''
    max_freq = calculate_fundamental_frequency(sound)[-1]
    min_freq = calculate_fundamental_frequency(sound)[-2]
    point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", min_freq, max_freq)
    # parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 
    # minimum_pitch, 
    # maximum_period, 
    # maximum_period_factor, 
    # maximum_amplitude_factor, 
    # minimum_amplitude, 
    # maximum_amplitude, 
    # maximum_silence
    # average difference in amplitude between consecutive periods/average amplitude
    localShimmer =  call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    # average difference in amplitude between consecutive periods (absolute)
    localdbShimmer = call([sound, point_process], "Get shimmer (local_dB)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    # Amplitude pertubation quotient over 3 periods (period and its two neighbors) / average amplitude
    apq3Shimmer = call([sound, point_process], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    # Amplitude pertubation quotient over 5 periods (period and its four neighbors) / average amplitude
    aqpq5Shimmer = call([sound, point_process], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    return [localShimmer, localdbShimmer, apq3Shimmer, aqpq5Shimmer]

    
def calculate_jitter(sound):
    '''
    Given parselmouth Sound, calculate jitter features.
    Jitter: represents the change in duration of each period.
    Period: duration of one complete cycle of a soundwave.
    '''
    max_freq = calculate_fundamental_frequency(sound)[-1]
    min_freq = calculate_fundamental_frequency(sound)[-2]
    point_process = call(sound, "To PointProcess (periodic, cc)", min_freq, max_freq)
    # Jitter metrics are called on the PointProcess object, not [sound, point_process]
    # Praat signature: (time range start [s], time range end [s], min period [s], max period [s], max period factor)
    # Defaults: 0, 0, 0.0001, 0.02, 1.3
    jitter_local = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    # average difference in period duration between consecutive periods / average period duration
    jitter_local_absolute = call(point_process, "Get jitter (local, absolute)", 0, 0, 0.0001, 0.02, 1.3)
    # average absolute difference in period duration (in seconds)
    jitter_rap = call(point_process, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
    # relative average perturbation (mean diff with two neighbors)
    jitter_ppq5 = call(point_process, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
    # five-point period perturbation quotient (mean diff with four neighbors)
    return [jitter_local, jitter_local_absolute, jitter_rap, jitter_ppq5]
def calculate_mfcc(sound):
    mfcc = sound.to_mfcc(number_of_coefficients=13)
    mfcc_matrix = mfcc.to_array().T
    if np.any(np.isnan(mfcc_matrix)):
        print("Warning: MFCC matrix contains NaN values!")
    if np.any(np.isinf(mfcc_matrix)):
        print("Warning: MFCC matrix contains Inf values!")
    if np.any(np.abs(mfcc_matrix) > 1e6):
        print("Warning: MFCC matrix contains extremely large values!")
    return np.mean(mfcc_matrix, axis=0), np.std(mfcc_matrix, axis=0), np.min(mfcc_matrix, axis=0), np.max(mfcc_matrix, axis=0)
def calculate_ppe(sound):
    '''
    Reference:github.com/Mak-Sim/Troparion/blob/5126f434b96e0c1a4a41fa99dd9148f3c959cfac/Perturbation_analysis/pitch_period_entropy.m
    '''
    f0_mean = calculate_fundamental_frequency(sound)[0]
    f_min = f0_mean / np.sqrt(2)
    frequencies = calculate_fundamental_frequency(sound, "frequencies")
    ratio_frequencies = np.array(frequencies/f_min)
    semitone_frequencies = np.log(ratio_frequencies)/np.log(2**(1/12))
    a = librosa.lpc(semitone_frequencies, order=2)
    semitone_filtered = lfilter(a, [1], semitone_frequencies)
    semitone_filtered = semitone_filtered[5:]

    r = np.linspace(-1.5, 1.5, 3)
    hist, bin_edges = np.histogram(semitone_filtered, bins=r)
    dpd = hist/len(semitone_filtered)

    PPE = -np.sum(dpd[dpd != 0] * np.log2(dpd[dpd != 0]))
    return PPE

def calculate_interword_pauses(sound):
    try:
        intensity = sound.to_intensity()
        textgrid = call(intensity, "To TextGrid (silences)",  -16, 0.1, 0.1, "silent", "sounding")
        silencetier = call(textgrid, "Extract tier", 1)
        silencetable = call(silencetier, "Down to TableOfReal", "silent")
        npauses = call(silencetable, "Get number of rows")
        pause_durations = []
        for ipause in range(npauses):
            pause = ipause + 1
            begin = call(silencetable, "Get value", pause, 1)
            end = call(silencetable, "Get value", pause, 2)
            pause_durations.append(end - begin)
        std_pause_durations = np.std(pause_durations)
        pause_durations_inlying = [x for x in pause_durations if x < std_pause_durations * 3]
        mean = np.mean(pause_durations_inlying)
        return mean
    except:
        print("No silence detected in audio file, returning 0")
        return 0

def calculate_audio_features(audio_path):
    sound = parselmouth.Sound(audio_path)
    data = {}
    data['fundamental_frequency'] = calculate_fundamental_frequency(sound)
    data["intensity"] = calculate_intensity(sound)
    data['harmonicity'] = calculate_harmonicity(sound)
    data['shimmer'] = calculate_shimmer(sound)
    data['jitter'] = calculate_jitter(sound)
    data['ppe'] = calculate_ppe(sound)
    data['avg_pause_duration'] = calculate_interword_pauses(sound)
    # Check for NaNs or infs in feature dict
    for k, v in data.items():
        if isinstance(v, (list, np.ndarray)):
            if np.any(np.isnan(v)):
                print(f"Warning: Feature '{k}' contains NaN values!")
            if np.any(np.isinf(v)):
                print(f"Warning: Feature '{k}' contains Inf values!")
    return data
    

if __name__ == "__main__":
    audio_path = "/Users/thomas.cong/Downloads/ResearchCode/MDVR-KCL/ReadText/PD/ID07_pd_2_0_0.wav"
    data = calculate_audio_features(audio_path)
    print(data)
