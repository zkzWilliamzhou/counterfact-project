"""Behaviour-equivalence gate for refactors.

Runs a fixed, deterministic corpus through the real execution path and records
a normalized snapshot of *observable behaviour*. A refactor is only allowed to
land if the snapshot is byte-identical.

Usage:
    python scripts/equivalence.py --record   # freeze golden (before refactor)
    python scripts/equivalence.py --check    # compare (after refactor)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from counterfact.cli import _flow  # noqa: E402
from counterfact.config import DEFAULTS  # noqa: E402
from counterfact.state import snapshot_from_obj  # noqa: E402

GOLDEN = os.path.join(REPO, "tests", "fixtures", "golden_behaviour.json")

TZ_SCRIPT = (
    "import os, sys\n"
    "if os.environ.get('TZ') == 'UTC':\n"
    "    print('FAIL: timezone-sensitive branch', file=sys.stderr)\n"
    "    sys.exit(1)\n"
    "print('ok')\n"
)

INTERACTION_SCRIPT = (
    "import os, sys\n"
    "if os.environ.get('TZ') == 'UTC' and os.environ.get('CI') == 'true':\n"
    "    print('FAIL: interaction branch', file=sys.stderr)\n"
    "    sys.exit(1)\n"
    "print('ok')\n"
)

ALWAYS_OK_SCRIPT = "print('always fine')\n"


def _snap(factors):
    return snapshot_from_obj(
        {"schema_version": 1, "factors": dict(factors), "metadata": {}}
    )


def _scenario(script, good, bad, fail_text):
    with tempfile.TemporaryDirectory() as workdir:
        with open(os.path.join(workdir, "check.py"), "w", encoding="utf-8") as handle:
            handle.write(script)
        cfg = dict(DEFAULTS)
        cfg["workdir"] = workdir
        cfg["expect_fail_text"] = fail_text
        cfg["repeats"] = 3
        finding, plan, _ = _flow(good, bad, [sys.executable, "check.py"], cfg)
        data = finding.to_dict(plan)
        for exp in data["experiments"]:
            exp.pop("duration_ms", None)
        command = data.get("plan", {}).get("command", [])
        data["plan"]["command"] = [
            "<PYTHON>" if item == sys.executable else item for item in command
        ]
        return data


def corpus():
    single_good = _snap(
        {"TZ": "Asia/Shanghai", "LANG": "C.UTF-8", "CI": "false", "@UMASK": "022"}
    )
    single_bad = _snap(
        {"TZ": "UTC", "LANG": "C.UTF-8", "CI": "true", "@UMASK": "022"}
    )
    inter_good = _snap(
        {"TZ": "Asia/Shanghai", "CI": "false", "TERM": "dumb", "@UMASK": "022"}
    )
    inter_bad = _snap(
        {"TZ": "UTC", "CI": "true", "TERM": "xterm", "@UMASK": "077"}
    )
    return {
        "single_factor": _scenario(
            TZ_SCRIPT, single_good, single_bad, "FAIL: timezone-sensitive branch"
        ),
        "two_factor_interaction": _scenario(
            INTERACTION_SCRIPT, inter_good, inter_bad, "FAIL: interaction branch"
        ),
        "no_reproduction": _scenario(
            ALWAYS_OK_SCRIPT, single_good, single_bad, "never appears"
        ),
    }


def canonical(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--record", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    current = canonical(corpus())
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)

    if args.record:
        with open(GOLDEN, "w", encoding="utf-8") as handle:
            handle.write(current)
        print("recorded golden: %s (%d bytes)" % (GOLDEN, len(current)))
        return 0

    if not os.path.exists(GOLDEN):
        print("FAIL: no golden file; run --record before the refactor")
        return 1
    with open(GOLDEN, "r", encoding="utf-8") as handle:
        expected = handle.read()
    if expected == current:
        print("EQUIVALENCE OK: observable behaviour unchanged (%d bytes)" % len(current))
        return 0
    print("EQUIVALENCE FAILED: observable behaviour changed")
    import difflib

    diff = list(
        difflib.unified_diff(
            expected.splitlines(), current.splitlines(),
            fromfile="golden", tofile="current", lineterm="",
        )
    )
    for line in diff[:80]:
        print(line)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
