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

    # Create figure and axis with GridSpec for better layout control
    fig = plt.figure(figsize=(10, 10), dpi=300)
    gs = plt.GridSpec(1, 2, width_ratios=[20, 1], wspace=0.1)
    ax = fig.add_subplot(gs[0])
    cbar_ax = fig.add_subplot(gs[1])

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
        cbar_ax=cbar_ax,
        cbar_kws={"label": "Correlation"}
    )
    
    # Adjust layout
    plt.tight_layout()
    plt.show()

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

    # Create figure and axis with GridSpec
    fig = plt.figure(figsize=(10, 10), dpi=300)
    gs = plt.GridSpec(1, 2, width_ratios=[20, 1], wspace=0.1)
    ax = fig.add_subplot(gs[0])
    cbar_ax = fig.add_subplot(gs[1])

    # Create heatmap
    sns.heatmap(
        df,
        cmap="coolwarm",
        square=True,
        ax=ax,
        cbar_ax=cbar_ax,
        cbar_kws={"label": "Z-Score"}
    )
    
    # Adjust layout
    plt.tight_layout()
    plt.show()

    return fig