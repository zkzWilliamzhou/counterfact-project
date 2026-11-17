"""Deterministic helpers. No network, no sleeps, no real shells."""

from __future__ import annotations

import os
import sys
import tempfile
from typing import Callable, Dict, Optional

from counterfact.config import DEFAULTS
from counterfact.errors import BudgetExceeded
from counterfact.oracle import Oracle
from counterfact.plan import build_run_spec
from counterfact.state import snapshot_from_obj
from counterfact.types import Budget, Experiment, Factor, RunSpec, Snapshot


class FakeRunner:
    """An Observer double for pure algorithm tests."""

    def __init__(self, predicate: Callable[[tuple], str], max_calls: Optional[int] = None):
        self.predicate = predicate
        self.max_calls = max_calls
        self.log = []
        self.executions = 0

    def run(self, applied, use_cache: bool = True) -> Experiment:
        if self.max_calls is not None and self.executions >= self.max_calls:
            raise BudgetExceeded("fake budget exhausted")
        self.executions += 1
        outcome = self.predicate(tuple(applied))
        exp = Experiment(
            index=len(self.log) + 1,
            applied=tuple(applied),
            outcome=outcome,
            exit_code=1 if outcome == "FAIL" else 0,
            timed_out=False,
            truncated=False,
            duration_ms=1,
            stdout_sha256="",
            stderr_sha256="",
            stdout_excerpt="",
            stderr_excerpt="",
        )
        self.log.append(exp)
        return exp


def make_snapshot(factors: Dict[str, str], metadata: Optional[Dict[str, str]] = None) -> Snapshot:
    return snapshot_from_obj(
        {"schema_version": 1, "factors": dict(factors), "metadata": dict(metadata or {})}
    )


def write_script(directory: str, name: str, body: str) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


def make_spec(script_name: str, workdir: str, good: Optional[Snapshot] = None) -> RunSpec:
    cfg = dict(DEFAULTS)
    cfg["workdir"] = workdir
    return build_run_spec([sys.executable, script_name], good or make_snapshot({}), cfg)


def make_runner(spec: RunSpec, factors, budget: Optional[Budget] = None, oracle=None):
    from counterfact.runner import Runner

    return Runner(
        spec,
        {f.name: f for f in factors},
        budget or Budget(),
        oracle or Oracle(),
    )
