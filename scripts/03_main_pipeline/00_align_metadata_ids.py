#!/usr/bin/env python3
"""Align input metadata to the existing STM Doc_ID without changing analysis data."""

import argparse
import csv
import os
from pathlib import Path
import tempfile


RETAINED = "Retained_for_STM"
EXCLUDED = "Excluded_before_STM"
CONTROL_COLUMNS = ("Seed", "Source_Row_ID", "Doc_ID", "STM_Status")
CROSSWALK_COLUMNS = ("Seed", "Source_Row_ID", "Doc_ID", "News Link", "STM_Status")
FUNDING_LABELS = {
    "Independent Media": "Other Sources",
    "Foreign Government": "Foreign Gov-Affiliated",
    "Other Sources": "Other Sources",
    "Foreign Gov-Affiliated": "Foreign Gov-Affiliated",
}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def positive_id(value, label):
    value = str(value).strip()
    if not value.isdecimal() or int(value) < 1:
        raise ValueError(f"{label} must contain a positive integer.")
    return str(int(value))


def unique_index(rows, column, label):
    index = {}
    for row in rows:
        value = row.get(column, "")
        if not value or value in index:
            raise ValueError(f"{label}: missing or duplicate {column}.")
        index[value] = row
    return index


def prepare_seed(package_root, seed):
    package_root = Path(package_root)
    metadata_path = package_root / "data/metadata" / f"corpus_metadata_seed_{seed}.csv"
    theta_path = package_root / "data/derived/stm" / f"seed_{seed}" / "theta_all_stm_documents.csv"
    columns, source = read_csv(metadata_path)
    _, theta = read_csv(theta_path)
    source_by_url = unique_index(source, "News Link", f"seed {seed} metadata")
    theta_by_url = unique_index(theta, "News Link", f"seed {seed} theta")
    unique_index(theta, "Doc_ID", f"seed {seed} theta")
    if set(theta_by_url) - set(source_by_url):
        raise ValueError(f"seed {seed}: STM documents are missing from the input metadata.")

    output_columns = list(CONTROL_COLUMNS) + [name for name in columns if name not in CONTROL_COLUMNS]
    aligned, crosswalk, source_ids = [], [], set()
    for original in source:
        if original.get("Seed", str(seed)) != str(seed):
            raise ValueError(f"seed {seed}: metadata has an inconsistent Seed value.")
        source_id = positive_id(original.get("Source_Row_ID", original.get("Doc_ID", "")), "Source_Row_ID")
        if source_id in source_ids:
            raise ValueError(f"seed {seed}: duplicate Source_Row_ID.")
        source_ids.add(source_id)
        match = theta_by_url.get(original["News Link"])
        if match is not None:
            if match.get("Seed", str(seed)) != str(seed):
                raise ValueError(f"seed {seed}: theta has an inconsistent Seed value.")
            comparisons = (
                (original["News Title"], match["Title"]),
                (original["Media Name"], match["Media Name"]),
                (original["News Date"], match["News Date"]),
                (original["Media Region"], match["Media Region"]),
                (original["Is_Taiwan"], match["Is_Taiwan"]),
                (FUNDING_LABELS.get(original["Funding Source"]), match["Funding_Sources"]),
            )
            if any(left != right for left, right in comparisons):
                raise ValueError(f"seed {seed}, source row {source_id}: article fields disagree after URL matching.")
            doc_id = positive_id(match["Doc_ID"], "Doc_ID")
            status = RETAINED
        else:
            doc_id, status = "", EXCLUDED
        row = dict(original)
        row.update(Seed=str(seed), Source_Row_ID=source_id, Doc_ID=doc_id, STM_Status=status)
        aligned.append(row)
        crosswalk.append({name: row[name] for name in CROSSWALK_COLUMNS})
    mapping_path = metadata_path.with_name(f"document_id_crosswalk_seed_{seed}.csv")
    return {
        "seed": seed, "metadata_path": metadata_path, "mapping_path": mapping_path,
        "columns": output_columns, "rows": aligned, "crosswalk": crosswalk,
        "retained": len(theta), "excluded": len(source) - len(theta),
    }


def atomic_write(path, columns, rows):
    path = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.chmod(temporary_path, (path.stat().st_mode & 0o777) if path.exists() else 0o644)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 2024, 12345])
    parser.add_argument("--check", action="store_true", help="Validate existing files without writing them.")
    args = parser.parse_args(argv)
    # Validate every requested seed before writing any files.
    prepared = [prepare_seed(args.package_root, seed) for seed in args.seeds]
    for result in prepared:
        if args.check:
            columns, rows = read_csv(result["metadata_path"])
            cross_columns, cross_rows = read_csv(result["mapping_path"])
            if columns != result["columns"] or rows != result["rows"]:
                raise ValueError(f"seed {result['seed']}: metadata needs alignment.")
            if cross_columns != list(CROSSWALK_COLUMNS) or cross_rows != result["crosswalk"]:
                raise ValueError(f"seed {result['seed']}: the crosswalk does not match the metadata.")
        else:
            atomic_write(result["metadata_path"], result["columns"], result["rows"])
            atomic_write(result["mapping_path"], CROSSWALK_COLUMNS, result["crosswalk"])
        print(f"Seed {result['seed']}: {result['retained']} aligned STM documents; {result['excluded']} excluded input rows.")


if __name__ == "__main__":
    main()
