#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from collections import OrderedDict
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


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def accuracy(rows: list[dict], key: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get(key)) / len(rows)


def stop_reason(row: dict) -> str:
    return str(row.get("meta", {}).get("stop_reason", ""))


def failure_pattern_counts(rows: list[dict]) -> OrderedDict[str, int]:
    return OrderedDict(
        [
            ("debate_beats_both", sum(1 for row in rows if row.get("correct_debate") and not row.get("correct_direct") and not row.get("correct_sc"))),
            ("debate_loses_to_both", sum(1 for row in rows if not row.get("correct_debate") and row.get("correct_direct") and row.get("correct_sc"))),
            ("debate_and_sc_beat_direct", sum(1 for row in rows if row.get("correct_debate") and not row.get("correct_direct") and row.get("correct_sc"))),
            ("all_fail", sum(1 for row in rows if not row.get("correct_debate") and not row.get("correct_direct") and not row.get("correct_sc"))),
            ("max_rounds_reached", sum(1 for row in rows if stop_reason(row) == "max_rounds_reached")),
            ("initial_consensus", sum(1 for row in rows if stop_reason(row) == "initial_consensus")),
            ("adaptive_convergence", sum(1 for row in rows if stop_reason(row).startswith("adaptive_convergence"))),
        ]
    )


def markdown_failure_patterns(rows: list[dict]) -> str:
    counts = failure_pattern_counts(rows)
    lines = [
        "| Pattern | Count |",
        "|---|---:|",
    ]
    for key, value in counts.items():
        lines.append(f"| `{key}` | {value} |")
    return "\n".join(lines)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def select_case_studies(rows: list[dict]) -> list[dict[str, str]]:
    selectors = [
        (
            "all_fail_initial_consensus",
            "All three methods fail and the debate ends before any rounds.",
            lambda row: (not row.get("correct_debate"))
            and (not row.get("correct_direct"))
            and (not row.get("correct_sc"))
            and stop_reason(row) == "initial_consensus",
        ),
        (
            "debate_loses_to_both_max_rounds",
            "Debate uses the full round budget and still loses to both baselines.",
            lambda row: (not row.get("correct_debate"))
            and row.get("correct_direct")
            and row.get("correct_sc")
            and stop_reason(row) == "max_rounds_reached",
        ),
        (
            "debate_and_sc_beat_direct",
            "Debate and self-consistency recover an answer that direct QA misses.",
            lambda row: row.get("correct_debate")
            and (not row.get("correct_direct"))
            and row.get("correct_sc"),
        ),
        (
            "all_correct_initial_consensus",
            "All methods are correct and the debate resolves immediately by consensus.",
            lambda row: row.get("correct_debate")
            and row.get("correct_direct")
            and row.get("correct_sc")
            and stop_reason(row) == "initial_consensus",
        ),
        (
            "adaptive_convergence_example",
            "Debaters converge after multiple rounds instead of hitting the maximum budget.",
            lambda row: stop_reason(row).startswith("adaptive_convergence"),
        ),
    ]

    picked_ids: set[str] = set()
    selected: list[dict[str, str]] = []
    for label, description, predicate in selectors:
        for row in rows:
            item_id = str(row.get("item", {}).get("id", ""))
            if not item_id or item_id in picked_ids:
                continue
            if predicate(row):
                picked_ids.add(item_id)
                selected.append(
                    {
                        "label": label,
                        "description": description,
                        "item_id": item_id,
                        "question": str(row.get("item", {}).get("question", "")),
                        "path": f"case_studies/{item_id}.json",
                    }
                )
                break
    return selected


def write_case_studies(rows: list[dict], out_dir: Path) -> None:
    case_dir = out_dir / "case_studies"
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    selected = select_case_studies(rows)
    by_id = {str(row.get("item", {}).get("id", "")): row for row in rows}
    for record in selected:
        item_id = record["item_id"]
        payload = copy.deepcopy(by_id[item_id])
        payload.setdefault("meta", {})
        payload["meta"]["case_study_label"] = record["label"]
        payload["meta"]["case_study_description"] = record["description"]
        write_json(case_dir / f"{item_id}.json", payload)

    lines = ["| Label | Item ID | Why It Was Selected |", "|---|---|---|"]
    for record in selected:
        lines.append(f"| `{record['label']}` | `{record['item_id']}` | {record['description']} |")
    (case_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(case_dir / "manifest.json", selected)


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
    legacy_summary = args.out_dir / f"{args.run_jsonl.stem}.summary.json"
    if legacy_summary.exists():
        legacy_summary.unlink()

    (args.out_dir / "metrics_table.md").write_text(markdown_results_table(rows) + "\n", encoding="utf-8")
    (args.out_dir / "stats_summary.md").write_text(markdown_stats_block(results, args.run_jsonl.stem) + "\n", encoding="utf-8")
    (args.out_dir / "failure_patterns.md").write_text(markdown_failure_patterns(rows) + "\n", encoding="utf-8")
    write_json(args.out_dir / "failure_patterns.json", failure_pattern_counts(rows))
    save_plot(rows, args.out_dir / "accuracy_comparison.png")
    write_case_studies(rows, args.out_dir)

    summary = compute_summary(args.run_jsonl.stem, results)
    sibling_summary_path = args.run_jsonl.with_name(f"{args.run_jsonl.stem}.summary.json")
    sibling_summary = read_json(sibling_summary_path)
    if not summary.dataset_path and sibling_summary.get("dataset_path"):
        summary.dataset_path = str(sibling_summary["dataset_path"])
    if not summary.experiment_config and isinstance(sibling_summary.get("experiment_config"), dict):
        summary.experiment_config = sibling_summary["experiment_config"]
    (args.out_dir / "summary.json").write_text(summary.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
