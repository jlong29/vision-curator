from __future__ import annotations

import os
import re
from pathlib import Path


SOURCE_HINT = "Run: source ~/openclaw-env.sh"
_ENV_PATTERN = re.compile(r"\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set. {SOURCE_HINT}")
    return value


def openclaw_curator_store() -> str:
    return require_env("OPENCLAW_CURATOR_STORE")


def expand_env_value(value: str) -> str:
    for match in _ENV_PATTERN.finditer(value):
        name = match.group("braced") or match.group("plain")
        if name and name.startswith("OPENCLAW_") and not os.environ.get(name):
            raise RuntimeError(f"Required environment variable {name} is not set. {SOURCE_HINT}")
    return os.path.expandvars(value)


def path_from_arg_or_env(value: str | None, env_name: str) -> Path:
    return Path(value if value else require_env(env_name))
