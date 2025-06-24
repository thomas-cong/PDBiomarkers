# Load necessary libraries
library(ggplot2)
library(dplyr)
library(tidyr)

# Source the custom theme
# This assumes 'theme.R' defines a function called 'custom_theme()'
source("/Users/thomas.cong/Downloads/ResearchCode/R Visualizations/theme.R")

#' Creates and saves a scatterplot comparing two features from a CSV file.
#'
#' This function generates a scatterplot with a linear regression line and
#' annotates it with the Pearson correlation coefficient (r) and the
#' coefficient of determination (R²).
#'
#' @param x_feature The name of the column to be plotted on the x-axis.
#' @param y_feature The name of the column to be plotted on the y-axis.
#' @param file_path The absolute path to the input CSV file.
#' @param save_path The path where the output plot image will be saved.
#'
#' @return Invisibly returns the ggplot object.
#' @examples
#' # make_scatterplot("YFD", "aavs", "path/to/data.csv", "path/to/plot.png")
make_scatterplot <- function(x_feature, y_feature, file_path, save_path) {
  
  # --- 1. Load and Validate Data ---
  data <- read.csv(file_path)
  
  required_cols <- c(x_feature, y_feature)
  if (!all(required_cols %in% colnames(data))) {
    missing_cols <- required_cols[!required_cols %in% colnames(data)]
    stop(paste("Error: The following required columns are missing from the data:", paste(missing_cols, collapse = ", ")))
  }
  
  # --- 2. Filter Data and Perform Transformations ---
  # Remove rows where the selected features have NA values
  data <- data %>%
    filter(!is.na(.data[[x_feature]]) & !is.na(.data[[y_feature]]))

  # Additionally, filter for patients with PD status if the column exists
  if ("Status" %in% colnames(data)) {
    data <- data %>% filter(Status == "PD")
  }

  # Z-score the y-feature and cap the values at +/- 3
  y_values <- data[[y_feature]]
  # The scale function returns a matrix, so we convert it to a numeric vector
  z_scores <- as.numeric(scale(y_values))
  capped_z_scores <- pmin(pmax(z_scores, -3), 3)
  
  # Create a new column name for the z-scored feature
  z_score_col_name <- paste0(y_feature, "_zscore")
  data[[z_score_col_name]] <- capped_z_scores

  # --- 3. Statistical Analysis ---
  # Calculate Pearson correlation on the transformed data
  stats_label <- "Correlation not available"
  if (nrow(data) > 2) {
    corr_test <- cor.test(data[[x_feature]], data[[z_score_col_name]], method = "pearson")
    r_value <- corr_test$estimate
    r_squared <- r_value^2
    
    # Create label for annotation
    stats_label <- paste(
      "r = ", format(r_value, digits = 2),
      "  R² = ", format(r_squared, digits = 2)
    )
  }
  
  # --- 4. Build Plot ---
  # Initialize plot
  p <- ggplot(data, aes(x = .data[[x_feature]], y = .data[[z_score_col_name]]))
  
  # Add points layer first, so it's underneath the regression line
  if ("Status" %in% colnames(data)) {
    p <- p + geom_point(aes(color = Status), alpha = 0.6, size = 3)
  } else {
    p <- p + geom_point(alpha = 0.6, size = 3)
  }
  
  # Add regression line and other elements on top
  p <- p +
    geom_smooth(method = "lm", se = TRUE, color = "#377eb8", linewidth = 1) +
    labs(
      title = paste("Z-score of", y_feature, "vs.", x_feature),
      x = x_feature,
      y = paste("Z-score of", y_feature, "(capped at ±3)")
    ) +
    annotate(
      "text",
      x = Inf, y = Inf,
      label = stats_label,
      hjust = 1.1, vjust = 2,
      size = 5,
      fontface = "italic"
    )
  
  # --- 4. Save Plot ---
  ggsave(save_path, p, width = 8, height = 6, dpi = 300)
  print(paste("Plot saved to", save_path))
  
  invisible(p)
}

#' Creates and saves a violin plot showing the distribution of a feature at each point of another feature.
#'
#' This function generates a violin plot, which is useful for visualizing the distribution
#' of a continuous variable (y_feature) across different categories or points of another
#' variable (x_feature). It includes the same data filtering and z-score transformation
#' as the scatterplot function.
#'
#' @param x_feature The name of the column for the x-axis (treated as discrete categories).
#' @param y_feature The name of the column for the y-axis (will be z-scored).
#' @param file_path The absolute path to the input CSV file.
#' @param save_path The path where the output plot image will be saved.
#'
#' @return Invisibly returns the ggplot object.
make_violin_plot <- function(x_feature, y_feature, file_path, save_path) {
  
  # --- 1. Load and Validate Data ---
  data <- read.csv(file_path)
  
  required_cols <- c(x_feature, y_feature)
  if (!all(required_cols %in% colnames(data))) {
    missing_cols <- required_cols[!required_cols %in% colnames(data)]
    stop(paste("Error: Missing required columns:", paste(missing_cols, collapse = ", ")))
  }
  
  # --- 2. Filter Data and Perform Transformations ---
  data <- data %>%
    filter(!is.na(.data[[x_feature]]) & !is.na(.data[[y_feature]]))
  
  if ("Status" %in% colnames(data)) {
    data <- data %>% filter(Status == "PD")
  }

  # Filter for groups with more than one data point to avoid warnings in the violin plot
  data <- data %>%
    group_by(.data[[x_feature]]) %>%
    filter(n() > 1) %>%
    ungroup()
  
  # Treat x-feature as a factor for discrete plotting
  data[[x_feature]] <- as.factor(data[[x_feature]])
  
  # --- 3. Build Plot ---
  p <- ggplot(data, aes(x = .data[[x_feature]], y = .data[[y_feature]])) +
    geom_violin(trim = FALSE, fill = "#456e9d", alpha = 0.7) +
    geom_boxplot(width = 0.1, fill = "white", outlier.shape = NA) +
    # Add a regression line across all violins
    geom_smooth(method = "lm", se = TRUE, aes(group = 1), color = "red", linewidth = 1) +
    labs(
      title = paste("Distribution of", y_feature, "across", x_feature, "Levels with Trend Line"),
      x = x_feature,
      y = y_feature
    )
  
  # --- 4. Save Plot ---
  ggsave(save_path, p, width = 12, height = 7, dpi = 300)
  print(paste("Violin plot saved to", save_path))
  
  invisible(p)
}

# --- Execution ---
# Define common parameters
csv_file_path <- "/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/Park_Celeb_Biomarkers.csv"
x_axis_feature <- "YFD"
features <- read.csv(csv_file_path)
for (feature in colnames(features)){
    if (feature %in% c("subjid", "Status", "Age", "Sex", "UPDRSIII", "YFD")){
        next
    }
    make_scatterplot(
        x_feature = x_axis_feature,
        y_feature = feature,
        file_path = csv_file_path,
        save_path = paste0("/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/LongitudinalProgression/", x_axis_feature, "_vs_", feature, "_scatterplot.png")
    )
    make_violin_plot(
        x_feature = x_axis_feature,
        y_feature = feature,
        file_path = csv_file_path,
        save_path = paste0("/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/LongitudinalProgression/", x_axis_feature, "_vs_", feature, "_violinplot.png")
        )
    }
