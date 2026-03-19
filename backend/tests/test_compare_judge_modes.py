from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_compare_judge_modes_generates_bonus_artifacts(tmp_path: Path) -> None:
    single_rows = [
        {
            "item": {"id": "q1", "question": "Q1?", "context": "", "ground_truth": "yes"},
            "judge": {"verdict_answer": "yes"},
            "correct_debate": True,
            "correct_direct": True,
            "correct_sc": True,
        },
        {
            "item": {"id": "q2", "question": "Q2?", "context": "", "ground_truth": "yes"},
            "judge": {"verdict_answer": "no"},
            "correct_debate": False,
            "correct_direct": False,
            "correct_sc": True,
        },
        {
            "item": {"id": "q3", "question": "Q3?", "context": "", "ground_truth": "yes"},
            "judge": {"verdict_answer": "no"},
            "correct_debate": False,
            "correct_direct": False,
            "correct_sc": False,
        },
    ]
    panel_rows = [
        {
            "item": {"id": "q1", "question": "Q1?", "context": "", "ground_truth": "yes"},
            "judge": {"verdict_answer": "yes"},
            "judge_panel": [{"verdict_answer": "yes"}, {"verdict_answer": "yes"}, {"verdict_answer": "yes"}],
            "judge_panel_summary": {
                "panel_size": 3,
                "majority_answer": "yes",
                "disagreement": False,
                "deliberation_changed_majority": False,
            },
            "correct_debate": True,
            "correct_judge_panel_majority": True,
            "correct_direct": True,
            "correct_sc": True,
        },
        {
            "item": {"id": "q2", "question": "Q2?", "context": "", "ground_truth": "yes"},
            "judge": {"verdict_answer": "yes"},
            "judge_panel": [{"verdict_answer": "yes"}, {"verdict_answer": "no"}, {"verdict_answer": "no"}],
            "judge_panel_summary": {
                "panel_size": 3,
                "majority_answer": "no",
                "disagreement": True,
                "deliberation_changed_majority": True,
            },
            "correct_debate": True,
            "correct_judge_panel_majority": False,
            "correct_direct": False,
            "correct_sc": True,
        },
        {
            "item": {"id": "q3", "question": "Q3?", "context": "", "ground_truth": "yes"},
            "judge": {"verdict_answer": "no"},
            "judge_panel": [{"verdict_answer": "yes"}, {"verdict_answer": "no"}, {"verdict_answer": "no"}],
            "judge_panel_summary": {
                "panel_size": 3,
                "majority_answer": "no",
                "disagreement": True,
                "deliberation_changed_majority": False,
            },
            "correct_debate": False,
            "correct_judge_panel_majority": False,
            "correct_direct": False,
            "correct_sc": False,
        },
    ]

    single_path = tmp_path / "single.jsonl"
    single_path.write_text("\n".join(json.dumps(row) for row in single_rows) + "\n", encoding="utf-8")
    panel_path = tmp_path / "panel.jsonl"
    panel_path.write_text("\n".join(json.dumps(row) for row in panel_rows) + "\n", encoding="utf-8")

    out_dir = tmp_path / "jury-compare"
    script = Path(__file__).resolve().parents[2] / "scripts" / "compare_judge_modes.py"
    subprocess.run(
        [sys.executable, str(script), str(single_path), str(panel_path), "--out-dir", str(out_dir)],
        check=True,
    )

    assert (out_dir / "jury_vs_single_accuracy.md").exists()
    assert (out_dir / "jury_vs_single_stats.md").exists()
    assert (out_dir / "jury_panel_behavior.md").exists()
    assert (out_dir / "jury_difficulty_correlation.md").exists()
    assert (out_dir / "deliberation_changed_cases.json").exists()
    assert (out_dir / "jury_compare_summary.json").exists()
    assert (out_dir / "judge_mode_accuracy.png").exists()
