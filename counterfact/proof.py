"""Independent verification of a candidate causal set.

ddmin gives a 1-minimal set under the observations it happened to make. This
module re-runs the anchors independently (cache disabled), checks necessity of
each member, and refuses to confirm anything when the command is flaky.
"""

from __future__ import annotations

import dataclasses
from typing import List, Tuple

from .errors import BudgetExceeded
from .ports import Observer
from .types import (
    FAIL,
    PASS,
    STATUS_CONFIRMED,
    STATUS_FLAKY,
    STATUS_INCONCLUSIVE,
    STATUS_PROBABLE,
)


@dataclasses.dataclass(frozen=True)
class ProofResult:
    status: str
    replication: Tuple[int, int]
    warnings: List[str]
    partial: bool


def verify(runner: Observer, minimal: Tuple[str, ...], repeats: int) -> ProofResult:
    warnings: List[str] = []
    successes = 0
    trials = 0
    flaky = False
    partial = False

    try:
        # 1. Sufficiency + stability of the candidate set.
        for _ in range(max(1, repeats)):
            observation = runner.run(tuple(minimal), use_cache=False)
            trials += 1
            if observation.outcome == FAIL:
                successes += 1
            elif observation.outcome == PASS:
                flaky = True

        # 2. Stability of the passing anchor.
        for _ in range(max(1, repeats)):
            observation = runner.run((), use_cache=False)
            trials += 1
            if observation.outcome == PASS:
                successes += 1
            elif observation.outcome == FAIL:
                flaky = True

        # 3. Necessity: removing any single member should restore PASS.
        necessary = True
        for name in minimal:
            rest = tuple(x for x in minimal if x != name)
            observation = runner.run(rest, use_cache=False)
            trials += 1
            if observation.outcome == FAIL:
                necessary = False
                warnings.append(
                    "Removing %s still reproduces the failure: the reported set "
                    "is not 1-minimal under independent re-runs." % name
                )
            elif observation.outcome == PASS:
                successes += 1
    except BudgetExceeded as exc:
        partial = True
        warnings.append("Verification stopped early: %s" % exc)

    strong = bool(trials) and successes >= 0.8 * trials

    if flaky:
        status = STATUS_FLAKY
        warnings.append(
            "The command changed outcome with no factor changed. This is "
            "experimental noise, not a causal result. Do not act on this finding."
        )
    elif partial:
        status = STATUS_INCONCLUSIVE
    elif not necessary:
        # Anchors held, but the set is not 1-minimal under independent re-runs.
        status = STATUS_PROBABLE if strong else STATUS_INCONCLUSIVE
    elif successes == trials:
        status = STATUS_CONFIRMED
    elif strong:
        status = STATUS_PROBABLE
        warnings.append(
            "One or more anchor re-runs were UNRESOLVED (timeout or unmatched "
            "failure signature). The result is probable, not confirmed."
        )
    else:
        status = STATUS_INCONCLUSIVE

    if repeats < 3 and status == STATUS_CONFIRMED:
        warnings.append(
            "Verification used fewer than 3 repeats; treat the replication "
            "rate as weak evidence."
        )

    return ProofResult(status, (successes, trials), warnings, partial)
