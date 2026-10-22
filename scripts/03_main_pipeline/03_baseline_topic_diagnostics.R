# Reproduce the main-sample reference-topic rule in Section 3.7.1.
# Input: the existing final regression sample; no article texts are required.
script_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_argument) != 1L) stop("Run this script with Rscript.")
script_dir <- dirname(normalizePath(sub("^--file=", "", script_argument)))
package_root <- normalizePath(file.path(script_dir, "../.."))
d <- read.csv(file.path(package_root, "data", "derived", "analysis_dataset_seed_42.csv"), check.names = FALSE)
d$Funding_Sources <- factor(d$Funding_Sources, levels = c("Other Sources", "Foreign Gov-Affiliated"))
stopifnot(nrow(d) == 3251L, all(d$Final_Stance %in% c(-1, 0, 1)))
diagnostics <- do.call(rbind, lapply(1:20, function(topic) {
  column <- paste0("Topic_", topic)
  m <- lm(reformulate("Funding_Sources", column), data = d)
  data.frame(Seed = 42L, N = nrow(d), Topic = topic,
             Mean_Proportion = mean(d[[column]]),
             Univariate_Group_P_Value = summary(m)$coefficients[2L, "Pr(>|t|)"])
}))
diagnostics$Eligible_Mean_Above_5_Percent <- diagnostics$Mean_Proportion > 0.05
eligible <- diagnostics[diagnostics$Eligible_Mean_Above_5_Percent, ]
eligible <- eligible[order(eligible$Univariate_Group_P_Value, decreasing = TRUE), ]
selected <- eligible$Topic[1L]
diagnostics$Selected_Reference <- diagnostics$Topic == selected
eligible$Selected_Reference <- eligible$Topic == selected
eligible$Candidate_Rank <- seq_len(nrow(eligible))
stopifnot(selected == 19L, nrow(eligible) == 9L)
out_dir <- file.path(package_root, "outputs", "tables")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write.csv(diagnostics, file.path(out_dir, "baseline_topic_diagnostics_seed_42.csv"), row.names = FALSE)
write.csv(eligible, file.path(out_dir, "baseline_topic_candidates_seed_42.csv"), row.names = FALSE)
cat("Reference T", selected, " selected from ", nrow(eligible), " eligible topics in the regression sample.\n", sep = "")
print(eligible, row.names = FALSE)
