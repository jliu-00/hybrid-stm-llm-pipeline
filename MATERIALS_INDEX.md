# Materialindex R1–R5

Der zentrale Repository-Einstieg und die zur Arbeit gehörende feste Fassung werden in der [README](README.md#elektronische-replikationsmaterialien) angegeben. Dieser Index ordnet Verweise aus der Arbeit konkreten Dateien zu.

| Kennung | Inhalt | Dateien und Ordner |
| --- | --- | --- |
| R1 | Eingefrorenes Codebuch, tatsächliche Promptvorlage und API-Parameter | [Prompt und Codierregeln](promptbook/prompt_codebook_frozen.md); [Parameter](promptbook/vertex_ai_config.json) |
| R2 | Unabhängige Validierung und Entwicklungsstichprobe | [100 Validierungsfälle und Kennzahlen](data/validation/); [ausführbare Validierungsprüfung](scripts/03_main_pipeline/02_reproduce_validation.R); [30 Entwicklungsfälle mit Auswahlkriterien](data/development/development_sample_30.csv) |
| R3 | Metadaten, Annotationen, Regressionsdaten und vollständige STM-Themenanteile | [Eingabemetadaten](data/metadata/); [LLM-Annotationen](data/annotations/); [Regressionsdaten](data/derived/); [Theta und Themenresultate aller drei Seeds](data/derived/stm/) |
| R4 | Abbildungen, Themenzahldiagnostik, Agenda-Ergebnisse und Modellvergleiche | [Seed 42](outputs/figures/seed_42/); [Seed 2024](outputs/figures/seed_2024/); [Seed 12345](outputs/figures/seed_12345/); [numerische Vergleichstabellen](outputs/tables/); [Grafiken aus öffentlichen Tabellen neu erstellen](scripts/03_main_pipeline/04_reproduce_public_figures.R) |
| R5 | Programme, Sprachressourcen und Softwareumgebung | [Erhebung und Vorbereinigung](scripts/00_data_scraping/); [Downsampling](scripts/01_sampling/); [LLM-Verarbeitung](scripts/02_llm_pipeline/); [Hauptregression und Referenzthemenregel](scripts/03_main_pipeline/); [End-to-End-Hauptanalyse](scripts/03_main_pipeline/main_analysis_pipeline.Rmd); [Robustheit](scripts/04_robustness/); [Wörterbücher](data/dictionaries/); [Umgebung](environment/) |

## Themenmaterialien pro Seed

In `data/derived/stm/seed_42/`, `seed_2024/` und `seed_12345/` stehen jeweils:

- `theta_all_stm_documents.csv`: alle gültigen STM-Dokumente mit 20 Themenanteilen, ausgewählten Metadaten und dem STM-bezogenen `Doc_ID`;
- `topic_names.csv` und `topic_summaries.xlsx`: Zuordnung von Themennummer und deutscher Bezeichnung;
- `topic_frex_keywords_german.xlsx`, `topic_frex_keywords_sorted_loc.xlsx` und `topic_top20_keywords_loc.xlsx`: deutsche FREX-Wörter, chinesische Ausgangswörter und weitere Themenwortlisten;
- `search_k_diagnostics.csv`: numerische Diagnosewerte für die untersuchten Themenzahlen;
- `agenda_effects_with_intervals.csv` und `stm_effects_summary_loc.xlsx`: gespeicherte Schätzungen der Finanzierungsgruppenunterschiede mit Intervallen bzw. Standardfehlern;
- `session_info.txt`: Umgebung des jeweiligen lokalen Modells.

Die Zeilenzahlen der Theta-Tabellen betragen 3.483 (42), 3.484 (2024) und 3.485 (12345). Die zugehörigen Diagramme stehen getrennt nach Seed unter `outputs/figures/`.

## Einheitliche Dokumentkennungen

Die Metadaten verwenden dieselbe `Doc_ID` wie die jeweiligen Annotationen, Theta- und Regressionsdaten. `Source_Row_ID` bewahrt die ursprüngliche Eingabezeile; ausgeschlossene Zeilen haben eine leere `Doc_ID` und einen entsprechenden `STM_Status`. Die Zuordnungstabellen gehören zu R3: [Seed 42](data/metadata/document_id_crosswalk_seed_42.csv), [Seed 2024](data/metadata/document_id_crosswalk_seed_2024.csv) und [Seed 12345](data/metadata/document_id_crosswalk_seed_12345.csv). Für Verbindungen wird `Seed + Doc_ID` auf den beibehaltenen Dokumenten verwendet.

## Referenzthema und Modellvergleich

- [Neun Referenzthemen-Kandidaten der Hauptstichprobe](outputs/tables/baseline_topic_candidates_seed_42.csv): mittlerer Anteil über 5 Prozent, absteigend nach dem univariaten Gruppen-p-Wert; T19 ist ausgewählt.
- [Diagnostik aller 20 Hauptthemen](outputs/tables/baseline_topic_diagnostics_seed_42.csv).
- [Drei-Seed-Modellvergleich](outputs/tables/robustness_seeds_comparison.csv): Finanzierungskoeffizienten, Standardfehler, Konfidenzintervalle, gewöhnliches R² und korrigiertes R².
- [Gemeinsame Grafikroutine](scripts/03_main_pipeline/02_funding_coefficient_plot.R): Finanzierungskoeffizientenvergleich für jeden Seed mit 95%-Konfidenzintervallen; PDF/SVG, PNG/TIFF und zugehörige CSV unter den jeweiligen Abbildungsordnern.
- Vollständige Forest-Plots: [Seed 42](outputs/figures/seed_42/Full_Model_Coefficient_Forest_Plot.pdf), [Seed 12345](outputs/figures/seed_12345/Full_Model_Coefficient_Forest_Plot.pdf), [Seed 2024](outputs/figures/seed_2024/Full_Model_Coefficient_Forest_Plot.pdf). Die [gemeinsame Routine](scripts/03_main_pipeline/full_model_forest_plot.R) verwendet die Themenbezeichnungen und das Referenzthema des jeweiligen Seeds (T19, T7 bzw. T14). Zu jedem Plot gehören SVG, PNG, TIFF und eine Quelldatentabelle; im übergeordneten Abbildungsordner liegt keine weitere Kopie.

Der Verweis auf den vollständigen Modellkoeffizientenplot in Abschnitt 4.3.2 führt zu Anhang C, Abbildung C.1. Diese Abbildung verwendet den [Forest-Plot der Hauptstichprobe (Seed 42, PNG)](outputs/figures/seed_42/Full_Model_Coefficient_Forest_Plot.png).

## Zuordnung zum Anhang der Arbeit

| Teil | Materialien |
| --- | --- |
| Anhang A: Entwicklung und Validierung | R1 und R2; Programme unter R5 |
| Anhang B.1: Themenübersicht und Agenda-Unterschiede | R3 und R4; die Gesamtthemenanteile beziehen sich auf alle gültigen STM-Dokumente |
| Anhang B.2: Themenzahldiagnostik | R4, `search_k_diagnostics.csv` je Seed |
| Anhang B.3: Auswahl des Referenzthemas | R4, `baseline_topic_candidates_seed_42.csv`; Rechenprogramm unter R5 |
| Anhang C, Abbildung C.1: vollständige Modellkoeffizienten | R4, `seed_42/Full_Model_Coefficient_Forest_Plot` und Quelldatentabelle |
| Anhang D: Downsampling-Robustheit | Tabellen D.1–D.2: Drei-Seed-Vergleich und Themenzuordnung; ergänzende Grafiken unter R4, darunter der [Koeffizientenvergleich für Seed 2024](outputs/figures/seed_2024/Path1_2_Coefficient_Comparison_loc.png) |

## Hinweise zur Nutzung

Die [Codierstatus-Dokumentation](data/annotations/README.md) und die [Statusübersicht](data/annotations/coding_status_summary.csv) gehören zu R3. Sie trennen inhaltliches −99 von technischen Ausfällen und bewahren die importierten Originalscores. Die [Schnellanleitung](README.md#3-schnellanleitung-zur-reproduktion-quick-start) erläutert die öffentlichen Programme sowie deren schreibfreie Prüfung mit `--check`.

Die Themenanteile und Themenbezeichnungen gehören jeweils zu einem bestimmten Modell. Gleiche Themennummern verschiedener Seeds stehen nicht automatisch für denselben Inhalt. Die [README](README.md#kennungen-und-zuordnung-zwischen-tabellen) erläutert Kennungen, Status und die Prüfung der Zuordnung. Die öffentlichen Tabellen enthalten ausgewählte Metadaten und abgeleitete Ergebnisse. Eine erneute Schätzung bzw. Codierung aus Artikeltexten verwendet die separat aufbewahrten lokalen Eingaben.
