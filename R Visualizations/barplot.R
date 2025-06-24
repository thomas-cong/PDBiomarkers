library(ggplot2)
library(RColorBrewer)
library(dplyr)
library(tidyr)
source("/Users/thomas.cong/Downloads/ResearchCode/R Visualizations/theme.R")

make_barplot <- function(feature, file_path, save_path){
data <- read.csv(file_path)
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
      select(pair_id, Status, all_of(feature)) %>%
      tidyr::pivot_wider(names_from = Status, 
                         values_from = all_of(feature),
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
    p <- p + geom_jitter(width = 0.2, height = 0, alpha = 0.7, size = 3)
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
       na.value     = 1 # Default shape for NA
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
# for (file in list.files("./2157-Generated-Data/Clinical/Regular/",
#                         pattern = "\\.csv$",
#                         full.names = TRUE,
#                         ignore.case = TRUE)){
#   folder <- gsub("\\.csv$", "", file, ignore.case = TRUE)
#   folder <- gsub("Regular", "Regular/Scatterplots", folder)
#   dir.create(folder, recursive = TRUE, showWarnings = FALSE)
#   features <- read.csv(file)
#   for (feature in colnames(features)){
#     save_path <- file.path(folder, paste0(feature, "_scatterplot.png"))
#     make_barplot(feature, file, save_path)
#   }
# }
# file <- "/Users/thomas.cong/Downloads/ResearchCode/ParkCelebCode/Park_Celeb_Biomarkers.csv"
# features <- read.csv(file)
# for (feature in colnames(features)){
#   make_barplot(feature, file, paste0("./ParkCelebCode/", feature, "_barplot.png"))
# }
