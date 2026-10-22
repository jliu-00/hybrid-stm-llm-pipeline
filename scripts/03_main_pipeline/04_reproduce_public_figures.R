#!/usr/bin/env Rscript
# Replot saved STM results and refit the public regression models. No model files.
file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
source(file.path(dirname(sub("^--file=", "", file_arg[1])), "public_results_helpers.R"))
opts <- public_options("figures", allow_seeds = TRUE)
source(file.path(opts$root, "scripts/03_main_pipeline/full_model_forest_plot.R"))
public_require(c("ggplot2", "readxl", "svglite", "ragg", "broom"))
suppressPackageStartupMessages(library(ggplot2))
comparisons <- public_read(file.path(opts$root, "outputs/tables/robustness_seeds_comparison.csv"))
topic_columns <- paste0("Topic_", 1:20)
k_labels <- c(heldout = "Held-out-Likelihood", residual = "Residualdispersion",
              semcoh = "Semantische Kohärenz", lbound = "Variationsuntergrenze (ELBO)")

for (seed in opts$seeds) {
  src <- file.path(opts$root, "data/derived/stm", paste0("seed_", seed))
  out <- file.path(opts$output, paste0("seed_", seed))
  theta <- public_read(file.path(src, "theta_all_stm_documents.csv"), c("Doc_ID", topic_columns))
  mat <- as.matrix(theta[topic_columns])
  if (anyNA(mat) || any(!is.finite(mat)) || any(mat < 0) ||
      max(abs(rowSums(mat) - 1)) > 1e-8 || anyDuplicated(theta$Doc_ID)) stop("Invalid theta")
  expected_n <- c(`42` = 3483, `2024` = 3484, `12345` = 3485)[as.character(seed)]
  if (nrow(theta) != expected_n) stop("Unexpected STM sample size")
  names_df <- public_read(file.path(src, "topic_names.csv"), c("Topic", "Title_DE"))
  if (!setequal(names_df$Topic, 1:20) || anyDuplicated(names_df$Topic)) stop("Invalid topic names")
  words <- as.data.frame(readxl::read_excel(file.path(src, "topic_frex_keywords_german.xlsx")))
  words$Topic <- as.integer(gsub("[^0-9]", "", words$Topic_Num))
  if (!setequal(words$Topic, 1:20) || anyDuplicated(words$Topic)) stop("Invalid FREX topics")
  prevalence <- data.frame(Topic = 1:20, Mean_Proportion = colMeans(mat))
  prevalence$Title_DE <- names_df$Title_DE[match(prevalence$Topic, names_df$Topic)]
  prevalence$FREX <- apply(words[match(prevalence$Topic, words$Topic), paste("Keyword", 1:10)],
    1, function(x) paste(x, collapse = "; "))
  prevalence <- prevalence[order(prevalence$Mean_Proportion), ]
  prevalence$label <- public_wrap(paste0("T", prevalence$Topic, " · ", prevalence$Title_DE), 37)
  prevalence$label <- factor(prevalence$label, levels = prevalence$label)
  diag <- public_read(file.path(src, "search_k_diagnostics.csv"), c("K", names(k_labels)))
  if (anyNA(diag[c("K", names(k_labels))]) || anyDuplicated(diag$K) || !20 %in% diag$K)
    stop("Invalid K diagnostics")
  agenda <- public_read(file.path(src, "agenda_effects_with_intervals.csv"),
    c("topic_num", "estimate", "conf.low", "conf.high", "p.value"))
  if (!setequal(agenda$topic_num, 1:20) || anyDuplicated(agenda$topic_num) ||
      anyNA(agenda[c("estimate", "conf.low", "conf.high", "p.value")]) ||
      any(agenda$conf.low > agenda$estimate) || any(agenda$conf.high < agenda$estimate))
    stop("Invalid saved agenda intervals")
  agenda <- agenda[order(agenda$topic_num, decreasing = TRUE), ]
  agenda$label <- public_wrap(paste0("T", agenda$topic_num, " · ",
    names_df$Title_DE[match(agenda$topic_num, names_df$Topic)]), 43)
  agenda$label <- factor(agenda$label, levels = agenda$label)
  d <- public_read(file.path(opts$root, "data/derived", paste0("analysis_dataset_seed_", seed, ".csv")),
    c("Final_Stance", "Funding_Sources", "Is_Taiwan", topic_columns, "Doc_ID"))
  if (any(!d$Final_Stance %in% c(-1, 0, 1)) || anyDuplicated(d$Doc_ID)) stop("Invalid regression labels")
  # Check that regression rows retain the original full-STM topic proportions.
  idx <- match(d$Doc_ID, theta$Doc_ID)
  if (anyNA(idx)) stop("Regression Doc_ID absent from theta")
  public_equal(as.matrix(d[topic_columns]), mat[idx, ], "regression/theta", 1e-12)
  d$Funding_Sources <- relevel(factor(d$Funding_Sources), "Other Sources")
  reference_topic <- select_regression_reference_topic(d, seed)
  models <- list(M1 = lm(Final_Stance ~ Funding_Sources + Is_Taiwan, d),
    M2 = lm(reformulate(c("Funding_Sources", "Is_Taiwan", paste0("Topic_", setdiff(1:20, reference_topic))),
                       "Final_Stance"), d))
  coefficients <- do.call(rbind, lapply(names(models), function(name) {
    m <- models[[name]]; term <- "Funding_SourcesForeign Gov-Affiliated"
    ci <- confint(m)[term, ]; s <- summary(m)
    if (nobs(m) != nrow(d)) stop("Regression silently omitted rows")
    data.frame(Seed = seed, Model = name, N = nobs(m), Estimate = coef(m)[term],
      SE = s$coefficients[term, "Std. Error"], P = s$coefficients[term, "Pr(>|t|)"],
      CI_Lower = ci[1], CI_Upper = ci[2], R2 = s$r.squared, Adjusted_R2 = s$adj.r.squared,
      row.names = NULL)
  }))
  saved <- comparisons[comparisons$Seed == seed, ]
  if (nrow(saved) != 1) stop("Missing seed in stored comparison")
  for (i in 1:2) {
    prefix <- coefficients$Model[i]
    public_equal(coefficients$N[i], saved$N, "model N")
    for (field in c("R2", "Adjusted_R2"))
      public_equal(round(coefficients[[field]][i], 4), saved[[paste0(prefix, "_", field)]], field)
    for (field in c("CI_Lower", "CI_Upper"))
      public_equal(coefficients[[field]][i], saved[[paste0(prefix, "_", field)]], field)
  }
  cat("Seed", seed, ": theta, saved intervals and regression comparison verified\n")
  forest_result <- make_full_model_forest_plot(models$M1, models$M2, names_df, seed)
  if (opts$check) next
  dir.create(out, recursive = TRUE, showWarnings = FALSE)
  save_full_model_forest_plot(forest_result, out)
  write.csv(prevalence[c("Topic", "Title_DE", "Mean_Proportion", "FREX")],
            file.path(out, "topic_prevalence_plot_data.csv"), row.names = FALSE)
  write.csv(coefficients, file.path(out, "coefficient_plot_data.csv"), row.names = FALSE)
  for (metric in names(k_labels)) {
    plot_d <- diag[order(diag$K), ]; plot_d$value <- plot_d[[metric]]
    p <- ggplot(plot_d, aes(K, value)) + geom_line(colour = "#1B7A60", linewidth = .7) +
      geom_point(colour = "#1B7A60", size = 2) +
      geom_vline(xintercept = 20, linetype = "dashed", colour = "#777777") +
      scale_x_continuous(breaks = diag$K) + labs(x = "Themenzahl K", y = k_labels[[metric]],
        title = k_labels[[metric]], subtitle = paste0("Seed ", seed),
        caption = "Gestrichelte Linie: gewähltes K = 20. Gespeicherte Diagnosewerte.") + public_theme()
    public_save(p, file.path(out, paste0("search_k_", metric)), 7.5, 5)
  }
  max_mean <- max(prevalence$Mean_Proportion) * 100
  p <- ggplot(prevalence, aes(Mean_Proportion * 100, label)) +
    geom_col(fill = "#8BA09E", width = .62) +
    geom_text(aes(x = max_mean * 1.15, label = public_wrap(FREX, 87)),
              hjust = 0, size = 2.85, lineheight = 1.1) +
    scale_x_continuous(limits = c(0, max_mean * 4),
      breaks = pretty(c(0, max_mean)), expand = expansion(mult = c(0, .01))) +
    labs(x = "Mittlerer Themenanteil (%) · rechts: zehn deutsche FREX-Wörter", y = NULL,
      title = "Themenprävalenz und FREX-Wörter", subtitle = paste0("Seed ", seed,
        " · alle ", nrow(theta), " gültigen STM-Dokumente")) + public_theme() +
    theme(axis.text.y = element_text(size = 9), panel.grid = element_blank())
  public_save(p, file.path(out, "overall_topic_prevalence_frex"), 14, 13)
  p <- ggplot(agenda, aes(estimate, label)) +
    geom_vline(xintercept = 0, linetype = "dashed", colour = "#777777") +
    geom_segment(aes(x = conf.low, xend = conf.high, yend = label),
                 colour = "#1B7A60", linewidth = .7) +
    geom_point(colour = "#1B7A60", size = 2) +
    labs(x = "Differenz des Themenanteils", y = NULL, title = "Finanzierungsgruppen und Themenanteile",
      subtitle = paste0("Seed ", seed, " · gespeicherte STM-Schätzungen"),
      caption = "Punkte: staatlich/öffentlich finanzierte Medien minus andere Finanzierungsquellen.\nLinien: gespeicherte 95%-Intervalle; Kovariate: Taiwan-Merkmal.") + public_theme()
  public_save(p, file.path(out, "agenda_effects"), 10.5, 10)
  coefficients$Model <- factor(coefficients$Model, levels = c("M2", "M1"))
  p <- ggplot(coefficients, aes(Estimate, Model)) +
    geom_vline(xintercept = 0, linetype = "dashed", colour = "#777777") +
    geom_segment(aes(x = CI_Lower, xend = CI_Upper, yend = Model),
                 colour = "#1B7A60", linewidth = .9) +
    geom_point(colour = "#1B7A60", size = 3) +
    scale_y_discrete(labels = c(M1 = "M1: ohne Themenkontrolle", M2 = "M2: mit Themenkontrolle")) +
    labs(x = "Finanzierungskoeffizient (OLS)", y = NULL, title = "Finanzierungskoeffizient vor und nach Themenkontrolle",
      subtitle = paste0("Seed ", seed, " · N = ", nrow(d)),
      caption = paste0("Linien: 95%-Konfidenzintervalle (t-Verteilung). Beide Modelle kontrollieren das Taiwan-Merkmal.\nM2 enthält 19 Themenanteile; ausgelassenes Referenzthema: T", reference_topic, ".")) + public_theme()
  public_save(p, file.path(out, "coefficient_comparison"), 10, 4.5)
}
if (!opts$check) cat("Outputs:", opts$output, "\n")
