#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.contingency_tables import mcnemar

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.types import normalize_answer  # type: ignore


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def align_rows(single_rows: list[dict], panel_rows: list[dict]) -> list[tuple[dict, dict]]:
    single_by_id = {row["item"]["id"]: row for row in single_rows}
    panel_by_id = {row["item"]["id"]: row for row in panel_rows}
    if set(single_by_id) != set(panel_by_id):
        missing_from_panel = sorted(set(single_by_id) - set(panel_by_id))
        missing_from_single = sorted(set(panel_by_id) - set(single_by_id))
        raise SystemExit(
            "Run item IDs do not match.\n"
            f"Missing from panel run: {missing_from_panel[:10]}\n"
            f"Missing from single run: {missing_from_single[:10]}"
        )
    return [(single_by_id[item_id], panel_by_id[item_id]) for item_id in sorted(single_by_id)]


def accuracy_from_bools(values: list[bool]) -> float:
    return sum(values) / len(values) if values else 0.0


def bool_field(row: dict, key: str) -> bool:
    return bool(row.get(key))


def majority_correct(row: dict) -> bool | None:
    value = row.get("correct_judge_panel_majority")
    if value is not None:
        return bool(value)
    summary = row.get("judge_panel_summary") or row.get("meta", {}).get("judge_panel_summary", {})
    majority_answer = normalize_answer(str(summary.get("majority_answer", "")))
    if not majority_answer:
        return None
    ground_truth = normalize_answer(str(row["item"]["ground_truth"]))
    return majority_answer == ground_truth


def panel_summary(row: dict) -> dict:
    summary = row.get("judge_panel_summary")
    if isinstance(summary, dict) and summary:
        return summary
    meta_summary = row.get("meta", {}).get("judge_panel_summary", {})
    return meta_summary if isinstance(meta_summary, dict) else {}


def disagreement(row: dict) -> bool:
    summary = panel_summary(row)
    if "disagreement" in summary:
        return bool(summary["disagreement"])
    return len({normalize_answer(v["verdict_answer"]) for v in row.get("judge_panel", [])}) > 1


def deliberation_changed_majority(row: dict) -> bool:
    summary = panel_summary(row)
    if "deliberation_changed_majority" in summary:
        return bool(summary["deliberation_changed_majority"])
    final_answer = normalize_answer(str(row.get("judge", {}).get("verdict_answer", "")))
    majority_answer = normalize_answer(str(summary.get("majority_answer", "")))
    panel_size = int(summary.get("panel_size", len(row.get("judge_panel", [])) or 1))
    return panel_size > 1 and bool(majority_answer) and final_answer != majority_answer


def difficulty_bucket(row: dict) -> str:
    baseline_correct = int(bool(row.get("correct_direct"))) + int(bool(row.get("correct_sc")))
    return {2: "easy", 1: "medium", 0: "hard"}[baseline_correct]


def mcnemar_p(a: list[bool], b: list[bool]) -> float | None:
    n00 = n01 = n10 = n11 = 0
    for ax, bx in zip(a, b, strict=True):
        if ax and bx:
            n11 += 1
        elif ax and not bx:
            n10 += 1
        elif (not ax) and bx:
            n01 += 1
        else:
            n00 += 1

    discordant = n01 + n10
    if discordant == 0:
        return 1.0

    table = [[n00, n01], [n10, n11]]
    exact = discordant < 25
    result = mcnemar(table, exact=exact, correction=not exact)
    return float(result.pvalue)


def bootstrap_diff(a: list[bool], b: list[bool], *, n_boot: int = 2000, seed: int = 7) -> tuple[float, float, float]:
    if not a or not b:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(seed)
    n = len(a)
    diffs: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        a_acc = sum(a[i] for i in idx) / n
        b_acc = sum(b[i] for i in idx) / n
        diffs.append(a_acc - b_acc)

    diffs.sort()
    return float(np.mean(diffs)), float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))


