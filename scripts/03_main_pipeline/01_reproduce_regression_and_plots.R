# ==============================================================================
# Replikationsskript: OLS-Regressionsmodelle (M1 & M2) und Schaetzung der Medieneffekte
# Projekt: Hybride Inhaltsanalyse mit Structural Topic Models und Large Language Models (Hauptmodell Seed 42)
# ==============================================================================

suppressPackageStartupMessages({
  library(tidyverse)
  library(broom)
  library(ggeffects)
  library(scales)
})

# ------------------------------------------------------------------------------
# 1. Pfaddefinition und Einlesen der abgeleiteten Analysedaten
# ------------------------------------------------------------------------------
# Automatische Ermittlung des Projekt-Wurzelverzeichnisses
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
data_file <- file.path(project_root, "data", "derived", "analysis_dataset_seed_42.csv")

if (!file.exists(data_file)) {
  stop("Analysedatensatz nicht gefunden: ", data_file)
}

cat("Lese abgeleiteten Analysedatensatz ein: ", data_file, "\n")
df <- read_csv(data_file, show_col_types = FALSE)

# ------------------------------------------------------------------------------
# 2. Datenvorbereitung und deutsche Beschriftungskonventionen
# ------------------------------------------------------------------------------
# Bereinigung auf evaluierbare Stichprobe (Ausschluss der nicht zutreffenden Faelle -99)
df_model <- df %>%
  filter(Final_Stance %in% c(-1, 0, 1)) %>%
  mutate(
    Final_Stance = as.numeric(Final_Stance),
    Funding_Sources = as.factor(Funding_Sources),
    Is_Taiwan = as.numeric(Is_Taiwan)
  )

# Setzen der Referenzkategorie: "Other Sources" (Nicht-staatlich finanzierte Medien)
df_model$Funding_Sources <- relevel(df_model$Funding_Sources, ref = "Other Sources")

cat("Stichprobengroesse fuer Regressionsanalyse:", nrow(df_model), "Artikel\n")

funding_labels_de <- c(
  "Other Sources" = "Medien mit anderen\nFinanzierungsquellen",
  "Foreign Gov-Affiliated" = "Staatlich bzw. öffentlich\nfinanzierte Medien"
)

# ------------------------------------------------------------------------------
# 3. Schaetzung von Modell 1 (Pfad 1 / M1: Basiseffekt ohne Themenkontrolle)
# ------------------------------------------------------------------------------
cat("\n=======================================================\n")
cat("Modell 1 (M1): OLS-Regression ohne Themenkontrolle\n")
cat("=======================================================\n")

model_m1 <- lm(Final_Stance ~ Funding_Sources + Is_Taiwan, data = df_model)
print(summary(model_m1))

# ------------------------------------------------------------------------------
# 4. Schaetzung von Modell 2 (Pfad 2 / M2: Vollstaendiges Modell mit 19 Themenanteilen)
# ------------------------------------------------------------------------------
cat("\n=======================================================\n")
cat("Modell 2 (M2): OLS-Regression mit 19 Themenkontrollen (Basis: Thema 19)\n")
cat("=======================================================\n")

# Definition der 19 Kontrollthemen. T19 erfuellt in der Hauptstichprobe die
# Regel aus Abschnitt 3.7.1: mittlerer Anteil > 5 Prozent und darunter der
# hoechste p-Wert im univariaten Finanzierungsgruppenvergleich.
# Kandidatentabelle: Rscript scripts/03_main_pipeline/03_baseline_topic_diagnostics.R
control_topics <- paste0("Topic_", c(1:18, 20))
formula_m2_str <- paste("Final_Stance ~ Funding_Sources + Is_Taiwan +", paste(control_topics, collapse = " + "))
formula_m2 <- as.formula(formula_m2_str)

model_m2 <- lm(formula_m2, data = df_model)
print(summary(model_m2))

# ------------------------------------------------------------------------------
# 5. Koeffizientenvergleich und Effektverschiebung (M1 vs. M2)
# ------------------------------------------------------------------------------
tidy_m1 <- tidy(model_m1) %>% mutate(Model = "Modell 1 (ohne Themenkontrolle)")
tidy_m2 <- tidy(model_m2) %>% mutate(Model = "Modell 2 (mit Themenkontrolle)")

