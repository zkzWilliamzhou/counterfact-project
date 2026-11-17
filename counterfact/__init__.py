"""counterfact — a counterfactual debugger for environment-dependent command failures.

Public API is intentionally tiny. Everything else is an implementation detail.
"""

from .errors import BudgetExceeded, ConfigError, CounterfactError, SafetyError, UsageError
from .types import SCHEMA_VERSION, Experiment, Factor, Finding, Snapshot

__all__ = [
    "SCHEMA_VERSION",
    "Experiment",
    "Factor",
    "Finding",
    "Snapshot",
    "CounterfactError",
    "ConfigError",
    "SafetyError",
    "UsageError",
    "BudgetExceeded",
]

__version__ = "0.1.0"
