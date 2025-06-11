library(ggplot2)
ggsave <- function(..., bg = 'white') ggplot2::ggsave(..., bg = bg)

library(reshape2)
library(dplyr)
library(tidyr)
library(ggthemes)
heatmap_data <- read.csv("2157-Generated-Data/2157-Clinical-Biomarkers-Normalized.csv")
heatmap_long_data <- heatmap_data %>%
    select(-any_of("subjid")) %>% 
    pivot_longer(cols = -c(winterlight_id, Status),      
                 names_to = "biomarker", 
                 values_to = "value") %>%     
    mutate(
        winterlight_id = as.factor(winterlight_id),
        Status = as.factor(Status) 
    )
hm <-ggplot(heatmap_long_data, aes(x = winterlight_id, y = biomarker, fill = value)) +
  geom_tile() +
  scale_fill_gradient2(low = "blue", mid = "white", high = "red", midpoint = 0) +
  labs(title = "Heatmap of Biomarker Values by Status") + 
  facet_grid(~ Status, scales = "free_x", space = "free_x") + 
  theme_tufte(base_family="Helvetica") + theme(
    axis.title.x=element_blank(),
    axis.text.x=element_blank(),
    axis.ticks.x=element_blank()
    )
ggsave("heatmap.png", plot = hm, width = 24, height = 8, dpi = 300)