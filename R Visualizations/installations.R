packages <- list("BiocManager","ggplot2", "styler", "reshape2", "dplyr", "tidyr", "RColorBrewer")

# Install packages if they are not already installed
for (pkg in packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg)
  }
}
BiocManager::install("ComplexHeatmap")