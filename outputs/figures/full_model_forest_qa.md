# Prüfung der vollständigen Forest-Plots

Die Abbildungen dokumentieren die Finanzierungs- und Taiwan-Koeffizienten aus M1/M2 sowie die 19 Themenkoeffizienten aus M2. Die Konstante ist ausgelassen. Jeder Seed verwendet seinen eigenen Regressionsdatensatz und seine eigenen deutschen Themenbezeichnungen.

| Seed | Regressionsfälle | Referenzthema | M1-Finanzierungskoeffizient | M2-Finanzierungskoeffizient |
| --- | ---: | --- | ---: | ---: |
| 42 | 3.251 | T19 | 0,1614720820 | -0,0238828839 |
| 12345 | 3.293 | T7 | 0,1835088099 | -0,0249523387 |
| 2024 | 3.292 | T14 | 0,1833146083 | 0,0326501127 |

- Die Referenzthemen wurden mit der ursprünglichen Auswahlregel aus den öffentlichen Daten bestätigt. Der Wechsel des ausgelassenen Themas gegenüber der bisherigen einheitlichen T19-Parametrisierung verändert die Finanzierungskoeffizienten, ihre Intervalle und die Modellgüte nur innerhalb numerischer Rundungsgenauigkeit. Die maximale Änderung der vorhergesagten Werte liegt unter 3 × 10⁻¹⁴.
- Aus den Eingabetabellen wurden keine weiteren Regressionsfälle ausgeschlossen. Jede Quelldatentabelle enthält die 23 dargestellten Koeffizienten mit Standardfehlern, 95%-Intervallen und exakten p-Werten. Die vorhandene Drei-Seed-Vergleichstabelle blieb unverändert.
- Intervalle und p-Werte folgen gewöhnlichen OLS-t-Tests, zweiseitig und ohne Mehrfachtestkorrektur. Themenanteile liegen auf der Skala 0-1; die Themenkoeffizienten beziehen sich auf das jeweilige ausgelassene Referenzthema. Themennummern verschiedener Seeds sind inhaltlich nicht gleichzusetzen.
- Exportgröße: 183 × 210 mm. PDF/SVG enthalten editierbaren Text; PNG/TIFF besitzen 600 dpi. Die minimale gemessene PDF-Schriftgröße beträgt 6,54 pt. Sämtliche Konfidenzintervalle liegen vollständig innerhalb der Achsengrenzen.
- R-Syntaxprüfung und statische Quellenprüfung bestanden. Die PDF-Geometrieprüfung meldet bei allen drei Abbildungen keine Überlagerungs- oder Beschnittbefunde. Farbige Zeilenhintergründe unter Text sind beabsichtigt. Alle drei R-gerenderten PNGs wurden visuell geprüft. Mehrpanel-Ausrichtung ist für diese einzelne Tabellen-/Forest-Fläche nicht anwendbar.
- Haupt- und Robustheitseinstieg wurden mit öffentlichen Tabellen in einer separaten Paketkopie ausgeführt; die schreibfreie Prüfung des öffentlichen Grafikeinstiegs und der geänderte Abbildungsblock des Gesamtskripts wurden ebenfalls geprüft.

Pro Seed stehen PDF, SVG, PNG, TIFF und `Full_Model_Coefficient_Forest_Plot_source_data.csv` ausschließlich im zugehörigen Ordner `seed_42`, `seed_12345` oder `seed_2024`. Die gemeinsame Erzeugungsroutine ist `scripts/03_main_pipeline/full_model_forest_plot.R`.
