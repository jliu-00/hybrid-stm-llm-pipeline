# ==============================================================================
# Robustheitsanalyse: Replikation der parallelen Zufallsstichproben (Seeds 12345 & 2024)
# Projekt: Hybride Inhaltsanalyse mit Structural Topic Models und Large Language Models
# ==============================================================================

suppressPackageStartupMessages({
  library(tidyverse)
  library(broom)
})

get_script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg[1]))))
  }
  return(getwd())
}

script_dir <- get_script_dir()
project_root <- normalizePath(file.path(script_dir, "../.."), mustWork = FALSE)
source(file.path(project_root, "scripts", "03_main_pipeline", "02_funding_coefficient_plot.R"))
source(file.path(project_root, "scripts", "03_main_pipeline", "full_model_forest_plot.R"))

estimate_seed <- function(seed_num) {
  file_path <- file.path(project_root, "data", "derived", paste0("analysis_dataset_seed_", seed_num, ".csv"))
  if (!file.exists(file_path)) {
    stop("Datensatz nicht gefunden: ", file_path)
  }
  
  df <- read_csv(file_path, show_col_types = FALSE) %>%
    filter(Final_Stance %in% c(-1, 0, 1)) %>%
    mutate(
      Final_Stance = as.numeric(Final_Stance),
      Funding_Sources = as.factor(Funding_Sources),
      Is_Taiwan = as.numeric(Is_Taiwan)
    )
  df$Funding_Sources <- relevel(df$Funding_Sources, ref = "Other Sources")
  
  # Modell 1 (ohne Themenkontrolle)
  m1 <- lm(Final_Stance ~ Funding_Sources + Is_Taiwan, data = df)
  beta1 <- coef(m1)["Funding_SourcesForeign Gov-Affiliated"]
  se1 <- summary(m1)$coefficients["Funding_SourcesForeign Gov-Affiliated", "Std. Error"]
  p1 <- summary(m1)$coefficients["Funding_SourcesForeign Gov-Affiliated", "Pr(>|t|)"]
  r2_1 <- summary(m1)$r.squared
  adj_r2_1 <- summary(m1)$adj.r.squared
  ci1 <- confint(m1)["Funding_SourcesForeign Gov-Affiliated", ]
  
  # Modell 2: dieselbe seed-spezifische Referenzregel wie in der vollstaendigen Pipeline.
  reference_topic <- select_regression_reference_topic(df, seed_num)
  control_topics <- paste0("Topic_", setdiff(1:20, reference_topic))
  f2 <- as.formula(paste("Final_Stance ~ Funding_Sources + Is_Taiwan +", paste(control_topics, collapse = " + ")))
  m2 <- lm(f2, data = df)
  beta2 <- coef(m2)["Funding_SourcesForeign Gov-Affiliated"]
  se2 <- summary(m2)$coefficients["Funding_SourcesForeign Gov-Affiliated", "Std. Error"]
  p2 <- summary(m2)$coefficients["Funding_SourcesForeign Gov-Affiliated", "Pr(>|t|)"]
  r2_2 <- summary(m2)$r.squared
  adj_r2_2 <- summary(m2)$adj.r.squared
  ci2 <- confint(m2)["Funding_SourcesForeign Gov-Affiliated", ]

  # Stichprobenspezifische Koeffizienten, Intervalle, p-Werte und Fallzahlen.
  funding_coef_result <- make_funding_coefficient_plot(m1, m2)
  save_funding_coefficient_plot(
    funding_coef_result,
    file.path(project_root, "outputs", "figures", paste0("seed_", seed_num))
  )
  
  # Vollstaendige Tabelle: keine Kopie der Themenlabels oder Schaetzungen von Seed 42.
  topic_names <- read_csv(file.path(project_root, "data", "derived", "stm",
    paste0("seed_", seed_num), "topic_names.csv"), show_col_types = FALSE)
  forest_result <- make_full_model_forest_plot(m1, m2, topic_names, seed_num)
  save_full_model_forest_plot(forest_result,
    file.path(project_root, "outputs", "figures", paste0("seed_", seed_num)))

  shift <- ((beta2 - beta1) / abs(beta1)) * 100
  stars <- if (p1 < 0.001) "***" else if (p1 < 0.01) "**" else if (p1 < 0.05) "*" else ""
  
  tibble(
    Seed = as.character(seed_num),
    N = nrow(df),
    `M1_Beta (SE)` = sprintf("%.4f (%.4f)%s", beta1, se1, stars),
    `M1_p_Wert` = p1,
    `M1_CI_Lower` = unname(ci1[1]),
    `M1_CI_Upper` = unname(ci1[2]),
    `M1_R2` = sprintf("%.4f", r2_1),
    `M1_Adjusted_R2` = sprintf("%.4f", adj_r2_1),
    `M2_Beta (SE)` = sprintf("%.4f (%.4f)", beta2, se2),
    `M2_p_Wert` = sprintf("%.4f", p2),
    `M2_CI_Lower` = unname(ci2[1]),
    `M2_CI_Upper` = unname(ci2[2]),
    `M2_R2` = sprintf("%.4f", r2_2),
    `M2_Adjusted_R2` = sprintf("%.4f", adj_r2_2),
    `Veraenderung (%)` = sprintf("%.2f%%", shift)
  )
}

cat("==============================================================================\n")
cat("Robustheitspruefung ueber drei Zufallsstichproben (Seeds 42, 12345, 2024)\n")
cat("==============================================================================\n")

results <- bind_rows(
  estimate_seed(42),
  estimate_seed(12345),
  estimate_seed(2024)
)

print(as.data.frame(results), row.names = FALSE)

out_table <- file.path(project_root, "outputs", "tables", "robustness_seeds_comparison.csv")
dir.create(dirname(out_table), recursive = TRUE, showWarnings = FALSE)
write_csv(results, out_table)
cat("\nErgebnistabelle gespeichert unter: ", out_table, "\n")
