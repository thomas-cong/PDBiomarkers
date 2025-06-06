import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from . import data_preprocessing

def correlation_heatmap(df, method="pearson", feature_axis=1):
    '''
    Given a dataframe, return a heatmap of the correlation matrix
    df: dataframe
    method: correlation method, default is pearson
    feature_axis: axis to calculate pairwise correlation, default is 1 (columns)
    '''
    if feature_axis == 1:
        correlation_matrix = df.corr(method=method)
    elif feature_axis == 0:
        correlation_matrix = df.corr(method=method, axis=0)

    # Create figure and axis with adjusted figsize to account for labels
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    
    # Mask to show only the bottom triangle
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))

    # Create heatmap
    sns.heatmap(
        correlation_matrix,
        mask=mask,
        annot=False,
        cmap="coolwarm",
        ax=ax,
        square=True,
        cbar_kws={"label": "Correlation", "shrink": 0.8}
    )
    
    # Precise subplot adjustments instead of tight_layout
    # Increase left margin, reduce top margin
    fig.subplots_adjust(left=0.2, right=0.9, top=0.9, bottom=0.1)
    
    # Increase font size and padding of y-tick labels
    ax.tick_params(axis='y', labelsize=9, pad=5)

    return fig

def distribution_heatmap(df, feature_axis=1):
    '''
    Given a dataframe, return a heatmap of the distribution of the features
    df: dataframe
    feature_axis: axis to calculate pairwise correlation, default is 1 (columns)
    '''
    if feature_axis == 1:
        df = data_preprocessing.normalize_df(df).transpose()
    elif feature_axis == 0:
        df = data_preprocessing.normalize_df(df)

    # Create figure and axis with adjusted figsize
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    
    # Create heatmap
    sns.heatmap(
        df,
        cmap="coolwarm",
        square=True,
        ax=ax,
        cbar_kws={"label": "Z-Score", "shrink": 0.8}
    )
    
    # Precise subplot adjustments
    fig.subplots_adjust(left=0.2, right=0.9, top=0.9, bottom=0.1)
    
    # Increase font size and padding of y-tick labels
    ax.tick_params(axis='y', labelsize=9, pad=5)

    return fig