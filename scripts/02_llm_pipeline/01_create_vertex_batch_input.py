#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellung der Batch-Inferenz-Anfragen fuer Google Cloud Vertex AI (gemini-3.5-flash-lite).
Prueft eine explizit angegebene lokale Volltextdatei und erstellt JSONL gemaess Codebuch.
Dieser Schritt erzeugt nur Anfragen; er fuehrt keine API-Aufrufe aus.
"""

import argparse
import json
from pathlib import Path

import pandas as pd

system_instruction = (
    "You are an expert academic coder for quantitative content analysis in communication research. "
    "Your task is to conduct 'Entity-Level Stance Analysis' on overseas Chinese media articles. "
    "Strictly follow the codebook instructions and output ONLY valid JSON."
)

def load_and_validate_articles(input_file):
    input_path = Path(input_file).expanduser()
    if input_path.suffix.lower() == ".csv":
        df = pd.read_csv(input_path, dtype={"Doc_ID": str})
    elif input_path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(input_path, dtype={"Doc_ID": str})
    else:
        raise ValueError("Die Volltextdatei muss im Format CSV, XLSX oder XLS vorliegen.")

    required_columns = {
        "Doc_ID": ("Doc_ID",),
        "Titel": ("News Title", "Title"),
        "Artikelvolltext": ("News Content", "Text"),
    }
    selected_columns = {}
    for label, candidates in required_columns.items():
        column = next((name for name in candidates if name in df.columns), None)
        if column is None:
            raise ValueError(
                f"Pflichtspalte fuer {label} fehlt: {' oder '.join(candidates)}. "
                "Bitte eine lokale Volltextdatei angeben; die oeffentliche Metadatentabelle "
                "enthaelt keine Artikelvolltexte."
            )
        selected_columns[label] = column

    if df.empty:
        raise ValueError("Die Volltextdatei enthaelt keine Artikel.")

    for label, column in selected_columns.items():
        empty = df[column].isna() | df[column].astype(str).str.strip().eq("")
        if empty.any():
            rows = ", ".join(str(index + 2) for index in df.index[empty][:10])
            raise ValueError(
                f"{label} fehlt oder ist leer in {int(empty.sum())} Artikel(n). "
                f"Tabellenzeilen einschliesslich Kopfzeile (max. 10): {rows}. "
                "Es werden keine Anfragen geschrieben."
            )

    if df["Doc_ID"].astype(str).str.strip().duplicated().any():
        raise ValueError("Doc_ID muss fuer jeden Artikel eindeutig sein.")

    return df, selected_columns["Titel"], selected_columns["Artikelvolltext"]


def export_to_batch(input_file, output_file):
    input_path = Path(input_file).expanduser().resolve()
    output_path = Path(output_file).expanduser().resolve()
    if input_path == output_path:
        raise ValueError("Eingabe- und Ausgabedatei muessen unterschiedliche Pfade haben.")

    print(f"Lese Datensatz ein: {input_file}")
    # Erst den gesamten Datensatz pruefen, bevor die Ausgabedatei geoeffnet wird.
    df, title_column, text_column = load_and_validate_articles(input_path)

    with output_path.open('w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            title = str(row[title_column])
            text = str(row[text_column])
            doc_id = row['Doc_ID']
            
            prompt = f"""
[Doc_ID: {doc_id}]

Please analyze the following news article from an overseas Chinese media outlet.
Your specific task is to determine the author's/media outlet's overall stance directed EXCLUSIVELY towards "Chinese Government-Related Entities" within the text.

## 1. Definition of the Target Entity ("Chinese Government-Related Entities")

INCLUDES: The Chinese central and local governments, the Chinese Communist Party (CCP), state officials, state-owned enterprises, Chinese state media, military/police, national macro-policies/strategies (e.g., "Zero-COVID", "Belt and Road", "Economic reforms", financial regulations, border policies, historical wars), AND state-enforced ideological environments (e.g., political censorship, "speech environment", "red lines", political loyalty tests like "flag bearers").

