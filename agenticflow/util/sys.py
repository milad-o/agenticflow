from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CommandResult:
    code: int
    stdout: str
    stderr: str


def run(cmd: List[str], *, timeout: Optional[float] = None) -> CommandResult:
    """Run a system command safely with optional timeout.

    This is a minimal helper; callers are responsible for redacting secrets in args.
    """
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return CommandResult(code=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except subprocess.TimeoutExpired as e:
        return CommandResult(code=124, stdout=e.stdout or "", stderr=e.stderr or "timeout")