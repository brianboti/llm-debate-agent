#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.eval import bootstrap_accuracy_diff, compute_summary  # type: ignore
from src.types import ItemResult  # type: ignore


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def to_item_results(rows: list[dict]) -> list[ItemResult]:
    return [ItemResult.model_validate(row) for row in rows]


def accuracy(rows: list[dict], key: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get(key)) / len(rows)


def _fmt_p(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value < 0.001:
        return "< 0.001"
    return f"{value:.4f}"


def markdown_results_table(rows: list[dict]) -> str:
    return "\n".join(
        [
            "| Method | Accuracy | Correct / Total |",
            "|---|---:|---:|",
            f"| Debate + Judge | {accuracy(rows, 'correct_debate'):.3f} | {sum(1 for row in rows if row.get('correct_debate'))} / {len(rows)} |",
            f"| Direct QA | {accuracy(rows, 'correct_direct'):.3f} | {sum(1 for row in rows if row.get('correct_direct'))} / {len(rows)} |",
            f"| Self-Consistency | {accuracy(rows, 'correct_sc'):.3f} | {sum(1 for row in rows if row.get('correct_sc'))} / {len(rows)} |",
        ]
    )


def markdown_stats_block(results: list[ItemResult], run_id: str) -> str:
    summary = compute_summary(run_id, results)
    debate_vs_direct_mean, dvd_lo, dvd_hi = bootstrap_accuracy_diff(results, a="debate", b="direct")
    debate_vs_sc_mean, dvs_lo, dvs_hi = bootstrap_accuracy_diff(results, a="debate", b="sc")

    lines = [
        f"- Number of questions: **{summary.n_items}**",
        f"- McNemar p-value (Debate vs Direct QA): **{_fmt_p(summary.mcnemar_debate_vs_direct_p)}**",
        f"- McNemar p-value (Debate vs Self-Consistency): **{_fmt_p(summary.mcnemar_debate_vs_sc_p)}**",
        f"- Bootstrap accuracy difference, Debate − Direct QA: **{debate_vs_direct_mean:.3f}** (95% CI: **[{dvd_lo:.3f}, {dvd_hi:.3f}]**)",
        f"- Bootstrap accuracy difference, Debate − Self-Consistency: **{debate_vs_sc_mean:.3f}** (95% CI: **[{dvs_lo:.3f}, {dvs_hi:.3f}]**)",
    ]
    return "\n".join(lines)


def save_plot(rows: list[dict], out_path: Path) -> None:
    labels = ["Debate + Judge", "Direct QA", "Self-Consistency"]
    values = [
        accuracy(rows, "correct_debate"),
        accuracy(rows, "correct_direct"),
        accuracy(rows, "correct_sc"),
    ]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(labels, values)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Accuracy")
    ax.set_title("Accuracy by inference strategy")
    for idx, value in enumerate(values):
        ax.text(idx, value + 0.02, f"{value:.3f}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate report tables/figures from a run JSONL file.")
    parser.add_argument("run_jsonl", type=Path, help="Path to runs/<run_id>.jsonl")
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts"), help="Directory for generated artifacts")
    args = parser.parse_args()

    rows = read_jsonl(args.run_jsonl)
    results = to_item_results(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    (args.out_dir / "metrics_table.md").write_text(markdown_results_table(rows) + "\n", encoding="utf-8")
    (args.out_dir / "stats_summary.md").write_text(markdown_stats_block(results, args.run_jsonl.stem) + "\n", encoding="utf-8")
    save_plot(rows, args.out_dir / "accuracy_comparison.png")

    summary = compute_summary(args.run_jsonl.stem, results)
    (args.out_dir / "summary.json").write_text(summary.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
