import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def feature_comparison_scatterplot(df1, df2, feature):
    '''
    Make a scatterplot of the same feature across same patients from different pipelines
    df1: dataframe of the first pipeline (true)
    df2: dataframe of the second pipeline (test)
    feature: feature to compare
    ''' 
    df1.index = df1.index.astype(str)
    df2.index = df2.index.astype(str)
    sample_intersection = df1.index.intersection(df2.index)
    intersected_df1 = df1.loc[sample_intersection,:]
    intersected_df2 = df2.loc[sample_intersection,:]
    df1_feature_vector = intersected_df1[feature]
    df2_feature_vector = intersected_df2[feature]
    
    f, ax = plt.subplots(figsize=(6, 6), dpi=300)
    # Create linspace instead of arange to ensure proper number of points for the y=x line
    min_val = min(df1_feature_vector.min(), df2_feature_vector.min())
    max_val = max(df1_feature_vector.max(), df2_feature_vector.max())
    line_x = np.linspace(min_val, max_val, 100)  # 100 points should be sufficient
    sns.lineplot(x=line_x, y=line_x, ax=ax, color='red')
    ax.lines[0].set_linestyle("--")
    sns.regplot(x=df1_feature_vector, y=df2_feature_vector, ax=ax, scatter_kws={'alpha': 0.5})
    ax.set_xlabel('True')
    ax.set_ylabel('Test')
    f.suptitle(feature)
    return f

