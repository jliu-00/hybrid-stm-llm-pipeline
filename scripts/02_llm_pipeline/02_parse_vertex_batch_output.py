#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parsen der Rueckmeldungen der Vertex AI Batch Prediction API.
Extrahiert Doc_ID, Haltungsscore (LLM_Score) und den Chain-of-Thought (LLM_Reasoning)
und fuegt diese mit dem urspruenglichen Analysedatensatz zusammen.
"""

import os
import re
import json
import argparse
import pandas as pd
from coding_status import VALID_SCORES, normalize_record

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

DEFAULT_INPUT_DATA = os.path.join(PROJECT_ROOT, "data", "metadata", "corpus_metadata_seed_42.csv")
DEFAULT_BATCH_OUTPUT_JSONL = os.path.join(SCRIPT_DIR, "prediction.results.jsonl")
DEFAULT_FINAL_OUTPUT = os.path.join(PROJECT_ROOT, "data", "derived", "llm_scored_output_seed_42.csv")

def parse_response(data):
    """Return an explicit status even when the API supplies no stance label."""
    error = data.get('error')
    response = data.get('response') or {}
    candidates = response.get('candidates') or []
    candidate = candidates[0] if candidates else {}
    block = response.get('promptFeedback', {}).get('blockReason', '')
    finish = candidate.get('finishReason', '')
    if error:
        status = 'Safety_Blocked' if 'safety' in str(error).lower() else 'API_Error'
        return {'LLM_Score': '', 'LLM_Reasoning': str(error), 'Coding_Status': status}
    if block or finish in ('SAFETY', 'PROHIBITED_CONTENT', 'BLOCKLIST', 'SPII'):
        return {'LLM_Score': '', 'LLM_Reasoning': str(block or finish),
                'Coding_Status': 'Safety_Blocked'}
    parts = candidate.get('content', {}).get('parts', [])
    response_text = ''.join(part.get('text', '') for part in parts).strip()
    if not response_text:
        return {'LLM_Score': '', 'LLM_Reasoning': str(finish),
                'Coding_Status': 'Missing_Response'}
    clean_text = re.sub(r'^```(?:json)?\s*|\s*```$', '', response_text).strip()
    try:
        result = json.loads(clean_text)
        if not isinstance(result, dict):
            raise ValueError('Expected JSON object')
    except (ValueError, TypeError):
        return {'LLM_Score': '', 'LLM_Reasoning': response_text,
                'Coding_Status': 'Parse_Error'}
    score = result.get('stance_score')
    reasoning = ' | '.join(f'{k}: {result[k]}' for k in (
        'step1_entity_extraction', 'step2_voice_and_attribution', 'step3_core_conclusion'
    ) if result.get(k)) or json.dumps(result, ensure_ascii=False)
    if score is None:
        status = 'Missing_Score'
    elif isinstance(score, bool) or not isinstance(score, (int, float)) or score not in VALID_SCORES:
        status = 'Invalid_Score'
    else:
        status = 'Coded'
    return {'LLM_Score': '' if score is None else score,
            'LLM_Reasoning': reasoning, 'Coding_Status': status}

def parse_batch_output(batch_output_jsonl=DEFAULT_BATCH_OUTPUT_JSONL, 
                       input_data_path=DEFAULT_INPUT_DATA, 
                       final_output_path=DEFAULT_FINAL_OUTPUT):
    
    if not os.path.exists(batch_output_jsonl):
        raise FileNotFoundError(batch_output_jsonl)

    print(f"Lese JSONL-Batch-Ergebnisse: {batch_output_jsonl}")
    df = pd.read_csv(input_data_path) if input_data_path.endswith(".csv") else pd.read_excel(input_data_path)
    # The aligned metadata retain excluded input rows for provenance. Only
    # retained STM documents have the Doc_ID used in the original requests.
    if 'STM_Status' in df.columns:
        df = df.loc[df['STM_Status'] == 'Retained_for_STM'].copy()
    numeric_ids = pd.to_numeric(df['Doc_ID'], errors='raise')
    if numeric_ids.isna().any() or (numeric_ids <= 0).any() or (numeric_ids % 1 != 0).any():
        raise ValueError('Doc_ID muss fuer jedes beibehaltene Dokument eine positive ganze Zahl sein.')
    df['Doc_ID'] = numeric_ids.astype('int64')
    if df['Doc_ID'].duplicated().any():
        raise ValueError('Doppelte Doc_ID im Eingabedatensatz.')
    
    results_map = {}
    valid_ids = set(df['Doc_ID'])
    
    with open(batch_output_jsonl, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            req_text = data['request']['contents'][0]['parts'][0]['text']
            match = re.search(r"\[Doc_ID:\s*(\d+)\]", req_text)
            if not match:
                raise ValueError(f'Zeile {line_num}: Doc_ID fehlt im Anfrage-Header.')
            doc_id = int(match.group(1))
            if doc_id not in valid_ids:
                raise ValueError(f'Unbekannte Doc_ID: {doc_id}')
            if doc_id in results_map:
                raise ValueError(f'Doppelte Antwort fuer Doc_ID: {doc_id}')
            results_map[doc_id] = normalize_record(parse_response(data))

    # Ergebnisse dem Datensatz zuweisen
    missing = normalize_record({'LLM_Score': '', 'LLM_Reasoning': '',
                                'Coding_Status': 'Missing_Response'})
    for column in ('LLM_Score', 'LLM_Reasoning', 'LLM_Score_Original', 'Coding_Status'):
        df[column] = df['Doc_ID'].map(lambda x: results_map.get(x, missing)[column])
    
    success_count = (df['Coding_Status'] == 'Coded').sum()
    print(f"Parsen abgeschlossen: {success_count} von {len(df)} Artikeln erfolgreich zugeordnet.")
    
    df.to_csv(final_output_path, index=False)
    print(f"Zusammengefuehrter Datensatz gespeichert unter: {final_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch-output', default=DEFAULT_BATCH_OUTPUT_JSONL)
    parser.add_argument('--input', default=DEFAULT_INPUT_DATA)
    parser.add_argument('--output', default=DEFAULT_FINAL_OUTPUT)
    args = parser.parse_args()
    parse_batch_output(args.batch_output, args.input, args.output)
