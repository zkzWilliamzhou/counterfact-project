"""Capture, persist, validate and diff replayable environment states.

Only explicitly allowlisted keys are captured. Secrets are never captured by
default: capture is an allowlist, not a denylist.
"""

from __future__ import annotations

import datetime
import json
import os
import platform
import shutil
import sys
import tempfile
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from .errors import ConfigError, SafetyError
from .safety import (
    DENIED_ENV,
    SAFE_PATH,
    TOOL_PREFIX,
    UMASK_FACTOR,
    contained,
    factor_kind,
    read_bounded,
    validate_env_key,
    validate_env_value,
    validate_factor_name,
    validate_path_value,
    validate_tool_path,
    validate_umask_value,
)
from .types import SCHEMA_VERSION, Factor, Snapshot

# Keys whose values change program behaviour without granting code execution.
CAPTURE_ENV_KEYS: Tuple[str, ...] = (
    "TZ", "LANG", "LC_ALL", "LC_CTYPE", "LC_NUMERIC", "LC_TIME", "LC_COLLATE",
    "PYTHONHASHSEED", "PYTHONIOENCODING", "PYTHONUTF8", "PYTHONCOERCECLOCALE",
    "CI", "GITHUB_ACTIONS", "TERM", "NODE_ENV", "RUST_BACKTRACE", "GODEBUG",
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
)

DEFAULT_TOOL_NAMES: Tuple[str, ...] = ("python3", "python", "node", "go", "git")

# Metadata is descriptive only. Never replayable, never a factor.
_META_KEYS = ("captured_at", "platform", "python", "counterfact_version")


def _read_umask() -> int:
    """Read umask without leaving it changed (single-threaded CLI only)."""
    current = os.umask(0o022)
    os.umask(current)
    return current


def capture(extra_keys: Iterable[str] = (), tool_names: Iterable[str] = ()) -> Snapshot:
    """Build a snapshot from the current process environment."""
    from . import __version__

    keys = list(CAPTURE_ENV_KEYS) + ["PATH"] + [str(k) for k in extra_keys]
    factors: Dict[str, str] = {}
    seen = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        if key == "PATH":
            value = os.environ.get("PATH", SAFE_PATH)
            value = validate_path_value(value)
            factors[key] = value
            continue
        # Extra keys are operator-supplied and must still pass the same checks.
        validate_env_key(key)
        if key in os.environ:
            factors[key] = validate_env_value(key, os.environ[key])

    factors[UMASK_FACTOR] = format(_read_umask(), "o")

    for tool in tool_names:
        resolved = shutil.which(tool, path=SAFE_PATH)
        if resolved:
            factors[TOOL_PREFIX + tool] = validate_tool_path(resolved)

    metadata = {
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "counterfact_version": __version__,
    }
    return Snapshot(SCHEMA_VERSION, factors, metadata)


def _validate_factor(name: str, value: str) -> str:
    validate_factor_name(name)
    kind = factor_kind(name)
    if kind == "umask":
        validate_umask_value(value)
        return value
    if kind == "tool":
        return validate_tool_path(value)
    if name == "PATH":
        return validate_path_value(value)
    return validate_env_value(name, value)


def snapshot_from_obj(obj) -> Snapshot:
    if not isinstance(obj, dict):
        raise ConfigError("snapshot root must be an object")
    allowed = {"schema_version", "factors", "metadata"}
    unknown = set(obj) - allowed
    if unknown:
        raise ConfigError("unknown snapshot keys: %s" % ", ".join(sorted(unknown)))
    version = obj.get("schema_version")
    # bool is a subclass of int; True would otherwise be accepted as version 1.
    if isinstance(version, bool) or not isinstance(version, int) or version != SCHEMA_VERSION:
        raise ConfigError("unsupported snapshot schema_version")
    raw_factors = obj.get("factors")
    raw_meta = obj.get("metadata", {})
    if not isinstance(raw_factors, dict) or not isinstance(raw_meta, dict):
        raise ConfigError("factors and metadata must be objects")
    if len(raw_factors) > 256:
        raise ConfigError("too many factors")
    factors: Dict[str, str] = {}
    for name, value in raw_factors.items():
        if not isinstance(value, str):
            raise ConfigError("factor %r must be a string" % str(name)[:64])
        factors[name] = _validate_factor(name, value)
    metadata: Dict[str, str] = {}
    for name, value in raw_meta.items():
        if name not in _META_KEYS:
            raise ConfigError("unknown metadata key %r" % str(name)[:64])
        if not isinstance(value, str) or len(value) > 512:
            raise ConfigError("invalid metadata value")
        metadata[name] = value
    return Snapshot(version, factors, metadata)


def load_snapshot(path: str) -> Snapshot:
    try:
        obj = read_bounded(path)
    except SafetyError as exc:
        raise ConfigError("cannot read snapshot %s: %s" % (str(path)[:120], exc)) from exc
    return snapshot_from_obj(obj)


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Atomic, private write. Never follows a symlink at the destination."""
    parent = os.path.dirname(os.path.abspath(path)) or "."
    if not os.path.isdir(parent):
        raise ConfigError("snapshot parent directory does not exist")
    if os.path.islink(path):
        raise ConfigError("refusing to write through a symlink")
    body = json.dumps(snapshot.to_json_obj(), indent=2, sort_keys=True).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".counterfact-", dir=parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
        os.replace(tmp, path)
        tmp = ""
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def diff_states(good: Snapshot, bad: Snapshot) -> List[Factor]:
    """Return replayable differences only. Metadata is explicitly excluded."""
    names = sorted(set(good.factors) | set(bad.factors))
    out: List[Factor] = []
    for name in names:
        a = good.factors.get(name)
        b = bad.factors.get(name)
        if a == b:
            continue
        out.append(Factor(name=name, good=a, bad=b, kind=factor_kind(name)))
    return out


def unreplayable_warnings(good: Snapshot, bad: Snapshot) -> List[str]:
    """Warn when a difference cannot be varied by this runner."""
    warnings: List[str] = []
    for key in ("platform", "python"):
        a = good.metadata.get(key)
        b = bad.metadata.get(key)
        if a and b and a != b:
            warnings.append(
                "%s differs between snapshots (%s vs %s) and cannot be replayed "
                "by this runner; results are scope-limited." % (key, a[:60], b[:60])
            )
    return warnings


def assert_no_denied(factors: Mapping[str, str]) -> None:
    for name in factors:
        if name.upper() in DENIED_ENV and name not in ("PATH",):
            raise SafetyError("denied factor %s" % name)


def resolve_contained(base: str, rel: str) -> str:
    return contained(base, os.path.join(base, rel))
