#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill dataset/config metadata into an existing run JSONL.")
    parser.add_argument("run_jsonl", type=Path, help="Path to runs/<run_id>.jsonl")
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=None,
        help="Optional path to runs/<run_id>.summary.json. Defaults to the sibling summary file.",
    )
    parser.add_argument("--in-place", action="store_true", help="Rewrite the input file instead of writing a sibling output.")
    args = parser.parse_args()

    run_jsonl = args.run_jsonl.expanduser().resolve()
    summary_json = (args.summary_json or run_jsonl.with_name(f"{run_jsonl.stem}.summary.json")).expanduser().resolve()

    if not run_jsonl.exists():
        raise SystemExit(f"Run JSONL not found: {run_jsonl}")
    if not summary_json.exists():
        raise SystemExit(f"Summary JSON not found: {summary_json}")

    rows = read_jsonl(run_jsonl)
    summary = read_json(summary_json)
    dataset_path = summary.get("dataset_path")
    experiment_config = summary.get("experiment_config")

    for row in rows:
        meta = row.setdefault("meta", {})
        if dataset_path and "dataset_path" not in meta:
            meta["dataset_path"] = dataset_path
        if experiment_config and "experiment_config" not in meta:
            meta["experiment_config"] = experiment_config

    out_path = run_jsonl if args.in_place else run_jsonl.with_name(f"{run_jsonl.stem}.enriched.jsonl")
    write_jsonl(out_path, rows)
    print(out_path)


if __name__ == "__main__":
    main()
