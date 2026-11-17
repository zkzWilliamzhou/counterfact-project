import os
import sys
import tempfile
import time
import unittest

from counterfact.oracle import Oracle
from counterfact.types import Budget, Factor
from helpers import make_runner, make_snapshot, make_spec, write_script


class RunnerTests(unittest.TestCase):
    def test_basic_pass_and_output_capture(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "print('hello-from-child')\n")
            runner = make_runner(make_spec("check.py", workdir), [])
            exp = runner.run(())
            self.assertEqual(exp.outcome, "PASS")
            self.assertEqual(exp.exit_code, 0)
            self.assertIn("hello-from-child", exp.stdout_excerpt)
            self.assertEqual(runner.executions, 1)

    def test_environment_is_constructed_not_inherited(self):
        previous = os.environ.get("LD_PRELOAD")
        os.environ["LD_PRELOAD"] = "/tmp/definitely-malicious.so"
        try:
            with tempfile.TemporaryDirectory() as workdir:
                write_script(
                    workdir, "check.py",
                    "import os\nprint('LD_PRELOAD=' + os.environ.get('LD_PRELOAD','MISSING'))\n"
                    "print('HOME_IS_SET=' + str(bool(os.environ.get('HOME'))))\n",
                )
                exp = make_runner(make_spec("check.py", workdir), []).run(())
                self.assertIn("LD_PRELOAD=MISSING", exp.stdout_excerpt)
                self.assertIn("HOME_IS_SET=True", exp.stdout_excerpt)
        finally:
            if previous is None:
                del os.environ["LD_PRELOAD"]
            else:
                os.environ["LD_PRELOAD"] = previous

    def test_factor_application_changes_only_that_factor(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "import os\nprint('TZ=' + os.environ.get('TZ','MISSING'))\n")
            good = make_snapshot({"TZ": "UTC"})
            factor = Factor("TZ", "UTC", "Pacific/Kiritimati", "env")
            runner = make_runner(make_spec("check.py", workdir, good), [factor])
            self.assertIn("TZ=UTC", runner.run(()).stdout_excerpt)
            self.assertIn("TZ=Pacific/Kiritimati", runner.run(("TZ",)).stdout_excerpt)

    def test_timeout_is_unresolved_not_failure_and_is_fast(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "import time\ntime.sleep(30)\n")
            runner = make_runner(
                make_spec("check.py", workdir), [], budget=Budget(timeout_s=0.5, max_runs=5)
            )
            started = time.monotonic()
            exp = runner.run(())
            elapsed = time.monotonic() - started
            self.assertTrue(exp.timed_out)
            self.assertEqual(exp.outcome, "UNRESOLVED")
            self.assertLess(elapsed, 8.0)

    def test_output_is_capped(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "import sys\nsys.stdout.write('x'*200000)\n")
            runner = make_runner(
                make_spec("check.py", workdir), [], budget=Budget(max_output_bytes=1024)
            )
            exp = runner.run(())
            self.assertTrue(exp.truncated)
            self.assertLessEqual(len(exp.stdout_excerpt), 1024)

    def test_workspace_cleanup_and_symlink_skipping(self):
        with tempfile.TemporaryDirectory() as workdir:
            outside = os.path.join(tempfile.gettempdir(), "counterfact-outside-marker")
            write_script(workdir, "check.py", "print('ok')\n")
            link = os.path.join(workdir, "evil")
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError):
                pass
            runner = make_runner(make_spec("check.py", workdir), [])
            exp = runner.run(())
            self.assertEqual(exp.outcome, "PASS")
            self.assertFalse(os.path.exists(outside))
            self.assertEqual(len(os.listdir(workdir)) >= 1, True)

    def test_fingerprint_oracle_never_promotes_a_wrong_failure(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "import sys\nprint('unrelated crash', file=sys.stderr)\nsys.exit(2)\n")
            runner = make_runner(
                make_spec("check.py", workdir), [],
                oracle=Oracle(mode="fingerprint", expect_fail_text="THE_TARGET"),
            )
            self.assertEqual(runner.run(()).outcome, "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
