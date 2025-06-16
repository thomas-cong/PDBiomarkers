data <- read.csv("./2157-Generated-Data/Clinical/Regular/2157-Clinical-Biomarkers.csv")
feature_vectors <- subset(data, select = ("aavs"))
View(feature_vectors)
