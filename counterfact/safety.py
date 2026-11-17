"""Safety primitives. Everything imported from disk passes through here.

Design rule: an untrusted value never becomes an argv element, a shell string,
a regex, a pickle, or a path outside the sandbox. Snapshot values only ever
become environment variables (validated below) or tool-path overrides.

There is deliberately no YAML, no regex from user input, no eval/exec, and no
pickle anywhere in this package.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from typing import Any, Dict, Iterable, Optional, Tuple

from .errors import SafetyError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_BYTES = 256 * 1024
MAX_DEPTH = 12
MAX_NODES = 5000
MAX_STRING = 4096
MAX_ARRAY = 512
MAX_OBJECT_KEYS = 256

MAX_ENV_VALUE = 4096
MAX_ARG = 4096
MAX_PATH = 512

# Linear-time only. No nested quantifiers, no backreferences, no lookarounds.
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SECRET_KEY = re.compile(
    r"(KEY|TOKEN|SECRET|PASSW|CREDENTIAL|AUTH|COOKIE|PRIVATE|SESSION|PEM|APIKEY|SIG)",
    re.IGNORECASE,
)
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

REDACTED = "***REDACTED***"

# Variables that can change loader / interpreter / shell / allocator behaviour.
# They are refused from snapshots unless the operator explicitly names them.
DENIED_ENV = frozenset(
    x.upper()
    for x in [
        "LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "LD_DEBUG", "LD_ORIGIN_PATH",
        "LD_PROFILE", "LD_BIND_NOW",
        "PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME", "PYTHONINSPECT",
        "PYTHONWARNINGS", "PYTHONBREAKPOINT", "PYTHONEXECUTABLE",
        "BASH_ENV", "ENV", "PS4", "SHELLOPTS", "BASHOPTS", "CDPATH", "GLOBIGNORE",
        "IFS", "PERL5LIB", "PERL5OPT", "RUBYOPT", "NODE_OPTIONS",
        "GCONV_PATH", "LOCPATH", "NLSPATH", "HOSTALIASES", "RESOLV_HOST_CONF",
        "TZDIR", "MALLOC_PERTURB_", "MALLOC_CHECK_", "MALLOC_TRACE",
        "TMPDIR", "HOME", "USER", "LOGNAME", "SHELL", "PATH",
    ]
)

# Only these are ever inherited into a constructed baseline. Everything else is
# set explicitly by the runner.
SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

TOOL_PREFIX = "TOOL:"
UMASK_FACTOR = "@UMASK"

SHELL_METACHARS = frozenset("$`;&|()<>*?[]{}!\\\"'\n\r\t")


# ---------------------------------------------------------------------------
# Bounded JSON
# ---------------------------------------------------------------------------

def _walk(obj: Any, depth: int, counter: list) -> None:
    counter[0] += 1
    if counter[0] > MAX_NODES:
        raise SafetyError("document has too many nodes")
    if depth > MAX_DEPTH:
        raise SafetyError("document is nested too deeply")
    if isinstance(obj, str):
        if len(obj) > MAX_STRING:
            raise SafetyError("string exceeds maximum length")
        if "\x00" in obj:
            raise SafetyError("NUL byte in string")
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if abs(obj) > 10 ** 12:
            raise SafetyError("number out of range")
    elif isinstance(obj, dict):
        if len(obj) > MAX_OBJECT_KEYS:
            raise SafetyError("object has too many keys")
        for k, v in obj.items():
            if not isinstance(k, str):
                raise SafetyError("non-string object key")
            _walk(k, depth + 1, counter)
            _walk(v, depth + 1, counter)
    elif isinstance(obj, list):
        if len(obj) > MAX_ARRAY:
            raise SafetyError("array is too long")
        for v in obj:
            _walk(v, depth + 1, counter)
    elif obj is None or isinstance(obj, bool):
        return
    else:
        raise SafetyError("unsupported JSON value type")


def _no_duplicate_keys(pairs):
    out: Dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise SafetyError("duplicate JSON key: %r" % key[:64])
        out[key] = value
    return out


def loads_bounded(raw: bytes) -> Any:
    """Parse untrusted JSON with hard limits. Duplicate keys are rejected."""
    if not isinstance(raw, bytes):
        raise SafetyError("expected bytes")
    if len(raw) > MAX_BYTES:
        raise SafetyError("document exceeds %d bytes" % MAX_BYTES)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SafetyError("document is not valid UTF-8") from exc
    try:
        obj = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except RecursionError as exc:
        raise SafetyError("JSON nesting exceeds the parser recursion limit") from exc
    except (ValueError, SafetyError) as exc:
        raise SafetyError("invalid JSON: %s" % str(exc)[:120]) from exc
    _walk(obj, 0, [0])
    return obj


def read_bounded(path: str) -> Any:
    """Read a file with an atomic, symlink-resistant open where supported."""
    p = os.path.realpath(path)
    if not os.path.isfile(p):
        raise SafetyError("not a regular file: %s" % p[:120])
    st = os.stat(p)
    if st.st_size > MAX_BYTES:
        raise SafetyError("file exceeds %d bytes" % MAX_BYTES)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(p, flags)
    try:
        raw = os.read(fd, MAX_BYTES + 1)
    finally:
        os.close(fd)
    if len(raw) > MAX_BYTES:
        raise SafetyError("file grew while being read")
    return loads_bounded(raw)


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def looks_secret(name: str) -> bool:
    return bool(_SECRET_KEY.search(name or ""))


def redact(value: Optional[str], name: str = "") -> str:
    """Deterministic redaction for anything that reaches a report or a log."""
    if value is None:
        return ""
    text = str(value)
    if looks_secret(name):
        return REDACTED
    # Well-known token shapes.
    for prefix in ("sk-", "ghp_", "gho_", "ghs_", "xoxb-", "AKIA", "ASIA", "AIza"):
        if prefix in text:
            return REDACTED
    if len(text) >= 32 and _looks_high_entropy(text):
        return REDACTED
    return _sanitize_text(text)


def _looks_high_entropy(text: str) -> bool:
    # Linear scan; no regex.
    if len(set(text)) < max(8, len(text) // 6):
        return False
    classes = 0
    classes += any(c.islower() for c in text)
    classes += any(c.isupper() for c in text)
    classes += any(c.isdigit() for c in text)
    return classes >= 3 and " " not in text


def sanitize_output(data: bytes, cap: int) -> Tuple[str, str, bool]:
    """Return (excerpt, sha256 of the bytes examined, truncated)."""
    truncated = len(data) > cap
    chunk = data[:cap]
    digest = hashlib.sha256(chunk).hexdigest()
    try:
        text = chunk.decode("utf-8", errors="replace")
    except Exception:
        text = ""
    return _sanitize_text(text), digest, truncated


def _sanitize_text(text: str) -> str:
    text = _ANSI.sub("", text)
    text = _CONTROL.sub("", text)
    # Unicode dash variants must not silently become CLI options in a report.
    for dash in "\u2010\u2011\u2012\u2013\u2014\u2015\u2212":
        text = text.replace(dash, "-")
    return text[:MAX_STRING]


# ---------------------------------------------------------------------------
# Value validation
# ---------------------------------------------------------------------------

def validate_env_key(name: str) -> str:
    if not isinstance(name, str) or not _IDENTIFIER.match(name):
        raise SafetyError("invalid environment variable name")
    if len(name) > MAX_STRING:
        raise SafetyError("environment variable name too long")
    upper = name.upper()
    if upper in DENIED_ENV or upper.startswith("BASH_FUNC_"):
        raise SafetyError("refusing dangerous environment variable %s" % name)
    return name


def validate_factor_name(name: str) -> str:
    """Factor names are either env names, TOOL:<name>, @UMASK, or PATH.

    PATH is a legitimate replayable factor but is handled by a dedicated
    validator (absolute, existing, non-world-writable directories), so it is
    exempted from the generic environment-variable denylist here.
    """
    if name in (UMASK_FACTOR, "PATH"):
        return name
    if name.startswith(TOOL_PREFIX):
        tool = name[len(TOOL_PREFIX):]
        if not _IDENTIFIER.match(tool):
            raise SafetyError("invalid tool name in factor")
        return name
    return validate_env_key(name)


def validate_env_value(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise SafetyError("environment value for %s must be a string" % name)
    if len(value) > MAX_ENV_VALUE:
        raise SafetyError("environment value for %s is too long" % name)
    if any(ord(c) < 32 for c in value):
        raise SafetyError("control character in environment value for %s" % name)
    if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise SafetyError("surrogate codepoint in environment value for %s" % name)
    return value


def validate_path_value(value: str) -> str:
    """PATH entries must be absolute, non-empty and free of traversal.

    Deliberately structural only: a snapshot may come from a different machine,
    where its directories need not exist locally. PATH is not a security
    boundary here because argv[0] is always resolved to a validated absolute
    executable and the whole environment is constructed from scratch.
    """
    validate_env_value("PATH", value)
    parts = value.split(":")
    if not parts or len(parts) > 64:
        raise SafetyError("PATH has an unreasonable number of entries")
    for part in parts:
        if not part or not os.path.isabs(part) or part in (".", ".."):
            raise SafetyError("PATH contains a relative or empty entry")
        if ".." in part.split("/"):
            raise SafetyError("PATH contains traversal")
        if any(ord(c) < 32 for c in part):
            raise SafetyError("control character in PATH entry")
    return value


def validate_umask_value(value: str) -> int:
    try:
        n = int(value, 8)
    except (TypeError, ValueError) as exc:
        raise SafetyError("umask must be an octal string") from exc
    if not 0 <= n <= 0o777:
        raise SafetyError("umask out of range")
    return n


def validate_tool_path(value: str) -> str:
    validate_env_value("TOOL", value)
    if not os.path.isabs(value):
        raise SafetyError("tool path must be absolute")
    real = os.path.realpath(value)
    if not os.path.isfile(real):
        raise SafetyError("tool path is not a regular file")
    if not os.access(real, os.X_OK):
        raise SafetyError("tool path is not executable")
    st = os.stat(real)
    if st.st_mode & stat.S_IWOTH:
        raise SafetyError("tool executable is world-writable")
    return real


def validate_argv(argv: Iterable[str]) -> tuple:
    items = tuple(argv)
    if not items:
        raise SafetyError("empty command")
    if len(items) > 128:
        raise SafetyError("too many arguments")
    for item in items:
        if not isinstance(item, str):
            raise SafetyError("argument is not a string")
        if len(item) > MAX_ARG:
            raise SafetyError("argument too long")
        if any(ord(c) < 32 for c in item):
            raise SafetyError("control character in argument")
        if any(0xD800 <= ord(c) <= 0xDFFF for c in item):
            raise SafetyError("surrogate codepoint in argument")
    return items


def validate_relpath(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_PATH:
        raise SafetyError("invalid relative path")
    if os.path.isabs(value) or "\\" in value:
        raise SafetyError("absolute or windows-style path rejected")
    if any(c in value for c in SHELL_METACHARS):
        raise SafetyError("shell metacharacter in path")
    if value.startswith("-") or any(ord(c) > 0x2010 and ord(c) < 0x2016 for c in value[:1]):
        raise SafetyError("option-like path rejected")
    parts = value.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise SafetyError("path traversal rejected")
    return value


def contained(base: str, candidate: str) -> str:
    """Canonicalize and assert containment. Rejects symlink escapes."""
    root = os.path.realpath(base)
    target = os.path.realpath(candidate)
    if target != root and not target.startswith(root + os.sep):
        raise SafetyError("path escapes sandbox")
    return target


def ensure_private_dir(path: str) -> str:
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def factor_kind(name: str) -> str:
    if name == UMASK_FACTOR:
        return "umask"
    if name.startswith(TOOL_PREFIX):
        return "tool"
    return "env"
