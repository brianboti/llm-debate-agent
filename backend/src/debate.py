from __future__ import annotations

from dataclasses import dataclass

from .config import settings
from .debater_agent import DebaterAgent, TranscriptTurn
from .judge_agent import JudgeAgent
from .openai_client import OpenAIClient
from .prompts import PromptStore
from .types import DebateRound, Item, JudgeVerdict, ModelAnswer, normalize_answer


@dataclass(frozen=True)
class DebateExecution:
    consensus: bool
    initial_a: ModelAnswer
    initial_b: ModelAnswer
    rounds: list[DebateRound]
    judge: JudgeVerdict
    judge_panel: list[JudgeVerdict]
    stop_reason: str
    judge_llm_calls: int

    @property
    def llm_call_count(self) -> int:
        return 2 + (2 * len(self.rounds)) + self.judge_llm_calls


def run_debate(
    *,
    client: OpenAIClient,
    prompts: PromptStore,
    item: Item,
    rounds_max_override: int | None = None,
) -> DebateExecution:
    requested_rounds = rounds_max_override or settings.debate_max_rounds
    rounds_max = max(settings.debate_min_rounds, requested_rounds)
    rounds_min = settings.debate_min_rounds
    converge_k = settings.debate_convergence_rounds

    debater_a = DebaterAgent(client=client, prompts=prompts, side="A")
    debater_b = DebaterAgent(client=client, prompts=prompts, side="B")
    judge_agent = JudgeAgent(client=client, prompts=prompts)

    transcript: list[TranscriptTurn] = []

    a0 = debater_a.initial(item=item)
    transcript.append(TranscriptTurn(speaker="Debater A (initial)", round_index=0, payload=a0.model_dump()))

    b0 = debater_b.initial(item=item)
    transcript.append(TranscriptTurn(speaker="Debater B (initial)", round_index=0, payload=b0.model_dump()))

    if normalize_answer(a0.answer) == normalize_answer(b0.answer):
        judge_execution = judge_agent.evaluate(item=item, transcript=transcript)
        return DebateExecution(
            consensus=True,
            initial_a=a0,
            initial_b=b0,
            rounds=[],
            judge=judge_execution.final_verdict,
            judge_panel=judge_execution.panel,
            stop_reason="initial_consensus",
            judge_llm_calls=judge_execution.llm_call_count,
        )

    rounds: list[DebateRound] = []
    consecutive_agreement = 0
    stop_reason = "max_rounds_reached"

    for round_index in range(1, rounds_max + 1):
        a = debater_a.debate_turn(item=item, round_index=round_index, transcript=transcript)
        transcript.append(TranscriptTurn(speaker="Debater A", round_index=round_index, payload=a.model_dump()))

        b = debater_b.debate_turn(item=item, round_index=round_index, transcript=transcript)
        transcript.append(TranscriptTurn(speaker="Debater B", round_index=round_index, payload=b.model_dump()))

        rounds.append(DebateRound(round_index=round_index, debater_a=a, debater_b=b))

        if normalize_answer(a.answer) == normalize_answer(b.answer):
            consecutive_agreement += 1
        else:
            consecutive_agreement = 0

        if round_index >= rounds_min and consecutive_agreement >= converge_k:
            stop_reason = f"adaptive_convergence_after_{converge_k}_agreements"
            break

    judge_execution = judge_agent.evaluate(item=item, transcript=transcript)
    return DebateExecution(
        consensus=False,
        initial_a=a0,
        initial_b=b0,
        rounds=rounds,
        judge=judge_execution.final_verdict,
        judge_panel=judge_execution.panel,
        stop_reason=stop_reason,
        judge_llm_calls=judge_execution.llm_call_count,
    )
