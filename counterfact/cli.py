"""Command line interface.

Exit codes: 0 confirmed/probable | 1 inconclusive | 2 usage/config |
3 safety refusal | 4 internal error | 130 interrupted.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import __version__
from .config import DEFAULTS, load_config, merge
from .errors import CounterfactError, SafetyError, UsageError
from .minimize import (
    STATUS_BUDGET_EXCEEDED,
    STATUS_NO_REPRODUCTION,
    STATUS_OK,
    STATUS_BASELINE_FAILS,
    STATUS_EMPTY_DIFF,
    search,
)
from .oracle import Oracle
from .plan import build_plan, build_run_spec
from .proof import verify
from .report import render_github, render_json, render_sarif, render_text
from .runner import Runner
from .safety import redact
from .state import (
    DEFAULT_TOOL_NAMES,
    assert_no_denied,
    capture,
    diff_states,
    load_snapshot,
    save_snapshot,
    snapshot_from_obj,
    unreplayable_warnings,
)
from .types import (
    STATUS_CONFIRMED,
    STATUS_FLAKY,
    STATUS_INCONCLUSIVE,
    STATUS_PARTIAL,
    STATUS_PROBABLE,
    Budget,
    Finding,
    Snapshot,
)

DEMO_FAIL_TEXT = "FAIL: timezone-sensitive branch"


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="optional JSON config file")
    parser.add_argument("--good", required=True, help="snapshot of the passing state")
    parser.add_argument("--bad", required=True, help="snapshot of the failing state")
    parser.add_argument("--max-runs", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--max-total", type=float, default=None)
    parser.add_argument("--repeats", type=int, default=None)
    parser.add_argument("--max-output-bytes", type=int, default=None)
    parser.add_argument("--expect-fail-text", default=None)
    parser.add_argument("--workdir", default=None)


def _add_command(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="command to replay, preceded by -- (no shell)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="counterfact",
        description=(
            "Find the smallest tested environment change that flips a passing "
            "command into a specific failure, by running controlled experiments."
        ),
    )
    parser.add_argument("--version", action="version", version="counterfact " + __version__)
    sub = parser.add_subparsers(dest="subcommand", required=True)

    cap = sub.add_parser("capture", help="record a replayable environment snapshot")
    cap.add_argument("--out", required=True)
    cap.add_argument("--config")
    cap.add_argument("--factor", action="append", default=[], help="extra env key to capture")
    cap.add_argument("--tool", action="append", default=[], help="tool whose path becomes a factor")
    cap.add_argument("--all-tools", action="store_true")

    cmp = sub.add_parser("compare", help="READ-ONLY static diff; hypotheses, not evidence")
    _add_common(cmp)

    pln = sub.add_parser("plan", help="print the inert experiment plan; executes nothing")
    _add_common(pln)
    _add_command(pln)

    run = sub.add_parser("run", help="run controlled counterfactual experiments")
    _add_common(run)
    _add_command(run)
    run.add_argument("--yes", action="store_true", help="explicitly authorize command execution")
    run.add_argument("--format", choices=("text", "json", "sarif", "github"), default="text")
    run.add_argument("--out", help="write the report to this file")
    run.add_argument("--save-experiments", help="write the full experiment log JSON")

    demo = sub.add_parser("demo", help="self-contained end-to-end demonstration")
    demo.add_argument("--format", choices=("text", "json"), default="text")

    return parser


def _config_for(args) -> Dict[str, Any]:
    cfg = load_config(args.config) if getattr(args, "config", None) else dict(DEFAULTS)
    overrides = {
        "max_runs": getattr(args, "max_runs", None),
        "timeout_s": getattr(args, "timeout", None),
        "max_total_s": getattr(args, "max_total", None),
        "repeats": getattr(args, "repeats", None),
        "max_output_bytes": getattr(args, "max_output_bytes", None),
        "expect_fail_text": getattr(args, "expect_fail_text", None),
        "workdir": getattr(args, "workdir", None),
    }
    return merge(overrides, cfg)


def _pair(args) -> Tuple[Snapshot, Snapshot, List[str]]:
    good = load_snapshot(args.good)
    bad = load_snapshot(args.bad)
    assert_no_denied(good.factors)
    assert_no_denied(bad.factors)
    return good, bad, unreplayable_warnings(good, bad)


def _command(args) -> List[str]:
    command = list(getattr(args, "command", []) or [])
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise UsageError("a command is required after --")
    return command


def _oracle(cfg: Dict[str, Any]) -> Oracle:
    text = cfg.get("expect_fail_text") or ""
    return Oracle(mode="fingerprint" if text else "exit", expect_fail_text=text)


def _budget(cfg: Dict[str, Any]) -> Budget:
    return Budget(
        max_runs=int(cfg["max_runs"]),
        timeout_s=float(cfg["timeout_s"]),
        max_output_bytes=int(cfg["max_output_bytes"]),
        max_total_s=float(cfg["max_total_s"]),
        repeats=int(cfg["repeats"]),
    )


def _flow(good, bad, command, cfg, *, state_warnings=None) -> Tuple[Finding, Dict, list]:
    oracle = _oracle(cfg)
    budget = _budget(cfg)
    factors = diff_states(good, bad)
    spec = build_run_spec(command, good, cfg)
    plan = build_plan(
        good=good,
        bad=bad,
        factors=factors,
        spec=spec,
        budget=budget,
        oracle_warnings=oracle.warnings(),
        state_warnings=list(state_warnings or []),
        oracle_desc=oracle.to_dict(),
    )
    runner = Runner(spec, {f.name: f for f in factors}, budget, oracle)

    result = search(factors, runner)
    warnings = list(plan["warnings"]) + list(result.warnings)

    if result.status == STATUS_OK:
        proof = verify(runner, result.minimal, budget.repeats)
        status = proof.status
        replication = proof.replication
        warnings.extend(proof.warnings)
        partial = result.partial or proof.partial
        minimal = result.minimal
    elif result.status == STATUS_BUDGET_EXCEEDED:
        proof = None
        status = STATUS_PARTIAL
        replication = (0, 0)
        partial = True
        minimal = result.minimal
    else:
        proof = None
        status = STATUS_INCONCLUSIVE
        replication = (0, 0)
        partial = False
        minimal = ()

    finding = Finding(
        status=status,
        factors=tuple(minimal),
        replication=replication,
        experiments=list(runner.log),
        warnings=warnings,
        oracle=oracle.to_dict(),
        partial=partial,
    )
    return finding, plan, factors


def _static_compare(good: Snapshot, bad: Snapshot, as_json: bool) -> str:
    factors = diff_states(good, bad)
    if as_json:
        return json.dumps(
            {
                "schema_version": 1,
                "notice": "These are ranked-looking hypotheses, NOT tested causes. "
                          "Use 'counterfact run' to intervene.",
                "differences": [f.to_dict() for f in factors],
            },
            indent=2,
            sort_keys=True,
        ) + "\n"
    lines = [
        "counterfact compare — %d replayable difference(s)" % len(factors),
        "These are HYPOTHESES. No command was executed.",
        "-" * 72,
    ]
    for factor in factors:
        lines.append(
            "  %-24s %-8s %s -> %s"
            % (
                redact(factor.name)[:24],
                factor.kind,
                redact(factor.good, factor.name)[:26] or "(unset)",
                redact(factor.bad, factor.name)[:26] or "(unset)",
            )
        )
    lines.append("-" * 72)
    lines.append("A diff cannot tell you which difference actually flips the outcome.")
    return "\n".join(lines) + "\n"


def _write_report(path: str, body: str) -> None:
    """Write a report, refusing symlinks and non-existent parent directories."""
    if os.path.islink(path):
        raise SafetyError("refusing to write report through a symlink")
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        raise SafetyError("report parent directory does not exist")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)


def _demo(args) -> int:
    workdir = tempfile.mkdtemp(prefix="counterfact-demo-")
    try:
        script = os.path.join(workdir, "check.py")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(
                "import os, sys\n"
                "if os.environ.get('TZ') == 'UTC':\n"
                "    print('FAIL: timezone-sensitive branch', file=sys.stderr)\n"
                "    sys.exit(1)\n"
                "print('ok')\n"
            )
        good = snapshot_from_obj(
            {
                "schema_version": 1,
                "factors": {
                    "TZ": "Asia/Shanghai", "LANG": "C.UTF-8", "CI": "false",
                    "TERM": "dumb", "PYTHONHASHSEED": "0", "@UMASK": "022",
                },
                "metadata": {},
            }
        )
        bad = snapshot_from_obj(
            {
                "schema_version": 1,
                "factors": {
                    "TZ": "UTC", "LANG": "C.UTF-8", "CI": "true",
                    "TERM": "xterm", "PYTHONHASHSEED": "7", "@UMASK": "077",
                },
                "metadata": {},
            }
        )
        cfg = dict(DEFAULTS)
        cfg["workdir"] = workdir
        cfg["expect_fail_text"] = DEMO_FAIL_TEXT
        cfg["repeats"] = 3
        finding, plan, factors = _flow(
            good, bad, [sys.executable, "check.py"], cfg
        )
        if args.format == "json":
            sys.stdout.write(render_json(finding, plan))
        else:
            sys.stdout.write(
                "DEMO: 5 harmless differences, 1 real cause (TZ).\n\n"
            )
            sys.stdout.write(render_text(finding, plan, factors))
        return 0 if finding.status in (STATUS_CONFIRMED, STATUS_PROBABLE) else 1
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def dispatch(args) -> int:
    if args.subcommand == "version":
        print("counterfact " + __version__)
        return 0

    if args.subcommand == "demo":
        return _demo(args)

    if args.subcommand == "capture":
        cfg = load_config(args.config) if args.config else dict(DEFAULTS)
        tools = list(args.tool)
        if args.all_tools:
            tools = list(DEFAULT_TOOL_NAMES)
        snap = capture(extra_keys=list(args.factor) + list(cfg["capture_keys"]), tool_names=tools)
        save_snapshot(snap, args.out)
        print("captured %d factor(s) -> %s" % (len(snap.factors), args.out))
        return 0

    good, bad, state_warnings = _pair(args)

    if args.subcommand == "compare":
        sys.stdout.write(_static_compare(good, bad, False))
        return 0

    cfg = _config_for(args)
    command = _command(args)

    if args.subcommand == "plan":
        _, plan, _ = _flow_setup_only(good, bad, command, cfg, state_warnings)
        sys.stdout.write(json.dumps(plan, indent=2, sort_keys=True) + "\n")
        # Human commentary goes to stderr so stdout stays pipeable JSON.
        sys.stderr.write(
            "# INERT: nothing was executed. Add --yes to the 'run' command to authorize.\n"
        )
        return 0

    if args.subcommand == "run":
        if not args.yes:
            raise SafetyError(
                "execution not authorized: 'counterfact run' requires --yes. "
                "Run 'counterfact plan' first to inspect the experiment specification."
            )
        finding, plan, factors = _flow(
            good, bad, command, cfg, state_warnings=state_warnings
        )
        renderers = {
            "text": lambda: render_text(finding, plan, factors),
            "json": lambda: render_json(finding, plan),
            "sarif": lambda: render_sarif(finding),
            "github": lambda: render_github(finding),
        }
        body = renderers[args.format]()
        sys.stdout.write(body)
        if args.out:
            _write_report(args.out, body)
        if args.save_experiments:
            _write_report(args.save_experiments, render_json(finding, plan))
        return 0 if finding.status in (STATUS_CONFIRMED, STATUS_PROBABLE) else 1

    raise UsageError("unknown subcommand")


def _flow_setup_only(good, bad, command, cfg, state_warnings):
    """Build a plan without creating a Runner (and therefore without any I/O)."""
    oracle = _oracle(cfg)
    budget = _budget(cfg)
    factors = diff_states(good, bad)
    spec = build_run_spec(command, good, cfg)
    plan = build_plan(
        good=good,
        bad=bad,
        factors=factors,
        spec=spec,
        budget=budget,
        oracle_warnings=oracle.warnings(),
        state_warnings=list(state_warnings),
        oracle_desc=oracle.to_dict(),
    )
    return None, plan, factors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return dispatch(args)
    except CounterfactError as exc:
        sys.stderr.write("counterfact: %s\n" % redact(str(exc)))
        return exc.exit_code
    except KeyboardInterrupt:
        sys.stderr.write("counterfact: interrupted\n")
        return 130
    except Exception as exc:  # pragma: no cover - last-resort boundary
        sys.stderr.write("counterfact: internal error: %s\n" % redact(type(exc).__name__))
        return 4
