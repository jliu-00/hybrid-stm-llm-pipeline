# Finanzierungsgruppenvergleich vor und nach Themenkontrolle.
# Alle Beschriftungen und Unsicherheiten werden aus den uebergebenen Modellen abgeleitet.
make_funding_coefficient_plot <- function(model_m1, model_m2) {
  term <- "Funding_SourcesForeign Gov-Affiliated"
  extract <- function(model, model_id, x) {
    sm <- summary(model)
    if (sum(rownames(sm$coefficients) == term) != 1L) {
      stop("Der Finanzierungskoeffizient fehlt oder ist nicht eindeutig.")
    }
    ci <- stats::confint(model, parm = term, level = 0.95)
    data.frame(
      model = model_id, x = x, estimate = unname(stats::coef(model)[term]),
      conf_low = ci[1, 1], conf_high = ci[1, 2],
      p_value = sm$coefficients[term, "Pr(>|t|)"],
      n_articles = stats::nobs(model), adjusted_r2 = sm$adj.r.squared,
      row.names = NULL
    )
  }
  dat <- rbind(extract(model_m1, "M1", 1), extract(model_m2, "M2", 2))
  stopifnot(
    identical(rownames(stats::model.frame(model_m1)), rownames(stats::model.frame(model_m2))),
    dat$n_articles[1] == dat$n_articles[2],
    all(is.finite(as.matrix(dat[, c("estimate", "conf_low", "conf_high", "p_value")]))),
    all(dat$conf_low < dat$estimate), all(dat$estimate < dat$conf_high),
    all((dat$p_value < 0.05) == (dat$conf_low > 0 | dat$conf_high < 0))
  )
  decimal <- function(x, digits = 4, signed = FALSE) {
    fmt <- paste0(if (signed) "%+." else "%.", digits, "f")
    gsub(".", ",", sprintf(fmt, x), fixed = TRUE)
  }
  topic_count <- sum(grepl("^Topic_", names(stats::coef(model_m2))))
  sample_label <- format(dat$n_articles[1], big.mark = ".", decimal.mark = ",", scientific = FALSE, trim = TRUE)
  font_family <- if (requireNamespace("systemfonts", quietly = TRUE) &&
                     "Arial" %in% systemfonts::system_fonts()$family) "Arial" else "sans"
  dat$estimate_label <- decimal(dat$estimate, signed = TRUE)
  dat$ci_label <- paste0("[", decimal(dat$conf_low), "; ", decimal(dat$conf_high), "]")
  dat$p_label <- ifelse(dat$p_value < 0.001, "p < 0,001", paste0("p = ", decimal(dat$p_value, 3)))
  dat$label_x <- c(0.90, 2.10)
  dat$hjust <- c(1, 0)
  dat$estimate_y <- dat$estimate + c(0.014, 0.001)
  dat$ci_y <- dat$estimate + c(-0.009, -0.022)
  dat$p_y <- dat$estimate + c(-0.032, -0.045)
  # Bei einem positiven M2-Koeffizienten steht der ganze Textblock oberhalb der Nulllinie.
  # So kann die Referenzlinie keine der drei Zahlenbeschriftungen kreuzen.
  if (dat$estimate[2] > 0) {
    dat$p_y[2] <- max(0.015, dat$p_y[2])
    dat$ci_y[2] <- dat$p_y[2] + 0.023
    dat$estimate_y[2] <- dat$ci_y[2] + 0.023
  }
  y_limits <- c(
    min(-0.10, floor((min(dat$conf_low, dat$p_y) - 0.015) / 0.05) * 0.05),
    max(0.25, ceiling((max(dat$conf_high, dat$estimate_y) + 0.015) / 0.05) * 0.05)
  )
  footnote <- paste0(
    "Beide Modelle kontrollieren die Taiwan-Zuordnung.\n",
    "95%-Konfidenzintervalle; zweiseitige t-Tests (OLS). 0 = kein Gruppenunterschied.\n",
    "Korr. R²: M1 = ", decimal(dat$adjusted_r2[1]), "; M2 = ", decimal(dat$adjusted_r2[2]),
    "; Differenz = ", decimal(diff(dat$adjusted_r2), signed = TRUE), "."
  )
  plot <- ggplot2::ggplot(dat, ggplot2::aes(x = x, y = estimate)) +
    ggplot2::geom_hline(yintercept = 0, colour = "#9299A1", linewidth = 0.50, linetype = "dashed") +
    ggplot2::geom_line(ggplot2::aes(group = 1), colour = "#1B7A60", linewidth = 1.0, alpha = 0.72) +
    ggplot2::geom_errorbar(ggplot2::aes(ymin = conf_low, ymax = conf_high, colour = model), width = 0.055, linewidth = 0.90) +
    ggplot2::geom_point(ggplot2::aes(colour = model, shape = model), size = 3.7, stroke = 0.8) +
    ggplot2::geom_text(ggplot2::aes(x = label_x, y = estimate_y, label = estimate_label, hjust = hjust),
                       colour = "#17212B", family = font_family, fontface = "bold", size = 3.55) +
    ggplot2::geom_text(ggplot2::aes(x = label_x, y = ci_y, label = ci_label, hjust = hjust),
                       colour = "#34414D", family = font_family, size = 2.95) +
    ggplot2::geom_text(ggplot2::aes(x = label_x, y = p_y, label = p_label, hjust = hjust),
                       colour = "#596573", family = font_family, size = 2.95) +
    ggplot2::scale_colour_manual(values = c(M1 = "#596573", M2 = "#1B7A60")) +
    ggplot2::scale_shape_manual(values = c(M1 = 16, M2 = 17)) +
    ggplot2::scale_x_continuous(
      limits = c(0.30, 2.70), breaks = c(1, 2), expand = c(0, 0),
      labels = c("M1: Basismodell\nOhne Themenkontrolle",
                 paste0("M2: Themenkontrolle\nMit ", topic_count, " STM-Themenanteilen"))
    ) +
    ggplot2::scale_y_continuous(
      limits = y_limits, breaks = seq(y_limits[1], y_limits[2], by = 0.05),
      expand = c(0, 0), labels = function(x) decimal(x, digits = 2)
    ) +
    ggplot2::labs(
      title = "Finanzierungsgruppe und mediale Haltung",
      subtitle = paste0(
        "Staatlich / öffentlich finanzierte Medien minus Medien mit anderen Finanzierungsquellen\n",
        "Gruppendifferenz im Stance-Wert  -  N = ", sample_label, " Artikel"
      ),
      x = NULL, y = "Unstandardisierter OLS-Koeffizient b", caption = footnote
    ) +
    ggplot2::guides(colour = "none", shape = "none") +
    ggplot2::theme_classic(base_size = 9, base_family = font_family) +
    ggplot2::theme(
      plot.title.position = "plot", plot.caption.position = "plot",
      plot.title = ggplot2::element_text(size = 12, face = "bold", colour = "#17212B", margin = ggplot2::margin(b = 5)),
      plot.subtitle = ggplot2::element_text(size = 8.3, colour = "#596573", lineheight = 1.25, margin = ggplot2::margin(b = 15)),
      axis.title.y = ggplot2::element_text(size = 8.6, colour = "#263440", margin = ggplot2::margin(r = 9)),
      axis.text.y = ggplot2::element_text(size = 8.5, colour = "#34414D", margin = ggplot2::margin(r = 4)),
      axis.text.x = ggplot2::element_text(size = 9.1, colour = "#263440", lineheight = 1.2, margin = ggplot2::margin(t = 8)),
      axis.line = ggplot2::element_line(colour = "#53606C", linewidth = 0.35),
      axis.ticks = ggplot2::element_line(colour = "#53606C", linewidth = 0.35),
      axis.ticks.length = grid::unit(1.3, "mm"),
      plot.caption = ggplot2::element_text(size = 7.5, colour = "#596573", hjust = 0, lineheight = 1.3, margin = ggplot2::margin(t = 12)),
      plot.margin = ggplot2::margin(t = 12, r = 13, b = 10, l = 12),
      panel.grid = ggplot2::element_blank(),
      plot.background = ggplot2::element_rect(fill = "white", colour = NA)
    )
  list(plot = plot, data = dat, font_family = font_family)
}

save_funding_coefficient_plot <- function(result, output_dir,
                                         stem = "Path1_2_Coefficient_Comparison_loc",
                                         width_mm = 160, height_mm = 110, dpi = 600) {
  for (package in c("ggplot2", "ragg", "svglite")) {
    if (!requireNamespace(package, quietly = TRUE)) {
      stop("Fehlendes R-Paket: ", package, ". Bitte mit install.packages() installieren.")
    }
  }
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  output <- file.path(output_dir, stem)
  # Showtext-Hooks temporaer entfernen, damit Vektortext editierbar bleibt.
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
  utils::write.csv(result$data, paste0(output, "_source_data.csv"), row.names = FALSE)
  invisible(result)
}