def fmt_p(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value < 0.001:
        return "< 0.001"
    return f"{value:.4f}"


def save_plot(single_acc: float, majority_acc: float, jury_acc: float, out_path: Path) -> None:
    labels = ["Single Judge", "Panel Majority", "Deliberated Jury"]
    values = [single_acc, majority_acc, jury_acc]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(labels, values)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Accuracy")
    ax.set_title("Judge-mode accuracy comparison")
    for idx, value in enumerate(values):
        ax.text(idx, value + 0.02, f"{value:.3f}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare a single-judge run against a multi-judge jury run.")
    parser.add_argument("single_run_jsonl", type=Path, help="Path to the single-judge runs/<run_id>.jsonl file")
    parser.add_argument("panel_run_jsonl", type=Path, help="Path to the jury/panel runs/<run_id>.jsonl file")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory for generated comparison artifacts")
    args = parser.parse_args()

    single_rows = read_jsonl(args.single_run_jsonl)
    panel_rows = read_jsonl(args.panel_run_jsonl)
    aligned = align_rows(single_rows, panel_rows)

    single_correct = [bool_field(single_row, "correct_debate") for single_row, _ in aligned]
    jury_correct = [bool_field(panel_row, "correct_debate") for _, panel_row in aligned]
    majority_correct_values = [majority_correct(panel_row) for _, panel_row in aligned]
    majority_correct_bools = [bool(value) for value in majority_correct_values if value is not None]

    single_acc = accuracy_from_bools(single_correct)
    jury_acc = accuracy_from_bools(jury_correct)
    majority_acc = accuracy_from_bools(majority_correct_bools)
    mean_diff, ci_lo, ci_hi = bootstrap_diff(jury_correct, single_correct)
    p_value = mcnemar_p(jury_correct, single_correct)

    jury_beats_single = sum(1 for s, j in zip(single_correct, jury_correct, strict=True) if j and not s)
    single_beats_jury = sum(1 for s, j in zip(single_correct, jury_correct, strict=True) if s and not j)

    unanimous_rows = [panel_row for _, panel_row in aligned if not disagreement(panel_row)]
    split_rows = [panel_row for _, panel_row in aligned if disagreement(panel_row)]
    changed_rows = [panel_row for _, panel_row in aligned if deliberation_changed_majority(panel_row)]
    changed_to_correct = sum(
        1
        for row in changed_rows
        if bool(row.get("correct_debate")) and majority_correct(row) is False
    )
    changed_to_wrong = sum(
        1
        for row in changed_rows
        if bool(row.get("correct_debate")) is False and majority_correct(row) is True
    )

    difficulty_rows: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for _, panel_row in aligned:
        difficulty_rows[difficulty_bucket(panel_row)].append(panel_row)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    accuracy_table = "\n".join(
        [
            "| Judge Mode | Accuracy | Correct / Total |",
            "|---|---:|---:|",
            f"| Single Judge | {single_acc:.3f} | {sum(single_correct)} / {len(single_correct)} |",
            f"| Panel Majority | {majority_acc:.3f} | {sum(majority_correct_bools)} / {len(majority_correct_bools)} |",
            f"| Deliberated Jury | {jury_acc:.3f} | {sum(jury_correct)} / {len(jury_correct)} |",
        ]
    )
    (args.out_dir / "jury_vs_single_accuracy.md").write_text(accuracy_table + "\n", encoding="utf-8")

    stats_lines = [
        f"- Number of shared questions: **{len(aligned)}**",
        f"- McNemar p-value (Deliberated Jury vs Single Judge): **{fmt_p(p_value)}**",
        f"- Bootstrap accuracy difference, Deliberated Jury - Single Judge: **{mean_diff:.3f}** (95% CI: **[{ci_lo:.3f}, {ci_hi:.3f}]**)",
        f"- Jury beats single on **{jury_beats_single}** items.",
        f"- Single beats jury on **{single_beats_jury}** items.",
    ]
    (args.out_dir / "jury_vs_single_stats.md").write_text("\n".join(stats_lines) + "\n", encoding="utf-8")

    behavior_lines = [
        f"- Jury run panel size: **{panel_summary(aligned[0][1]).get('panel_size', len(aligned[0][1].get('judge_panel', [])))}**" if aligned else "- Jury run panel size: **N/A**",
        f"- Unanimous panel items: **{len(unanimous_rows)} / {len(aligned)}**",
        f"- Split panel items: **{len(split_rows)} / {len(aligned)}**",
        f"- Accuracy on unanimous items: **{accuracy_from_bools([bool_field(row, 'correct_debate') for row in unanimous_rows]):.3f}**",
        f"- Accuracy on split items: **{accuracy_from_bools([bool_field(row, 'correct_debate') for row in split_rows]):.3f}**",
        f"- Panel-majority accuracy: **{majority_acc:.3f}**",
        f"- Deliberated-jury accuracy: **{jury_acc:.3f}**",
        f"- Deliberation changed the majority answer on **{len(changed_rows)}** items.",
        f"- Deliberation changed the outcome from wrong to correct on **{changed_to_correct}** items.",
        f"- Deliberation changed the outcome from correct to wrong on **{changed_to_wrong}** items.",
    ]
    (args.out_dir / "jury_panel_behavior.md").write_text("\n".join(behavior_lines) + "\n", encoding="utf-8")

    difficulty_lines = [
        "Difficulty proxy: `easy` means both Direct QA and Self-Consistency were correct, `medium` means exactly one was correct, and `hard` means both were wrong.",
        "",
        "| Difficulty | N | Panel Disagreement Rate | Jury Accuracy | Single Accuracy |",
        "|---|---:|---:|---:|---:|",
    ]
    difficulty_summary: dict[str, dict[str, float | int]] = {}
    for bucket in ["easy", "medium", "hard"]:
        rows = difficulty_rows[bucket]
        disagreement_rate = accuracy_from_bools([disagreement(row) for row in rows])
        jury_bucket_acc = accuracy_from_bools([bool_field(row, "correct_debate") for row in rows])
        single_bucket_acc = accuracy_from_bools(
            [bool_field(single_row, "correct_debate") for single_row, panel_row in aligned if difficulty_bucket(panel_row) == bucket]
        )
        difficulty_lines.append(
            f"| {bucket} | {len(rows)} | {disagreement_rate:.3f} | {jury_bucket_acc:.3f} | {single_bucket_acc:.3f} |"
        )
        difficulty_summary[bucket] = {
            "n_items": len(rows),
            "disagreement_rate": disagreement_rate,
            "jury_accuracy": jury_bucket_acc,
            "single_accuracy": single_bucket_acc,
        }
    (args.out_dir / "jury_difficulty_correlation.md").write_text("\n".join(difficulty_lines) + "\n", encoding="utf-8")

    changed_payload = [
        {
            "item_id": row["item"]["id"],
            "question": row["item"]["question"],
            "ground_truth": row["item"]["ground_truth"],
            "panel_majority_answer": panel_summary(row).get("majority_answer", ""),
            "final_jury_answer": row.get("judge", {}).get("verdict_answer", ""),
            "majority_correct": majority_correct(row),
            "jury_correct": bool_field(row, "correct_debate"),
        }
        for row in changed_rows
    ]
    write_json(args.out_dir / "deliberation_changed_cases.json", changed_payload)

    summary_payload = {
        "n_items": len(aligned),
        "single_accuracy": single_acc,
        "panel_majority_accuracy": majority_acc,
        "deliberated_jury_accuracy": jury_acc,
        "jury_vs_single_mcnemar_p": p_value,
        "jury_vs_single_bootstrap_diff_mean": mean_diff,
        "jury_vs_single_bootstrap_diff_ci": [ci_lo, ci_hi],
        "jury_beats_single": jury_beats_single,
        "single_beats_jury": single_beats_jury,
        "panel_unanimous_items": len(unanimous_rows),
        "panel_split_items": len(split_rows),
        "deliberation_changed_majority_items": len(changed_rows),
        "deliberation_changed_to_correct": changed_to_correct,
        "deliberation_changed_to_wrong": changed_to_wrong,
        "difficulty_summary": difficulty_summary,
    }
    write_json(args.out_dir / "jury_compare_summary.json", summary_payload)
    save_plot(single_acc, majority_acc, jury_acc, args.out_dir / "judge_mode_accuracy.png")


if __name__ == "__main__":
    main()