EXCLUDES: Ordinary Chinese citizens, diaspora, society at large, independent Chinese private companies (e.g., TikTok, BYD, TSMC), non-state actors (e.g., scammers, smugglers, criminal gangs), and purely demographic/economic data or social phenomena (e.g., "aging population", "youth unemployment") WITHOUT explicit attribution to government policy failures.
CRITICAL RULE: If the article criticizes private companies, non-state actors, or citizens, or states demographic facts WITHOUT attributing their faults/causes to government governance, censorship, or institutional flaws, the stance toward the government is NOT negative (score 0 or -99).

## 2. Important Coding Rules & Anti-Pitfall Guide

Pitfall A: Confusing Tone/Descriptive Reporting with Stance (The "Academic/Rational" Trap).
Do not mistake a calm, academic, or highly descriptive tone for a "Neutral" stance. If the author traces economic decline or diplomatic isolation back to "systemic flaws" or "policy failures," it is Negative (-1).
CRITICAL ADDITION 1: If an article uses a social investigative framework to expose institutional absurdity, highlights regulatory vacuums, or evaluates public welfare policy as failing the public (e.g., "the unemployment system disqualifies those who need it most"), it is evaluating governance negatively and MUST be coded as Negative (-1).
CRITICAL ADDITION 2: Similarly, objective-sounding journalistic descriptions of heavy-handed state security, suppression of civil liberties, or the silencing of media/dissent (e.g., "heavy police presence," "shutting down newspapers," "national security trials") inherently frame the state as authoritarian and MUST be coded as Negative (-1).

Pitfall B: Confusing Quoted Speech/Interviews with "Objective" Authorial Voice.
If the article simply reports an event and genuinely balances quotes from both sides, it is Neutral (0).
CRITICAL EXCEPTION 1 (Geopolitical): If the article uses foreign analysts, military experts, or neighboring countries to describe China's "military expansion", "maritime actions", or "territorial claims" (e.g., in the South China Sea) as causing "tensions," "friction," or driving other nations to ally/drill against China, WITHOUT quoting the Chinese government defending itself, this constitutes a ONE-SIDED NEGATIVE NARRATIVE. You MUST code it as Negative (-1). DO NOT excuse this as "neutral analytical reporting", "factual descriptions of state actions", or "objective geopolitical background." Portraying China as the catalyst for defensive alliances against it IS a negative stance.
CRITICAL EXCEPTION 2 (Interviews): If the media outlet publishes an interview, round-table, or cites critics who extensively describe an oppressive political environment, censorship, or state vetting, and the outlet provides no counter-narrative, the outlet is adopting this negative stance. It MUST be coded as Negative (-1). DO NOT dismiss this as an "objective interview format" or "external industry constraints."

Pitfall C: Explicit Political, Systemic & Cultural/Ideological Critique.
Labeling the system as "authoritarian", "oppressive", criticizing "censorship", portraying state leaders as engaging in manipulative power struggles, or declaring a signature state policy as a failure, is automatically Negative (-1).
CRITICAL ADDITION: In cultural, entertainment, or industry articles, if the text (including quotes/interviewees) mentions a deteriorating "speech environment" (言论环境), "red lines" (踩线), artists being forced into political loyalty (e.g., "flag bearers"/护旗手), or political scrutiny by netizens (e.g., "magnifying glass"/放大镜), you MUST treat this as a critique of the state's ideological control and code it as Negative (-1). DO NOT dismiss these as mere "cultural phenomena", "internet phenomena", or "industry historical background."

Pitfall D: Incomplete/Irrelevant Texts & The "Background Context" Exception.
If the text is entirely about foreign countries with NO mention of China, is too short to determine a stance, OR merely states social/demographic facts with zero mention of state policies, code as Uncertain/None (-99).
CRITICAL ADDITION: If an article mentions Chinese policies or geopolitical tensions merely as an objective background, do NOT use -99. However, WARNING: You can ONLY score this as Neutral (0) IF the article strictly states facts WITHOUT adopting a one-sided negative narrative (Pitfall B) AND WITHOUT mentioning censorship/oppressive environments (Pitfall C). If Pitfall B or C apply, they OVERRIDE this background exception and the score MUST be -1. "Geopolitical background" or "industry constraints" are NOT valid excuses to ignore anti-China expert quotes or censorship critiques.

