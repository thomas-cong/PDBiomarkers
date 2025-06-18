import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


def make_boxplot(
    dataframes=None, dataframe_labels=None, feature=None, title=None, save_path=None
):
    if dataframes is None or feature is None or dataframe_labels is None:
        raise ValueError("dataframes, dataframe_labels and feature must be provided")
    if len(dataframes) != len(dataframe_labels):
        raise ValueError("dataframes and dataframe_labels must have the same length")

    data = {}
    for i, df in enumerate(dataframes):
        feature_values = df[feature]
        data[dataframe_labels[i]] = feature_values
    data = pd.DataFrame(data)
    if data.empty:
        return None

    f, ax = plt.subplots(figsize=(4, 6), dpi=300)

    # Create a custom palette based on labels
    palette = [
        "#FF4B4B" if "PD" in label.upper() else "#4B8DFF" for label in dataframe_labels
    ]

    # Create boxplot with custom colors
    ax = sns.boxplot(data=data, palette=palette)

    # Add individual data points with jitter
    sns.stripplot(data=data, color="black", alpha=0.5, jitter=0.0, size=4, ax=ax)

    # Improve the plot appearance
    ax.set_xlabel("Dataset")
    ax.set_ylabel(feature)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Add grid for better readability
    ax.grid(True, linestyle="-", alpha=0.7)
    if title is not None:
        ax.set_title(title)

    if save_path is not None:
        plt.savefig(save_path)
    plt.close()
    return f


def make_boxplot_one_df(dataframe, feature, separator_col, save_path, title=None):
    dataframes = [
        dataframe[dataframe[separator_col] == label]
        for label in sorted(dataframe[separator_col].unique())
    ]
    f = make_boxplot(
        dataframes=dataframes,
        dataframe_labels=sorted(dataframe[separator_col].unique()),
        feature=feature,
        title=title,
        save_path=save_path,
    )
    plt.close()
    return f
