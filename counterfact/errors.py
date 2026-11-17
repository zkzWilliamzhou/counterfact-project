"""Error types with a stable, documented exit-code contract.

0  finding confirmed (or reported as probable)
1  no confirmed finding / inconclusive / flaky / budget exhausted
2  usage or configuration error
3  safety refusal (explicit opt-in missing, dangerous input rejected)
4  internal error
"""

from __future__ import annotations


class CounterfactError(Exception):
    """Base class. Subclasses declare their process exit code."""

    exit_code = 4


class UsageError(CounterfactError):
    exit_code = 2


class ConfigError(CounterfactError):
    exit_code = 2


class SafetyError(CounterfactError):
    exit_code = 3


class BudgetExceeded(CounterfactError):
    exit_code = 1
