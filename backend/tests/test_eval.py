from src.eval import bootstrap_accuracy_diff, compute_summary
from src.types import Baselines, Item, ItemResult, JudgeVerdict, ModelAnswer


def make_result(*, debate: bool, direct: bool, sc: bool) -> ItemResult:
    item = Item(id="1", question="Q", context="", ground_truth="yes")
    answer = ModelAnswer(answer="yes", rationale="because", citations=[])
    judge = JudgeVerdict(
        verdict_answer="yes",
        confidence_1_to_5=4,
        analysis="A was better",
        debater_a_strongest="fact",
        debater_a_weakest="gap",
        debater_b_strongest="counter",
        debater_b_weakest="mistake",
        reasoning="final",
    )
    baselines = Baselines(direct=answer, self_consistency_samples=[answer], self_consistency_vote="yes")
    return ItemResult(
        item=item,
        consensus=False,
        initial_a=answer,
        initial_b=answer,
        debate_rounds=[],
        judge=judge,
        judge_panel=[judge],
        baselines=baselines,
        correct_debate=debate,
        correct_direct=direct,
        correct_sc=sc,
        meta={},
    )


def test_compute_summary_returns_expected_accuracies() -> None:
    results = [
        make_result(debate=True, direct=False, sc=False),
        make_result(debate=False, direct=False, sc=True),
        make_result(debate=True, direct=True, sc=True),
    ]
    summary = compute_summary("run_x", results)
    assert summary.n_items == 3
    assert summary.accuracy_debate == 2 / 3
    assert summary.accuracy_direct == 1 / 3
    assert summary.accuracy_sc == 2 / 3


def test_bootstrap_accuracy_diff_handles_nonempty_input() -> None:
    results = [
        make_result(debate=True, direct=False, sc=False),
        make_result(debate=True, direct=False, sc=True),
        make_result(debate=False, direct=False, sc=True),
    ]
    mean, lo, hi = bootstrap_accuracy_diff(results, a="debate", b="direct", n_boot=100, seed=1)
    assert lo <= mean <= hi
    assert mean > 0
