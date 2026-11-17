"""Falsifiable quality gate: recovery rate on planted environment failures.

Claim under test (from ADOPTION.md):
  * recover the planted factor set in >= 90% of planted cases
  * 95% of successful searches complete in <= 50 command executions

Every case is a real end-to-end run through the real Runner: a real Python
child process, real constructed environments, real ddmin and real verification.
No mocks. Deterministic seeds.

Usage:
    python scripts/benchmark.py            # writes BENCHMARK.md + JSON
    python scripts/benchmark.py --json     # machine-readable only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from counterfact.cli import _flow  # noqa: E402
from counterfact.config import DEFAULTS  # noqa: E402
from counterfact.state import snapshot_from_obj  # noqa: E402
from counterfact.types import STATUS_CONFIRMED, STATUS_PROBABLE  # noqa: E402

FACTOR_KEYS = ("F0", "F1", "F2", "F3", "F4", "F5")
DECOYS = ("TZ", "CI", "@UMASK")
FAIL_TEXT = "FAIL: planted"

GATE_RECOVERY = 0.90
GATE_COST_PCT = 0.95
GATE_MAX_RUNS = 50


def _snap(factors):
    return snapshot_from_obj(
        {"schema_version": 1, "factors": dict(factors), "metadata": {}}
    )


def _script(planted):
    return (
        "import os, sys\n"
        "planted = %r\n"
        "if all(os.environ.get(k) == '1' for k in planted):\n"
        "    print('FAIL: planted', file=sys.stderr)\n"
        "    sys.exit(1)\n"
        "print('ok')\n" % (list(planted),)
    )


def run_benchmark(cases: int = 20, seed: int = 20261114) -> dict:
    import random

    rng = random.Random(seed)
    rows = []
    started = time.monotonic()

    with tempfile.TemporaryDirectory() as workdir:
        script = os.path.join(workdir, "check.py")
        good = _snap(
            {**{k: "0" for k in FACTOR_KEYS},
             "TZ": "Asia/Shanghai", "CI": "false", "@UMASK": "022"}
        )
        bad = _snap(
            {**{k: "1" for k in FACTOR_KEYS},
             "TZ": "UTC", "CI": "true", "@UMASK": "077"}
        )
        cfg = dict(DEFAULTS)
        cfg["workdir"] = workdir
        cfg["expect_fail_text"] = FAIL_TEXT
        cfg["repeats"] = 2
        cfg["max_runs"] = 60

        for index in range(cases):
            planted = tuple(sorted(rng.sample(FACTOR_KEYS, rng.randint(1, 3))))
            with open(script, "w", encoding="utf-8") as handle:
                handle.write(_script(planted))
            finding, _, _ = _flow(good, bad, [sys.executable, "check.py"], cfg)
            actual_executions = sum(
                1 for experiment in finding.experiments if not experiment.cache_hit
            )
            recovered = (
                finding.status in (STATUS_CONFIRMED, STATUS_PROBABLE)
                and set(finding.factors) == set(planted)
            )
            rows.append(
                {
                    "case": index,
                    "planted": list(planted),
                    "recovered": recovered,
                    "status": finding.status,
                    "found": list(finding.factors),
                    "executions": actual_executions,
                    "under_50": actual_executions <= GATE_MAX_RUNS,
                }
            )

    recovered_count = sum(1 for row in rows if row["recovered"])
    successful = [row for row in rows if row["recovered"]]
    cost_ok = sum(1 for row in successful if row["under_50"])
    result = {
        "cases": cases,
        "seed": seed,
        "recovered": recovered_count,
        "recovery_rate": round(recovered_count / cases, 4),
        "cost_ok": cost_ok,
        "cost_rate": round(cost_ok / max(1, len(successful)), 4),
        "max_executions": max(row["executions"] for row in rows),
        "median_executions": sorted(row["executions"] for row in rows)[len(rows) // 2],
        "elapsed_s": round(time.monotonic() - started, 2),
        "gates": {
            "recovery_ge_90pct": recovered_count / cases >= GATE_RECOVERY,
            "cost_95pct_under_50": cost_ok / max(1, len(successful)) >= GATE_COST_PCT,
        },
        "rows": rows,
    }
    result["passed"] = all(result["gates"].values())
    return result


def markdown(result: dict) -> str:
    lines = [
        "# Benchmark: recovery on planted environment failures",
        "",
        "Deterministic seed `%d`, %d cases, real child processes (no mocks)."
        % (result["seed"], result["cases"]),
        "",
        "| Metric | Result | Gate | Verdict |",
        "| --- | --- | --- | --- |",
        "| Recovery rate | %.0f%% (%d/%d) | >= 90%% | %s |"
        % (result["recovery_rate"] * 100, result["recovered"], result["cases"],
           "PASS" if result["gates"]["recovery_ge_90pct"] else "FAIL"),
        "| Searches under 50 executions | %.0f%% (%d/%d) | >= 95%% | %s |"
        % (result["cost_rate"] * 100, result["cost_ok"],
           sum(1 for r in result["rows"] if r["recovered"]),
           "PASS" if result["gates"]["cost_95pct_under_50"] else "FAIL"),
        "| Max / median executions | %d / %d | report | — |"
        % (result["max_executions"], result["median_executions"]),
        "| Wall clock | %.2f s | report | — |" % result["elapsed_s"],
        "",
        "**Overall: %s**" % ("PASS" if result["passed"] else "FAIL"),
        "",
        "Each case plants 1–3 causal factors among 6 candidate keys, plus 3 "
        "harmless decoy differences (`TZ`, `CI`, `@UMASK`). The failing script "
        "exits non-zero only when every planted factor is present, so the "
        "failure predicate is monotone and ddmin's assumptions hold.",
        "",
        "## Per-case detail",
        "",
        "| # | Planted | Found | Status | Executions | Recovered |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            "| %d | %s | %s | %s | %d | %s |"
            % (row["case"], ", ".join(row["planted"]), ", ".join(row["found"]) or "—",
               row["status"], row["executions"], "yes" if row["recovered"] else "NO")
        )
    lines += [
        "",
        "## What this does not prove",
        "",
        "It does not prove recovery on real-world flaky commands, on failures "
        "caused by un-captured state (kernel, network, wall clock), or on "
        "non-monotone multi-factor interactions. It is a lower bound on the "
        "algorithm under controlled conditions, not a real-world accuracy claim.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20261114)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_benchmark(args.cases, args.seed)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        output = markdown(result)
        with open(os.path.join(REPO, "BENCHMARK.md"), "w", encoding="utf-8") as handle:
            handle.write(output)
        with open(os.path.join(REPO, "BENCHMARK.json"), "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
        print(output)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
