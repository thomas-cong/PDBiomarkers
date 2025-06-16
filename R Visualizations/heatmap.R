library(ComplexHeatmap)
# Save high-resolution PNG (3000×1000 pixels @ 300 dpi)
make_distribution_heatmap <- function(file_path){
# replace .csv with _heatmap.png so we don't double-append extensions
png(sub("\\.csv$", "_heatmap.png", file_path, ignore.case = TRUE),
    width = 3000, height = 2000, units = "px", res = 300)

# Load data
heatmap_data <- read.csv(file_path, row.names = 1)

# Sort data by Status, then UPDRSIII
heatmap_data <- heatmap_data[order(heatmap_data$Status, heatmap_data$UPDRSIII), ]
if (all(is.na(heatmap_data$UPDRSIII))){
    return("No UPDRSIII data")
}

# Extract annotation data
annotation_data <- heatmap_data[, c("UPDRSIII", "Speech", "Status", "Age", "Sex", "Weight")]

# Remove annotation columns from heatmap data
feature_cols <- setdiff(colnames(heatmap_data), c("Status", "UPDRSIII", "Speech", "subjid", "Age", "Sex", "Weight"))
heatmap_matrix <- as.matrix(heatmap_data[, feature_cols])
# Calculate correlation of each feature with UPDRSIII score
feature_correlation <- sapply(heatmap_data[, feature_cols], function(x) {
  cor(x, heatmap_data$UPDRSIII, use = "pairwise.complete.obs")
})

# Sort features by absolute correlation with UPDRSIII
feature_cols <- names(sort(feature_correlation, decreasing = FALSE))
heatmap_matrix <- as.matrix(heatmap_data[, feature_cols])


# Create color functions for annotations
updrs_col <- colorRamp2(c(min(na.omit(annotation_data$UPDRSIII)),
                         median(na.omit(annotation_data$UPDRSIII)),
                         max(na.omit(annotation_data$UPDRSIII))),
                        c("blue", "white", "red"))

speech_col <- colorRamp2(c(min(na.omit(annotation_data$Speech)),
                          median(na.omit(annotation_data$Speech)),
                          max(na.omit(annotation_data$Speech))),
                        c("blue", "white", "red"))
correlation_col <- colorRamp2(c(min(feature_correlation),
                                median(feature_correlation),
                                max(feature_correlation)),
                                c("blue", "white", "red"))
age_col <- colorRamp2(c(min(na.omit(annotation_data$Age)),
                        median(na.omit(annotation_data$Age)),
                        max(na.omit(annotation_data$Age))),
                        c("blue", "white", "red"))
weight_col <- colorRamp2(c(min(na.omit(annotation_data$Weight)),
                        median(na.omit(annotation_data$Weight)),
                        max(na.omit(annotation_data$Weight))),
                        c("blue", "white", "red"))
col_fun <- colorRamp2(c(-3, 0, 3), c("blue", "white", "red"))
# discrete categorical colour mappings
sex_col    <- c("Male"   = "#7ceeff",
                "Female" = "#ff89da")
status_col <- c("HC" = "green",
                "ON" = "blue",
                "OFF"= "red")
# For the row annotation
rowAnnotations <- rowAnnotation(
  Correlation = anno_simple(
    sort(feature_correlation, decreasing = FALSE), 
    col = correlation_col,
    simple_anno_size = unit(0.25, "cm"),
    na_col = "white",
  ),
  annotation_name_gp = gpar(fontsize = 6)

)

# For the top annotation
ha <- HeatmapAnnotation(
  UPDRSIII = anno_simple(
    annotation_data$UPDRSIII,
    col = updrs_col,
    simple_anno_size = unit(0.25, "cm")
  ),
  Speech = anno_simple(
    annotation_data$Speech,
    col = speech_col,
    simple_anno_size = unit(0.25, "cm")
  ),
  Age = anno_simple(
    annotation_data$Age,
    col = age_col,
    simple_anno_size = unit(0.25, "cm")
  ),
  Weight = anno_simple(
    annotation_data$Weight,
    col = weight_col,
    simple_anno_size = unit(0.25, "cm")
  ),
  Sex = anno_simple(
    annotation_data$Sex,
    col = sex_col,
    simple_anno_size = unit(0.25, "cm")
  ),
  Status = anno_simple(
    annotation_data$Status,
    col = status_col,
    simple_anno_size = unit(0.25, "cm")
  ),
  annotation_name_gp = gpar(fontsize = 6)
)

# Create heatmap with Status grouping
ht <- Heatmap(t(heatmap_matrix),
  name = "Features",
  top_annotation = ha,
  left_annotation = rowAnnotations,
  show_row_names = TRUE,
  show_column_names = FALSE,
  column_split = factor(annotation_data$Status, levels = unique(annotation_data$Status)),
  cluster_columns = FALSE,
  cluster_rows = FALSE,  # Remove row clustering
  show_row_dend = FALSE,  # Hide row dendrogram
  show_column_dend = FALSE,  # Hide column dendrogram
  column_title = NULL,
  column_gap = unit(2, "mm"),
  border = FALSE,
  row_names_gp = gpar(fontsize = 4),
  show_heatmap_legend = FALSE
)
lgd_list <- list(
    Legend(title = "Z-score", col_fun = col_fun),
  Legend(title = "UPDRSIII", col_fun = updrs_col),
  Legend(title = "Speech", col_fun = speech_col),
  Legend(title = "Correlation", col_fun = correlation_col),
  Legend(title = "Age", col_fun = age_col),
  Legend(title = "Weight", col_fun = weight_col),
  Legend(title = "Sex",    at = names(sex_col),    legend_gp = gpar(fill = sex_col)),
  Legend(title = "Status", at = names(status_col), legend_gp = gpar(fill = status_col))
)

# Draw the heatmap
draw(
  ht,
  annotation_legend_list  = lgd_list,      # custom order
  heatmap_legend_side     = "right",
  annotation_legend_side  = "right"
)
dev.off()
}
csv_files <- list.files("./2157-Generated-Data/Clinical/Normalized/", 
                         pattern = "\\.csv$", full.names = TRUE, ignore.case = TRUE)
for (file_path in csv_files) {
    make_distribution_heatmap(file_path)
}