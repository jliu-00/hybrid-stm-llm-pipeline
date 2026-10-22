# Replikationspaket (Replication Package)

**Titel der Arbeit / Research Title:**  
*Hybride Inhaltsanalyse mit Structural Topic Models und Large Language Models am Beispiel chinesischsprachiger Medien außerhalb Festlandchinas*  
(*Hybrid Content Analysis with Structural Topic Models and Large Language Models: The Case of Chinese-Language Media Outside Mainland China*)

## Elektronische Replikationsmaterialien

Das Replikationspaket (Skripte, abgeleitete Daten und Validierungstabellen) ist öffentlich auf [GitHub](https://github.com/jliu-00/hybrid-stm-llm-pipeline) verfügbar. Die zur Arbeit gehörende feste Fassung ist [Release v1.0.0](https://github.com/jliu-00/hybrid-stm-llm-pipeline/releases/tag/v1.0.0).

Die [Mediennamen und historischen Kennungen](MEDIA_NAMES.md) dokumentieren die offiziellen Namen der sieben Medien sowie ihre Bezeichnungen in Dateien und Skripten.

Der [Materialindex R1–R5](MATERIALS_INDEX.md) bezeichnet die einzelnen Materialien. Verweise in der Arbeit können diesen Index und den konkreten Materialnamen nennen; die Repository-Adresse wird zentral gepflegt.

Das Paket enthält die öffentlichen Daten und Programme zur erneuten Berechnung der Validierungskennzahlen und der Regressionen sowie zur grafischen Darstellung der gespeicherten Themenresultate aller drei STM-Stichproben. Die erneute Schätzung eines STM und eine erneute LLM-Codierung setzen die separat aufbewahrten Artikeltexte voraus. RData-Modelldateien bleiben ebenfalls lokal. Die öffentlichen Einstiege verwenden ausschließlich die bereitgestellten Tabellen und vergebenen Labels.

---

## 1. Urheberrecht und Open-Science-Erklärung (Data Availability & Copyright)

### Rechtlicher Rahmen (Urheberrechtsgesetz §§ 15, 19a, 60d & EU DSM-Richtlinie 2019/790)
Gemäß § 60d des deutschen Urheberrechtsgesetzes (UrhG) sowie Artikel 3 der Richtlinie (EU) 2019/790 über das Urheberrecht im digitalen Binnenmarkt ist die Vervielfältigung und Speicherung von urheberrechtlich geschützten Nachrichtenartikeln für Zwecke der wissenschaftlichen Forschung gestattet. Gemäß den allgemeinen Schutzbestimmungen (§§ 15, 19a UrhG) in Verbindung mit den engen Grenzen dieser Forschungsschranke (§ 60d Abs. 4 UrhG) ist die öffentliche Zugänglichmachung der vollständigen Textkorpora jedoch strikt untersagt.

### Prinzip der getrennten Datenhaltung (Hsu & Rauber, 2021, S. 10)
Zur Wahrung von **Open Science, Transparenz und rechnerischer Reproduzierbarkeit der Ergebnisse auf Basis öffentlicher abgeleiteter Daten** folgt diese Arbeit dem Prinzip der Trennung von Originaltexten und abgeleiteten Analysedaten (*Derived Text Formats / Non-Consumptive Use*; vgl. Sag, 2019; Schöch et al., 2020; Text+ Konsortium):
1. **Keine Volltexte im Replikationspaket:** Die geschützten Volltexte verbleiben auf einer gesicherten lokalen Forschungsinfrastruktur und werden nicht öffentlich verteilt.
2. **Bereitstellung abgeleiteter Merkmale:** Die öffentlichen Materialien umfassen:
   - Metadaten mit `Source_Row_ID` für jede Eingabezeile sowie der zugehörigen `Doc_ID` für gültige STM-Dokumente, Titel, Datum, Medienkategorie und Quell-URLs; die Herkunftsfelder werden der LLM-Codierung nicht als eigene Eingabefelder übergeben.
   - Themenanteilsmatrizen für alle gültigen STM-Dokumente: $3.483 \times 20$ (Seed 42), $3.484 \times 20$ (Seed 2024) und $3.485 \times 20$ (Seed 12345); die Regressionsdatensätze enthalten die jeweiligen Teilstichproben;
   - LLM-Haltungskodierungen inklusive schrittweiser Begründungslogik (*Chain-of-Thought*, CoT);
   - Den manuell codierten Referenzstandard (100 Artikel) und die Liste der 30 Entwicklungsfälle mit ihrem Auswahlkriterium;
   - Ausführbare Programme für Validierung, Regression, Referenzthemen-Diagnostik und Ergebnisgrafiken; gespeicherte STM-Diagnosen, Themenwörter, Agenda-Schätzungen mit Intervallen und Abbildungen für alle drei Seeds.

Qualifizierte Wissenschaftler können zu wissenschaftlichen Überprüfungszwecken gemäß § 60d Abs. 4 Nr. 2 UrhG über ein entsprechendes *Data Use Agreement (DUA)* Zugang zu den archivierten Originaldaten beantragen.

---

## 2. Struktur des Replikationspakets (Directory Structure)

```text
Replication_Package/
├── README.md                      # Gesamtdokumentation und Anleitung (dieses Dokument)
├── MEDIA_NAMES.md                 # Offizielle Mediennamen und historische Kennungen
├── LICENSE                        # Lizenzen (MIT für Code, CC-BY 4.0 für abgeleitete Daten)
│
├── environment/                   # Umgebungskonfigurationen
│   ├── requirements.txt           # Python-Bibliotheken (pandas, openpyxl, etc.)
│   ├── session_info.txt           # R-Sitzungsdetails (R 4.x, Pakete und Versionen)
│   └── song.ttf                   # CJK-Schriftart zur korrekten Abbildung chinesischer Schriftzeichen
│
├── data/                          # Analysedaten (ohne geschützte Originaltexte)
│   ├── metadata/                  # Metadaten-Indizes
│   │   ├── corpus_metadata_seed_42.csv     # 3.486 Artikel (Hauptstichprobe, Seed 42)
│   │   ├── corpus_metadata_seed_12345.csv  # 3.486 Artikel (Parallele Stichprobe, Seed 12345)
│   │   ├── corpus_metadata_seed_2024.csv   # 3.486 Artikel (Parallele Stichprobe, Seed 2024)
│   │   └── document_id_crosswalk_seed_*.csv # Eingabezeile, STM-Kennung und Ausschlussstatus
│   │
│   ├── derived/                   # Abgeleitete Analysedaten
│   │   ├── analysis_dataset_seed_42.csv    # 3.251 analysierte Artikel (Themen 1..20, Haltung, Kovariaten)
│   │   ├── analysis_dataset_seed_12345.csv # 3.293 Artikel (Robustheitsstichprobe 12345)
│   │   ├── analysis_dataset_seed_2024.csv  # 3.292 Artikel (Robustheitsstichprobe 2024)
│   │   ├── topic_frex_keywords_german.xlsx # FREX-Schlüsselwörter und deutsche Übersetzungen
│   │   ├── topic_summaries_loc_42.xlsx     # Zusammenfassung der 20 Themen mit Labels
│   │   ├── stm_effects_summary_loc.xlsx    # Geschätzte Kovariateneffekte (Seed 42)
│   │   └── stm/seed_{42,2024,12345}/       # Vollständige Theta-Matrizen, Diagnosen und Themenmaterialien
│   │
│   ├── development/
│   │   └── development_sample_30.csv      # Tatsächliche Auswahl: 20 Themenmaxima + 10 hohe Entropien
│   │
│   ├── annotations/               # Vollständige LLM-Haltungskodierungen (aller 3 Seeds mit Chain-of-Thought)
│   │   ├── llm_scored_full_seed_42.csv     # 3.483 Artikel (Doc_ID, Title, LLM_Score, LLM_Reasoning)
│   │   ├── llm_scored_full_seed_12345.csv  # 3.485 Artikel (Doc_ID, Title, LLM_Score, LLM_Reasoning)
│   │   └── llm_scored_full_seed_2024.csv   # 3.484 Artikel (Doc_ID, Title, LLM_Score, LLM_Reasoning)
│   │
│   ├── validation/                # Validierungsdaten und Reliabilitätskennzahlen
│   │   ├── gold_standard_validation_100.xlsx # 100 Validierungsartikel (Mensch vs. LLM)
│   │   ├── validation_metrics.csv            # Krippendorffs Alpha & Klassifikationsgenauigkeit
│   │   ├── validation_confusion_matrix.csv   # 4x4-Konfusionsmatrix (Haltungsklassen)
│   │   └── validation_per_class.csv          # Präzision, Recall und F1 je Haltungsklasse
│   │
│   └── dictionaries/              # Sprachliche Ressourcen und Wörterbücher
│       ├── baidu_stopwords.txt    # Standard-Stoppwörter
│       ├── custom_stopwords.txt   # Projektspezifische Stoppwörter (151 Termini)
│       └── user_dict_jieba.txt    # Benutzerdefiniertes Entitäten-Lexikon (56 Termini)
│
├── promptbook/                    # Eingefrorenes LLM-Codebuch (Törnberg, 2024)
│   ├── prompt_codebook_frozen.md  # Tatsächlich verwendete Systeminstruktion und Promptvorlage
│   └── vertex_ai_config.json      # API-Hyperparameter (Temperature=0.0, TopP=0.2, Modell-ID)
│
├── scripts/                       # Ausführbare Replikationsskripte
│   ├── 00_data_scraping/          # Web-Scraping- und Filterroutinen (7 Medien)
│   ├── 01_sampling/               # Schichtung und Zufallsziehung (stratified_downsample.py)
│   ├── 02_llm_pipeline/           # LLM-Batch-Inferenz (Vorbereitung und JSONL-Parsing)
│   │   ├── 01_create_vertex_batch_input.py
│   │   ├── 02_parse_vertex_batch_output.py
│   │   ├── 03_normalize_coding_status.py # Technische Ausfälle getrennt ausweisen
│   │   └── coding_status.py             # Gemeinsame Statusregeln
│   ├── 03_main_pipeline/          # Kernanalyse: STM, Validierung und Regressionen
│   │   ├── 00_align_metadata_ids.py # Metadatenkennungen abgleichen oder mit --check prüfen
│   │   ├── 01_reproduce_regression_and_plots.R # Sofortige 1-Klick-Reproduktion von M1 & M2
│   │   ├── 02_funding_coefficient_plot.R # Gemeinsame Darstellung der Finanzierungskoeffizienten
│   │   ├── full_model_forest_plot.R # Vollständiger Forest-Plot mit seed-spezifischen Themen
│   │   ├── 02_reproduce_validation.R    # Kennzahlen und Konfusionsmatrix aus 100 Labels
│   │   ├── 03_baseline_topic_diagnostics.R # Prüfung der Referenzthemenregel für Seed 42
│   │   ├── 04_reproduce_public_figures.R # Gespeicherte Resultate aller drei Seeds neu zeichnen
│   │   ├── public_results_helpers.R     # Gemeinsame Pfad-, Prüf- und Exportfunktionen
│   │   └── main_analysis_pipeline.Rmd          # Umfassendes R-Markdown-Gesamtskript (Hauptanalyse: Vorverarbeitung, STM, Regressionen)
│   └── 04_robustness/             # Robustheitsprüfung paralleler Stichproben
│       └── reproduce_robustness_seeds.R        # Schätzung und Vergleich der Seeds 42, 12345, 2024
│
└── outputs/                       # Reproduzierte Abbildungen und Tabellen
    ├── figures/seed_{42,2024,12345}/ # Abbildungen getrennt nach Stichprobe
    ├── reproduced/                 # Neue Tabellen und PNG/PDF aus öffentlichen Einstiegen (wird bei Skriptausführung erzeugt)
    └── tables/                     # Drei-Seed-Vergleich und Referenzthemen-Diagnostik
```

---

## 3. Schnellanleitung zur Reproduktion (Quick Start)

### Voraussetzung
Eine installierte R-Umgebung (Version $\ge$ 4.0.0) mit den Bibliotheken `tidyverse`, `broom`, `ggeffects`, `scales`, `ragg` und `svglite` (für die Abbildungen `ggplot2` ab Version 3.4).

Die neuen Validierungs- und Grafikprogramme benötigen `ggplot2` (Version $\ge$ 3.4.0), `readxl`, `svglite` und eine R-Installation mit Cairo-PDF-Unterstützung. Die Status- und Kennungsprüfungen benötigen Python 3; der Antwortparser zusätzlich `pandas`.

### 1. Sofortige Reproduktion der Hauptmodelle (M1 & M2)
Führen Sie im Terminal folgenden Befehl aus:
```bash
Rscript scripts/03_main_pipeline/01_reproduce_regression_and_plots.R
```
**Ergebnis:**
- Schätzung des Basiseffekts (Modell 1: $\beta = 0.1615^{***}$, $p < 0.001$);
- Schätzung des themenbereinigten Modells (Modell 2: $\beta' = -0.0239$, $p = 0.2928$);
- Berechnung der Effektverschiebung ($-114.79\%$);
- Automatische Erstellung der Vorhersagegrafiken sowie des Finanzierungskoeffizientenvergleichs unter `outputs/figures/`.
- Der Koeffizientenvergleich wird zusätzlich unter `outputs/figures/seed_42/` abgelegt: PNG/TIFF mit 600 dpi, editierbare PDF/SVG und eine CSV mit den dargestellten Zahlen.
- Die Punkte zeigen den Unterschied „staatlich / öffentlich finanzierte Medien minus Medien mit anderen Finanzierungsquellen“. Grau und Grün unterscheiden M1 und M2; die gemeinsame Taiwan-Kontrolle steht in der Bildunterschrift.
- Der vollständige Forest-Plot `Full_Model_Coefficient_Forest_Plot` steht ausschließlich unter `outputs/figures/seed_42/`, ohne zusätzliche Kopie im übergeordneten Abbildungsordner.

### 2. Reproduktion der Robustheitsanalyse über alternative Zufallsstichproben
```bash
Rscript scripts/04_robustness/reproduce_robustness_seeds.R
```
**Ergebnis:**
- Berechnet und vergleicht die Regressionskoeffizienten über alle drei Seeds (42, 12345, 2024);
- Vergleicht die statistischen Gruppenunterschiede vor und nach Themenkontrolle;
- Berichtet gewöhnliches und korrigiertes R² getrennt sowie die Konfidenzintervalle der Finanzierungskoeffizienten;
- Speichert die Vergleichstabelle unter `outputs/tables/robustness_seeds_comparison.csv`.
- Erstellt denselben Koeffizientenvergleich mit den jeweiligen Modellergebnissen unter `outputs/figures/seed_{42,12345,2024}/`. Stichprobengröße, Koeffizienten, Konfidenzintervalle, p-Werte und korrigiertes R² werden aus jedem Modell berechnet.
- Die Funktion `scripts/03_main_pipeline/02_funding_coefficient_plot.R` enthält die gemeinsame Zeichen- und Exportroutine; die vollständige Pipeline enthält dieselbe Routine auch direkt im Skript.
- Erstellt zusätzlich `Full_Model_Coefficient_Forest_Plot` in jedem der drei Seed-Ordner: Finanzierung und Taiwan-Zuordnung aus M1/M2 sowie alle 19 Themenkoeffizienten aus M2. Die gemeinsame Routine `full_model_forest_plot.R` verwendet die jeweiligen deutschen Themenbezeichnungen und die ursprüngliche Referenzregel (T19 für Seed 42, T7 für Seed 12345, T14 für Seed 2024). Die Finanzierungskoeffizienten und Modellgüte bleiben bei der Wahl des ausgelassenen Themas unverändert. Export: editierbare PDF/SVG (183 × 210 mm), PNG/TIFF mit 600 dpi und CSV mit den dargestellten Werten. Die Konstante wird nicht dargestellt; Themenkoeffizienten beziehen sich auf die Substitution des jeweiligen Referenzthemas.

### 3. Erneute Erstellung der LLM-Batch-Anfragen aus lokalen Volltexten
Hierfür werden Python mit `pandas` und für XLSX-Dateien `openpyxl` sowie eine lokale Volltextdatei benötigt. Die Pflichtspalten sind `Doc_ID`, `News Title` (alternativ `Title`) und `News Content` (alternativ `Text`). Alle drei Felder müssen für jeden Artikel ausgefüllt und die `Doc_ID` eindeutig sein. Die öffentliche Metadatentabelle enthält keine Volltexte und kann diesen Schritt allein nicht reproduzieren.

Geben Sie Eingabe- und Ausgabepfad ausdrücklich an; die folgenden Pfade sind durch eigene lokale Pfade zu ersetzen:
```bash
python3 scripts/02_llm_pipeline/01_create_vertex_batch_input.py \
  --input /pfad/zu/privaten/volltexten.csv \
  --output /pfad/zu/privaten/batch_anfragen.jsonl
```
Der Schritt prüft sämtliche Artikel vor dem Schreiben. Bei fehlenden Spalten, leeren Feldern oder doppelten `Doc_ID` bricht er mit einer Fehlermeldung ab; eine bestehende Ausgabedatei bleibt bei diesen Eingabefehlern erhalten. Gültige Eingaben erzeugen pro Artikel eine Anfrage nach der eingefrorenen Vorlage. Es erfolgen keine API-Aufrufe. Da auch die JSONL-Datei die vollständigen Artikel enthält, bleiben Volltextdatei und JSONL lokal außerhalb des veröffentlichten Replikationspakets.

### 4. Prüfung der Referenzthemenregel

```bash
Rscript scripts/03_main_pipeline/03_baseline_topic_diagnostics.R
```

Die Berechnung verwendet die $3.251$ Artikel der Hauptregression. Zunächst werden Themen mit einem mittleren Anteil über $5\,\%$ ausgewählt. Unter diesen neun Kandidaten hat T19 den höchsten p-Wert im univariaten Finanzierungsgruppenvergleich. Das Skript speichert sowohl alle 20 Themen als auch die sortierte Kandidatentabelle unter `outputs/tables/`.

### 5. Downsampling lokaler vorbereinigter Mediendateien

Der Startwert wird ausdrücklich angegeben. Die sieben Eingabedateien entsprechen den Namen im Skript; sie werden aus einem lokalen Ordner eingelesen. Für weitere Stichproben wird `--seed` auf `2024` oder `12345` gesetzt. Die Auswahl- und Rundungsregeln des ursprünglichen Skripts bleiben erhalten.

```bash
python3 scripts/01_sampling/stratified_downsample.py \
  --input-dir /pfad/zu/privaten/vorbereinigten_mediendateien \
  --output-dir /pfad/zu/privaten/stichproben \
  --seed 42
```

Der Dateiname enthält den Startwert, z. B. `downsampled_dataset_seed_42.csv`. Die Python-Vorbereinigung des Gesamtkorpus ist ein vorgelagerter Schritt; die vorhandene Datei `data_cleaning_stats_loc.xlsx` dokumentiert dagegen die STM-Vorverarbeitung der bereits gezogenen Hauptstichprobe.

### 6. Unabhängige Reproduktion der Validierung

```bash
Rscript scripts/03_main_pipeline/02_reproduce_validation.R
```

Das Programm liest ausschließlich die 100 öffentlichen Mensch-LLM-Labelpaare, berechnet die drei Reliabilitäts- und Genauigkeitsmaße, die klassenweisen Kennzahlen und alle 16 Zellen der Konfusionsmatrix. Es prüft die Werte gegen die drei gespeicherten Tabellen und schreibt neue Tabellen sowie eine Konfusionsmatrix als PNG/PDF/SVG nach `outputs/reproduced/validation/`.

Mit `--check` erfolgt nur die numerische Prüfung ohne Ausgabedateien. Mit `--output-dir /pfad/zur/ausgabe` lässt sich der Ausgabeordner ändern.

### 7. Ergebnisgrafiken ausschließlich aus öffentlichen Tabellen

```bash
Rscript scripts/03_main_pipeline/04_reproduce_public_figures.R
```

Für jeden Seed entstehen vier einzelne K-Diagnostikgrafiken, die gesamte Themenverteilung mit zehn deutschen FREX-Wörtern je Thema, die gespeicherten Agenda-Schätzungen mit 95%-Intervallen, ein neu berechneter M1/M2-Koeffizientenvergleich und der vollständige Forest-Plot. Die numerischen Plotdaten zur Themenverteilung und zu den Koeffizienten werden ebenfalls exportiert. Das Programm prüft die Theta-Zuordnung der Regressionsfälle und die Modellresultate gegen die vorhandene Drei-Seed-Tabelle. Alle neuen Grafiken werden als PNG, PDF und SVG unter `outputs/reproduced/figures/seed_*/` gespeichert; der vollständige Forest-Plot zusätzlich als TIFF. Die archivierten Originalgrafiken bleiben erhalten.

```bash
Rscript scripts/03_main_pipeline/04_reproduce_public_figures.R --check
Rscript scripts/03_main_pipeline/04_reproduce_public_figures.R --seeds 42,2024 --output-dir /pfad/zur/ausgabe
```

`--check` prüft die öffentlichen Eingaben und Modellvergleiche ohne Schreiben. Die Grafiken zeigen dieselben gespeicherten Ergebnisse in einem portablen Layout; sie reproduzieren die archivierten PNG-Dateien nicht pixelgenau. Die Agenda-Intervalle und K-Diagnosen werden aus den Resultattabellen übernommen. Eine erneute STM-Schätzung erfolgt dabei nicht.

### Inhaltliche Codierung und technische Ausfälle

Die Annotationen unterscheiden `Coding_Status` und `LLM_Score`. Ein inhaltliches −99 bedeutet weiterhin, dass das Codierziel nicht anwendbar ist. Technische Ausfälle haben einen leeren `LLM_Score`; `LLM_Score_Original` bewahrt den ursprünglich importierten Wert. Die [Feldbeschreibung und Statusregeln](data/annotations/README.md) sowie die [Fallzahlen pro Seed](data/annotations/coding_status_summary.csv) dokumentieren die Unterscheidung. Die Regressionsdatensätze und Validierungslabels bleiben unverändert.

```bash
python3 scripts/02_llm_pipeline/03_normalize_coding_status.py --check
```

Der lokale Batch-Antwortparser führt diese Statusfelder ebenfalls. Fehlende Antworten, API-Fehler, Sicherheitsblockaden sowie ungültige oder unlesbare Scores erhalten eigene Statuswerte. Doppelte oder unbekannte Antwortkennungen führen vor dem Schreiben zu einem Abbruch. Eingabemetadaten, Batch-Datei und Ausgabe lassen sich mit `--input`, `--batch-output` und `--output` angeben.

### Kennungen und Zuordnung zwischen Tabellen

`Doc_ID` bezeichnet innerhalb jedes Seeds dasselbe gültige STM-Dokument in den Metadaten, Annotationen, Entwicklungs- und Validierungsdaten, Regressionsdaten und Theta-Tabellen. Die bestehenden Kennungen der Codierung und Analyse bleiben erhalten. Verbindungen zwischen Tabellen verwenden `Seed + Doc_ID`; bei Dateien für genau einen Seed ergibt sich der Seed aus dem Dateinamen.

Die Metadaten enthalten außerdem `Source_Row_ID` als unveränderte Zeilennummer der gezogenen Eingabe vor dem Ausschluss leerer STM-Dokumente. `STM_Status = Retained_for_STM` kennzeichnet ein gültiges Dokument. Ausgeschlossene Eingabezeilen behalten ihre `Source_Row_ID`, haben eine leere `Doc_ID` und den Status `Excluded_before_STM`. Die drei Metadatentabellen enthalten weiterhin jeweils 3.486 Eingabezeilen; für Seed 42, 2024 und 12345 sind davon 3, 2 bzw. 1 Zeilen ausgeschlossen.

Die Dateien `data/metadata/document_id_crosswalk_seed_{42,2024,12345}.csv` dokumentieren `Seed`, `Source_Row_ID`, `Doc_ID`, Artikel-URL und Status. Die Zuordnung wurde anhand der innerhalb jeder Stichprobe eindeutigen Artikel-URL aufgebaut und über Titel, Medium, Datum, Region, Finanzierungsgruppe und Taiwan-Merkmal geprüft. Beim Verbinden der Tabellen werden die gültigen Zeilen mit ausgefüllter `Doc_ID` verwendet. Ein Vergleich derselben Artikel über verschiedene Seeds erfolgt anhand der Artikel-URL.

```bash
python3 scripts/03_main_pipeline/00_align_metadata_ids.py --check
```

Ohne `--check` erstellt das Skript die Metadatenzuordnung und die drei Zuordnungstabellen aus den vorhandenen Metadaten und Theta-Tabellen erneut. Bereits vorhandene `Source_Row_ID` bleiben dabei erhalten. Alle ausgewählten Stichproben werden vor dem Schreiben auf eindeutige Schlüssel und übereinstimmende Artikelfelder geprüft. Der Batch-Antwortparser verwendet nur die beibehaltenen STM-Dokumente.

Die Theta-Exporte wurden über Titel, Dokumentreihenfolge und Themenanteile mit den vorhandenen Annotationen und Regressionsdaten abgeglichen. Quelle und Prüfsumme der lokal gespeicherten Modelle stehen in `data/derived/stm/export_provenance.json`. Die Modelle unter `STM/ALL/Results_All` beziehen sich auf eine andere, unbalancierte Voranalyse mit $15.789$ gültigen Dokumenten und werden für diese drei Exporte nicht verwendet.

### 8. End-to-End-Hauptanalyse aus Volltexten (main_analysis_pipeline.Rmd)

Das R-Markdown-Gesamtskript `scripts/03_main_pipeline/main_analysis_pipeline.Rmd` dokumentiert den vollständigen Modellierungs- und Validierungsablauf der Abschlussarbeit von der Vorverarbeitung und chinesischen Wortsegmentierung (via `jiebaR`) über die K-Diagnostik und STM-Schätzung bis hin zu den Regressionsmodellen und Ergebnisabbildungen.

Gemäß Urheberrechtsgesetz (§ 60d UrhG) dürfen geschützte Nachrichten-Volltextkorpora nicht öffentlich im Paket mitgegeben werden. Für Wissenschaftler mit Zugang zu den Volltexten (bzw. eigenem Korpus) ist das Skript vollständig portabel parametrisiert und kann wie folgt ausgeführt werden:

#### Konfigurationsparameter
Das Skript wertet vorrangig definierte R-Variablen sowie Umgebungsvariablen aus:
* **`base_dir` / `STM_BASE_DIR`**: Basispfad zum lokalen Korpusordner. Das Skript sucht den Teildatensatz automatisch unter `Local/data/downsampled_dataset_seed_{seed}.csv`, `Downsampled/data/...`, `data/...` oder direkt im Basispfad.
* **`current_seed`**: Zufallsstartwert der Stichprobe (Standard: `"42"`, unterstützt auch `"12345"` oder `"2024"`).
* **`font_path` / `FONT_PATH`**: Pfad zur CJK-Schriftart (greift automatisch auf die mitgelieferte Schriftart `environment/song.ttf` zurück).
* **Stoppwörter**: `baidu_stopwords.txt` wird automatisch im Paketordner `data/dictionaries/` oder im angegebenen Basispfad erkannt.

#### Ausführung

**Variante A: Ausführung im Terminal mit Umgebungsvariablen**
```bash
# 1. Pfad zum lokalen Volltextkorpus setzen
export STM_BASE_DIR="/pfad/zu/ihren/volltexten"

# 2. R Markdown für den Standard-Seed (42) rendern
Rscript -e "rmarkdown::render('scripts/03_main_pipeline/main_analysis_pipeline.Rmd')"
```

**Variante B: Spezifischen Seed und Pfad direkt in R übergeben**
```bash
Rscript -e '
  current_seed <- "12345"
  base_dir <- "/pfad/zu/ihren/volltexten"
  rmarkdown::render("scripts/03_main_pipeline/main_analysis_pipeline.Rmd")
'
```

*Hinweis:* Ohne die geschützten Rohvolltexte verwenden Sie bitte die öffentlichen Einstiege (Abschnitte 1, 2, 6 und 7). Diese reproduzieren sämtliche Regressionsergebnisse, Validierungsmetriken und Abbildungen direkt aus den bereitgestellten abgeleiteten Daten.

---

## 4. Methodische Kernspezifikationen

### A. Strukturelles Themenmodell (STM)
- **Paket:** `stm` in R;
- **Hauptstichprobe:** $3.486$ gezogene Artikel, $3.483$ gültige STM-Dokumente und $3.251$ Artikel in der Regression nach den Ausschlüssen aus Abschnitt 3.7.1;
- **Themenanzahl:** $K = 20$ (determiniert über diagnostische Kriterien: semantische Kohärenz, Exklusivität und Residualanalyse);
- **Kovariatenstruktur:** Prävalenz formuliert über `Funding_Sources + Is_Taiwan`.

### B. LLM-Haltungsanalyse (Prompt Codebook)
- **Modell:** `gemini-3.5-flash-lite` via Google Cloud Vertex AI Batch API;
- **Parameter:** `temperature = 0.0` (fixierte Sampling-Temperatur), `top_p = 0.2`;
- **Prompt:** Codebuchbasierte Zero-Shot-Klassifikation mit regelintegrierten Kurzbeispielen; die ausgeführte Systeminstruktion und Nutzervorlage stehen in `promptbook/prompt_codebook_frozen.md`. Jeder Auftrag verarbeitet einen Artikel unabhängig von der Gesprächshistorie anderer Artikel;
- **Kategorien:** $+1$ (Positiv), $0$ (Neutral), $-1$ (Negativ), $-99$ (Nicht zutreffend);
- **Reliabilität (Validierungsstichprobe $N = 100$):**
  - Nominales Krippendorffs $\alpha = 0.7598$;
  - Zielanwendbarkeit (Target Applicability) $\alpha = 0.8894$;
  - Haltung bei beidseitiger Zielanwendbarkeit $\alpha = 0.7277$;
  - Gesamtklassifikationsgenauigkeit $= 86.00\%$.

---

## 5. Zitierweise & Lizenz (Citation & License)

Wenn Sie diese Daten oder Skripte nutzen, zitieren Sie bitte die dazugehörige Abschlussarbeit:

> Liu, J. (2026). *Hybride Inhaltsanalyse mit Structural Topic Models und Large Language Models am Beispiel chinesischsprachiger Medien außerhalb Festlandchinas*. Bachelorarbeit, Fachbereich Politik- und Sozialwissenschaften, Freie Universität Berlin.

- **Programmcode:** MIT License  
- **Abgeleitete Datensätze & Dokumentation:** Creative Commons Attribution 4.0 International (CC BY 4.0)
