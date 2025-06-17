library(ComplexHeatmap)
library(circlize)
library(RColorBrewer)         

source("/Users/thomas.cong/Downloads/ResearchCode/R Visualizations/theme.R")


# Save high-resolution PNG (3000×1000 pixels @ 300 dpi)
make_distribution_heatmap <- function(file_path, save_path){
# replace .csv with _heatmap.png so we don't double-append extensions
png(save_path,
    width = 3000, height = 2000, units = "px", res = 300)
on.exit(dev.off())          # <- always executed, even on error

# Load data
heatmap_data <- read.csv(file_path, row.names = 1)

# Sort data by Status, then UPDRSIII
heatmap_data <- heatmap_data[order(heatmap_data$Status, heatmap_data$UPDRSIII), ]
if (all(is.na(heatmap_data$UPDRSIII))){
    return("No UPDRSIII data")
}

# Extract annotation data
annotation_data <- heatmap_data[, c("UPDRSIII",
                                    "Speech",
                                    "Status",
                                    "Age",
                                    "Sex",
                                    "Weight")]

# Remove annotation columns from heatmap data
feature_cols <- setdiff(colnames(heatmap_data), c("Status",
                                                  "UPDRSIII",
                                                  "Speech",
                                                  "subjid",
                                                  "Age",
                                                  "Sex",
                                                  "Weight"))
heatmap_matrix <- as.matrix(heatmap_data[, feature_cols])
# Calculate correlation of each feature with UPDRSIII score
feature_correlation <- sapply(heatmap_data[, feature_cols], function(x) {
  cor(x, heatmap_data$UPDRSIII, use = "pairwise.complete.obs")
})

# Sort features by absolute correlation with UPDRSIII
feature_cols <- names(sort(feature_correlation, decreasing = FALSE))
heatmap_matrix <- as.matrix(heatmap_data[, feature_cols])


# Create color functions for annotations
updrs_col <- colorRamp2(
    breaks = c(min(na.omit(annotation_data$UPDRSIII)),
               median(na.omit(annotation_data$UPDRSIII)),
               max(na.omit(annotation_data$UPDRSIII))),
    colors = rev(brewer.pal(n = 7, name = "RdBu"))[c(1, 4, 7)]
)
speech_col <- colorRamp2(
    breaks = c(min(na.omit(annotation_data$Speech)),
               median(na.omit(annotation_data$Speech)),
               max(na.omit(annotation_data$Speech))),
    colors = rev(brewer.pal(n = 7, name = "RdBu"))[c(1, 4, 7)]
)
correlation_col <- colorRamp2(
    breaks = c(min(feature_correlation),
               median(feature_correlation),
               max(feature_correlation)),
    colors = rev(brewer.pal(n = 7, name = "RdBu"))[c(1, 4, 7)]
)
age_col <- colorRamp2(
    breaks = c(min(na.omit(annotation_data$Age)),
               median(na.omit(annotation_data$Age)),
               max(na.omit(annotation_data$Age))),
    colors = rev(brewer.pal(n = 7, name = "RdBu"))[c(1, 4, 7)]
)
weight_col <- colorRamp2(
    breaks = c(min(na.omit(annotation_data$Weight)),
               median(na.omit(annotation_data$Weight)),
               max(na.omit(annotation_data$Weight))),
    colors = rev(brewer.pal(n = 7, name = "RdBu"))[c(1, 4, 7)]
)
col_fun <- colorRamp2(
    breaks = c(-3, 0, 3),
    colors = rev(brewer.pal(n = 7, name = "RdBu"))[c(1, 4, 7)]
)
# discrete categorical colour mappings
sex_col    <- c("Male"   = "pink",
                "Female" = "turquoise")
status_col <- c("HC" = "green",
                "ON" = "blue",
                "OFF"= "red")
# For the row annotation
rowAnnotations <- rowAnnotation(
  Correlation = anno_simple(
    sort(feature_correlation, decreasing = FALSE), 
    col = correlation_col,
    simple_anno_size = unit(0.125, "cm"),
    na_col = "white",
  ),
  annotation_name_gp = gpar(fontsize = 4)

)

# For the top annotation
ha <- HeatmapAnnotation(
  UPDRSIII = anno_simple(
    annotation_data$UPDRSIII,
    col = updrs_col,
    simple_anno_size = unit(0.125, "cm")
  ),
  Speech = anno_simple(
    annotation_data$Speech,
    col = speech_col,
    simple_anno_size = unit(0.125, "cm")
  ),
  Age = anno_simple(
    annotation_data$Age,
    col = age_col,
    simple_anno_size = unit(0.125, "cm")
  ),
  Weight = anno_simple(
    annotation_data$Weight,
    col = weight_col,
    simple_anno_size = unit(0.125, "cm")
  ),
  Sex = anno_simple(
    annotation_data$Sex,
    col = sex_col,
    simple_anno_size = unit(0.125, "cm")
  ),
  Status = anno_simple(
    annotation_data$Status,
    col = status_col,
    simple_anno_size = unit(0.125, "cm")
  ),
  annotation_name_gp = gpar(fontsize = 4)
)

# Create heatmap with Status grouping
ht <- Heatmap(t(heatmap_matrix),
  col = col_fun,
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
    Legend(title = "Sex",
           at = names(sex_col),
           legend_gp = gpar(fill = sex_col)),
    Legend(title = "Status",
           at = names(status_col),
           legend_gp = gpar(fill = status_col))
)

# Draw the heatmap
draw(
  ht,
  annotation_legend_list  = lgd_list,      # custom order
  heatmap_legend_side     = "right",
  annotation_legend_side  = "right"
)
}

