"""Immutable value types. No I/O, no subprocess, no globals that mutate.

Keeping these as plain data is what makes the search algorithm independently
testable and makes reports reproducible byte-for-byte.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .safety import redact

SCHEMA_VERSION = 1

PASS = "PASS"
FAIL = "FAIL"
UNRESOLVED = "UNRESOLVED"

STATUS_CONFIRMED = "CONFIRMED"
STATUS_PROBABLE = "PROBABLE"
STATUS_INCONCLUSIVE = "INCONCLUSIVE"
STATUS_FLAKY = "FLAKY"
STATUS_PARTIAL = "BUDGET_EXCEEDED"
STATUS_NO_REPRODUCTION = "NO_REPRODUCTION"

SCOPE_NOTICE = (
    "This is a 1-minimal tested causal set under the supplied oracle, runner and "
    "captured states. It is NOT proof of a unique root cause, NOT proof that the "
    "underlying code is correct, and NOT valid outside these bounded conditions."
)


@dataclasses.dataclass(frozen=True)
class Factor:
    """One difference between a passing state and a failing state."""

    name: str
    good: Optional[str]
    bad: Optional[str]
    kind: str = "env"

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "good": self.good, "bad": self.bad, "kind": self.kind}


@dataclasses.dataclass(frozen=True)
class Snapshot:
    """A captured, replayable environment state.

    ``factors`` contains only validated, replayable values. ``metadata`` is
    descriptive only and is never used as an experimental factor.
    """

    schema_version: int
    factors: Mapping[str, str]
    metadata: Mapping[str, str]

    def to_json_obj(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "factors": dict(self.factors),
            "metadata": dict(self.metadata),
        }


@dataclasses.dataclass(frozen=True)
class Budget:
    max_runs: int = 60
    timeout_s: float = 10.0
    max_output_bytes: int = 65536
    max_total_s: float = 300.0
    repeats: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class RunSpec:
    """A fully resolved, typed execution model (no shell, ever)."""

    argv: Tuple[str, ...]
    base_env: Mapping[str, str]
    good_factors: Mapping[str, str]
    tool_paths: Mapping[str, str]
    umask: int
    workdir: Optional[str] = None

    def to_dict(self, redact) -> Dict[str, Any]:
        return {
            "argv": [redact(a) for a in self.argv],
            "base_env_keys": sorted(self.base_env),
            "good_factor_count": len(self.good_factors),
            "tool_paths": {k: redact(v) for k, v in sorted(self.tool_paths.items())},
            "umask": oct(self.umask),
            "workdir": redact(self.workdir) if self.workdir else None,
        }


@dataclasses.dataclass(frozen=True)
class Experiment:
    """One controlled replay. An observation, never a proof."""

    index: int
    applied: Tuple[str, ...]
    outcome: str
    exit_code: Optional[int]
    timed_out: bool
    truncated: bool
    duration_ms: int
    stdout_sha256: str
    stderr_sha256: str
    stdout_excerpt: str
    stderr_excerpt: str
    error: str = ""
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "applied": list(self.applied),
            "outcome": self.outcome,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "truncated": self.truncated,
            "duration_ms": self.duration_ms,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "stdout_excerpt": self.stdout_excerpt,
            "stderr_excerpt": self.stderr_excerpt,
            "error": self.error,
            "cache_hit": self.cache_hit,
        }


@dataclasses.dataclass
class Finding:
    """The auditable result of a search."""

    status: str
    factors: Tuple[str, ...]
    replication: Tuple[int, int]
    experiments: List[Experiment]
    warnings: List[str]
    oracle: Dict[str, str]
    scope_notice: str = SCOPE_NOTICE
    partial: bool = False

    def to_dict(self, plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        experiments = []
        for exp in self.experiments:
            item = exp.to_dict()
            for key in ("stdout_excerpt", "stderr_excerpt", "error"):
                item[key] = redact(item[key])
            item["applied"] = [redact(name) for name in item["applied"]]
            experiments.append(item)
        return {
            "schema_version": SCHEMA_VERSION,
            "status": self.status,
            "factors": [redact(name) for name in self.factors],
            "replication": {"successes": self.replication[0], "trials": self.replication[1]},
            "experiment_count": len(self.experiments),
            "experiments": experiments,
            "warnings": [redact(warning) for warning in self.warnings],
            "oracle": {key: redact(value, key) for key, value in self.oracle.items()},
            "scope_notice": self.scope_notice,
            "partial": self.partial,
            "plan": plan or {},
        }
