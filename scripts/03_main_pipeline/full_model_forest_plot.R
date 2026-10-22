# Vollstaendige Koeffiziententabelle mit Forest-Plot fuer jeden Seed.
# Themenbezeichnungen und Referenzthema stammen immer aus demselben Modell.
select_regression_reference_topic <- function(data, seed) {
  topics <- grep("^Topic_[0-9]+$", names(data), value = TRUE)
  topic_ids <- as.integer(sub("Topic_", "", topics, fixed = TRUE))
  stopifnot(setequal(topic_ids, 1:20), all(is.finite(as.matrix(data[topics]))),
            max(abs(rowSums(data[topics]) - 1)) < 1e-8)
  if (as.character(seed) == "42") {
    # Hauptstichprobe: Anteil > 5 Prozent, dann groesster univariater Gruppen-p-Wert.
    eligible <- colMeans(data[topics]) > 0.05
    scores <- vapply(topics, function(topic) {
      model <- stats::lm(stats::reformulate("Funding_Sources", topic), data = data)
      summary(model)$coefficients["Funding_SourcesForeign Gov-Affiliated", "Pr(>|t|)"]
    }, numeric(1))
    scores[!eligible] <- -Inf
  } else {
    # Originalregel der Zusatzstichproben: hoechster p-Wert beider Kovariaten.
    scores <- vapply(topics, function(topic) {
      model <- stats::lm(stats::reformulate(c("Funding_Sources", "Is_Taiwan"), topic), data = data)
      max(summary(model)$coefficients[-1, "Pr(>|t|)"])
    }, numeric(1))
  }
  if (!any(is.finite(scores))) stop("Kein gueltiges Referenzthema gefunden.")
  topic_ids[which.max(scores)]
}

