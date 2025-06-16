library(ComplexHeatmap)
# Save high-resolution PNG (3000×1000 pixels @ 300 dpi)
make_distribution_heatmap <- function(file_path){
png(paste0(file_path, "_heatmap.png"), width = 3000, height = 2000, units = "px", res = 300)

# Load data
heatmap_data <- read.csv(file_path, row.names = 1)

# Sort data by Status, then UPDRSIII
heatmap_data <- heatmap_data[order(heatmap_data$Status, heatmap_data$UPDRSIII), ]
if (all(is.na(heatmap_data$UPDRSIII))){
    return("No UPDRSIII data")
}

# Extract annotation data
annotation_data <- heatmap_data[, c("UPDRSIII", "Speech", "Status")]

# Remove annotation columns from heatmap data
feature_cols <- setdiff(colnames(heatmap_data), c("Status", "UPDRSIII", "Speech", "subjid"))
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
correlation_col <- colorRamp2(c(min(feature_correlation), median(feature_correlation), max(feature_correlation)), c("blue", "white", "red"))

# For the row annotation
corAnnot <- rowAnnotation(
  Correlation = anno_simple(
    sort(feature_correlation, decreasing = FALSE), 
    col = correlation_col,
    simple_anno_size = unit(0.5, "cm"),
    na_col = "white"
  ),
  annotation_name_gp = gpar(fontsize = 8)
)

# For the top annotation
ha <- HeatmapAnnotation(
  UPDRSIII = anno_simple(
    annotation_data$UPDRSIII, 
    col = updrs_col,
    simple_anno_size = unit(0.5, "cm")
  ),
  Speech = anno_simple(
    annotation_data$Speech, 
    col = speech_col,
    simple_anno_size = unit(0.5, "cm")
  ),
  Status = annotation_data$Status,
  col = list(Status = c("HC" = "green", "ON" = "blue", "OFF" = "red")),
  annotation_name_gp = gpar(fontsize = 8)
)

# Create heatmap with Status grouping
ht <- Heatmap(t(heatmap_matrix),
  name = "Features",
  top_annotation = ha,
  left_annotation = corAnnot,
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
  heatmap_legend_param = list(
    title = "Z-score",
    title_position = "leftcenter-rot",
    legend_height = unit(3, "cm"),
    grid_width = unit(0.8, "cm")
  )

)
lgd_list <- list(
  Legend(title = "UPDRSIII", col_fun = updrs_col),
  Legend(title = "Speech", col_fun = speech_col),
  Legend(title = "Correlation", col_fun = correlation_col)
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
for (file in list.files("./2157-Generated-Data/Clinical/Normalized/")){
    file_path <- paste0("./2157-Generated-Data/Clinical/Normalized/", file)
    make_distribution_heatmap(file_path)
}