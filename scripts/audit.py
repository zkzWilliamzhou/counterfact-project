"""Twelve independent review rounds — deliberately more than the 8 requested.

Each round makes real assertions and returns concrete findings. An empty
finding list is the only PASS condition; a broken harness is a failure too.

Run: python scripts/audit.py
Output: REVIEW_LOG.json (machine-readable evidence for REVIEW.md)
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

from counterfact.errors import CounterfactError  # noqa: E402
from counterfact.safety import DENIED_ENV, loads_bounded, redact  # noqa: E402
from counterfact.state import snapshot_from_obj  # noqa: E402
from helpers import FakeRunner  # noqa: E402

ENV = {**os.environ, "PYTHONPATH": REPO}
LOG_PATH = os.path.join(REPO, "REVIEW_LOG.json")


def cli(*args, timeout=240):
    return subprocess.run(
        [sys.executable, "-m", "counterfact", *args],
        cwd=REPO, env=ENV, capture_output=True, text=True, timeout=timeout,
    )


def _random_obj(rng, depth):
    if depth > 5:
        return rng.choice([None, True, 1, "x", 1.5])
    kind = rng.randrange(7)
    if kind == 0:
        return {rng.choice(["schema_version", "factors", "metadata", "junk", "TZ"]):
                _random_obj(rng, depth + 1) for _ in range(rng.randrange(4))}
    if kind == 1:
        return [_random_obj(rng, depth + 1) for _ in range(rng.randrange(5))]
    return rng.choice([None, True, False, 1, 99, "UTC", "x" * 30, "LD_PRELOAD", ""])


# ---------------------------------------------------------------------------
# Round 1 — static / supply-chain / protocol invariants
# ---------------------------------------------------------------------------
def round_1():
    findings = []
    banned = (
        "shell=True", "eval(", "exec(", "import pickle", "pickle.load", "yaml.load", "os.system",
        "subprocess.getoutput", "urllib.request", "requests.", "input(",
        "__import__", "setattr(", "globals()",
    )
    package = os.path.join(REPO, "counterfact")
    for name in sorted(os.listdir(package)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(package, name)
        with open(path, "r", encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for token in banned:
                    if token in line:
                        findings.append(
                            "round1: %s:%d contains banned construct %r" % (name, lineno, token)
                        )
    result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "counterfact"],
        cwd=REPO, env=ENV, capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        findings.append("round1: compileall failed: %s" % result.stderr[:200])
    for required in ("brainstorming.md", "grilling.md", "stop-slop.md",
                     "improve-codebase-architecture.md", "tdd.md"):
        path = os.path.join(REPO, "skills", required)
        if not os.path.isfile(path):
            findings.append("round1: missing vendored protocol %s" % required)
    return findings


# ---------------------------------------------------------------------------
# Round 2 — full test suite
# ---------------------------------------------------------------------------
def round_2():
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=REPO, env=ENV, capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        return ["round2: unittest suite failed:\n" + result.stderr[-1500:]]
    match = re.search(r"Ran (\d+) tests", result.stderr)
    if not match or int(match.group(1)) < 55:
        return ["round2: test count suspiciously low: %s" % result.stderr[-300:]]
    return []


# ---------------------------------------------------------------------------
# Round 3 — adversarial fuzz of every untrusted parser
# ---------------------------------------------------------------------------
def round_3():
    findings = []
    deep = b"[" * 1500 + b"0" + b"]" * 1500
    try:
        loads_bounded(deep)
        findings.append("round3: deeply nested JSON bypassed the parser depth limit")
    except CounterfactError:
        pass
    except Exception as exc:
        findings.append(
            "round3: loads_bounded leaked unhandled %s on deep input" % type(exc).__name__
        )

    try:
        snapshot_from_obj({"schema_version": True, "factors": {}, "metadata": {}})
        findings.append("round3: boolean schema_version accepted as version 1")
    except CounterfactError:
        pass

    rng = random.Random(20261113)
    for index in range(300):
        obj = _random_obj(rng, 0)
        try:
            snapshot_from_obj(obj)
        except CounterfactError:
            pass
        except Exception as exc:
            findings.append(
                "round3: snapshot_from_obj leaked unhandled %s on fuzz case %d"
                % (type(exc).__name__, index)
            )
            break
    for index in range(120):
        raw = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 200)))
        try:
            loads_bounded(raw)
        except CounterfactError:
            pass
        except Exception as exc:
            findings.append(
                "round3: loads_bounded leaked unhandled %s on byte fuzz %d"
                % (type(exc).__name__, index)
            )
            break
    return findings


# ---------------------------------------------------------------------------
# Round 4 — security controls and secret hygiene
# ---------------------------------------------------------------------------
def round_4():
    findings = []
    from counterfact.state import save_snapshot
    from helpers import make_snapshot, write_script

    # Behavioural exploit test: a report destination that is a symlink must be
    # refused and the link target must remain untouched.
    with tempfile.TemporaryDirectory() as workdir:
        write_script(workdir, "check.py", "print('ok')\n")
        good = os.path.join(workdir, "g.json")
        bad = os.path.join(workdir, "b.json")
        save_snapshot(make_snapshot({"TZ": "UTC"}), good)
        save_snapshot(make_snapshot({"TZ": "Asia/Shanghai"}), bad)
        target = os.path.join(workdir, "precious.txt")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("original")
        link = os.path.join(workdir, "report-link.json")
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            link = None
        if link:
            proc = cli(
                "run", "--good", good, "--bad", bad, "--yes", "--workdir", workdir,
                "--save-experiments", link, "--", sys.executable, "check.py",
            )
            if proc.returncode != 3:
                findings.append(
                    "round4: --save-experiments followed a symlink (exit %d, expected 3)"
                    % proc.returncode
                )
            with open(target, "r", encoding="utf-8") as handle:
                if handle.read() != "original":
                    findings.append("round4: symlink target was overwritten")
    for name in ("LD_PRELOAD", "PYTHONPATH", "BASH_ENV", "IFS", "NODE_OPTIONS",
                 "GCONV_PATH", "HOME", "TMPDIR"):
        if name not in DENIED_ENV:
            findings.append("round4: %s missing from environment denylist" % name)

    from counterfact.report import render_github, render_json, render_sarif, render_text
    from counterfact.types import Finding, Factor

    secret = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    finding = Finding(
        status="CONFIRMED", factors=("TZ",), replication=(7, 7), experiments=[],
        warnings=["leak candidate " + secret],
        oracle={"mode": "fingerprint", "expect_fail_text": secret},
    )
    outputs = [
        render_text(finding, {}, [Factor("TZ", "UTC", "UTC")]),
        render_json(finding, {}),
        render_sarif(finding),
        render_github(finding),
    ]
    for index, output in enumerate(outputs):
        if secret in output:
            findings.append("round4: renderer %d leaked a token-shaped secret" % index)
    return findings


# ---------------------------------------------------------------------------
# Round 5 — algorithm correctness and status reachability
# ---------------------------------------------------------------------------
def round_5():
    findings = []
    from counterfact.minimize import search
    from counterfact.proof import verify
    from counterfact.types import Experiment, Factor, STATUS_PROBABLE

    class PartiallyUnresolved:
        def __init__(self):
            self.calls = 0
            self.log = []

        def run(self, applied, use_cache=True):
            self.calls += 1
            outcome = "UNRESOLVED" if self.calls == 2 else (
                "FAIL" if "E" in applied else "PASS"
            )
            exp = Experiment(
                index=len(self.log) + 1, applied=tuple(applied), outcome=outcome,
                exit_code=1 if outcome == "FAIL" else 0, timed_out=False,
                truncated=False, duration_ms=1, stdout_sha256="", stderr_sha256="",
                stdout_excerpt="", stderr_excerpt="",
            )
            self.log.append(exp)
            return exp

    verdict = verify(PartiallyUnresolved(), ("E",), 3)
    if verdict.status != STATUS_PROBABLE:
        findings.append(
            "round5: STATUS_PROBABLE is unreachable (got %s). Strong-but-imperfect "
            "evidence is being collapsed into INCONCLUSIVE." % verdict.status
        )

    rng = random.Random(7)
    for case in range(30):
        names = tuple("F%02d" % j for j in range(10))
        planted = tuple(sorted(rng.sample(names, rng.randint(1, 3))))
        wanted = set(planted)

        def predicate(applied, wanted=wanted):
            return "FAIL" if wanted.issubset(set(applied)) else "PASS"

        result = search([Factor(x, "0", "1") for x in names], FakeRunner(predicate))
        if result.status != "OK" or set(result.minimal) != wanted:
            findings.append(
                "round5: ddmin failed monotone case %d (planted=%s got=%s status=%s)"
                % (case, sorted(wanted), sorted(result.minimal), result.status)
            )
            break
    return findings


# ---------------------------------------------------------------------------
# Round 6 — resources, process groups, cleanup
# ---------------------------------------------------------------------------
def round_6():
    findings = []
    from counterfact.types import Budget
    from helpers import make_runner, make_spec, write_script

    tmp_root = tempfile.gettempdir()
    before = {n for n in os.listdir(tmp_root) if n.startswith("counterfact-")}

    with tempfile.TemporaryDirectory() as workdir:
        write_script(workdir, "check.py", "print('ok')\n")
        runner = make_runner(make_spec("check.py", workdir), [])
        for _ in range(20):
            runner.run((), use_cache=False)
        after = {n for n in os.listdir(tmp_root) if n.startswith("counterfact-")}
        leaked = after - before
        if leaked:
            findings.append("round6: %d sandbox directories leaked: %s" % (len(leaked), sorted(leaked)[:3]))

    marker = os.path.join(tempfile.gettempdir(), "counterfact-orphan-marker-%d" % os.getpid())
    if os.path.exists(marker):
        os.unlink(marker)
    with tempfile.TemporaryDirectory() as workdir:
        write_script(
            workdir, "check.py",
            "import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c', "
            "\"import time,os; time.sleep(1.5); open(%r,'w').write('orphan')\"])\n"
            "time.sleep(30)\n" % marker,
        )
        runner = make_runner(
            make_spec("check.py", workdir), [], budget=Budget(timeout_s=0.5, max_runs=5)
        )
        runner.run(())
        time.sleep(2.2)
        if os.path.exists(marker):
            findings.append("round6: a descendant process survived process-group termination")
            os.unlink(marker)

    fd_path = "/proc/self/fd"
    if os.path.isdir(fd_path):
        start = len(os.listdir(fd_path))
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "print('ok')\n")
            runner = make_runner(make_spec("check.py", workdir), [], budget=Budget(max_runs=30))
            for _ in range(15):
                runner.run((), use_cache=False)
        end = len(os.listdir(fd_path))
        if end - start > 5:
            findings.append("round6: file-descriptor growth %d -> %d" % (start, end))
    return findings


# ---------------------------------------------------------------------------
# Round 7 — CI/UX contract
# ---------------------------------------------------------------------------
def round_7():
    findings = []
    from counterfact.state import save_snapshot
    from helpers import make_snapshot, write_script

    with tempfile.TemporaryDirectory() as workdir:
        write_script(workdir, "check.py", "print('ok')\n")
        good = os.path.join(workdir, "g.json")
        bad = os.path.join(workdir, "b.json")
        save_snapshot(make_snapshot({"TZ": "UTC"}), good)
        save_snapshot(make_snapshot({"TZ": "Asia/Shanghai"}), bad)

        planned = cli("plan", "--good", good, "--bad", bad, "--", sys.executable, "check.py")
        if planned.returncode != 0:
            findings.append("round7: plan exited %d" % planned.returncode)
        else:
            try:
                json.loads(planned.stdout)
            except ValueError:
                findings.append(
                    "round7: 'plan' stdout is not pure JSON (a trailing human comment "
                    "breaks piping into jq / CI parsers)"
                )

        missing = cli("run", "--yes")
        if missing.returncode != 2:
            findings.append("round7: missing required args should exit 2, got %d" % missing.returncode)

        helped = cli("--help")
        if helped.returncode != 0:
            findings.append("round7: --help exited %d" % helped.returncode)

        sarif = cli(
            "run", "--good", good, "--bad", bad, "--yes", "--workdir", workdir,
            "--expect-fail-text", "never", "--format", "sarif",
            "--", sys.executable, "check.py",
        )
        try:
            doc = json.loads(sarif.stdout)
            assert doc["version"] == "2.1.0"
            assert doc["runs"][0]["results"]
        except Exception as exc:
            findings.append("round7: SARIF output invalid: %s" % type(exc).__name__)

    readme = os.path.join(REPO, "README.md")
    with open(readme, "r", encoding="utf-8") as handle:
        text = handle.read()
    flags = set(re.findall(r"--[a-z][a-z0-9-]+", text))
    from counterfact.cli import build_parser

    parser = build_parser()
    known = set()
    for action in parser._actions:
        known.update(action.option_strings)
        if hasattr(action, "choices") and action.choices:
            for sub in action.choices.values() if isinstance(action.choices, dict) else []:
                for sub_action in sub._actions:
                    known.update(sub_action.option_strings)
    missing_flags = sorted(f for f in flags if f not in known)
    if missing_flags:
        findings.append("round7: README documents flags the CLI does not have: %s" % missing_flags)
    return findings


# ---------------------------------------------------------------------------
# Round 8 — equivalence, packaging, dogfooding
# ---------------------------------------------------------------------------
def round_8():
    findings = []
    equivalence = subprocess.run(
        [sys.executable, "scripts/equivalence.py", "--check"],
        cwd=REPO, env=ENV, capture_output=True, text=True, timeout=300,
    )
    if equivalence.returncode != 0:
        findings.append("round8: behaviour-equivalence gate failed:\n" + equivalence.stdout[-800:])

    pyproject = os.path.join(REPO, "pyproject.toml")
    with open(pyproject, "r", encoding="utf-8") as handle:
        content = handle.read()
    for key in ("[project]", "name =", "version =", "[project.scripts]", "counterfact ="):
        if key not in content:
            findings.append("round8: pyproject.toml missing %r" % key)

    with tempfile.TemporaryDirectory() as workdir:
        captured = os.path.join(workdir, "self.json")
        cap = cli("capture", "--out", captured)
        if cap.returncode != 0:
            findings.append("round8: self-capture failed: %s" % cap.stderr[:200])
        else:
            compared = cli("compare", "--good", captured, "--bad", captured)
            if compared.returncode != 0 or "0 replayable difference" not in compared.stdout:
                findings.append("round8: dogfooding compare did not produce a clean empty diff")
    return findings


# ---------------------------------------------------------------------------
# Round 9 — falsifiable recovery benchmark on real child processes
# ---------------------------------------------------------------------------
def round_9():
    findings = []
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    from benchmark import run_benchmark

    result = run_benchmark(cases=20)
    if not result["gates"]["recovery_ge_90pct"]:
        findings.append(
            "round9: recovery %.0f%% is below the 90%% gate"
            % (result["recovery_rate"] * 100)
        )
    if not result["gates"]["cost_95pct_under_50"]:
        findings.append(
            "round9: only %.0f%% of searches stayed under 50 executions"
            % (result["cost_rate"] * 100)
        )
    wrong = [r for r in result["rows"] if r["recovered"] is False
             and r["status"] in ("CONFIRMED", "PROBABLE")]
    if wrong:
        findings.append(
            "round9: %d case(s) CONFIRMED a wrong factor set: %s"
            % (len(wrong), [r["case"] for r in wrong])
        )
    return findings


# ---------------------------------------------------------------------------
# Round 10 — noise injection must never confirm a false cause
# ---------------------------------------------------------------------------
def round_10():
    findings = []
    from counterfact.minimize import search
    from counterfact.proof import verify
    from counterfact.types import Experiment, Factor

    class Noisy:
        """True cause is F2, but every observation may go UNRESOLVED."""

        def __init__(self, seed, noise):
            self.rng = random.Random(seed)
            self.noise = noise
            self.log = []

        def run(self, applied, use_cache=True):
            is_fail = "F2" in applied
            outcome = "UNRESOLVED" if self.rng.random() < self.noise else (
                "FAIL" if is_fail else "PASS"
            )
            exp = Experiment(
                index=len(self.log) + 1, applied=tuple(applied), outcome=outcome,
                exit_code=1 if outcome == "FAIL" else 0, timed_out=False,
                truncated=False, duration_ms=1, stdout_sha256="", stderr_sha256="",
                stdout_excerpt="", stderr_excerpt="",
            )
            self.log.append(exp)
            return exp

    names = tuple("F%d" % i for i in range(7))
    factors = [Factor(n, "0", "1") for n in names]
    for seed in range(18):
        observer = Noisy(seed, noise=0.18)
        result = search(factors, observer)
        if result.status != "OK":
            continue  # inconclusive is the correct safe outcome
        verdict = verify(observer, result.minimal, 3)
        if verdict.status == "CONFIRMED" and set(result.minimal) != {"F2"}:
            findings.append(
                "round10: seed %d CONFIRMED a wrong cause %s under 18%% noise"
                % (seed, sorted(result.minimal))
            )
    return findings


# ---------------------------------------------------------------------------
# Round 11 — documentation artifact and version consistency
# ---------------------------------------------------------------------------
def round_11():
    findings = []
    import importlib
    import pkgutil

    docs = []
    for root in (REPO, os.path.join(REPO, "docs"), os.path.join(REPO, "skills"),
                 os.path.join(REPO, "agents"), os.path.join(REPO, "docs", "adr")):
        if os.path.isdir(root):
            for name in os.listdir(root):
                if name.endswith(".md"):
                    docs.append(os.path.join(root, name))

    link_re = re.compile(r"\]\(([^)]+)\)")
    for path in docs:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for target in link_re.findall(text):
            if target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            clean = target.split("#")[0]
            if not clean:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), clean))
            if not os.path.exists(resolved):
                findings.append(
                    "round11: %s links to missing %s"
                    % (os.path.relpath(path, REPO), clean)
                )

    import counterfact
    from counterfact import errors

    declared = {
        "CounterfactError": 4, "UsageError": 2, "ConfigError": 2,
        "SafetyError": 3, "BudgetExceeded": 1,
    }
    for name, code in declared.items():
        if getattr(errors, name).exit_code != code:
            findings.append("round11: %s exit code changed from %d" % (name, code))
    with open(os.path.join(REPO, "README.md"), "r", encoding="utf-8") as handle:
        readme = handle.read()
    for name, code in declared.items():
        if "| %d |" % code not in readme:
            findings.append("round11: README exit-code table missing %d (%s)" % (code, name))

    with open(os.path.join(REPO, "pyproject.toml"), "r", encoding="utf-8") as handle:
        pyproject = handle.read()
    match = re.search(r'^version = "([^"]+)"', pyproject, re.M)
    if not match or match.group(1) != counterfact.__version__:
        findings.append("round11: pyproject version and __version__ disagree")

    shim = os.path.join(REPO, "setup.py")
    if not os.path.isfile(shim):
        findings.append("round11: setup.py compatibility shim is missing")
    else:
        with open(shim, "r", encoding="utf-8") as handle:
            shim_text = handle.read()
        shim_version = re.search(r'version="([^"]+)"', shim_text)
        if not shim_version or shim_version.group(1) != counterfact.__version__:
            findings.append("round11: setup.py shim version drifted from __version__")
        if 'counterfact = counterfact.cli:main' not in shim_text:
            findings.append("round11: setup.py shim lost the console entry point")

    for module in pkgutil.iter_modules([os.path.join(REPO, "counterfact")]):
        try:
            importlib.import_module("counterfact." + module.name)
        except Exception as exc:
            findings.append(
                "round11: module counterfact.%s failed to import: %s"
                % (module.name, type(exc).__name__)
            )
    return findings


# ---------------------------------------------------------------------------
# Round 12 — release candidate: CLI exit matrix, install smoke, final integrity
# ---------------------------------------------------------------------------
def round_12():
    findings = []
    import counterfact
    from counterfact.state import save_snapshot
    from helpers import make_snapshot, write_script

    with tempfile.TemporaryDirectory() as workdir:
        write_script(workdir, "check.py", "print('ok')\n")
        good = os.path.join(workdir, "g.json")
        bad = os.path.join(workdir, "b.json")
        save_snapshot(make_snapshot({"TZ": "UTC"}), good)
        save_snapshot(make_snapshot({"TZ": "Asia/Shanghai"}), bad)

        cases = [
            (cli("run", "--good", good, "--bad", bad,
                 "--", sys.executable, "check.py"), 3, "missing --yes"),
            (cli("run", "--yes"), 2, "missing required arguments"),
            (cli("compare", "--good", good, "--bad", bad), 0, "read-only compare"),
            (cli("run", "--good", good, "--bad", bad, "--yes",
                 "--workdir", workdir, "--expect-fail-text", "never-appears",
                 "--", sys.executable, "check.py"), 1, "no reproduction"),
        ]
        for proc, expected, label in cases:
            if proc.returncode != expected:
                findings.append(
                    "round12: %s exited %d, expected %d"
                    % (label, proc.returncode, expected)
                )

        demo = cli("demo")
        if demo.returncode != 0 or "CONFIRMED" not in demo.stdout:
            findings.append("round12: demo did not confirm the planted cause")

        install_dir = os.path.join(workdir, "site")
        installed = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps",
             "--no-build-isolation", "--quiet", "--target", install_dir, "."],
            cwd=REPO, env=ENV, capture_output=True, text=True, timeout=180,
        )
        if installed.returncode != 0:
            findings.append(
                "round12: clean install failed: %s" % installed.stderr[-300:]
            )
        else:
            smoke = subprocess.run(
                [sys.executable, "-c",
                 "import counterfact; print(counterfact.__version__)"],
                cwd=workdir,
                env={**ENV, "PYTHONPATH": install_dir},
                capture_output=True, text=True, timeout=60,
            )
            if smoke.returncode != 0 or smoke.stdout.strip() != counterfact.__version__:
                findings.append(
                    "round12: installed package smoke test failed: %s"
                    % smoke.stderr[-200:]
                )

    if counterfact.__version__ != "0.1.0":
        findings.append(
            "round12: unexpected version drift %r" % counterfact.__version__
        )
    return findings


ROUNDS = [
    ("Static analysis, supply chain, protocols", round_1),
    ("Full unit / integration test suite", round_2),
    ("Adversarial parser fuzzing", round_3),
    ("Security controls and secret hygiene", round_4),
    ("Algorithm correctness and status reachability", round_5),
    ("Resource bounds, process groups, cleanup", round_6),
    ("CI / UX / documentation contract", round_7),
    ("Equivalence, packaging, dogfooding", round_8),
    ("Planted-fixture recovery benchmark", round_9),
    ("Noise injection / false-cause resistance", round_10),
    ("Documentation and version consistency", round_11),
    ("Release-candidate CLI and install smoke", round_12),
]


def main() -> int:
    results = []
    for index, (name, fn) in enumerate(ROUNDS, 1):
        started = time.monotonic()
        try:
            findings = fn()
        except Exception as exc:  # a broken round is a failure, not a pass
            findings = ["harness error: %s: %s" % (type(exc).__name__, str(exc)[:200])]
        results.append(
            {
                "round": index,
                "name": name,
                "verdict": "PASS" if not findings else "REVISE",
                "findings": findings,
                "elapsed_s": round(time.monotonic() - started, 2),
            }
        )
        print("Round %d  %-6s  %s" % (index, results[-1]["verdict"], name))
        for item in findings:
            print("    - " + item.replace("\n", " ")[:300])
    with open(LOG_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    failed = sum(1 for r in results if r["verdict"] != "PASS")
    print("\n%d/%d rounds passed. Evidence: %s" % (len(ROUNDS) - failed, len(ROUNDS), LOG_PATH))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
