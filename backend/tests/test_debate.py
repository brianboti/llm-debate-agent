from src.debate import DebateExecution, run_debate
from src.types import Item


class FakeClient:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.calls: list[dict] = []

    def create_json(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)
        return self.payloads.pop(0)


class FakeTemplate:
    def render(self, **kwargs):  # noqa: ANN003
        return "prompt"


class FakePrompts:
    def debater_a(self) -> FakeTemplate:
        return FakeTemplate()

    def debater_b(self) -> FakeTemplate:
        return FakeTemplate()

    def judge(self) -> FakeTemplate:
        return FakeTemplate()

    def jury_deliberation(self) -> FakeTemplate:
        return FakeTemplate()


def make_answer(answer: str, rationale: str = "r") -> dict:
    return {"answer": answer, "rationale": rationale, "citations": []}


def make_judge(answer: str) -> dict:
    return {
        "verdict_answer": answer,
        "confidence_1_to_5": 4,
        "analysis": "analysis",
        "debater_a_strongest": "a+",
        "debater_a_weakest": "a-",
        "debater_b_strongest": "b+",
        "debater_b_weakest": "b-",
        "reasoning": "reason",
    }


def test_run_debate_skips_rounds_on_initial_consensus() -> None:
    client = FakeClient([make_answer("yes"), make_answer("yes"), make_judge("yes")])
    result = run_debate(client=client, prompts=FakePrompts(), item=Item(id="1", question="Q", ground_truth="yes"))
    assert isinstance(result, DebateExecution)
    assert result.consensus is True
    assert result.rounds == []
    assert result.stop_reason == "initial_consensus"
    assert result.llm_call_count == 3


def test_run_debate_enforces_minimum_three_rounds_before_early_stop() -> None:
    payloads = [
        make_answer("yes", "a0"),
        make_answer("no", "b0"),
        make_answer("yes", "a1"),
        make_answer("yes", "b1"),
        make_answer("yes", "a2"),
        make_answer("yes", "b2"),
        make_answer("yes", "a3"),
        make_answer("yes", "b3"),
        make_judge("yes"),
    ]
    client = FakeClient(payloads)
    result = run_debate(client=client, prompts=FakePrompts(), item=Item(id="1", question="Q", ground_truth="yes"), rounds_max_override=3)
    assert result.consensus is False
    assert len(result.rounds) == 3
    assert result.llm_call_count == 9
    assert result.stop_reason.startswith("adaptive_convergence")
