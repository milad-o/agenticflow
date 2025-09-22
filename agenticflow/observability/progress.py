from __future__ import annotations

import contextvars
from typing import Awaitable, Callable, Optional

_ProgressEmitter = Callable[[str, dict], Awaitable[None]]
_current_emitter: contextvars.ContextVar[Optional[_ProgressEmitter]] = contextvars.ContextVar(
    "agenticflow_progress_emitter", default=None
)


def set_progress_emitter(emitter: Optional[_ProgressEmitter]) -> contextvars.Token:
    return _current_emitter.set(emitter)


def reset_progress_emitter(token: contextvars.Token) -> None:
    try:
        _current_emitter.reset(token)
    except Exception:
        pass


async def emit_progress(kind: str, data: dict) -> None:
    emitter = _current_emitter.get()
    if emitter is not None:
        try:
            await emitter(kind, data)
        except Exception:
            # Do not crash tools on progress failures
            pass