make_full_model_forest_plot <- function(model_m1, model_m2, topic_names, seed) {
  funding_term <- "Funding_SourcesForeign Gov-Affiliated"
  stopifnot(all(c("Topic", "Title_DE") %in% names(topic_names)),
            !anyDuplicated(topic_names$Topic), setequal(topic_names$Topic, 1:20),
            !anyNA(topic_names$Title_DE), all(nzchar(topic_names$Title_DE)),
            identical(rownames(stats::model.frame(model_m1)), rownames(stats::model.frame(model_m2))),
            identical(levels(stats::model.frame(model_m1)$Funding_Sources),
                      c("Other Sources", "Foreign Gov-Affiliated")))
  extract <- function(model, name) {
    result <- as.data.frame(broom::tidy(model, conf.int = TRUE, conf.level = 0.95))
    result$model <- name
    result$n_articles <- stats::nobs(model)
    result$adjusted_r2 <- summary(model)$adj.r.squared
    result
  }
  m1 <- extract(model_m1, "M1")
  m2 <- extract(model_m2, "M2")
  taiwan_terms <- intersect(c("Is_Taiwan", "Is_Taiwan1"), m1$term)
  stopifnot(length(taiwan_terms) == 1L, taiwan_terms %in% m2$term,
            funding_term %in% m1$term, funding_term %in% m2$term)
  funding <- rbind(m1[m1$term == funding_term, ], m2[m2$term == funding_term, ])
  funding$label <- paste0("Staatlich / öffentlich finanziert (", funding$model, ")")
  taiwan <- rbind(m1[m1$term == taiwan_terms, ], m2[m2$term == taiwan_terms, ])
  taiwan$label <- paste0("Taiwan-Medium [Ja = 1] (", taiwan$model, ")")
  topics <- m2[grepl("^Topic_[0-9]+$", m2$term), ]
  topics$topic <- as.integer(sub("Topic_", "", topics$term, fixed = TRUE))
  reference <- setdiff(topic_names$Topic, topics$topic)
  stopifnot(nrow(topics) == 19L, length(reference) == 1L)
  topics$label <- sprintf("T%02d %s", topics$topic,
                         topic_names$Title_DE[match(topics$topic, topic_names$Topic)])
  topics <- topics[order(topics$estimate, decreasing = TRUE), ]
  topics$topic <- NULL
  funding$block <- "Finanzierung"
  taiwan$block <- "Taiwan"
  topics$block <- "Themen"
  funding$y <- c(26, 25)
  taiwan$y <- c(23, 22)
  topics$y <- seq(20, 2)
  dat <- rbind(funding, taiwan, topics)
  rownames(dat) <- NULL
  dat$seed <- as.integer(seed)
  dat$reference_topic <- reference
  stopifnot(nrow(dat) == 23L,
            all(is.finite(as.matrix(dat[c("estimate", "conf.low", "conf.high", "p.value")]))),
            all(dat$conf.low < dat$estimate), all(dat$estimate < dat$conf.high),
            all((dat$p.value < 0.05) == (dat$conf.low > 0 | dat$conf.high < 0)))
  decimal <- function(x, digits = 4, signed = FALSE) {
    format_string <- paste0(if (signed) "%+." else "%.", digits, "f")
    gsub(".", ",", sprintf(format_string, x), fixed = TRUE)
  }
  dat$significance <- ifelse(dat$p.value < 0.001, "***",
    ifelse(dat$p.value < 0.01, "**", ifelse(dat$p.value < 0.05, "*", "n.s.")))
  dat$significant <- dat$p.value < 0.05
  dat$estimate_ci_label <- paste0(decimal(dat$estimate, signed = TRUE), " [",
    decimal(dat$conf.low, signed = TRUE), "; ", decimal(dat$conf.high, signed = TRUE), "]")
  # Vier Dezimalstellen verhindern eine irrefuehrende Rundung nahe null.
  dat$display_label <- vapply(dat$label, function(x)
    paste(strwrap(x, width = 58), collapse = "\n"), character(1))
  # Gemeinsamer Mindestbereich umfasst alle drei Stichproben ohne gekappte Intervalle.
  axis_limits <- c(min(-0.8, floor(min(dat$conf.low) / 0.2) * 0.2),
                   max(1.0, ceiling(max(dat$conf.high) / 0.2) * 0.2))
  axis_breaks <- pretty(axis_limits, n = 5)
  axis_breaks <- axis_breaks[axis_breaks >= axis_limits[1] & axis_breaks <= axis_limits[2]]
  to_x <- function(x) 0.455 + (x - axis_limits[1]) / diff(axis_limits) * 0.245
  dat$x <- to_x(dat$estimate)
  dat$x_low <- to_x(dat$conf.low)
  dat$x_high <- to_x(dat$conf.high)
  ticks <- data.frame(x = to_x(axis_breaks), label = decimal(axis_breaks, 1))
  headers <- data.frame(y = c(27, 24, 21), label = c(
    "1. FINANZIERUNGSGRUPPE (Ref.: andere Finanzierungsquellen)",
    "2. TAIWAN-ZUORDNUNG (Ref.: Nicht-Taiwan)",
    sprintf("3. THEMENANTEILE IN M2 (Ref.: T%02d)", reference)))
  stripes <- dat[dat$block == "Themen", ][seq(2, nrow(topics), by = 2), ]
  zero <- data.frame(y_start = c(24.65, 21.65, 1.6), y_end = c(26.35, 23.35, 20.35))
  font_family <- if (requireNamespace("systemfonts", quietly = TRUE) &&
    "Arial" %in% systemfonts::system_fonts()$family) "Arial" else "sans"
  reference_name <- topic_names$Title_DE[match(reference, topic_names$Topic)]
  footnote <- paste0(
    "Punkte: unstandardisierte OLS-Koeffizienten; Linien: 95%-Konfidenzintervalle (t-Verteilung). Konstante nicht dargestellt.\n",
    "Stance-Wert: -1 ablehnend, 0 neutral, +1 befürwortend. Beide Modelle enthalten Finanzierung und Taiwan-Zuordnung.\n",
    "M2 ergänzt 19 Themenanteile (Skala 0-1). Themenkoeffizienten: Substitution des Referenzthemas bei konstanten übrigen Anteilen.\n",
    paste(strwrap(sprintf("Referenzthema T%02d: %s.", reference, reference_name), width = 120), collapse = "\n"), "\n",
    "Korr. R²: M1 = ", decimal(summary(model_m1)$adj.r.squared),
    "; M2 = ", decimal(summary(model_m2)$adj.r.squared), ".\n",
    "Grün: p < 0,05; Grau: p ≥ 0,05. Zweiseitige t-Tests ohne Mehrfachtestkorrektur.\n",
    "Signifikanz: *** p < 0,001; ** p < 0,01; * p < 0,05; n.s. p ≥ 0,05."
  )
  plot <- ggplot2::ggplot() +
    ggplot2::geom_rect(data = stripes,
      ggplot2::aes(ymin = y - 0.48, ymax = y + 0.48), xmin = 0, xmax = 1.02,
      fill = "#F4F6F8", colour = NA) +
    ggplot2::geom_segment(data = data.frame(y = c(24.45, 21.45)),
      ggplot2::aes(y = y, yend = y), x = 0, xend = 1.02, colour = "#D9DFE5", linewidth = 0.35) +
    ggplot2::geom_segment(data = zero, ggplot2::aes(y = y_start, yend = y_end),
      x = to_x(0), xend = to_x(0), colour = "#939AA2", linewidth = 0.35, linetype = "dashed") +
    ggplot2::geom_text(data = headers, ggplot2::aes(y = y, label = label),
      x = 0.005, hjust = 0, size = 2.65, family = font_family, fontface = "bold", colour = "#263440") +
    ggplot2::geom_text(data = dat, ggplot2::aes(y = y, label = display_label),
      x = 0.01, hjust = 0, size = 2.45, lineheight = 0.95, family = font_family, colour = "#17212B") +
    ggplot2::geom_errorbarh(data = dat, ggplot2::aes(xmin = x_low, xmax = x_high, y = y),
      height = 0.16, colour = "#34414D", linewidth = 0.5) +
    ggplot2::geom_point(data = dat, ggplot2::aes(x = x, y = y, colour = significant), size = 1.35) +
    ggplot2::geom_text(data = dat, ggplot2::aes(y = y, label = estimate_ci_label),
      x = 0.735, hjust = 0, size = 2.30, family = font_family, colour = "#263440") +
    ggplot2::geom_text(data = dat, ggplot2::aes(y = y, label = significance),
      x = 1.005, hjust = 1, size = 2.45, family = font_family, colour = "#263440") +
    ggplot2::annotate("segment", x = 0, xend = 1.02, y = 28.6, yend = 28.6, linewidth = 0.6, colour = "#34414D") +
    ggplot2::annotate("segment", x = 0, xend = 1.02, y = 27.45, yend = 27.45, linewidth = 0.35, colour = "#34414D") +
    ggplot2::annotate("text", x = 0.01, y = 28, label = "Variable / Modell", hjust = 0,
      size = 2.65, family = font_family, fontface = "bold", colour = "#34414D") +
    ggplot2::annotate("text", x = 0.5775, y = 28, label = "Koeffizient b",
      size = 2.65, family = font_family, fontface = "bold", colour = "#34414D") +
    ggplot2::annotate("text", x = 0.735, y = 28, label = "b [95%-KI]", hjust = 0,
      size = 2.65, family = font_family, fontface = "bold", colour = "#34414D") +
    ggplot2::annotate("text", x = 1.005, y = 28, label = "Sign.", hjust = 1,
      size = 2.65, family = font_family, fontface = "bold", colour = "#34414D") +
    ggplot2::annotate("segment", x = to_x(axis_limits[1]), xend = to_x(axis_limits[2]),
      y = 1.15, yend = 1.15, linewidth = 0.35, colour = "#34414D") +
    ggplot2::geom_segment(data = ticks, ggplot2::aes(x = x, xend = x),
      y = 1.15, yend = 0.9, linewidth = 0.35, colour = "#34414D") +
    ggplot2::geom_text(data = ticks, ggplot2::aes(x = x, label = label),
      y = 0.45, size = 2.4, family = font_family, colour = "#34414D") +
    ggplot2::scale_colour_manual(values = c(`TRUE` = "#1B7A60", `FALSE` = "#6B7280")) +
    ggplot2::guides(colour = "none") +
    ggplot2::scale_x_continuous(limits = c(0, 1.025), expand = c(0, 0)) +
    ggplot2::scale_y_continuous(limits = c(-0.3, 29.0), expand = c(0, 0)) +
    ggplot2::labs(title = "Vollständige Regressionsergebnisse: M1 und M2",
      subtitle = paste0("Seed ", seed, "  ·  N = ", format(stats::nobs(model_m1), big.mark = ".", decimal.mark = ",", trim = TRUE),
        " Artikel  ·  Finanzierung, Taiwan und 19 STM-Themenanteile"),
      x = NULL, y = NULL, caption = footnote) +
    ggplot2::theme_void(base_size = 8, base_family = font_family) +
    ggplot2::theme(
      plot.title.position = "plot", plot.caption.position = "plot",
      plot.title = ggplot2::element_text(size = 11, face = "bold", colour = "#17212B", margin = ggplot2::margin(b = 4)),
      plot.subtitle = ggplot2::element_text(size = 8, colour = "#596573", margin = ggplot2::margin(b = 9)),
      plot.caption = ggplot2::element_text(size = 6.8, colour = "#596573", hjust = 0,
        lineheight = 1.22, margin = ggplot2::margin(t = 7)),
      plot.margin = ggplot2::margin(10, 10, 10, 10),
      plot.background = ggplot2::element_rect(fill = "white", colour = NA))
  list(plot = plot, data = dat, font_family = font_family, axis_limits = axis_limits)
}

