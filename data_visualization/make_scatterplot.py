import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats


def feature_comparison_scatterplot(df1, df2, feature):
    """
    Make a scatterplot of the same feature across same patients from different pipelines
    df1: dataframe of the first pipeline (true)
    df2: dataframe of the second pipeline (test)
    feature: feature to compare
    """
    sample_intersection = df1.index.intersection(df2.index)
    intersected_df1 = df1.loc[sample_intersection, :]
    intersected_df2 = df2.loc[sample_intersection, :]
    df1_feature_vector = intersected_df1[feature]
    df2_feature_vector = intersected_df2[feature]

    f, ax = plt.subplots(figsize=(6, 6), dpi=300)
    # Create linspace instead of arange to ensure proper number of points for the y=x line
    min_val = min(df1_feature_vector.min(), df2_feature_vector.min())
    max_val = max(df1_feature_vector.max(), df2_feature_vector.max())
    line_x = np.linspace(min_val, max_val, 100)  # 100 points should be sufficient
    sns.lineplot(x=line_x, y=line_x, ax=ax, color="red")
    ax.lines[0].set_linestyle("--")
    # Perform the regression and get statistics
    sns.regplot(
        x=df1_feature_vector, y=df2_feature_vector, ax=ax, scatter_kws={"alpha": 0.5}
    )

    # Create a mask for non-NaN values in both vectors
    valid_mask = ~(df1_feature_vector.isna() | df2_feature_vector.isna())

    # Apply the mask to both vectors to get aligned, non-NaN values
    feature_vector_1 = df1_feature_vector[valid_mask]
    feature_vector_2 = df2_feature_vector[valid_mask]

    # Calculate Pearson's correlation coefficient and p-value
    try:
        pearson_corr, p_value = stats.pearsonr(feature_vector_1, feature_vector_2)
        print(f"Pearson correlation: {pearson_corr:.3f}, p-value: {p_value:.3f}")
    except Exception as e:
        print(f"Error calculating Pearson correlation: {e}")
        pearson_corr, p_value = np.nan, np.nan

    # Calculate R-squared (coefficient of determination)
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            feature_vector_1, feature_vector_2
        )
        r_squared = r_value**2
        print(f"R-squared: {r_squared:.3f}, p-value: {p_value:.3f}")
    except Exception as e:
        print(f"Error calculating linear regression: {e}")
        slope, intercept, r_value, p_value, std_err = [np.nan] * 5
        r_squared = np.nan

    # Add correlation and R-squared values as text annotation
    ax.annotate(
        f"r = {pearson_corr:.3f}\nR² = {r_squared:.3f}",
        xy=(0.05, 0.95),
        xycoords="axes fraction",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.7),
        verticalalignment="top",
    )

    ax.set_xlabel("True")
    ax.set_ylabel("Test")
    f.suptitle(feature)
    return f
