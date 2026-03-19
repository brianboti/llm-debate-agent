#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.app import _build_item_result, _persist_run  # type: ignore
from src.config import settings  # type: ignore
from src.eval import compute_summary  # type: ignore
from src.logs import load_item_dataset, new_run_id  # type: ignore
from src.openai_client import OpenAIClient  # type: ignore
from src.prompts import PromptStore  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a batch experiment from a JSONL dataset.")
    parser.add_argument("dataset_jsonl", type=Path, help="Path to the dataset JSONL file")
    parser.add_argument("--limit", type=int, default=None, help="Optional number of items to run")
    parser.add_argument("--judge-panel-size", type=int, default=None, help="Optional override for the number of judges")
    args = parser.parse_args()

    dataset_path = args.dataset_jsonl.expanduser().resolve()
    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")

    client = OpenAIClient()
    prompts = PromptStore(settings.prompts_path())
    experiment_config = settings.experiment_snapshot(
        judge_panel_size_override=args.judge_panel_size,
        prompt_manifest=prompts.manifest(),
    )
    items = load_item_dataset(dataset_path, limit=args.limit)
    if not items:
        raise SystemExit("Dataset is empty.")

    results = [
        _build_item_result(
            client=client,
            prompts=prompts,
            item=item,
            dataset_path=dataset_path,
            judge_panel_size_override=args.judge_panel_size,
            experiment_config=experiment_config,
        )
        for item in items
    ]

    run_id = new_run_id()
    _persist_run(run_id, results)
    summary = compute_summary(run_id, results)

    print(summary.model_dump_json(indent=2))
    print(f"\nSaved run logs to: {settings.runs_path() / (run_id + '.jsonl')}")
    print(f"Saved summary to: {settings.runs_path() / (run_id + '.summary.json')}")


if __name__ == "__main__":
    main()
