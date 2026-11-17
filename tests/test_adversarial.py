import json
import os
import sys
import tempfile
import unittest

from counterfact.errors import ConfigError, SafetyError
from counterfact.safety import loads_bounded, validate_relpath
from counterfact.state import load_snapshot, snapshot_from_obj
from helpers import make_runner, make_spec, write_script
from counterfact.types import Budget


class AdversarialTests(unittest.TestCase):
    def _write(self, directory, name, body):
        path = os.path.join(directory, name)
        with open(path, "wb") as handle:
            handle.write(body)
        return path

    def test_malicious_snapshot_with_loader_variable_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(
                directory, "evil.json",
                b'{"schema_version":1,"factors":{"LD_PRELOAD":"/tmp/x.so"},"metadata":{}}',
            )
            with self.assertRaises((SafetyError, ConfigError)):
                load_snapshot(path)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "dup.json", b'{"schema_version":1,"schema_version":1}')
            with self.assertRaises((SafetyError, ConfigError)):
                load_snapshot(path)

    def test_oversized_and_control_character_values_rejected(self):
        oversized = {"schema_version": 1, "factors": {"TZ": "x" * 5000}, "metadata": {}}
        with self.assertRaises((SafetyError, ConfigError)):
            snapshot_from_obj(oversized)
        with self.assertRaises((SafetyError, ConfigError)):
            snapshot_from_obj(
                {"schema_version": 1, "factors": {"TZ": "UTC\x00injected"}, "metadata": {}}
            )

    def test_option_injection_and_unicode_dashes_in_paths(self):
        for value in ("--output=/etc/cron.d/x", "\u2013evil", "$(id)", "a/../b"):
            with self.subTest(value=value), self.assertRaises(SafetyError):
                validate_relpath(value)

    def test_path_traversal_in_factor_value_rejected(self):
        with self.assertRaises((SafetyError, ConfigError)):
            snapshot_from_obj(
                {"schema_version": 1, "factors": {"PATH": "/usr/bin:../../tmp"}, "metadata": {}}
            )

    def test_output_bomb_is_bounded(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(workdir, "check.py", "import sys\nsys.stdout.write('A'*500000)\n")
            runner = make_runner(
                make_spec("check.py", workdir), [], budget=Budget(max_output_bytes=512)
            )
            exp = runner.run(())
            self.assertTrue(exp.truncated)
            self.assertLessEqual(len(exp.stdout_excerpt), 512)

    def test_spawning_child_does_not_outlive_timeout(self):
        with tempfile.TemporaryDirectory() as workdir:
            write_script(
                workdir, "check.py",
                "import subprocess, sys, time\n"
                "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
                "time.sleep(30)\n",
            )
            runner = make_runner(
                make_spec("check.py", workdir), [], budget=Budget(timeout_s=0.5, max_runs=5)
            )
            exp = runner.run(())
            self.assertTrue(exp.timed_out)

    def test_config_loader_rejects_unknown_keys(self):
        from counterfact.config import load_config

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "cfg.json", b'{"typo_key": true}')
            with self.assertRaises((SafetyError, ConfigError)):
                load_config(path)

    def test_bounded_json_rejects_billion_laughs_style_aliases(self):
        # JSON has no aliases, but deeply nested duplicate structures must still
        # be bounded by node/depth limits.
        payload = {"x": [1] * 600}
        with self.assertRaises(SafetyError):
            loads_bounded(json.dumps(payload).encode())


if __name__ == "__main__":
    unittest.main()
