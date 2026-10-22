# Codierstatus und Haltungsscores

`Doc_ID` ist die unveränderte Analysekennung innerhalb des im Dateinamen genannten Seeds.

| Feld | Bedeutung |
| --- | --- |
| `LLM_Score` | Inhaltliche Codierung: −99 (Ziel nicht anwendbar), −1, 0 oder +1. Bei technischen Ausfällen leer. |
| `LLM_Reasoning` | Vorhandene Modellbegründung oder ursprünglicher technischer Vermerk. |
| `LLM_Score_Original` | Unveränderter importierter Score vor der Statusbereinigung, einschließlich historischer −99-Platzhalter bei sieben technischen Ausfällen. |
| `Coding_Status` | `Coded` bei inhaltlicher Codierung; technische Statuswerte siehe unten. |

Die bestehenden Daten enthalten `Safety_Blocked`, `Missing_Or_Safety_Blocked` und `Missing_Score`. Der kombinierte Status bewahrt die Unsicherheit des ursprünglichen Vermerks; aus einer fehlenden Antwort allein wird keine Sicherheitsblockade abgeleitet. Der Antwortparser unterscheidet bei neuen lokalen Eingaben außerdem `Missing_Response`, `API_Error`, `Parse_Error` und `Invalid_Score`.

Die [Statusübersicht](coding_status_summary.csv) zählt diese Fälle pro Seed. Seed 42 enthält drei fehlende Scores; Seed 2024 vier und Seed 12345 drei technische Ausfälle, die zuvor als −99 gespeichert waren. Die sieben umgekennzeichneten Fälle waren bereits aus den Regressionsdaten ausgeschlossen. Die Regressionsstichproben und die 100 Validierungslabels bleiben unverändert. Ein inhaltlicher −99-Score zählt weiterhin als `Coded`.

Prüfung: `python3 scripts/02_llm_pipeline/03_normalize_coding_status.py --check` vom Paketverzeichnis aus. Ohne `--check` werden die Annotationen und die Statusübersicht anhand der vorhandenen Scores und technischen Vermerke erneut normalisiert. Es erfolgen keine API-Aufrufe.
