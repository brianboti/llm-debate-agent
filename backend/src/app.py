from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .baselines import run_baselines
from .config import settings
from .debate import run_debate
from .eval import compute_summary
from .logs import ensure_dir, load_item_dataset, load_single_run, new_run_id, save_item_results, write_summary
from .openai_client import OpenAIClient
from .prompts import PromptStore
from .types import BatchRequest, BatchResponse, Item, ItemResult, RunRequest, RunResponse, normalize_answer

app = FastAPI(title="LLM Debate + Judge API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_item_result(
    *,
    client: OpenAIClient,
    prompts: PromptStore,
    item: Item,
    dataset_path: Path | None = None,
    rounds_max_override: int | None = None,
) -> ItemResult:
    debate = run_debate(
        client=client,
        prompts=prompts,
        item=item,
        rounds_max_override=rounds_max_override,
    )
    baselines = run_baselines(
        client=client,
        prompts=prompts,
        item=item,
        self_consistency_samples=debate.llm_call_count,
    )

    ground_truth = normalize_answer(item.ground_truth)
    metadata = {
        "llm_call_budget": debate.llm_call_count,
        "rounds_executed": len(debate.rounds),
        "stop_reason": debate.stop_reason,
        "judge_panel_size": len(debate.judge_panel),
    }
    if dataset_path is not None:
        metadata["dataset_path"] = str(dataset_path)

    return ItemResult(
        item=item,
        consensus=debate.consensus,
        initial_a=debate.initial_a,
        initial_b=debate.initial_b,
        debate_rounds=debate.rounds,
        judge=debate.judge,
        judge_panel=debate.judge_panel,
        baselines=baselines,
        correct_debate=normalize_answer(debate.judge.verdict_answer) == ground_truth,
        correct_direct=normalize_answer(baselines.direct.answer) == ground_truth,
        correct_sc=normalize_answer(baselines.self_consistency_vote) == ground_truth,
        meta=metadata,
    )


def _persist_run(run_id: str, results: list[ItemResult]) -> None:
    runs_dir = settings.runs_path()
    ensure_dir(runs_dir)
    save_item_results(runs_dir / f"{run_id}.jsonl", results)
    write_summary(runs_dir / f"{run_id}.summary.json", compute_summary(run_id, results))


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/run", response_model=RunResponse)
def run_one(req: RunRequest) -> RunResponse:
    client = OpenAIClient()
    prompts = PromptStore(settings.prompts_path())

    result = _build_item_result(
        client=client,
        prompts=prompts,
        item=req.item,
        rounds_max_override=req.rounds_max,
    )
    run_id = new_run_id()
    _persist_run(run_id, [result])
    return RunResponse(run_id=run_id, result=result)


@app.post("/batch", response_model=BatchResponse)
def run_batch(req: BatchRequest) -> BatchResponse:
    dataset_path = Path(req.dataset_jsonl_path).expanduser().resolve()
    if not dataset_path.exists():
        raise HTTPException(status_code=400, detail=f"Dataset file not found: {dataset_path}")

    client = OpenAIClient()
    prompts = PromptStore(settings.prompts_path())

    items = load_item_dataset(dataset_path, limit=req.limit)
    if not items:
        raise HTTPException(status_code=400, detail="Dataset is empty or unreadable.")

    results = [
        _build_item_result(
            client=client,
            prompts=prompts,
            item=item,
            dataset_path=dataset_path,
        )
        for item in items
    ]

    run_id = new_run_id()
    _persist_run(run_id, results)
    return BatchResponse(run_id=run_id, summary=compute_summary(run_id, results))


@app.get("/logs/{run_id}")
def get_run_logs(run_id: str) -> dict[str, object]:
    path = settings.runs_path() / f"{run_id}.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run not found.")
    return {"run_id": run_id, "rows": load_single_run(path)}
