# Shared helpers for the public-data validation and figure entry points.
public_options <- function(default_name, allow_seeds = FALSE) {
  file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  root <- normalizePath(file.path(dirname(sub("^--file=", "", file_arg[1])), "../.."))
  args <- commandArgs(TRUE)
  opts <- list(root = root, output = file.path(root, "outputs", "reproduced", default_name),
               seeds = c(42L, 2024L, 12345L), check = FALSE)
  i <- 1L
  while (i <= length(args)) {
    key <- args[i]
    if (key == "--check") opts$check <- TRUE
    else if (key == "--output-dir" && i < length(args)) {
      i <- i + 1L; opts$output <- args[i]
    } else if (allow_seeds && key == "--seeds" && i < length(args)) {
      i <- i + 1L
      opts$seeds <- suppressWarnings(as.integer(strsplit(args[i], ",", fixed = TRUE)[[1]]))
      if (!length(opts$seeds) || anyNA(opts$seeds) || any(!opts$seeds %in% c(42, 2024, 12345)) ||
          anyDuplicated(opts$seeds)) stop("--seeds: choose distinct values from 42,2024,12345")
    } else stop("Unknown or incomplete option: ", key)
    i <- i + 1L
  }
  opts
}

public_require <- function(packages) {
  for (p in packages) if (!requireNamespace(p, quietly = TRUE))
    stop("Install required R package: ", p)
  if ("ggplot2" %in% packages && utils::packageVersion("ggplot2") < "3.4.0")
    stop("ggplot2 >= 3.4.0 is required")
  if (!capabilities("cairo")) stop("This entry point requires Cairo PDF support")
}

public_read <- function(path, columns = character()) {
  x <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
  if (!all(columns %in% names(x))) stop("Missing columns: ", path)
  x
}

public_theme <- function() {
  ggplot2::theme_bw(base_size = 11, base_family = "sans") +
    ggplot2::theme(panel.grid.minor = ggplot2::element_blank(),
      plot.title.position = "plot", plot.caption.position = "plot",
      plot.caption = ggplot2::element_text(hjust = 0, size = 9),
      axis.text = ggplot2::element_text(colour = "#303030"),
      plot.margin = ggplot2::margin(12, 16, 12, 12))
}

public_save <- function(plot, stem, width, height) {
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  vector_device <- function(open) {
    open()
    on.exit(grDevices::dev.off(), add = TRUE)
    print(plot)
  }
  vector_device(function() grDevices::cairo_pdf(paste0(stem, ".pdf"),
    width = width, height = height, bg = "white"))
  vector_device(function() svglite::svglite(paste0(stem, ".svg"),
    width = width, height = height, bg = "white"))
  ggplot2::ggsave(paste0(stem, ".png"), plot, width = width, height = height,
                 units = "in", dpi = 300, bg = "white")
}

public_equal <- function(actual, expected, label, tolerance = 1e-10) {
  if (!isTRUE(all.equal(actual, expected, tolerance = tolerance, check.attributes = FALSE)))
    stop("Stored result differs: ", label)
}

public_wrap <- function(x, width) vapply(x, function(s)
  paste(strwrap(s, width = width), collapse = "\n"), character(1))
