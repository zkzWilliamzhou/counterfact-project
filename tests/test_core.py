import json
import os
import sys
import tempfile
import unittest

from counterfact.errors import ConfigError, SafetyError
from counterfact.minimize import (
    STATUS_BASELINE_FAILS,
    STATUS_BUDGET_EXCEEDED,
    STATUS_EMPTY_DIFF,
    STATUS_NO_REPRODUCTION,
    STATUS_OK,
    search,
    split,
)
from counterfact.oracle import Oracle
from counterfact.proof import verify
from counterfact.report import render_github, render_json, render_sarif, render_text
from counterfact.safety import (
    REDACTED,
    loads_bounded,
    redact,
    sanitize_output,
    validate_env_key,
    validate_env_value,
    validate_relpath,
    validate_tool_path,
)
from counterfact.state import (
    diff_states,
    load_snapshot,
    save_snapshot,
    snapshot_from_obj,
    unreplayable_warnings,
)
from counterfact.types import (
    STATUS_CONFIRMED,
    STATUS_FLAKY,
    Finding,
    Factor,
)
from helpers import FakeRunner, make_snapshot


class SafetyTests(unittest.TestCase):
    def test_denied_environment_keys_are_refused(self):
        for name in ("LD_PRELOAD", "PYTHONPATH", "BASH_ENV", "IFS", "BASH_FUNC_x%%"):
            with self.subTest(name=name), self.assertRaises(SafetyError):
                validate_env_key(name)

    def test_valid_environment_keys(self):
        for name in ("TZ", "LANG", "CI", "NODE_ENV", "PYTHONHASHSEED"):
            self.assertEqual(validate_env_key(name), name)

    def test_control_characters_in_values(self):
        with self.assertRaises(SafetyError):
            validate_env_value("TZ", "UTC\x00evil")
        with self.assertRaises(SafetyError):
            validate_env_value("TZ", "UTC\nevil")

    def test_bounded_json_rejects_duplicate_keys(self):
        with self.assertRaises(SafetyError):
            loads_bounded(b'{"a": 1, "a": 2}')

    def test_bounded_json_rejects_deep_nesting(self):
        payload = json.dumps([[[[[[[[[[[[[[["x"]]]]]]]]]]]]]]]).encode()
        with self.assertRaises(SafetyError):
            loads_bounded(payload)

    def test_bounded_json_rejects_long_strings_and_huge_documents(self):
        with self.assertRaises(SafetyError):
            loads_bounded(b'{"a":"' + b"x" * 5000 + b'"}')
        with self.assertRaises(SafetyError):
            loads_bounded(b" " * (300 * 1024))

    def test_bounded_json_rejects_invalid_utf8(self):
        with self.assertRaises(SafetyError):
            loads_bounded(b'{"a":"\xff"}')

    def test_redaction(self):
        self.assertEqual(redact("whatever", "API_KEY"), REDACTED)
        self.assertIn(REDACTED, redact("ghp_abcdefghijklmnopqrstuvwxyz0123456789"))
        self.assertEqual(redact("hello world", "GREETING"), "hello world")

    def test_output_sanitization(self):
        text, digest, truncated = sanitize_output(b"\x1b[31mhello\x00world", 100)
        self.assertEqual(text, "helloworld")
        self.assertEqual(len(digest), 64)
        self.assertFalse(truncated)
        _, _, truncated = sanitize_output(b"x" * 100, 10)
        self.assertTrue(truncated)

    def test_relpath_guards(self):
        for value in ("../etc/passwd", "a/../../b", "/etc/passwd", "-oops", "$(id)", "a\\b"):
            with self.subTest(value=value), self.assertRaises(SafetyError):
                validate_relpath(value)
        self.assertEqual(validate_relpath("src/main.py"), "src/main.py")

    def test_tool_paths_must_be_absolute_executables(self):
        with self.assertRaises(SafetyError):
            validate_tool_path("python3")
        self.assertTrue(os.path.isabs(validate_tool_path(sys.executable)))


