"""The oracle decides what counts as PASS, FAIL, or UNRESOLVED.

A timeout, a launcher error, or a failure that does not match the requested
fingerprint is NEVER classified as FAIL. This prevents "any failure" from being
mistaken for the failure the operator is trying to explain.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional

from .errors import ConfigError
from .types import FAIL, PASS, UNRESOLVED


@dataclasses.dataclass(frozen=True)
class Oracle:
    mode: str = "exit"                 # "exit" | "fingerprint"
    expect_fail_text: str = ""

    def __post_init__(self) -> None:
        if self.mode not in ("exit", "fingerprint"):
            raise ConfigError("oracle mode must be 'exit' or 'fingerprint'")
        if self.mode == "fingerprint" and not self.expect_fail_text:
            raise ConfigError("fingerprint mode requires --expect-fail-text")
        if self.mode == "exit" and self.expect_fail_text:
            raise ConfigError("--expect-fail-text requires fingerprint mode")
        if len(self.expect_fail_text) > 512:
            raise ConfigError("--expect-fail-text is too long")
        if any(ord(c) < 32 for c in self.expect_fail_text):
            raise ConfigError("control character in --expect-fail-text")

    def classify(
        self,
        *,
        exit_code: Optional[int],
        timed_out: bool,
        error: str,
        stdout_excerpt: str,
        stderr_excerpt: str,
    ) -> str:
        if timed_out or error or exit_code is None:
            return UNRESOLVED
        if exit_code == 0:
            return PASS
        if self.mode == "exit":
            return FAIL
        haystack = stdout_excerpt + "\n" + stderr_excerpt
        return FAIL if self.expect_fail_text in haystack else UNRESOLVED

    def to_dict(self) -> Dict[str, str]:
        return {"mode": self.mode, "expect_fail_text": self.expect_fail_text}

    def warnings(self) -> List[str]:
        if self.mode == "exit":
            return [
                "Oracle is 'exit': ANY non-zero exit counts as the target failure. "
                "Use --expect-fail-text to require a specific failure signature."
            ]
        return [
            "Oracle is 'fingerprint': a non-zero exit without the expected text is "
            "UNRESOLVED, not FAIL. Matching uses the first --max-output-bytes of output."
        ]
