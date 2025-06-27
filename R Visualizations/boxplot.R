library(ggplot2)
library(RColorBrewer)
library(dplyr)
library(tidyr)
source("/Users/thomas.cong/Downloads/ResearchCode/R Visualizations/theme.R")

make_boxplot <- function(data, feature, save_path){
  # Define desired columns and find which are available in the data
  desired_cols <- c("subjid", "Status", feature, "Age", "Sex", "UPDRSIII")
  available_cols <- intersect(desired_cols, colnames(data))
  
  # Select only the available columns
  feature_vectors <- data[, available_cols, drop = FALSE]

  # Conditionally process columns only if they exist
  if ("UPDRSIII" %in% available_cols) {
    feature_vectors$UPDRSIII <- as.numeric(as.character(feature_vectors$UPDRSIII))
  }
  if ("Age" %in% available_cols) {
    feature_vectors$Age <- as.numeric(feature_vectors$Age)
  }
  if ("subjid" %in% available_cols) {
    # drop the ON/OFF suffix to get the subject ID common to both
    feature_vectors$pair_id <- sub("(ON|OFF)$", "",
                                   feature_vectors$subjid,
                                   ignore.case = TRUE)
  }
  if ("Sex" %in% available_cols) {
    # make sure Sex is a factor so ggplot treats it as discrete
    feature_vectors$Sex <- factor(feature_vectors$Sex)
  }

  # Set order of groups for plotting, ensuring all statuses are included
  all_statuses <- unique(feature_vectors$Status)
  status_levels <- c("OFF", "ON", setdiff(all_statuses, c("OFF", "ON")))
  feature_vectors$Status <- factor(feature_vectors$Status, levels = status_levels)

  t_test_result <- NULL
  # Paired analysis only if pair_id was created
  if ("pair_id" %in% colnames(feature_vectors)) {
    
    # Reshape data to wide format for paired test
    wide_data <- feature_vectors %>%
      select("pair_id", "Status", feature) %>%
      tidyr::pivot_wider(names_from = "Status", 
                         values_from = feature,
                         values_fn = function(x) mean(x, na.rm = TRUE))
    
    # Perform paired t-test if both ON and OFF columns exist after pivoting
    if ("ON" %in% colnames(wide_data) && "OFF" %in% colnames(wide_data)) {
      
      # Remove rows with NA in either ON or OFF columns for the test
      test_data <- na.omit(wide_data[, c("ON", "OFF")])
      
      if (nrow(test_data) > 1) { # t-test needs at least 2 pairs
        t_test_result <- tryCatch({
          t.test(test_data$ON, test_data$OFF, paired = TRUE)
        }, error = function(e) {
          if (grepl("data are essentially constant", e$message)) {
            print(paste("Skipping t-test for feature '", feature, "': data are essentially constant.", sep=""))
          } else {
            print(paste("An error occurred during t-test for feature '", feature, "': ", e$message, sep=""))
          }
          return(NULL)
        })
      }
    }
  }

  # --- Build the plot ---
  # Base plot
  p <- ggplot(feature_vectors, aes(x = Status, y = .data[[feature]])) +
    geom_boxplot(
      outlier.shape = NA,
      linewidth = 1.5,
      fill = "white"
    )

  # Add lines and points for paired data if pair_id exists
  if ("pair_id" %in% colnames(feature_vectors)) {
    p <- p + geom_line(
      aes(group = pair_id),
      alpha = 0.4,
      position = position_dodge(0.30),
      linewidth = 1.5
    )
    
    # Build aes for points conditionally
    point_aes <- aes(group = pair_id)
    if ("Sex" %in% colnames(feature_vectors)) {
      point_aes$shape <- as.name("Sex")
    }
    if ("UPDRSIII" %in% colnames(feature_vectors)) {
      point_aes$colour <- as.name("UPDRSIII")
    }
    
    p <- p + geom_point(
      point_aes,
      size = 4,
      alpha = 0.6,
      position = position_dodge(0.30)
    )
  } else {
    # If not paired, just show jittered points
    jitter_aes <- aes()
    if ("UPDRSIII" %in% colnames(feature_vectors)) {
      jitter_aes$colour <- as.name("UPDRSIII")
    }
    if ("Sex" %in% colnames(feature_vectors)) {
      jitter_aes$shape <- as.name("Sex")
    }
    p <- p + geom_jitter(
      mapping = jitter_aes,
      width = 0.2,
      height = 0,
      alpha = 0.7,
      size = 3
    )
  }

  # Add scales and theme conditionally
  if ("UPDRSIII" %in% colnames(feature_vectors)) {
    p <- p + scale_colour_distiller(
       palette   = "RdBu",
       direction = -1,
       limits    = range(feature_vectors$UPDRSIII, na.rm = TRUE),
       na.value = "grey50"
     )
  }
  
  if ("Sex" %in% colnames(feature_vectors)) {
     p <- p + scale_shape_manual(
       values = c("M" = 16, "F" = 17), # Example: circles for M, triangles for F
       na.translate = TRUE,
       na.value     = 16 # Default shape for NA (solid circle)
     )
  }

  p <- p + theme(axis.text  = element_text(size = 15, colour = "black"),
           axis.title = element_text(size = 15, colour = "black"),
           strip.text = element_text(size = 15))

  # Add p-value annotation to the plot if a test was performed
  if (!is.null(t_test_result) && !is.null(t_test_result$p.value)) {
    p_value <- t_test_result$p.value
    if (!is.na(p_value)) {
        p_label <- if (p_value < 0.001) "p < 0.001" else paste("p =", round(p_value, 3))
        
        # Position for the annotation
        y_pos <- max(feature_vectors[[feature]], na.rm = TRUE)
        
        p <- p + 
          annotate("segment", x = "OFF", xend = "ON", y = y_pos * 1.1, yend = y_pos * 1.1) +
          annotate("text", x = 1.5, y = y_pos * 1.15, label = p_label, size = 5)
    }
  }

ggsave(save_path, p)
}

