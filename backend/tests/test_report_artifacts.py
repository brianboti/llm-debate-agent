from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_generate_report_artifacts(tmp_path: Path) -> None:
    row = {
        "item": {"id": "1", "question": "Q?", "context": "", "ground_truth": "yes"},
        "consensus": False,
        "initial_a": {"answer": "yes", "rationale": "", "citations": []},
        "initial_b": {"answer": "no", "rationale": "", "citations": []},
        "debate_rounds": [
            {
                "round_index": 1,
                "debater_a": {"answer": "yes", "rationale": "", "citations": []},
                "debater_b": {"answer": "no", "rationale": "", "citations": []},
            }
        ],
        "judge": {
            "verdict_answer": "yes",
            "confidence_1_to_5": 4,
            "analysis": "A was better.",
            "debater_a_strongest": "Strong evidence",
            "debater_a_weakest": "Too brief",
            "debater_b_strongest": "Raised a counterpoint",
            "debater_b_weakest": "Ignored context",
            "reasoning": "Judge chose yes.",
        },
        "baselines": {
            "direct": {"answer": "yes", "rationale": "", "citations": []},
            "self_consistency_samples": [
                {"answer": "yes", "rationale": "", "citations": []},
                {"answer": "no", "rationale": "", "citations": []},
            ],
            "self_consistency_vote": "yes",
        },
        "correct_debate": True,
        "correct_direct": True,
        "correct_sc": True,
        "meta": {"llm_call_budget": 5, "rounds_executed": 1},
    }
    run_jsonl = tmp_path / "demo-run.jsonl"
    run_jsonl.write_text(json.dumps(row) + "\n", encoding="utf-8")

    out_dir = tmp_path / "artifacts"
    script = Path(__file__).resolve().parents[2] / "scripts" / "generate_report_artifacts.py"
    subprocess.run([sys.executable, str(script), str(run_jsonl), "--out-dir", str(out_dir)], check=True)

    assert (out_dir / "metrics_table.md").exists()
    assert (out_dir / "stats_summary.md").exists()
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "accuracy_comparison.png").exists()
