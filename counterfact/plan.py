"""Build the typed execution model and the auditable, inert experiment plan.

``plan`` is the default state: it produces a complete specification of what
WOULD be executed without executing anything. Running requires an explicit
opt-in at the CLI layer.
"""

from __future__ import annotations

import os
import shutil
from typing import Any, Dict, List, Sequence

from .errors import ConfigError, SafetyError
from .safety import (
    SAFE_PATH,
    TOOL_PREFIX,
    UMASK_FACTOR,
    redact,
    validate_argv,
    validate_tool_path,
    validate_umask_value,
)
from .types import Budget, RunSpec, Snapshot

# Constructed from scratch. Nothing is inherited from the parent process.
SAFE_BASE_ENV: Dict[str, str] = {
    "PATH": SAFE_PATH,
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TZ": "UTC",
    "TERM": "dumb",
    "USER": "counterfact",
    "LOGNAME": "counterfact",
    "SHELL": "/bin/sh",
    "HOME": "",       # filled with the sandbox path by the runner
    "TMPDIR": "",     # filled with the sandbox path by the runner
}


def build_run_spec(argv: Sequence[str], good: Snapshot, cfg: Dict[str, Any]) -> RunSpec:
    items = validate_argv(argv)
    token = items[0]
    tool_paths: Dict[str, str] = {}

    if os.path.isabs(token):
        validate_tool_path(token)
    else:
        resolved = shutil.which(token, path=SAFE_PATH)
        if not resolved:
            raise SafetyError("executable %r not found on the trusted PATH" % token[:64])
        tool_paths[token] = validate_tool_path(resolved)
        override = good.factors.get(TOOL_PREFIX + token)
        if override:
            tool_paths[token] = validate_tool_path(override)

    umask = validate_umask_value(good.factors.get(UMASK_FACTOR, "022"))

    workdir = cfg.get("workdir")
    if workdir:
        real = os.path.realpath(workdir)
        if not os.path.isdir(real):
            raise ConfigError("workdir does not exist: %s" % str(workdir)[:120])
        workdir = real

    return RunSpec(
        argv=items,
        base_env=dict(SAFE_BASE_ENV),
        good_factors=dict(good.factors),
        tool_paths=tool_paths,
        umask=umask,
        workdir=workdir,
    )


def estimated_executions(factor_count: int, repeats: int) -> int:
    """Conservative upper bound shown to the operator BEFORE execution."""
    return 2 + 4 * max(1, factor_count) + 2 * max(1, repeats) + max(1, factor_count)


def build_plan(
    *,
    good: Snapshot,
    bad: Snapshot,
    factors: Sequence,
    spec: RunSpec,
    budget: Budget,
    oracle_warnings: List[str],
    state_warnings: List[str],
    oracle_desc: Dict[str, str],
) -> Dict[str, Any]:
    redacted_factors = []
    for factor in factors:
        redacted_factors.append(
            {
                "name": factor.name,
                "kind": factor.kind,
                "good": redact(factor.good, factor.name),
                "bad": redact(factor.bad, factor.name),
            }
        )
    return {
        "schema_version": 1,
        "inert": True,
        "execution_authorized": False,
        "command": [redact(a) for a in spec.argv],
        "factor_count": len(factors),
        "factors": redacted_factors,
        "estimated_max_executions": estimated_executions(len(factors), budget.repeats),
        "budget": budget.to_dict(),
        "oracle": oracle_desc,
        "safety": [
            "No shell is used; argv is passed as a list.",
            "Each run gets a fresh private workspace and constructed environment.",
            "Snapshot values never become arguments or shell strings.",
            "Dangerous loader/interpreter variables are refused.",
            "Every run has wall-clock, CPU, file-size, fd and output caps.",
            "Process groups are terminated on timeout.",
            "Secrets are redacted in all emitted reports.",
        ],
        "warnings": list(oracle_warnings) + list(state_warnings),
        "scope": "No conclusion is printed unless anchors, minimality and stability all hold.",
    }
