"""Pure environment + argv composition. No filesystem, no subprocess, no clock.

This module is the deep seam the rest of the program hangs from: given a
RunSpec, a factor table and a set of interventions, it produces the complete,
typed execution model. It is independently testable because it has no adapter
dependencies.
"""

from __future__ import annotations

import dataclasses
import os
from typing import Dict, Mapping, Tuple

from .safety import (
    TOOL_PREFIX,
    factor_kind,
    validate_env_value,
    validate_path_value,
    validate_tool_path,
    validate_umask_value,
)
from .errors import SafetyError
from .types import Factor, RunSpec


@dataclasses.dataclass(frozen=True)
class Composition:
    """Everything a child process needs, fully resolved before it starts."""

    env: Dict[str, str]
    argv: Tuple[str, ...]
    umask: int


def compose(
    spec: RunSpec,
    factors: Mapping[str, Factor],
    applied: Tuple[str, ...],
    *,
    home: str = "",
    tmpdir: str = "",
) -> Composition:
    """Apply an intervention set to the 'good' state.

    Snapshot values only ever become environment variables or validated tool
    paths. They are never concatenated into an argument string.
    """
    env: Dict[str, str] = dict(spec.base_env)
    for name, value in spec.good_factors.items():
        if factor_kind(name) == "env":
            env[name] = value
    tool_paths: Dict[str, str] = dict(spec.tool_paths)
    umask = spec.umask

    for name in applied:
        factor = factors[name]
        kind = factor.kind
        if kind == "env":
            if factor.bad is None:
                env.pop(name, None)
            elif name == "PATH":
                env[name] = validate_path_value(factor.bad)
            else:
                env[name] = validate_env_value(name, factor.bad)
        elif kind == "tool":
            tool = name[len(TOOL_PREFIX):]
            if factor.bad is None:
                tool_paths.pop(tool, None)
            else:
                tool_paths[tool] = validate_tool_path(factor.bad)
        elif kind == "umask":
            umask = (
                validate_umask_value(factor.bad)
                if factor.bad is not None
                else spec.umask
            )

    env["HOME"] = home
    env["TMPDIR"] = tmpdir

    argv = list(spec.argv)
    token = argv[0]
    if os.path.isabs(token):
        validate_tool_path(token)
    elif token in tool_paths:
        argv[0] = validate_tool_path(tool_paths[token])
    else:
        raise SafetyError("no validated executable for %r" % token[:64])

    return Composition(env=env, argv=tuple(argv), umask=umask)