class StateTests(unittest.TestCase):
    def test_snapshot_roundtrip(self):
        snap = make_snapshot({"TZ": "UTC", "@UMASK": "022"})
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "s.json")
            save_snapshot(snap, path)
            loaded = load_snapshot(path)
            self.assertEqual(dict(loaded.factors), dict(snap.factors))
            self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")

    def test_unknown_keys_and_bad_schema_are_rejected(self):
        with self.assertRaises(ConfigError):
            snapshot_from_obj({"schema_version": 1, "factors": {}, "surprise": 1})
        with self.assertRaises(ConfigError):
            snapshot_from_obj({"schema_version": 99, "factors": {}})

    def test_dangerous_factor_is_rejected(self):
        with self.assertRaises((SafetyError, ConfigError)):
            snapshot_from_obj({"schema_version": 1, "factors": {"LD_PRELOAD": "/x"}})

    def test_non_string_factor_rejected(self):
        with self.assertRaises(ConfigError):
            snapshot_from_obj({"schema_version": 1, "factors": {"TZ": 5}})

    def test_diff_includes_changed_added_removed_and_ignores_metadata(self):
        good = make_snapshot({"TZ": "UTC", "KEEP": "1", "ONLY_GOOD": "x"}, {"platform": "linux"})
        bad = make_snapshot({"TZ": "Asia/Shanghai", "KEEP": "1", "ONLY_BAD": "y"}, {"platform": "darwin"})
        factors = {f.name: f for f in diff_states(good, bad)}
        self.assertEqual(set(factors), {"TZ", "ONLY_GOOD", "ONLY_BAD"})
        self.assertEqual(factors["TZ"].good, "UTC")
        self.assertEqual(factors["TZ"].bad, "Asia/Shanghai")
        self.assertIsNone(factors["ONLY_BAD"].good)
        self.assertIsNone(factors["ONLY_GOOD"].bad)
        self.assertTrue(unreplayable_warnings(good, bad))

    def test_capture_is_an_allowlist_not_a_snapshot_of_everything(self):
        os.environ["COUNTERFACT_TEST_SECRET"] = "ghp_should_not_be_captured"
        try:
            from counterfact.state import capture

            snap = capture()
            self.assertNotIn("COUNTERFACT_TEST_SECRET", snap.factors)
            self.assertIn("TZ", snap.factors) if "TZ" in os.environ else None
            self.assertIn("PATH", snap.factors)
        finally:
            del os.environ["COUNTERFACT_TEST_SECRET"]


class OracleTests(unittest.TestCase):
    def test_timeout_is_never_failure(self):
        oracle = Oracle()
        self.assertEqual(
            oracle.classify(exit_code=None, timed_out=True, error="", stdout_excerpt="", stderr_excerpt=""),
            "UNRESOLVED",
        )

    def test_fingerprint_requires_signature(self):
        oracle = Oracle(mode="fingerprint", expect_fail_text="TIMEOUT")
        self.assertEqual(
            oracle.classify(exit_code=1, timed_out=False, error="", stdout_excerpt="", stderr_excerpt="other crash"),
            "UNRESOLVED",
        )
        self.assertEqual(
            oracle.classify(exit_code=1, timed_out=False, error="", stdout_excerpt="", stderr_excerpt="TIMEOUT"),
            "FAIL",
        )

    def test_invalid_oracle_configuration(self):
        with self.assertRaises(ConfigError):
            Oracle(mode="fingerprint")
        with self.assertRaises(ConfigError):
            Oracle(mode="exit", expect_fail_text="x")


