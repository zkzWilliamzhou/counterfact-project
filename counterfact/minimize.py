"""Delta debugging (ddmin) over environment factors.

Pure control flow: the search only ever asks the runner for observations. It
never executes anything itself. That seam is what makes the algorithm testable
with a fake runner and what makes the architecture refactor safe.
"""

from __future__ import annotations

import dataclasses
from typing import List, Sequence, Tuple

from .errors import BudgetExceeded
from .ports import Observer
from .types import FAIL, UNRESOLVED, Factor

STATUS_OK = "OK"
STATUS_EMPTY_DIFF = "EMPTY_DIFF"
STATUS_NO_REPRODUCTION = "NO_REPRODUCTION"
STATUS_BASELINE_FAILS = "BASELINE_FAILS"
STATUS_BUDGET_EXCEEDED = "BUDGET_EXCEEDED"


@dataclasses.dataclass(frozen=True)
class SearchResult:
    minimal: Tuple[str, ...]
    status: str
    partial: bool
    warnings: List[str]
    unresolved: int


def split(sequence: Sequence[str], n: int) -> List[Tuple[str, ...]]:
    """Split into n near-equal, non-empty, ordered chunks."""
    length = len(sequence)
    n = max(1, min(n, length))
    base, extra = divmod(length, n)
    chunks: List[Tuple[str, ...]] = []
    offset = 0
    for index in range(n):
        size = base + (1 if index < extra else 0)
        chunk = tuple(sequence[offset:offset + size])
        offset += size
        if chunk:
            chunks.append(chunk)
    return chunks


def search(factors: Sequence[Factor], runner: Observer) -> SearchResult:
    """Find a 1-minimal subset of differences that flips PASS -> FAIL.

    Anchor assumptions are checked first: the passing state must actually PASS
    and the fully-failing state must actually FAIL under the supplied oracle.
    If either anchor does not hold, no causal claim is made.
    """
    names: Tuple[str, ...] = tuple(f.name for f in factors)
    warnings: List[str] = []
    if not names:
        return SearchResult(
            (), STATUS_EMPTY_DIFF, False,
            ["The two snapshots contain no replayable differences."], 0,
        )

    baseline = runner.run(())
    if baseline.outcome == FAIL:
        return SearchResult(
            (), STATUS_BASELINE_FAILS, False,
            ["The 'good' state already fails under this oracle; nothing to explain."], 0,
        )
    if baseline.outcome == UNRESOLVED:
        warnings.append(
            "The 'good' baseline run was UNRESOLVED (timeout, launcher error, or "
            "an unmatched failure signature). Search results are unreliable."
        )

    full = runner.run(names)
    if full.outcome == UNRESOLVED:
        warnings.append(
            "Applying ALL differences produced UNRESOLVED rather than the target "
            "failure. The failing state may depend on state that was not captured."
        )
    if full.outcome != FAIL:
        return SearchResult(
            (), STATUS_NO_REPRODUCTION, False,
            warnings + [
                "Applying all captured differences did not reproduce the failure. "
                "counterfact will not invent a cause."
            ], 0,
        )

    current = names
    granularity = 2
    partial = False
    unresolved = 0

    try:
        while len(current) >= 2:
            subsets = split(current, granularity)
            reduced = False

            # ddmin "test each subset": is this subset alone enough to fail?
            for subset in subsets:
                if len(subset) >= len(current):
                    continue
                observation = runner.run(subset)
                if observation.outcome == UNRESOLVED:
                    unresolved += 1
                if observation.outcome == FAIL:
                    current, granularity = subset, max(2, granularity - 1)
                    reduced = True
                    break
            if reduced:
                continue

            # ddmin "test each complement": can we remove this subset?
            for subset in subsets:
                drop = set(subset)
                complement = tuple(x for x in current if x not in drop)
                if not complement or len(complement) >= len(current):
                    continue
                observation = runner.run(complement)
                if observation.outcome == UNRESOLVED:
                    unresolved += 1
                if observation.outcome == FAIL:
                    current, granularity = complement, max(2, granularity - 1)
                    reduced = True
                    break
            if reduced:
                continue

            if granularity >= len(current):
                break
            granularity = min(len(current), granularity * 2)
    except BudgetExceeded as exc:
        partial = True
        warnings.append("Search stopped early: %s" % exc)

    if unresolved:
        warnings.append(
            "%d experiment(s) were UNRESOLVED; they were treated as 'not the "
            "target failure', which can bias the minimal set." % unresolved
        )

    return SearchResult(
        current,
        STATUS_BUDGET_EXCEEDED if partial else STATUS_OK,
        partial,
        warnings,
        unresolved,
    )
