#!/usr/bin/env Rscript
# Recalculate all validation summaries from the 100 public paired labels.
file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
source(file.path(dirname(sub("^--file=", "", file_arg[1])), "public_results_helpers.R"))
opts <- public_options("validation")
public_require(c("readxl", "ggplot2", "svglite"))
suppressPackageStartupMessages(library(ggplot2))
path <- file.path(opts$root, "data", "validation")
d <- as.data.frame(readxl::read_excel(file.path(path, "gold_standard_validation_100.xlsx")))
labels <- c(-99, -1, 0, 1)
h <- as.numeric(d$Human_Score); l <- as.numeric(d$LLM_Score)
if (nrow(d) != 100 || anyNA(c(h, l)) || any(!c(h, l) %in% labels) ||
    anyDuplicated(d$Doc_ID)) stop("Expected 100 unique, complete paired labels")

# Nominal Krippendorff alpha with finite-sample coincidence correction.
alpha_nominal <- function(a, b) {
  if (length(a) < 2) return(NA_real_)
  counts <- table(c(a, b)); n <- length(a)
  expected <- 1 - sum(counts * (counts - 1)) / (2 * n * (2 * n - 1))
  if (expected == 0) return(NA_real_)
  1 - mean(a != b) / expected
}
row_metric <- function(task, a, b) data.frame(Task = task, N = length(a),
  Alpha = alpha_nominal(a, b), Accuracy = mean(a == b))
both <- h != -99 & l != -99
metrics <- rbind(row_metric("Joint labels (nominal)", h, l),
  row_metric("Target applicability (nominal)", h != -99, l != -99),
  row_metric("Stance, both applicable (nominal)", h[both], l[both]))
cm <- as.data.frame(table(Human = factor(h, levels = labels), LLM = factor(l, levels = labels)))
cm$Human <- as.numeric(as.character(cm$Human)); cm$LLM <- as.numeric(as.character(cm$LLM))
per_class <- do.call(rbind, lapply(labels, function(k) {
  support <- sum(h == k); predicted <- sum(l == k); tp <- sum(h == k & l == k)
  data.frame(Class = k, Support = support, Predicted = predicted,
    Precision = if (predicted) tp / predicted else NA_real_,
    Recall = if (support) tp / support else NA_real_,
    F1 = if (support + predicted) 2 * tp / (support + predicted) else NA_real_)
}))
results <- list(validation_metrics = metrics, validation_confusion_matrix = cm,
                validation_per_class = per_class)
for (name in names(results)) {
  expected <- public_read(file.path(path, paste0(name, ".csv")))
  actual <- results[[name]]
  # Stored tables may have a different row order.
  key <- names(actual)[1]
  if (name == "validation_confusion_matrix") {
    actual <- actual[order(actual$Human, actual$LLM), ]
    expected <- expected[order(expected$Human, expected$LLM), ]
  } else {
    actual <- actual[order(actual[[key]]), ]; expected <- expected[order(expected[[key]]), ]
  }
  public_equal(actual, expected, name)
}
print(metrics, row.names = FALSE)
if (!opts$check) {
  dir.create(opts$output, recursive = TRUE, showWarnings = FALSE)
  for (name in names(results)) write.csv(results[[name]],
    file.path(opts$output, paste0(name, ".csv")), row.names = FALSE, na = "")
  cm$Human <- factor(cm$Human, levels = rev(labels))
  cm$LLM <- factor(cm$LLM, levels = labels)
  p <- ggplot(cm, aes(LLM, Human, fill = Freq)) +
    geom_tile(colour = "#DDDDDD", linewidth = .4) +
    geom_text(aes(label = Freq, colour = Freq > 25), size = 4.2, show.legend = FALSE) +
    scale_colour_manual(values = c("FALSE" = "#303030", "TRUE" = "white")) +
    scale_fill_gradient(low = "white", high = "#1B7A60", name = "Anzahl") +
    coord_equal() + labs(x = "LLM-Codierung", y = "Manuelle Codierung",
      title = "Manuelle und LLM-basierte Codierung", subtitle = "Unabhängige Validierung · N = 100",
      caption = "−99: Ziel nicht anwendbar; −1: negativ; 0: neutral; +1: positiv.") + public_theme() +
    theme(panel.grid = element_blank())
  public_save(p, file.path(opts$output, "validation_confusion_matrix"), 7.5, 6.4)
  cat("Outputs:", opts$output, "\n")
}
cat("All three stored validation tables agree.\n")
