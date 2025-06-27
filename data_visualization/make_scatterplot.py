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
    # --- Start of Diagnostic Checks ---
    # 1. Check if the feature exists in both dataframes
    if feature not in df1.columns:
        print(f"Error: Feature '{feature}' not found in the first dataframe's columns.")
        return None
    if feature not in df2.columns:
        print(f"Error: Feature '{feature}' not found in the second dataframe's columns.")
        return None

    # 2. Find common samples and extract feature vectors
    sample_intersection = df1.index.intersection(df2.index)
    print(f"Found {len(sample_intersection)} common samples between the two dataframes.")
    if len(sample_intersection) == 0:
        print("No common samples to plot. Aborting.")
        return None
    
    intersected_df1 = df1.loc[sample_intersection, :]
    intersected_df2 = df2.loc[sample_intersection, :]
    df1_feature_vector = intersected_df1[feature]
    df2_feature_vector = intersected_df2[feature]

    # 3. Create a mask for non-NaN values and apply it
    valid_mask = ~(df1_feature_vector.isna() | df2_feature_vector.isna())
    feature_vector_1 = df1_feature_vector[valid_mask]
    feature_vector_2 = df2_feature_vector[valid_mask]
    
    num_valid_points = len(feature_vector_1)
    print(f"Found {num_valid_points} valid (non-NaN) data points for the feature '{feature}'.")
    # --- End of Diagnostic Checks ---

    # Initialize plot and correlation variables
    f, ax = plt.subplots(figsize=(6, 6), dpi=300)
    pearson_corr, r_squared = np.nan, np.nan

    # Only proceed with plotting and correlation if there are enough data points
    if num_valid_points >= 2:
        # Create y=x line
        min_val = min(feature_vector_1.min(), feature_vector_2.min())
        max_val = max(feature_vector_1.max(), feature_vector_2.max())
        line_x = np.linspace(min_val, max_val, 100)
        sns.lineplot(x=line_x, y=line_x, ax=ax, color="red")
        ax.lines[0].set_linestyle("--")

        # Perform the regression and get statistics
        sns.regplot(
            x=feature_vector_1, y=feature_vector_2, ax=ax, scatter_kws={"alpha": 0.5}
        )

        # Calculate Pearson's correlation coefficient
        try:
            pearson_corr, p_value = stats.pearsonr(feature_vector_1, feature_vector_2)
        except ValueError as e:
            print(f"Error calculating Pearson correlation: {e}")
            pearson_corr = np.nan

        # Calculate R-squared (coefficient of determination)
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                feature_vector_1, feature_vector_2
            )
            r_squared = r_value**2
        except ValueError as e:
            print(f"Error calculating linear regression: {e}")
            r_squared = np.nan
    else:
        # If not enough points, print a message on the plot
        ax.text(0.5, 0.5, f"Not enough data points to plot '{feature}'\n(Found {num_valid_points})",
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12, color='red')

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
