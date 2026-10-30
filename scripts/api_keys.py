"""Reading of API keys outside the code.

A key is never written in a notebook, a script or an output cell.
`get_api_key()` looks for it, in this order:

1. an environment variable of the operating system (e.g. defined in Windows
   with `setx OPENAI_API_KEY "..."`, which takes effect in new terminals);
2. the file `.env` at the root of the repository, created by the user from
   `.env.example` and excluded from version control by `.gitignore`.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"


def read_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    """Reads NAME=value lines; ignores blank lines and comments (#)."""
    path = Path(path)
    values = {}
    if not path.is_file():
        return values
    # utf-8-sig: Windows Notepad may save the file with a BOM
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def get_api_key(name: str, env_file: Path = ENV_FILE) -> str:
    """Returns the key `name`. The value is never printed, not even in the error message."""
    value = os.environ.get(name) or read_env_file(env_file).get(name)
    if not value:
        raise LookupError(
            f"API key '{name}' not found. Copy .env.example to .env at the root of the "
            f"repository and fill in {name}=..., or define the environment variable {name}."
        )
    return value
