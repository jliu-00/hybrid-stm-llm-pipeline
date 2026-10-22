#!/usr/bin/env python3
"""Normalize existing public annotations without changing analysis IDs or data."""
import argparse
import csv
from collections import Counter
from pathlib import Path

from coding_status import normalize_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--check", action="store_true", help="Read-only consistency check")
    args = parser.parse_args()
    prepared, summary = [], []
    for seed in (42, 2024, 12345):
        path = args.package_root / f"data/annotations/llm_scored_full_seed_{seed}.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = list(reader.fieldnames)
            rows = list(reader)
        ids = [int(row["Doc_ID"]) for row in rows]
        if len(set(ids)) != len(ids) or any(x <= 0 for x in ids):
            raise ValueError(f"Invalid Doc_ID: seed {seed}")
        normalized = [normalize_record(row) for row in rows]
        for field in ("LLM_Score_Original", "Coding_Status"):
            if field not in fields:
                fields.append(field)
        counts = Counter(row["Coding_Status"] for row in normalized)
        summary.extend({"Seed": seed, "Coding_Status": status, "N": n}
                       for status, n in sorted(counts.items()))
        if args.check and rows != normalized:
            raise ValueError(f"Annotations need normalization: seed {seed}")
        prepared.append((path, fields, normalized))
        print(f"Seed {seed}: {len(rows)} rows; {dict(counts)}")
    summary_path = args.package_root / "data/annotations/coding_status_summary.csv"
    if args.check:
        with summary_path.open(encoding="utf-8", newline="") as stream:
            actual = list(csv.DictReader(stream))
        expected = [{k: str(v) for k, v in row.items()} for row in summary]
        if actual != expected:
            raise ValueError("Coding status summary differs")
    else:
        # Validate every seed before writing any file.
        for path, fields, rows in prepared:
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
        with summary_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["Seed", "Coding_Status", "N"])
            writer.writeheader()
            writer.writerows(summary)


if __name__ == "__main__":
    main()
