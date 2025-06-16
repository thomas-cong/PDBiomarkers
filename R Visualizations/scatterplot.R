library(ggplot2)


make_scatterplot <- function(feature, file_path, save_path){
data <- read.csv(file_path)
feature_vectors <- subset(data, 
                          select = c("subjid",
                                     "Status",
                                     feature,
                                     "Age",
                                     "Sex",
                                     "UPDRSIII"))
feature_vectors$UPDRSIII <- as.numeric(as.character(feature_vectors$UPDRSIII))
feature_vectors$Age <- as.numeric(feature_vectors$Age)

# drop the ON/OFF suffix to get the subject ID common to both
feature_vectors$pair_id <- sub("(ON|OFF)$", "", 
                               feature_vectors$subjid, 
                               ignore.case = TRUE)
# make sure Sex is a factor so ggplot treats it as discrete
feature_vectors$Sex <- factor(feature_vectors$Sex)

p <- ggplot(feature_vectors,
            aes(x = Status, y = .data[[feature]])) +
  geom_boxplot(outlier.shape = NA,
               linewidth = 1.5,
               fill = "white") +
  geom_line(aes(group = pair_id),
            alpha = 0.4,
            position = position_dodge(0.30),
            linewidth = 1.5) +
  geom_point(aes(group  = pair_id,
                 shape  = Sex,   # Sex → shape
                 colour = UPDRSIII,
                 size   = Age),
            alpha     = 0.8,
            position  = position_dodge(0.30),
            ) +
            scale_size(range = c(2, 10)) +
            scale_colour_gradient2(low = "#2600ff",
                                   mid = "white",
                                   high = "#ff0000") +
            theme_bw(base_size = 15) +
            theme(axis.text  = element_text(size = 15, colour = "black"),
                  axis.title = element_text(size = 15, colour = "black"),
                  strip.text = element_text(size = 15))
ggsave(save_path, p)
}
for (file in list.files("./2157-Generated-Data/Clinical/Regular/",
                        pattern = "\\.csv$",
                        full.names = TRUE,
                        ignore.case = TRUE)){
  folder <- gsub("\\.csv$", "", file, ignore.case = TRUE)
  folder <- gsub("Regular", "Regular/Scatterplots", folder)
  dir.create(folder, recursive = TRUE, showWarnings = FALSE)
  features <- read.csv(file)
  for (feature in colnames(features)){
    save_path <- file.path(folder, paste0(feature, "_scatterplot.png"))
    make_scatterplot(feature, file, save_path)
  }
}