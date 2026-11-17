import os
import subprocess
import sys
import tempfile
import unittest

from counterfact.state import save_snapshot
from helpers import make_snapshot, write_script

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL_TEXT = "FAIL: timezone-sensitive branch"

TZ_SCRIPT = (
    "import os, sys\n"
    "if os.environ.get('TZ') == 'UTC':\n"
    "    print('FAIL: timezone-sensitive branch', file=sys.stderr)\n"
    "    sys.exit(1)\n"
    "print('ok')\n"
)


def run_cli(*args, timeout=180):
    return subprocess.run(
        [sys.executable, "-m", "counterfact", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "PYTHONPATH": REPO},
    )


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workdir = self.tmp.name
        write_script(self.workdir, "check.py", TZ_SCRIPT)
        good = make_snapshot(
            {"TZ": "Asia/Shanghai", "LANG": "C.UTF-8", "CI": "false", "@UMASK": "022"}
        )
        bad = make_snapshot(
            {"TZ": "UTC", "LANG": "C.UTF-8", "CI": "true", "@UMASK": "022"}
        )
        self.good = os.path.join(self.workdir, "good.json")
        self.bad = os.path.join(self.workdir, "bad.json")
        save_snapshot(good, self.good)
        save_snapshot(bad, self.bad)

    def tearDown(self):
        self.tmp.cleanup()

    def test_plan_is_inert_and_executes_nothing(self):
        marker = os.path.join(self.workdir, "EXECUTED")
        write_script(
            self.workdir, "marker.py",
            "open(%r, 'w').write('ran')\n" % marker,
        )
        proc = run_cli(
            "plan", "--good", self.good, "--bad", self.bad,
            "--", sys.executable, "marker.py",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(os.path.exists(marker), "plan executed the command")
        self.assertIn("inert", proc.stdout)

    def test_run_without_yes_is_a_safety_refusal(self):
        proc = run_cli(
            "run", "--good", self.good, "--bad", self.bad,
            "--", sys.executable, "check.py",
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("--yes", proc.stderr)

    def test_compare_is_read_only(self):
        proc = run_cli("compare", "--good", self.good, "--bad", self.bad)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("HYPOTHESES", proc.stdout)
        self.assertIn("No command was executed", proc.stdout)

    def test_run_with_yes_confirms_and_exits_zero(self):
        proc = run_cli(
            "run", "--good", self.good, "--bad", self.bad, "--yes",
            "--workdir", self.workdir, "--expect-fail-text", FAIL_TEXT,
            "--", sys.executable, "check.py",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CONFIRMED", proc.stdout)
        self.assertIn("TZ", proc.stdout)
        self.assertIn("1-minimal tested causal set", proc.stdout)

    def test_no_differences_is_inconclusive_exit_one(self):
        proc = run_cli(
            "run", "--good", self.good, "--bad", self.good, "--yes",
            "--workdir", self.workdir, "--expect-fail-text", FAIL_TEXT,
            "--", sys.executable, "check.py",
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("INCONCLUSIVE", proc.stdout)

    def test_demo_exits_zero(self):
        proc = run_cli("demo")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CONFIRMED", proc.stdout)

    def test_capture_writes_private_json(self):
        out = os.path.join(self.workdir, "captured.json")
        proc = run_cli("capture", "--out", out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(oct(os.stat(out).st_mode & 0o777), "0o600")

    def test_json_and_sarif_formats(self):
        for fmt, needle in (("json", '"schema_version"'), ("sarif", '"2.1.0"')):
            with self.subTest(fmt=fmt):
                proc = run_cli(
                    "run", "--good", self.good, "--bad", self.bad, "--yes",
                    "--workdir", self.workdir, "--expect-fail-text", FAIL_TEXT,
                    "--format", fmt, "--", sys.executable, "check.py",
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn(needle, proc.stdout)


if __name__ == "__main__":
    unittest.main()
