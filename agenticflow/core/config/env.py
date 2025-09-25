"""Environment loader for AgenticFlow.

Loads a .env file from the project root (or nearest parent) so that
API keys like GROQ_API_KEY and settings like AGENTICFLOW_LLM_PROVIDER
are available during development.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv, find_dotenv


def load_env(dotenv_path: Optional[Path] = None) -> None:
    """Load environment variables from a .env file.

    - If dotenv_path is provided and exists, use it.
    - Otherwise, search upwards from CWD for a .env file.
    - Do nothing if already loaded.
    """
    # Avoid reloading repeatedly
    if os.getenv("AGENTICFLOW_ENV_LOADED"):
        return

    path = None
    if dotenv_path and Path(dotenv_path).exists():
        path = str(dotenv_path)
    else:
        found = find_dotenv(usecwd=True)
        if found:
            path = found

    if path:
        load_dotenv(path)  # does not override existing env vars by default

    os.environ["AGENTICFLOW_ENV_LOADED"] = "1"
