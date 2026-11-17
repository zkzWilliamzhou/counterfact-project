"""The single seam between pure search/verification and the adapters.

``minimize`` and ``proof`` depend on this interface, not on ``Runner``. The
interface is the test surface: a fake observer exercises the entire algorithm
without a filesystem or a process.
"""

from __future__ import annotations

from typing import Protocol, Tuple, runtime_checkable

from .types import Experiment


@runtime_checkable
class Observer(Protocol):
    def run(self, applied: Tuple[str, ...], use_cache: bool = True) -> Experiment:
        ...
