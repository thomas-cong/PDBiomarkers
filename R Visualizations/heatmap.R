library(ggplot2)
ggsave <- function(..., bg = "white") ggplot2::ggsave(..., bg = bg)

library(reshape2)
library(dplyr)
library(tidyr)
library(ggthemes)
heatmap_function <- function(file_path, save_path, title) {
    heatmap_data <- read.csv(file_path)
    # Sort by UPDRSIII Score
    heatmap_data <- heatmap_data %>%
        arrange(UPDRSIII) # Replace with exact column name if different

    # Set winterlight_id as a factor with levels in sorted order
    heatmap_data$winterlight_id <- factor(heatmap_data$winterlight_id, levels = heatmap_data$winterlight_id)

    heatmap_long_data <- heatmap_data %>%
        select(-any_of("subjid")) %>%
        pivot_longer(
            cols = -c(winterlight_id, Status),
            names_to = "biomarker",
            values_to = "value"
        )
    # Reorder biomarker so 'Speech' is second to last
    biomarker_levels <- unique(heatmap_long_data$biomarker)
    biomarker_levels <- biomarker_levels[biomarker_levels != "Speech"]
    if (length(biomarker_levels) >= 1) {
        biomarker_levels <- append(biomarker_levels, "Speech", after = length(biomarker_levels) - 1)
    } else {
        biomarker_levels <- c("Speech")
    }
    heatmap_long_data$biomarker <- factor(heatmap_long_data$biomarker, levels = biomarker_levels)
    heatmap_long_data <- heatmap_long_data %>%
        mutate(
            winterlight_id = as.factor(winterlight_id),
            Status = as.factor(Status)
        )
    hm <- ggplot(heatmap_long_data, aes(x = winterlight_id, y = biomarker, fill = value)) +
        geom_tile() +
        scale_fill_gradient2(low = "blue", mid = "white", high = "red", midpoint = 0) +
        labs(title = title) +
        facet_grid(~Status, scales = "free_x", space = "free_x") +
        theme_tufte(base_family = "Helvetica") +
        theme(
            axis.title.x = element_blank(),
            axis.text.x = element_blank(),
            axis.ticks.x = element_blank()
        )
    ggsave(save_path, plot = hm, width = 24, height = 8, dpi = 300)
}
files <- list.files("2157-Generated-Data/Clinical", pattern = "normalized.csv", full.names = TRUE)
for (file in files) {
    file_name <- tail(strsplit(file, "/")[[1]], 1)
    save_path <- paste0("./R Figures/", gsub("normalized.csv", "heatmap.png", file_name))
    heatmap_function(file, save_path, paste(gsub("normalized.csv", "", file_name), "Biomarker Heatmap"))
}