class MinimizeTests(unittest.TestCase):
    def test_split_is_ordered_and_complete(self):
        chunks = split(list("ABCDEFG"), 3)
        self.assertEqual(tuple("".join(c) for c in chunks), ("ABC", "DE", "FG"))

    def test_finds_single_planted_factor(self):
        factors = [Factor(n, "0", "1") for n in "ABCDEFGH"]
        result = search(factors, FakeRunner(lambda a: "FAIL" if "E" in a else "PASS"))
        self.assertEqual(result.status, STATUS_OK)
        self.assertEqual(result.minimal, ("E",))

    def test_finds_two_factor_interaction(self):
        factors = [Factor(n, "0", "1") for n in "ABCDEFGH"]
        result = search(
            factors, FakeRunner(lambda a: "FAIL" if ("A" in a and "B" in a) else "PASS")
        )
        self.assertEqual(result.status, STATUS_OK)
        self.assertEqual(set(result.minimal), {"A", "B"})

    def test_anchor_failures_refuse_to_invent_a_cause(self):
        factors = [Factor(n, "0", "1") for n in "ABCDE"]
        self.assertEqual(
            search(factors, FakeRunner(lambda a: "FAIL")).status, STATUS_BASELINE_FAILS
        )
        self.assertEqual(
            search(factors, FakeRunner(lambda a: "PASS")).status, STATUS_NO_REPRODUCTION
        )
        self.assertEqual(search([], FakeRunner(lambda a: "PASS")).status, STATUS_EMPTY_DIFF)

    def test_budget_exhaustion_is_reported_as_partial(self):
        factors = [Factor(n, "0", "1") for n in "ABCDEFGH"]
        result = search(factors, FakeRunner(lambda a: "FAIL" if "E" in a else "PASS", max_calls=3))
        self.assertEqual(result.status, STATUS_BUDGET_EXCEEDED)
        self.assertTrue(result.partial)

    def test_unresolved_observations_are_counted_not_silently_dropped(self):
        factors = [Factor(n, "0", "1") for n in "ABCDE"]
        def predicate(applied):
            if len(applied) == 2:
                return "UNRESOLVED"
            return "FAIL" if "C" in applied else "PASS"
        result = search(factors, FakeRunner(predicate))
        self.assertGreater(result.unresolved, 0)
        self.assertTrue(any("UNRESOLVED" in w for w in result.warnings))


class ProofTests(unittest.TestCase):
    def test_deterministic_command_is_confirmed(self):
        result = verify(FakeRunner(lambda a: "FAIL" if "E" in a else "PASS"), ("E",), 3)
        self.assertEqual(result.status, STATUS_CONFIRMED)
        self.assertEqual(result.replication, (7, 7))

    def test_flaky_command_is_never_confirmed(self):
        class Flaky(FakeRunner):
            def __init__(self):
                super().__init__(lambda a: "PASS")
                self.calls = 0

            def run(self, applied, use_cache=True):
                self.calls += 1
                outcome = "FAIL" if self.calls % 2 else "PASS"
                return super().run(applied, use_cache) if False else self._make(applied, outcome)

            def _make(self, applied, outcome):
                from counterfact.types import Experiment

                exp = Experiment(
                    index=len(self.log) + 1, applied=tuple(applied), outcome=outcome,
                    exit_code=1 if outcome == "FAIL" else 0, timed_out=False,
                    truncated=False, duration_ms=1, stdout_sha256="", stderr_sha256="",
                    stdout_excerpt="", stderr_excerpt="",
                )
                self.log.append(exp)
                return exp

        result = verify(Flaky(), ("E",), 3)
        self.assertEqual(result.status, STATUS_FLAKY)


class ReportTests(unittest.TestCase):
    def _finding(self):
        return Finding(
            status=STATUS_CONFIRMED,
            factors=("TZ",),
            replication=(7, 7),
            experiments=[],
            warnings=["token ghp_abcdefghijklmnopqrstuvwxyz0123456789 must not leak"],
            oracle={"mode": "fingerprint", "expect_fail_text": "TIMEOUT"},
        )

    def test_json_shape(self):
        data = json.loads(render_json(self._finding(), {"inert": True}))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["status"], STATUS_CONFIRMED)
        self.assertIn("scope_notice", data)

    def test_sarif_is_valid_minimal_document(self):
        data = json.loads(render_sarif(self._finding()))
        self.assertEqual(data["version"], "2.1.0")
        self.assertEqual(data["runs"][0]["results"][0]["ruleId"], "CF001")

    def test_github_annotations(self):
        self.assertTrue(render_github(self._finding()).startswith("::notice"))

    def test_secrets_are_redacted_in_every_renderer(self):
        for renderer in (
            render_text(self._finding(), {}, [Factor("TZ", "UTC", "UTC")]),
            render_json(self._finding(), {}),
            render_sarif(self._finding()),
            render_github(self._finding()),
        ):
            self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz0123456789", renderer)


if __name__ == "__main__":
    unittest.main()
