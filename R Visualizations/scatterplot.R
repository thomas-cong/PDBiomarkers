# Load necessary libraries
library(ggplot2)
library(dplyr)
library(tidyr)

# Source the custom theme
# This assumes 'theme.R' defines a function called 'custom_theme()'
source("/Users/thomas.cong/Downloads/ResearchCode/R Visualizations/theme.R")

#' Creates and saves a scatterplot comparing two features from a CSV file.
#'
#' This function generates a scatterplot. If a grouping feature is provided,
#' it connects points with lines. It allows for coloring points by a specified feature.
#'
#' @param x_feature The name of the column to be plotted on the x-axis.
#' @param y_feature The name of the column to be plotted on the y-axis.
#' @param file_path The absolute path to the input CSV file.
#' @param save_path The path where the output plot image will be saved.
#' @param grouping_feature Optional column to group data for lines.
#' @param point_color_feature Optional column to color points by.
#'
#' @return Invisibly returns the ggplot object.
make_scatterplot <- function(x_feature, y_feature, file_path, save_path, grouping_feature = NULL, point_color_feature = NULL) {
  
  # --- 1. Load and Validate Data ---
  data <- read.csv(file_path, check.names = FALSE)
  
  required_cols <- c(x_feature, y_feature)
  if (!is.null(grouping_feature)) {
    required_cols <- c(required_cols, grouping_feature)
  }
  if (!is.null(point_color_feature)) {
    required_cols <- c(required_cols, point_color_feature)
  }
  
  if (!all(required_cols %in% colnames(data))) {
    missing_cols <- required_cols[!required_cols %in% colnames(data)]
    stop(paste("Error: The following required columns are missing from the data:", paste(missing_cols, collapse = ", ")))
  }
  
  # --- 2. Filter Data and Perform Transformations ---
  data <- data %>%
    filter(!is.na(.data[[x_feature]]) & !is.na(.data[[y_feature]]))

  if ("Status" %in% colnames(data)) {
    data <- data %>% filter(Status == "PD")
  }

  y_values <- data[[y_feature]]
  z_scores <- as.numeric(scale(y_values))
  capped_z_scores <- pmin(pmax(z_scores, -3), 3)
  
  z_score_col_name <- paste0(y_feature, "_zscore")
  data[[z_score_col_name]] <- capped_z_scores

  # --- 3. Build Plot ---
  p <- ggplot(data, aes(x = .data[[x_feature]], y = .data[[z_score_col_name]]))
  
  # Add lines first so points are drawn on top
  if (!is.null(grouping_feature)) {
    # If coloring points by a feature, use neutral lines to avoid color scale conflicts
    if (!is.null(point_color_feature) && point_color_feature %in% colnames(data)) {
      p <- p + geom_line(aes(group = .data[[grouping_feature]]), color = "grey50", alpha = 0.5)
    } else if ("Status" %in% colnames(data)) {
      p <- p + geom_line(aes(group = .data[[grouping_feature]], color = Status), alpha = 0.3, linewidth = 0.8)
    } else {
      p <- p + geom_line(aes(group = .data[[grouping_feature]]), alpha = 0.3, linewidth = 0.8)
    }
  }

  # Add points layer
  if (!is.null(point_color_feature) && point_color_feature %in% colnames(data)) {
    p <- p + geom_point(aes(color = .data[[point_color_feature]]), alpha = 0.8, size = 3)
  } else if ("Status" %in% colnames(data)) {
    p <- p + geom_point(aes(color = Status), alpha = 0.8, size = 3)
  } else {
    p <- p + geom_point(alpha = 0.8, size = 3)
  }
  
  # Add labels
  p <- p +
    labs(
      title = paste("Z-score of", y_feature, "vs.", x_feature),
      x = x_feature,
      y = paste("Z-score of", y_feature, "(capped at ±3)"),
      color = if (!is.null(point_color_feature)) point_color_feature else "Status"
    )
  
  # --- 4. Save Plot ---
  ggsave(save_path, p, width = 12, height = 6, dpi = 300)
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

#' Creates a paired boxplot for 'First' and 'Last' sessions.
#'
#' This function generates a boxplot comparing a feature's values between
#' a 'First' and 'Last' session. The plot is faceted by 'Status'
#' to show differences between patient groups. Points for each subject are
#' connected by a line to visualize pairing.
#'
#' @param feature The name of the column containing the feature to plot.
#' @param file_path The path to the CSV file.
#' @param save_path The path where the plot image will be saved.
#' @param grouping_feature The column name for subject IDs (e.g., "subjid").
#' @param session_feature The column name distinguishing 'First' and 'Last' sessions.
#' @return Invisibly returns the ggplot object.
make_paired_boxplot <- function(feature, file_path, save_path, grouping_feature, session_feature = "First/Last") {

  # --- 1. Load and Validate Data ---
  data <- read.csv(file_path, check.names = FALSE)

  required_cols <- c(feature, grouping_feature, session_feature, "Status")
  if (!all(required_cols %in% colnames(data))) {
    missing_cols <- required_cols[!required_cols %in% colnames(data)]
    stop(paste("Error: Missing required columns:", paste(missing_cols, collapse = ", ")))
  }

  # --- 2. Filter and Prepare Data ---
  data <- data %>%
    filter(!is.na(.data[[feature]]) & .data[[session_feature]] %in% c("First", "Last"))

  # Ensure session_feature is a factor to control plotting order
  data[[session_feature]] <- factor(data[[session_feature]], levels = c("First", "Last"))

  # --- 3. Build Plot ---
  p <- ggplot(data, aes(x = .data[[session_feature]], y = .data[[feature]], fill = .data[[session_feature]])) +
    geom_boxplot(alpha = 0.7, outlier.shape = NA) +
    geom_point(position = position_jitter(width = 0.1), alpha = 0.5, size = 2) +
    geom_line(aes(group = .data[[grouping_feature]]), alpha = 0.4, color = "gray") +
    facet_wrap(~ Status, scales = "free_y") + # Use free_y for better visualization if scales differ
    labs(
      title = paste("Comparison of", feature, "between First and Last Sessions"),
      subtitle = "Faceted by Status, paired by Subject",
      x = "Session",
      y = feature,
      fill = "Session"
    ) +
    theme(legend.position = "none") # Hide legend as fill is redundant with x-axis

  # --- 4. Save Plot ---
  ggsave(save_path, p, width = 8, height = 6, dpi = 300)
  print(paste("Paired box plot saved to", save_path))

  invisible(p)
}


# --- Execution ---
# Define common parameters
csv_file_path <- "/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/Park_Celeb_Biomarkers.csv"
x_axis_feature <- "YFD"
features <- read.csv(csv_file_path)
for (feature in colnames(features)){
    if (feature %in% c("subjid", "Status", "Age", "Sex", "UPDRSIII", "YFD", "filename")){
        next
    }
    make_scatterplot(
        x_feature = x_axis_feature,
        y_feature = feature,
        file_path = csv_file_path,
        save_path = paste0("/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/LongitudinalProgression/", x_axis_feature, "_vs_", feature, "_scatterplot.png"),
        grouping_feature = "subjid"
    )
    make_violin_plot(
        x_feature = x_axis_feature,
        y_feature = feature,
        file_path = csv_file_path,
        save_path = paste0("/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/LongitudinalProgression/", x_axis_feature, "_vs_", feature, "_violinplot.png")
        )
    }
first_last_file_path <- "/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/Park_Celeb_Biomarkers_First_Last.csv"
first_last_data <- read.csv(first_last_file_path, check.names = FALSE)
for (feature in colnames(first_last_data)){
    if (feature %in% c("subjid", "Status", "Age", "Sex", "UPDRSIII", "YFD", "filename", "First/Last")){
        next
    }
    make_scatterplot(
        x_feature = x_axis_feature,
        y_feature = feature,
        file_path = first_last_file_path,
        save_path = paste0("/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/LongitudinalProgression/", x_axis_feature, "_vs_", feature, "_first_last_scatterplot.png"),
        grouping_feature = "subjid",
        point_color_feature = "First/Last"
    )
    make_paired_boxplot(
        feature = feature,
        file_path = first_last_file_path,
        save_path = paste0("/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/LongitudinalProgression/", feature, "_first_last_boxplot.png"),
        grouping_feature = "subjid",
        session_feature = "First/Last"
    )
    }