combined_tidy <- bind_rows(tidy_m1, tidy_m2) %>%
  filter(term == "Funding_SourcesForeign Gov-Affiliated")

beta_m1 <- tidy_m1$estimate[tidy_m1$term == "Funding_SourcesForeign Gov-Affiliated"]
beta_m2 <- tidy_m2$estimate[tidy_m2$term == "Funding_SourcesForeign Gov-Affiliated"]
shift_pct <- ((beta_m2 - beta_m1) / abs(beta_m1)) * 100

cat("\n--- Koeffizientenvergleich fuer staatliche Finanzierung ---\n")
cat(sprintf("Modell 1 Koeffizient (Beta):  %.4f\n", beta_m1))
cat(sprintf("Modell 2 Koeffizient (Beta'): %.4f\n", beta_m2))
cat(sprintf("Relative Veraenderung:        %.2f%%\n", shift_pct))

# ------------------------------------------------------------------------------
# 6. Grafische Reproduktion der marginalen Effekte
# ------------------------------------------------------------------------------
output_fig_dir <- file.path(project_root, "outputs", "figures")
if (!dir.exists(output_fig_dir)) {
  dir.create(output_fig_dir, recursive = TRUE)
}

# Vorhergesagte Haltungswerte fuer M1
pred_m1 <- ggpredict(model_m1, terms = "Funding_Sources")
plot_m1 <- plot(pred_m1) +
  labs(
    title = "Vorhergesagte Haltung zur chinesischen Regierung (Modell 1)",
    subtitle = "Basismodell M1 (ohne Kontrolle der Themenzusammensetzung)",
    x = "Finanzierungsgruppe",
    y = "Vorhergesagter Stance-Wert (−1 = Ablehnend, 0 = Neutral, +1 = Befürwortend)"
  ) +
  scale_x_discrete(labels = funding_labels_de) +
  theme_minimal(base_size = 12)

# Vorhergesagte Haltungswerte fuer M2
pred_m2 <- ggpredict(model_m2, terms = "Funding_Sources")
plot_m2 <- plot(pred_m2) +
  labs(
    title = "Vorhergesagte Haltung zur chinesischen Regierung (Modell 2)",
    subtitle = "Modell M2 (bereinigt um 19 Themenanteile; Basis: Thema 19)",
    x = "Finanzierungsgruppe",
    y = "Vorhergesagter Stance-Wert (−1 = Ablehnend, 0 = Neutral, +1 = Befürwortend)"
  ) +
  scale_x_discrete(labels = funding_labels_de) +
  theme_minimal(base_size = 12)

ggsave(file.path(output_fig_dir, "Path1_Model1_Predicted_Stance_Replication.png"), plot = plot_m1, width = 8.5, height = 6, dpi = 300, bg = "white")
ggsave(file.path(output_fig_dir, "Path2_Model2_Predicted_Stance_Replication.png"), plot = plot_m2, width = 8.5, height = 6, dpi = 300, bg = "white")

# Finanzierungskoeffizient: dieselbe Darstellung im Hauptordner und unter Seed 42.
funding_coef_result <- make_funding_coefficient_plot(model_m1, model_m2)
plot_coef <- funding_coef_result$plot
for (figure_dir in c(output_fig_dir, file.path(output_fig_dir, "seed_42"))) {
  save_funding_coefficient_plot(funding_coef_result, figure_dir)
}

# ------------------------------------------------------------------------------
# 7. Vollstaendiges Regressions-Forest-Table-Diagramm (M1 vs. M2)
# ------------------------------------------------------------------------------
topic_names <- read_csv(file.path(project_root, "data", "derived", "stm", "seed_42", "topic_names.csv"),
                        show_col_types = FALSE)
forest_result <- make_full_model_forest_plot(model_m1, model_m2, topic_names, seed = 42)
p_forest_table <- forest_result$plot
save_full_model_forest_plot(forest_result, file.path(output_fig_dir, "seed_42"))
cat("Vollstaendiges Forest-Table-Diagramm gespeichert in outputs/figures/seed_42.\n")

cat("\nGrafiken erfolgreich gespeichert unter: ", output_fig_dir, "\n")
