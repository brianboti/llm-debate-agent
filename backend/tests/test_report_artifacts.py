from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_generate_report_artifacts(tmp_path: Path) -> None:
    judge = {
        "verdict_answer": "yes",
        "confidence_1_to_5": 4,
        "analysis": "A was better.",
        "debater_a_strongest": "Strong evidence",
        "debater_a_weakest": "Too brief",
        "debater_b_strongest": "Raised a counterpoint",
        "debater_b_weakest": "Ignored context",
        "reasoning": "Judge chose yes.",
    }
    answer_yes = {"answer": "yes", "rationale": "", "citations": []}
    answer_no = {"answer": "no", "rationale": "", "citations": []}
    rows = [
        {
            "item": {"id": "all-fail", "question": "Q1?", "context": "", "ground_truth": "yes"},
            "consensus": True,
            "initial_a": answer_no,
            "initial_b": answer_no,
            "debate_rounds": [],
            "judge": {**judge, "verdict_answer": "no"},
            "baselines": {
                "direct": answer_no,
                "self_consistency_samples": [answer_no, answer_no],
                "self_consistency_vote": "no",
            },
            "correct_debate": False,
            "correct_direct": False,
            "correct_sc": False,
            "meta": {"llm_call_budget": 3, "rounds_executed": 0, "stop_reason": "initial_consensus"},
        },
        {
            "item": {"id": "max-round-loss", "question": "Q2?", "context": "", "ground_truth": "yes"},
            "consensus": False,
            "initial_a": answer_yes,
            "initial_b": answer_no,
            "debate_rounds": [
                {
                    "round_index": 1,
                    "debater_a": answer_yes,
                    "debater_b": answer_no,
                }
            ],
            "judge": {**judge, "verdict_answer": "no"},
            "baselines": {
                "direct": answer_yes,
                "self_consistency_samples": [answer_yes, answer_yes],
                "self_consistency_vote": "yes",
            },
            "correct_debate": False,
            "correct_direct": True,
            "correct_sc": True,
            "meta": {"llm_call_budget": 5, "rounds_executed": 6, "stop_reason": "max_rounds_reached"},
        },
        {
            "item": {"id": "debate-sc-win", "question": "Q3?", "context": "", "ground_truth": "yes"},
            "consensus": True,
            "initial_a": answer_yes,
            "initial_b": answer_yes,
            "debate_rounds": [],
            "judge": judge,
            "baselines": {
                "direct": answer_no,
                "self_consistency_samples": [answer_yes, answer_yes],
                "self_consistency_vote": "yes",
            },
            "correct_debate": True,
            "correct_direct": False,
            "correct_sc": True,
            "meta": {"llm_call_budget": 3, "rounds_executed": 0, "stop_reason": "initial_consensus"},
        },
        {
            "item": {"id": "all-correct", "question": "Q4?", "context": "", "ground_truth": "yes"},
            "consensus": True,
            "initial_a": answer_yes,
            "initial_b": answer_yes,
            "debate_rounds": [],
            "judge": judge,
            "baselines": {
                "direct": answer_yes,
                "self_consistency_samples": [answer_yes, answer_yes],
                "self_consistency_vote": "yes",
            },
            "correct_debate": True,
            "correct_direct": True,
            "correct_sc": True,
            "meta": {"llm_call_budget": 3, "rounds_executed": 0, "stop_reason": "initial_consensus"},
        },
        {
            "item": {"id": "adaptive", "question": "Q5?", "context": "", "ground_truth": "yes"},
            "consensus": False,
            "initial_a": answer_yes,
            "initial_b": answer_no,
            "debate_rounds": [
                {
                    "round_index": 1,
                    "debater_a": answer_yes,
                    "debater_b": answer_yes,
                }
            ],
            "judge": judge,
            "baselines": {
                "direct": answer_yes,
                "self_consistency_samples": [answer_yes, answer_yes],
                "self_consistency_vote": "yes",
            },
            "correct_debate": True,
            "correct_direct": True,
            "correct_sc": True,
            "meta": {"llm_call_budget": 5, "rounds_executed": 3, "stop_reason": "adaptive_convergence_after_2_agreements"},
        },
    ]
    run_jsonl = tmp_path / "demo-run.jsonl"
    run_jsonl.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    out_dir = tmp_path / "artifacts"
    script = Path(__file__).resolve().parents[2] / "scripts" / "generate_report_artifacts.py"
    subprocess.run([sys.executable, str(script), str(run_jsonl), "--out-dir", str(out_dir)], check=True)

    assert (out_dir / "metrics_table.md").exists()
    assert (out_dir / "stats_summary.md").exists()
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "accuracy_comparison.png").exists()
    assert (out_dir / "failure_patterns.md").exists()
    assert (out_dir / "failure_patterns.json").exists()
    assert (out_dir / "case_studies" / "index.md").exists()
    assert (out_dir / "case_studies" / "manifest.json").exists()
