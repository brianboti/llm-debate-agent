from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .types import BatchSummary, Item, ItemResult


def new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{timestamp}_{uuid4().hex[:8]}"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_item_dataset(path: Path, *, limit: int | None = None) -> list[Item]:
    items: list[Item] = []
    for row in read_jsonl(path):
        items.append(Item(**row))
        if limit is not None and len(items) >= limit:
            break
    return items


def save_item_results(path: Path, results: list[ItemResult]) -> None:
    write_jsonl(path, [result.model_dump() for result in results])


def write_summary(path: Path, summary: BatchSummary) -> None:
    ensure_dir(path.parent)
    path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")


def load_single_run(path: Path) -> list[dict]:
    return read_jsonl(path)
