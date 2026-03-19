from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def normalize_answer(text: str) -> str:
    """
    Normalize answers for comparison across the system.

    Handles common patterns:
    - "No, ..." -> "no"
    - "Yes, ..." -> "yes"
    - "A." / "(B)" -> "b"
    """
    t = (text or "").strip().lower()

    # Strip common whitespace/punctuation safely.
    t = t.strip(" \t\n\r.:;!?\"'()[]{}")

    # Multiple-choice single-letter answers
    if t:
        first = t[0]
        if first in {"a", "b", "c", "d"} and (len(t) == 1 or not t[1].isalnum()):
            return first

    # Yes/No style answers
    if t.startswith("yes"):
        return "yes"
    if t.startswith("no"):
        return "no"

    return t


class Item(BaseModel):
    id: str
    question: str
    context: str = ""
    ground_truth: str


class RunRequest(BaseModel):
    item: Item
    rounds_max: Optional[int] = Field(default=None, ge=3)
    judge_panel_size: Optional[int] = Field(default=None, ge=1)


class BatchRequest(BaseModel):
    dataset_jsonl_path: str
    limit: Optional[int] = Field(default=None, ge=1)
    seed: int = 7
    judge_panel_size: Optional[int] = Field(default=None, ge=1)


class ModelAnswer(BaseModel):
    answer: str
    rationale: str = ""
    citations: List[str] = Field(default_factory=list)


class JudgeVerdict(BaseModel):
    verdict_answer: str
    confidence_1_to_5: int = Field(..., ge=1, le=5)

    analysis: str = ""
    debater_a_strongest: str = ""
    debater_a_weakest: str = ""
    debater_b_strongest: str = ""
    debater_b_weakest: str = ""
    reasoning: str = ""


class JudgePanelSummary(BaseModel):
    panel_size: int = 1
    panel_answers: List[str] = Field(default_factory=list)
    vote_counts: Dict[str, int] = Field(default_factory=dict)
    majority_answer: str = ""
    majority_count: int = 0
    minority_count: int = 0
    unique_answers: int = 0
    unanimous: bool = True
    disagreement: bool = False
    vote_margin: int = 0
    confidence_mean: float = 0.0
    confidence_min: int = 0
    confidence_max: int = 0
    deliberation_used: bool = False
    final_answer: str = ""
    final_agrees_with_majority: bool = True
    deliberation_changed_majority: bool = False


class DebateRound(BaseModel):
    round_index: int
    debater_a: ModelAnswer
    debater_b: ModelAnswer


class Baselines(BaseModel):
    direct: ModelAnswer
    self_consistency_samples: List[ModelAnswer]
    self_consistency_vote: str


class ItemResult(BaseModel):
    item: Item
    consensus: bool
    initial_a: ModelAnswer
    initial_b: ModelAnswer
    debate_rounds: List[DebateRound]
    judge: JudgeVerdict
    judge_panel: List[JudgeVerdict] = Field(default_factory=list)
    judge_panel_summary: JudgePanelSummary = Field(default_factory=JudgePanelSummary)
    baselines: Baselines
    correct_debate: bool
    correct_judge_panel_majority: Optional[bool] = None
    correct_direct: bool
    correct_sc: bool
    meta: Dict[str, Any] = Field(default_factory=dict)


class BatchSummary(BaseModel):
    run_id: str
    n_items: int
    accuracy_debate: float
    accuracy_direct: float
    accuracy_sc: float
    mcnemar_debate_vs_direct_p: Optional[float] = None
    mcnemar_debate_vs_sc_p: Optional[float] = None
    dataset_path: Optional[str] = None
    experiment_config: Dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    run_id: str
    result: ItemResult


class BatchResponse(BaseModel):
    run_id: str
    summary: BatchSummary
