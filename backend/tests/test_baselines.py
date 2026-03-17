from src.baselines import run_baselines
from src.types import Item


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def create_json(self, **kwargs):  # noqa: ANN003
        self.calls += 1
        answers = ["yes", "Yes.", "no", "YES", "no", "yes"]
        answer = answers[self.calls - 1]
        return {"answer": answer, "rationale": f"r{self.calls}", "citations": []}


class FakeTemplate:
    def render(self, **kwargs):  # noqa: ANN003
        return "prompt"


class FakePrompts:
    def direct_qa(self) -> FakeTemplate:
        return FakeTemplate()

    def self_consistency(self) -> FakeTemplate:
        return FakeTemplate()


def test_run_baselines_uses_requested_self_consistency_budget() -> None:
    client = FakeClient()
    out = run_baselines(
        client=client,
        prompts=FakePrompts(),
        item=Item(id="1", question="Q", ground_truth="yes"),
        self_consistency_samples=5,
    )
    assert client.calls == 6  # 1 direct + 5 self-consistency
    assert len(out.self_consistency_samples) == 5
    assert out.direct.answer == "yes"


def test_self_consistency_majority_vote_is_normalized() -> None:
    client = FakeClient()
    out = run_baselines(
        client=client,
        prompts=FakePrompts(),
        item=Item(id="1", question="Q", ground_truth="yes"),
        self_consistency_samples=5,
    )
    assert out.self_consistency_vote.lower().startswith("yes")
