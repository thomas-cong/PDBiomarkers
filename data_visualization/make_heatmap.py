import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from data_visualization import data_preprocessing

def correlation_heatmap(df, method="pearson", feature_axis=1, title = None):
    '''
    Given a dataframe, return a heatmap of the correlation matrix
    df: dataframe
    method: correlation method, default is pearson
    feature_axis: axis to calculate pairwise correlation, default is 1 (columns)
    '''
    if feature_axis == 1:
        df.dropna(axis=0, inplace=True)
        correlation_matrix = df.corr(method=method)
    elif feature_axis == 0:
        df.dropna(axis=1, inplace=True)
        correlation_matrix = df.corr(method=method, axis=0)
    if correlation_matrix.shape[0] == 0 or correlation_matrix.shape[1] == 0:
        return None

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
    ax.tick_params(axis='both', labelsize=9, pad=5)
    if title:
        ax.set_title(title, pad=10)  # Adjust pad as needed
    return fig

def distribution_heatmap(df, feature_axis=1, healthy_split=None, title=None, pairings=None):
    '''
    Given a dataframe, return a heatmap of the distribution of the features
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input data
    feature_axis : int, optional (default=1)
        Axis to calculate pairwise correlation (0 for rows, 1 for columns)
    healthy_split : int, optional
        If provided, draws a vertical line at this x-position
    title : str, optional
        Title for the plot
    pairings : list of tuples, optional
        List of column index pairs to connect with brackets, e.g., [(0, 12), (1, 13)]
    '''
    if feature_axis == 1:
        df.dropna(axis=0, inplace=True)
        df = data_preprocessing.normalize_df(df).transpose()
    elif feature_axis == 0:
        df.dropna(axis=1, inplace=True)
        df = data_preprocessing.normalize_df(df)
    if df.shape[0] == 0 or df.shape[1] == 0:
        return None
    def cap_at_3(x):
        return max(min(x, 3), -3)
    df = df.applymap(cap_at_3)

    # Create figure and axis with adjusted figsize
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    
    # Create heatmap with adjusted parameters
    show_xticks = True if df.shape[1] < 100 else False
    sns.heatmap(
        df,
        cmap="coolwarm",
        square=True,
        ax=ax,
        cbar_kws={"label": "Z-Score", "shrink": 0.6, "location": "bottom"},
        xticklabels=show_xticks,
        yticklabels=True,
        linewidths=0.1,  # Add grid lines between cells
        linecolor='white'  # Color of the grid lines
    )
    
    if healthy_split is not None:
        ax.axvline(x=healthy_split - 1, color='red', linestyle='--', linewidth=0.5)            
        
    # Increase font size and padding of y-tick labels
    ax.tick_params(axis='both', 
                  labelsize=6, 
                  pad=5,
                  length=0)  # Remove tick marks
    
    # Set the ticks to be centered
    ax.set_xticks(np.arange(df.shape[1]) + 0.5, minor=False)
    ax.set_yticks(np.arange(df.shape[0]) + 0.5, minor=False)
    if title:
        # Move title to the right to avoid overlap with brackets
        ax.set_title(title, rotation=270, x=1.02, y=0.5, va='center', ha='left')  # Vertical title on the right
    
    # Set the tick labels
    if show_xticks:
        ax.set_xticklabels(df.columns, rotation=90)
    else:
        ax.set_xticklabels([])
    ax.set_yticklabels(df.index)
    
    # Add pairings if provided
    if pairings and len(pairings) > 0:
        y_min_orig, y_max_orig = ax.get_ylim() # Original y-limits of the heatmap data (before any bracket adjustments)
        heatmap_y_range = y_max_orig - y_min_orig

        # Define spacing for the horizontal bars of the staples
        horizontal_bar_spacing = 0.03 * heatmap_y_range  # Vertical space between horizontal bars of consecutive staples
        first_horizontal_bar_y_offset = 0.005 * heatmap_y_range # Offset of the first horizontal bar from heatmap top

        # Y-coordinate for the horizontal bar of the first bracket
        current_horizontal_bar_y = y_max_orig + first_horizontal_bar_y_offset
        
        max_y_coord_for_all_brackets = current_horizontal_bar_y # Keep track of the highest point reached by any bracket's horizontal bar

        line_width = 0.5 # Make lines even thinner

        for i, (start_col, end_col) in enumerate(pairings):
            if (start_col >= df.shape[1] or end_col >= df.shape[1] or 
                start_col < 0 or end_col < 0):
                continue

            # Calculate y-position for the current bracket's horizontal bar
            if i > 0:
                # Each subsequent horizontal bar is drawn above the previous one
                current_horizontal_bar_y += horizontal_bar_spacing 
            
            max_y_coord_for_all_brackets = max(max_y_coord_for_all_brackets, current_horizontal_bar_y)

            x_start = min(start_col, end_col) + 0.5
            x_end = max(start_col, end_col) + 0.5
            
            # Draw the top horizontal line of the staple
            ax.hlines(y=current_horizontal_bar_y, xmin=x_start, xmax=x_end, 
                     colors='red', linewidth=line_width, zorder=10) # Increased zorder
            
            # Draw the vertical lines (legs of the staple, extending from heatmap top to horizontal bar)
            ax.vlines(x=x_start, ymin=y_max_orig, ymax=current_horizontal_bar_y, 
                     colors='red', linewidth=line_width, zorder=10) # Increased zorder
            ax.vlines(x=x_end, ymin=y_max_orig, ymax=current_horizontal_bar_y, 
                     colors='red', linewidth=line_width, zorder=10) # Increased zorder
        
        # Adjust overall y-axis upper limit to ensure all brackets are visible
        # Add a small padding above the topmost bracket's horizontal bar
        final_y_max_limit = max_y_coord_for_all_brackets + 0.02 * heatmap_y_range 
        ax.set_ylim(y_min_orig, final_y_max_limit)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return fig