save_full_model_forest_plot <- function(result, output_dir,
    stem = "Full_Model_Coefficient_Forest_Plot", width_mm = 183, height_mm = 210, dpi = 600) {
  for (package in c("ggplot2", "ragg", "svglite")) {
    if (!requireNamespace(package, quietly = TRUE)) stop("Fehlendes R-Paket: ", package)
  }
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  output <- file.path(output_dir, stem)
  # Showtext-Hooks temporaer entfernen; die editierbaren Textobjekte bleiben erhalten.
  hook_names <- c("plot.new", "grid.newpage")
  old_hooks <- lapply(hook_names, getHook)
  names(old_hooks) <- hook_names
  on.exit(for (name in hook_names) setHook(name, old_hooks[[name]], action = "replace"), add = TRUE)
  for (name in hook_names) {
    keep <- !vapply(old_hooks[[name]], inherits, logical(1), "showtext_hook")
    setHook(name, old_hooks[[name]][keep], action = "replace")
  }
  draw <- function(open_device) {
    open_device()
    on.exit(grDevices::dev.off(), add = TRUE)
    print(result$plot)
  }
  draw(function() grDevices::cairo_pdf(paste0(output, ".pdf"), width = width_mm / 25.4,
    height = height_mm / 25.4, family = result$font_family))
  draw(function() svglite::svglite(paste0(output, ".svg"), width = width_mm / 25.4, height = height_mm / 25.4))
  draw(function() ragg::agg_png(paste0(output, ".png"), width = width_mm, height = height_mm,
    units = "mm", res = dpi, background = "white"))
  draw(function() ragg::agg_tiff(paste0(output, ".tiff"), width = width_mm, height = height_mm,
    units = "mm", res = dpi, background = "white", compression = "lzw"))
  utils::write.csv(result$data, paste0(output, "_source_data.csv"), row.names = FALSE,
                   fileEncoding = "UTF-8")
  invisible(result)
}
