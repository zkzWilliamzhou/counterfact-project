"""Process adapter: shell-free launch, resource limits and group termination.

The only place in the program that calls ``subprocess.Popen``.
"""

from __future__ import annotations

import dataclasses
import os
import signal
import subprocess
from typing import Mapping, Optional, Sequence

from .errors import SafetyError
from .types import Budget


@dataclasses.dataclass(frozen=True)
class ProcessResult:
    exit_code: Optional[int]
    timed_out: bool
    error: str


def child_setup(umask: int, output_cap: int, timeout_s: float):
    cap = output_cap

    def setup() -> None:
        os.umask(umask)
        try:
            import resource

            cpu = max(1, int(timeout_s) + 2)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
            # One byte beyond the report cap: the child stays bounded while the
            # parent can still *observe* that truncation happened.
            resource.setrlimit(resource.RLIMIT_FSIZE, (cap + 1, cap + 1))
            resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
            # RLIMIT_AS is deliberately not set: it breaks legitimate
            # interpreters even when the workload is small.
        except Exception:
            pass

    return setup


def kill_group(proc: subprocess.Popen) -> None:
    try:
        if hasattr(os, "killpg"):
            os.killpg(proc.pid, signal.SIGTERM)
        else:
            proc.terminate()
        try:
            proc.wait(timeout=1.0)
            return
        except subprocess.TimeoutExpired:
            pass
        if hasattr(os, "killpg"):
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            proc.kill()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            pass
    except (ProcessLookupError, OSError):
        pass


def execute(
    argv: Sequence[str],
    env: Mapping[str, str],
    cwd: str,
    umask: int,
    budget: Budget,
    stdout_path: str,
    stderr_path: str,
) -> ProcessResult:
    timed_out = False
    error = ""
    exit_code: Optional[int] = None
    try:
        with open(stdout_path, "wb") as fo, open(stderr_path, "wb") as fe:
            proc = subprocess.Popen(
                list(argv),
                cwd=cwd,
                env=dict(env),
                stdin=subprocess.DEVNULL,
                stdout=fo,
                stderr=fe,
                shell=False,
                start_new_session=True,
                preexec_fn=child_setup(umask, budget.max_output_bytes, budget.timeout_s),
            )
            try:
                exit_code = proc.wait(timeout=budget.timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                kill_group(proc)
    except (SafetyError, OSError, ValueError) as exc:
        error = "%s: %s" % (type(exc).__name__, str(exc)[:200])
    return ProcessResult(exit_code=exit_code, timed_out=timed_out, error=error)
