#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.config import settings  # type: ignore
from src.debater_agent import TranscriptTurn  # type: ignore
from src.eval import compute_summary  # type: ignore
from src.judge_agent import JudgeAgent  # type: ignore
from src.logs import load_single_run, new_run_id, save_item_results, write_summary  # type: ignore
from src.openai_client import OpenAIClient  # type: ignore
from src.prompts import PromptStore  # type: ignore
from src.types import ItemResult, normalize_answer  # type: ignore


def build_transcript(result: ItemResult) -> list[TranscriptTurn]:
    transcript = [
        TranscriptTurn(speaker="Debater A (initial)", round_index=0, payload=result.initial_a.model_dump()),
        TranscriptTurn(speaker="Debater B (initial)", round_index=0, payload=result.initial_b.model_dump()),
    ]
    for round_result in result.debate_rounds:
        transcript.append(
            TranscriptTurn(
                speaker="Debater A",
                round_index=round_result.round_index,
                payload=round_result.debater_a.model_dump(),
            )
        )
        transcript.append(
            TranscriptTurn(
                speaker="Debater B",
                round_index=round_result.round_index,
                payload=round_result.debater_b.model_dump(),
            )
        )
    return transcript


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-evaluate a saved run with a multi-judge panel over fixed debate transcripts.")
    parser.add_argument("source_run_jsonl", type=Path, help="Path to an existing runs/<run_id>.jsonl file")
    parser.add_argument("--judge-panel-size", type=int, default=3, help="Number of judges to use for re-evaluation")
    args = parser.parse_args()

    source_path = args.source_run_jsonl.expanduser().resolve()
    if not source_path.exists():
        raise SystemExit(f"Run file not found: {source_path}")
    if args.judge_panel_size < 2:
        raise SystemExit("--judge-panel-size must be at least 2 for panel re-evaluation.")

    client = OpenAIClient()
    prompts = PromptStore(settings.prompts_path())
    judge_agent = JudgeAgent(client=client, prompts=prompts)
    source_run_id = source_path.stem

    source_rows = load_single_run(source_path)
    source_results = [ItemResult(**row) for row in source_rows]
    panel_results: list[ItemResult] = []
    for source_result in source_results:
        transcript = build_transcript(source_result)
        judge_execution = judge_agent.evaluate(
            item=source_result.item,
            transcript=transcript,
            panel_size_override=args.judge_panel_size,
        )
        meta = copy.deepcopy(source_result.meta)
        experiment_config = meta.get("experiment_config")
        if isinstance(experiment_config, dict):
            protocol = experiment_config.setdefault("protocol", {})
            if isinstance(protocol, dict):
                protocol["judge_panel_size"] = args.judge_panel_size
            experiment_config["evaluation_mode"] = "rejudge_saved_transcript"
            experiment_config["source_run_id"] = source_run_id
        meta["judge_panel_size"] = args.judge_panel_size
        meta["judge_panel_summary"] = judge_execution.panel_summary.model_dump()
        meta["rejudge_only"] = True
        meta["source_run_id"] = source_run_id
        meta["source_run_jsonl"] = str(source_path)
        meta["rejudge_llm_calls"] = judge_execution.llm_call_count

        ground_truth = normalize_answer(source_result.item.ground_truth)
        panel_results.append(
            source_result.model_copy(
                update={
                    "judge": judge_execution.final_verdict,
                    "judge_panel": judge_execution.panel,
                    "judge_panel_summary": judge_execution.panel_summary,
                    "correct_debate": normalize_answer(judge_execution.final_verdict.verdict_answer) == ground_truth,
                    "correct_judge_panel_majority": normalize_answer(judge_execution.panel_summary.majority_answer) == ground_truth
                    if judge_execution.panel_summary.majority_answer
                    else None,
                    "meta": meta,
                }
            )
        )

    run_id = new_run_id()
    run_path = settings.runs_path() / f"{run_id}.jsonl"
    summary_path = settings.runs_path() / f"{run_id}.summary.json"
    save_item_results(run_path, panel_results)
    write_summary(summary_path, compute_summary(run_id, panel_results))

    print(f"Source run: {source_run_id}")
    print(f"Saved rejudged panel run to: {run_path}")
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()