Pitfall E: The "Primary Target" Fallacy.
Even if the primary focus of the article is criticizing a third party (e.g., foreign leftists, a specific industry, or a foreign country), if the author explicitly describes the Chinese government's actions as "oppressive", "authoritarian", or criticizes its policies (e.g., in Xinjiang, Hong Kong, or Tibet) as part of their argument against that third party, it MUST be coded as Negative (-1). Do not ignore direct negative characterizations of the state just because the state is not the main subject of the article.

## 3. Coding Categories (Stance Score)

[ 1] Positive: The article explicitly praises the government's achievements, effective governance, system superiority, or global contribution.

[ 0] Neutral: Objective factual reporting, balanced presentation of opposing views without authorial bias. This ONLY applies if the text genuinely lacks one-sided negative expert quotes (Pitfall B) and lacks censorship/ideological critiques (Pitfall C).

[-1] Negative: The author subjectively critiques policy failures, systemic/bureaucratic flaws, censorship, authoritarianism, ideological tightening/suppression in cultural fields, describes state security suppression, OR adopts/curates a one-sided negative narrative against the state.

[-99] Uncertain/None: The text does NOT discuss Chinese government-related entities or policies at all, discusses pure social facts without government attribution/context, or is too short/incomplete.

## 4. Output Format (Strict JSON with Chain-of-Thought)

You must output a JSON object. ALL TEXT INSIDE THE JSON MUST BE IN ENGLISH ONLY. Do not use Chinese. To ensure proper reasoning, you MUST fill out the JSON keys in the exact order below, acting as your step-by-step reasoning process:

{{
"step1_entity_extraction": "List the specific Chinese government-related entities or policies mentioned. Are these actual government entities/policies, or just purely demographic/social facts? Do they include historical state policies (e.g., financial bans, border conflicts) acting as background? (If 100% absent, write 'None' and prepare to score -99).",
"step2_voice_and_attribution": "Are the evaluations coming from the author's own analysis, or curated third-party quotes? Is it a balanced report or a one-sided framing (e.g., portraying China as an aggressor or describing state suppression)? Does the author mention ideological/censorship pressures?",
"step3_core_conclusion": "Look past the tone and the primary topic. Determine the ultimate verdict. If the text contains one-sided negative quotes (Pitfall B) or mentions an oppressive/censored environment (Pitfall C), you MUST conclude it is a negative stance (-1). Do NOT excuse it as 'objective background' or 'standard geopolitical reporting'.",
"stance_score": <int> (-1, 0, 1, or -99)
}}

=== ARTICLE BEGIN ===
Title: {title}
Text: {text}
=== ARTICLE END ===
"""
            
            # Standardisiertes JSON-Anfrageformat fuer Vertex AI Batch Prediction
            request_obj = {
                "request": {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "systemInstruction": {"role": "system", "parts": [{"text": system_instruction}]},
                    "generationConfig": {
                        "temperature": 0.0,
                        "topP": 0.2,
                        "responseMimeType": "application/json"
                    }
                }
            }
            f.write(json.dumps(request_obj, ensure_ascii=False) + '\n')
            
    print(f"Vertex AI Batch-Datei erfolgreich generiert: {output_file}")
    print(f"Gesamtanzahl der verarbeiteten Zeilen: {len(df)}")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, type=Path,
        help="Lokale CSV-/Excel-Datei mit Doc_ID, News Title/Title und News Content/Text.",
    )
    parser.add_argument(
        "--output", required=True, type=Path,
        help="Zielpfad der JSONL-Anfragen; die Datei enthaelt die Artikelvolltexte.",
    )
    args = parser.parse_args()
    try:
        export_to_batch(args.input, args.output)
    except (ValueError, OSError, ImportError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
