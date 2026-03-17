from __future__ import annotations

from typing import Iterable

import numpy as np
from statsmodels.stats.contingency_tables import mcnemar

from .types import BatchSummary, ItemResult


def compute_summary(run_id: str, results: Iterable[ItemResult]) -> BatchSummary:
    results_list = list(results)
    n = len(results_list)

    debate = sum(result.correct_debate for result in results_list)
    direct = sum(result.correct_direct for result in results_list)
    sc = sum(result.correct_sc for result in results_list)

    return BatchSummary(
        run_id=run_id,
        n_items=n,
        accuracy_debate=debate / n if n else 0.0,
        accuracy_direct=direct / n if n else 0.0,
        accuracy_sc=sc / n if n else 0.0,
        mcnemar_debate_vs_direct_p=_mcnemar_p(results_list, a="debate", b="direct"),
        mcnemar_debate_vs_sc_p=_mcnemar_p(results_list, a="debate", b="sc"),
    )


def _pick(result: ItemResult, key: str) -> bool:
    return {"debate": result.correct_debate, "direct": result.correct_direct, "sc": result.correct_sc}[key]


def _mcnemar_p(results: list[ItemResult], *, a: str, b: str) -> float | None:
    n00 = n01 = n10 = n11 = 0
    for result in results:
        ax = _pick(result, a)
        bx = _pick(result, b)
        if ax and bx:
            n11 += 1
        elif ax and not bx:
            n10 += 1
        elif (not ax) and bx:
            n01 += 1
        else:
            n00 += 1

    discordant = n01 + n10
    if discordant == 0:
        return 1.0

    table = [[n00, n01], [n10, n11]]
    exact = discordant < 25
    result = mcnemar(table, exact=exact, correction=not exact)
    return float(result.pvalue)


def bootstrap_accuracy_diff(
    results: list[ItemResult],
    *,
    a: str,
    b: str,
    n_boot: int = 2000,
    seed: int = 7,
) -> tuple[float, float, float]:
    if not results:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(seed)
    n = len(results)
    diffs: list[float] = []

    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        a_acc = sum(_pick(results[i], a) for i in idx) / n
        b_acc = sum(_pick(results[i], b) for i in idx) / n
        diffs.append(a_acc - b_acc)

    diffs.sort()
    return float(np.mean(diffs)), float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))
