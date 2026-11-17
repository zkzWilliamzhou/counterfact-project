"""Optional, strictly validated configuration. JSON only, no YAML.

Unknown keys are rejected rather than ignored, so a typo can never silently
disable a safety control.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

from .errors import ConfigError, SafetyError
from .safety import read_bounded, validate_env_key

ALLOWED_KEYS = frozenset(
    {
        "capture_keys",
        "tool_names",
        "max_runs",
        "timeout_s",
        "repeats",
        "max_output_bytes",
        "max_total_s",
        "expect_fail_text",
        "workdir",
    }
)

DEFAULTS: Dict[str, Any] = {
    "capture_keys": [],
    "tool_names": [],
    "max_runs": 60,
    "timeout_s": 10.0,
    "repeats": 3,
    "max_output_bytes": 65536,
    "max_total_s": 300.0,
    "expect_fail_text": "",
    "workdir": None,
}


def _string_list(value: Any, label: str) -> list:
    if not isinstance(value, list) or len(value) > 64:
        raise ConfigError("%s must be a short list of strings" % label)
    for item in value:
        if not isinstance(item, str) or len(item) > 256:
            raise ConfigError("%s contains an invalid string" % label)
    return list(value)


def _int_in(value: Any, label: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ConfigError("%s must be an integer in [%d, %d]" % (label, low, high))
    return value


def _float_in(value: Any, label: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError("%s must be a number" % label)
    number = float(value)
    if not low <= number <= high:
        raise ConfigError("%s must be in [%s, %s]" % (label, low, high))
    return number


def load_config(path: str) -> Dict[str, Any]:
    try:
        obj = read_bounded(path)
    except SafetyError as exc:
        raise ConfigError("cannot read config: %s" % exc) from exc
    if not isinstance(obj, dict):
        raise ConfigError("config root must be an object")
    unknown = set(obj) - ALLOWED_KEYS
    if unknown:
        raise ConfigError("unknown config keys: %s" % ", ".join(sorted(unknown)))

    cfg = dict(DEFAULTS)
    if "capture_keys" in obj:
        keys = _string_list(obj["capture_keys"], "capture_keys")
        for key in keys:
            validate_env_key(key)
        cfg["capture_keys"] = keys
    if "tool_names" in obj:
        tools = _string_list(obj["tool_names"], "tool_names")
        for tool in tools:
            if not tool or any(ord(c) < 32 for c in tool):
                raise ConfigError("invalid tool name")
        cfg["tool_names"] = tools
    if "max_runs" in obj:
        cfg["max_runs"] = _int_in(obj["max_runs"], "max_runs", 1, 500)
    if "timeout_s" in obj:
        cfg["timeout_s"] = _float_in(obj["timeout_s"], "timeout_s", 0.1, 120.0)
    if "repeats" in obj:
        cfg["repeats"] = _int_in(obj["repeats"], "repeats", 1, 20)
    if "max_output_bytes" in obj:
        cfg["max_output_bytes"] = _int_in(
            obj["max_output_bytes"], "max_output_bytes", 1024, 4 * 1024 * 1024
        )
    if "max_total_s" in obj:
        cfg["max_total_s"] = _float_in(obj["max_total_s"], "max_total_s", 1.0, 3600.0)
    if "expect_fail_text" in obj:
        text = obj["expect_fail_text"]
        if not isinstance(text, str) or len(text) > 512 or any(ord(c) < 32 for c in text):
            raise ConfigError("invalid expect_fail_text")
        cfg["expect_fail_text"] = text
    if "workdir" in obj:
        value = obj["workdir"]
        if value is not None and (not isinstance(value, str) or len(value) > 512):
            raise ConfigError("invalid workdir")
        cfg["workdir"] = value
    return cfg


def merge(cli_values: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """CLI values win only when explicitly provided (None means 'not set')."""
    out = dict(cfg)
    for key, value in cli_values.items():
        if key in ALLOWED_KEYS and value is not None:
            out[key] = value
    return out
