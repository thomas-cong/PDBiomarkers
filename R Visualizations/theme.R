library(ggplot2)
library(grid)
library(circlize)
library(RColorBrewer)
library(ComplexHeatmap)

my_palette        <- c("#456e9d", "#f08127", "#6baeaa", "#509745", "#eac240", "#a66f97", "#ff929d", "#D22B2B", "#252525", "#ce1256","#8B4513")
names(my_palette) <- c("blue", "orange", "turquoise", "green", "yellow", "purple", "pink", "red", "black", "fusha","brown")
big_palette       <- c("#1f77b4","#aec7e8","#ff7f0e","#ffbb78","#2ca02c","#98df8a","#d62728",
                       "#ff9896","#9467bd","#c5b0d5","#8c564b","#c49c94","#e377c2","#f7b6d2",
                       "#7f7f7f","#c7c7c7","#bcbd22","#dbdb8d","#17becf","#9edae5","#000000")

# -- Set up for figures
theme_set(theme_bw(base_size = 12, base_family = "Helvetica"))

# -- Modifying plot elements globally
theme_update(
  axis.ticks        = element_line(color = "grey92"),
  axis.ticks.length = unit(.5, "lines"),
  panel.grid.minor  = element_blank(),
  legend.title      = element_text(size = 12),
  legend.text       = element_text(color = "grey30"),
  legend.background = element_rect(color = NA, fill = "#FBFCFC"), 
  legend.key        = element_rect(fill = "#FBFCFC"),
  legend.direction  = "horizontal",
  legend.position   = "top",
  plot.title        = element_text(size = 18, face = "bold"),
  plot.subtitle     = element_text(size = 12, color = "grey30"),
  plot.caption      = element_text(size = 9, margin = margin(t = 15)),
  plot.background   = element_rect(fill="#FBFCFC", color = "#FBFCFC"),
  panel.background  = element_rect(fill="#FBFCFC", color = NA),
  strip.text        = element_text(face = "bold", color = "white"),
  strip.background  = element_rect(fill = "#252525"))