# --- Main script execution ---

# Define paths for input data and output plots
input_dir <- "/Users/thomas.cong/Downloads/ResearchCode/2157-Generated-Data/Clinical/Regular"
output_dir <- file.path(input_dir, "Boxplot")

# Create the output directory if it doesn't already exist
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
  print(paste("Created directory:", output_dir))
}

# Get a list of all CSV files in the input directory
csv_files <- list.files(path = input_dir, pattern = "\\.csv$", full.names = TRUE)

# Check if any CSV files were found
if (length(csv_files) == 0) {
  stop("No CSV files found in the specified directory.")
}

print(paste("Found", length(csv_files), "CSV files to process."))

# Loop over each CSV file found
for (file_path in csv_files) {
  
  base_name <- basename(file_path)
  print(paste("Processing file:", base_name))
  
  # Read the data from the CSV file
  data <- read.csv(file_path, check.names = FALSE)
  
  # Define columns that are not features to be plotted
  non_feature_cols <- c("subjid", "Status", "Age", "Sex", "UPDRSIII", "pair_id")
  
  # Identify feature columns by excluding the non-feature ones
  feature_names <- setdiff(colnames(data), non_feature_cols)
  
  # Prepare a label for the plot from the CSV filename
  plot_label_name <- gsub("2157-Clinical-", "", base_name)
  plot_label_name <- gsub("\\.csv$", "", plot_label_name) # More robustly remove .csv
  
  # Loop over each identified feature column
  for (feature in feature_names) {
    
    # Sanitize feature name for use in filename by replacing special characters with underscores
    sanitized_feature <- gsub("[^A-Za-z0-9_.-]+", "_", feature)
    
    # Construct the filename for the output plot
    save_filename <- paste0(sanitized_feature, "_", plot_label_name, ".png")
    save_path <- file.path(output_dir, save_filename)
    
    print(paste("  - Generating boxplot for feature:", feature))
    
    # Use tryCatch to handle any errors during plot creation gracefully
        tryCatch({
      make_boxplot(data = data, feature = feature, save_path = save_path)
    }, error = function(e) {
      # Print an informative error message if plot generation fails
      print(paste("    ERROR: Failed to generate plot for feature '", feature, 
                  "' from file '", base_name, "'. Reason: ", e, sep=""))
    })
  }
}

print("--- Script finished ---")

