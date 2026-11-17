"""Thin orchestrator: compose -> workspace -> process -> oracle -> log.

All filesystem work lives in ``workspace``, all process work in ``process``,
and all pure state transformation in ``composition``. This module only wires
them together and keeps the auditable experiment log.
"""

from __future__ import annotations

import dataclasses
import time
from typing import Dict, List, Mapping, Optional, Tuple

from .composition import compose
from .errors import BudgetExceeded, SafetyError
from .oracle import Oracle
from .process import execute
from .safety import redact, sanitize_output
from .types import Budget, Experiment, Factor, RunSpec
from .workspace import Workspace


class Runner:
    """Executes experiments and keeps an ordered, auditable log."""

    def __init__(
        self,
        spec: RunSpec,
        factors: Mapping[str, Factor],
        budget: Budget,
        oracle: Oracle,
    ) -> None:
        self.spec = spec
        self.factors = dict(factors)
        self.budget = budget
        self.oracle = oracle
        self.log: List[Experiment] = []
        self._cache: Dict[Tuple[str, ...], Experiment] = {}
        self._executions = 0
        self._started = time.monotonic()

    @property
    def executions(self) -> int:
        return self._executions

    def run(self, applied: Tuple[str, ...], use_cache: bool = True) -> Experiment:
        key = tuple(sorted(applied))
        unknown = [n for n in key if n not in self.factors]
        if unknown:
            raise SafetyError("unknown factor applied: %s" % unknown[0][:64])
        if use_cache and key in self._cache:
            cached = self._cache[key]
            exp = dataclasses.replace(
                cached, index=len(self.log) + 1, cache_hit=True
            )
            self.log.append(exp)
            return exp

        self._guard()
        exp = self._execute(key)
        exp = dataclasses.replace(exp, index=len(self.log) + 1)
        self.log.append(exp)
        self._cache[key] = exp
        return exp

    def _guard(self) -> None:
        if self._executions >= self.budget.max_runs:
            raise BudgetExceeded("max_runs=%d exhausted" % self.budget.max_runs)
        if time.monotonic() - self._started > self.budget.max_total_s:
            raise BudgetExceeded("max_total_s exceeded")

    def _execute(self, applied: Tuple[str, ...]) -> Experiment:
        started = time.monotonic()
        self._executions += 1
        workspace: Optional[Workspace] = None
        timed_out = False
        error = ""
        exit_code = None
        out_bytes = b""
        err_bytes = b""

        try:
            workspace = Workspace(self.spec.workdir)
            composition = compose(
                self.spec,
                self.factors,
                applied,
                home=workspace.path,
                tmpdir=workspace.path,
            )
            workspace.copy_inputs()
            result = execute(
                composition.argv,
                composition.env,
                workspace.path,
                composition.umask,
                self.budget,
                workspace.stdout,
                workspace.stderr,
            )
            exit_code = result.exit_code
            timed_out = result.timed_out
            error = result.error
            out_bytes = workspace.read_capped(workspace.stdout, self.budget.max_output_bytes)
            err_bytes = workspace.read_capped(workspace.stderr, self.budget.max_output_bytes)
        except (SafetyError, OSError, ValueError) as exc:
            error = "%s: %s" % (type(exc).__name__, str(exc)[:200])
        finally:
            if workspace is not None:
                workspace.close()

        duration_ms = int((time.monotonic() - started) * 1000)
        out_text, out_sha, out_trunc = sanitize_output(
            out_bytes, self.budget.max_output_bytes
        )
        err_text, err_sha, err_trunc = sanitize_output(
            err_bytes, self.budget.max_output_bytes
        )
        outcome = self.oracle.classify(
            exit_code=exit_code,
            timed_out=timed_out,
            error=error,
            stdout_excerpt=out_text,
            stderr_excerpt=err_text,
        )
        return Experiment(
            index=0,
            applied=tuple(applied),
            outcome=outcome,
            exit_code=exit_code,
            timed_out=timed_out,
            truncated=out_trunc or err_trunc,
            duration_ms=duration_ms,
            stdout_sha256=out_sha,
            stderr_sha256=err_sha,
            stdout_excerpt=redact(out_text),
            stderr_excerpt=redact(err_text),
            error=redact(error),
        )
