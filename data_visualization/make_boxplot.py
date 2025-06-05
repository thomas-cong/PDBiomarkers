import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def make_boxplot(dataframes=None, dataframe_labels=None, feature = None):
    if dataframes is None or feature is None or dataframe_labels is None:
        raise ValueError("dataframes, dataframe_labels and feature must be provided")
    if len(dataframes) != len(dataframe_labels):
        raise ValueError("dataframes and dataframe_labels must have the same length")

    
    data = {}
    for i,df in enumerate(dataframes):
        feature_values = df[feature]
        data[dataframe_labels[i]] = feature_values
    data = pd.DataFrame(data)
    f, ax = plt.subplots(figsize=(6, 6), dpi=300)
    # Create boxplot
    ax = sns.boxplot(
        data=data,
        palette="coolwarm"
    )
    
    # Add individual data points with jitter
    sns.stripplot(
        data=data,
        color="black",
        alpha=0.5,
        jitter=0.2,
        size=4,
        ax=ax
    )
    
    # Improve the plot appearance
    ax.set_xlabel('Dataset')
    ax.set_ylabel(feature)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plt.show()
    return f
