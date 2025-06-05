import pandas as pd
import warnings
import numpy as np
warnings.filterwarnings('ignore')

def normalize_df(df, feature_axis = 1):
    df_copy = df.copy()
    if feature_axis == 1:
        for col in df.columns:
            df_copy[col] = (df_copy[col] - df_copy[col].mean()) / df_copy[col].std()
    elif feature_axis == 0:
        for col in df.columns:
            df_copy[col] = (df_copy[col] - df_copy[col].mean()) / df_copy[col].std()
    return df_copy

def remove_outliers_iqr(df, feature_axis=1, threshold=1.5):
    df_copy = df.copy()
    if feature_axis == 1:
        for col in df.columns:
            Q1 = df_copy[col].quantile(0.25)
            Q3 = df_copy[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df_copy[col] = df_copy[col][(df_copy[col] >= lower_bound) & (df_copy[col] <= upper_bound)]
    elif feature_axis == 0:
        for row in df.index:
            Q1 = df_copy.loc[row, :].quantile(0.25)
            Q3 = df_copy.loc[row, :].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df_copy.loc[row, :] = df_copy.loc[row, :][(df_copy.loc[row, :] >= lower_bound) & (df_copy.loc[row, :] <= upper_bound)]
    return df_copy