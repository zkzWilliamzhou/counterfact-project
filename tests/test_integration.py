import os
import tempfile
import unittest

from counterfact.cli import _flow
from counterfact.config import DEFAULTS
from counterfact.types import STATUS_CONFIRMED, STATUS_PROBABLE
from helpers import make_snapshot, write_script


class IntegrationTests(unittest.TestCase):
    def test_two_factor_interaction_is_recovered_end_to_end(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(
                workdir, "check.py",
                "import os, sys\n"
                "if os.environ.get('TZ') == 'UTC' and os.environ.get('CI') == 'true':\n"
                "    print('FAIL: interaction branch', file=sys.stderr)\n"
                "    sys.exit(1)\n"
                "print('ok')\n",
            )
            good = make_snapshot(
                {
                    "TZ": "Asia/Shanghai", "CI": "false", "LANG": "C.UTF-8",
                    "TERM": "dumb", "PYTHONHASHSEED": "0", "@UMASK": "022",
                }
            )
            bad = make_snapshot(
                {
                    "TZ": "UTC", "CI": "true", "LANG": "C.UTF-8",
                    "TERM": "xterm", "PYTHONHASHSEED": "7", "@UMASK": "077",
                }
            )
            cfg = dict(DEFAULTS)
            cfg["workdir"] = workdir
            cfg["expect_fail_text"] = "FAIL: interaction branch"
            cfg["repeats"] = 3
            finding, plan, _ = _flow(good, bad, [__import__("sys").executable, "check.py"], cfg)
            self.assertIn(finding.status, (STATUS_CONFIRMED, STATUS_PROBABLE))
            self.assertEqual(set(finding.factors), {"TZ", "CI"})
            self.assertGreater(len(finding.experiments), 3)
            self.assertTrue(plan["inert"] is False or plan["inert"] is True)

    def test_no_reproduction_never_invents_a_cause(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "print('always fine')\n")
            good = make_snapshot({"TZ": "UTC"})
            bad = make_snapshot({"TZ": "Asia/Shanghai"})
            cfg = dict(DEFAULTS)
            cfg["workdir"] = workdir
            cfg["expect_fail_text"] = "never appears"
            finding, _, _ = _flow(good, bad, [__import__("sys").executable, "check.py"], cfg)
            self.assertEqual(finding.factors, ())
            self.assertNotIn(finding.status, (STATUS_CONFIRMED, STATUS_PROBABLE))


if __name__ == "__main__":
    unittest.main()