make_correlation_heatmap <- function(file_path, save_path){
png(save_path, width = 3000, height = 3000, units = "px", res = 300)
on.exit(dev.off())          # <- always executed, even on error
heatmap_data <- read.csv(file_path, row.names = 1)
# remove cols with non-numeric values
heatmap_data <- subset(heatmap_data, Status != "HC")
heatmap_data <- subset(heatmap_data, select = -c(Status, subjid, Sex))
correlation_data <- cor(heatmap_data, use = "pairwise.complete.obs", method = "spearman")
if ("UPDRSIII" %in% rownames(correlation_data)) {
  other <- setdiff(rownames(correlation_data), "UPDRSIII")
  new_order <- c(other, "UPDRSIII")
  correlation_data <- correlation_data[new_order, new_order]  # rows & cols
}
col_fun <- colorRamp2(
    breaks = c(-1, 0, 1),
    colors = rev(brewer.pal(n = 7, name = "RdBu"))[c(1, 4, 7)]
)
ht <- Heatmap(correlation_data,
              col = col_fun,
              cluster_rows = FALSE,
              cluster_columns = FALSE,
              show_row_names = TRUE,
              show_column_names = TRUE,
              show_heatmap_legend = FALSE,
              row_names_gp = gpar(fontsize = 6),
              column_names_gp = gpar(fontsize = 6))
lgd_list <- list(
    Legend(title = "Correlation", col_fun = col_fun)
)
draw(ht, annotation_legend_list = lgd_list)
}




csv_files <- list.files("./2157-Generated-Data/Clinical/Normalized/", pattern = "\\.csv$", full.names = TRUE, ignore.case = TRUE)
for (file_path in csv_files) {
    save_path <- gsub("\\.csv$", "_heatmap.png", file_path, ignore.case = TRUE)
    save_path <- gsub("Normalized", "Normalized/Heatmaps", save_path)
    make_distribution_heatmap(file_path, save_path)
}
csv_files <- list.files("./2157-Generated-Data/Clinical/Regular/", pattern = "\\.csv$", full.names = TRUE, ignore.case = TRUE)
for (file_path in csv_files) {
    save_path <- gsub("\\.csv$", "_correlation.png", file_path, ignore.case = TRUE)
    save_path <- gsub("Regular", "Regular/Heatmaps", save_path)
    make_correlation_heatmap(file_path, save_path)
}