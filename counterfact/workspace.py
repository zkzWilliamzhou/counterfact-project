"""Filesystem adapter: owns sandbox creation, bounded input copying and cleanup.

One adapter = a hypothetical seam. Two adapters (this one and ``process``) make
it a real one: the Runner can be reasoned about without either.
"""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
from typing import Optional

from .errors import SafetyError
from .safety import contained, ensure_private_dir, validate_relpath

MAX_COPY_FILES = 200
MAX_COPY_BYTES = 10 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024


class Workspace:
    def __init__(self, workdir: Optional[str]):
        self.path = ensure_private_dir(tempfile.mkdtemp(prefix="counterfact-"))
        self._workdir = os.path.realpath(workdir) if workdir else None
        self.stdout = os.path.join(self.path, ".cf-stdout")
        self.stderr = os.path.join(self.path, ".cf-stderr")

    def copy_inputs(self) -> None:
        src = self._workdir
        if not src:
            return
        if not os.path.isdir(src):
            raise SafetyError("workdir is not a directory")
        copied = 0
        total = 0
        for root, dirs, files in os.walk(src, followlinks=False):
            dirs[:] = [
                d for d in dirs
                if not os.path.islink(os.path.join(root, d))
            ]
            for filename in files:
                full = os.path.join(root, filename)
                rel = os.path.relpath(full, src).replace(os.sep, "/")
                validate_relpath(rel)
                st = os.lstat(full)
                if not stat.S_ISREG(st.st_mode):
                    continue
                if st.st_size > MAX_FILE_BYTES:
                    raise SafetyError("workdir file too large")
                copied += 1
                total += st.st_size
                if copied > MAX_COPY_FILES or total > MAX_COPY_BYTES:
                    raise SafetyError("workdir exceeds copy budget")
                dest = contained(self.path, os.path.join(self.path, rel))
                os.makedirs(os.path.dirname(dest), mode=0o700, exist_ok=True)
                with open(full, "rb") as reader, open(dest, "wb") as writer:
                    shutil.copyfileobj(reader, writer, 64 * 1024)
                os.chmod(dest, 0o600)

    def read_capped(self, path: str, cap: int) -> bytes:
        try:
            with open(path, "rb") as handle:
                return handle.read(cap + 1)
        except OSError:
            return b""

    def close(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)

    def __enter__(self) -> "Workspace":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
