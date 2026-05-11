from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vision_curator.common.env import expand_env_value


def load_simple_config(path: str | Path) -> dict[str, Any]:
    """Load JSON or a small YAML subset used by the default configs."""
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected object config in {path}")
        return data
    return _parse_simple_yaml(text, str(path))


def _parse_simple_yaml(text: str, source: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise ValueError(f"Unsupported indentation in {source}:{line_no}")
        key, sep, value = raw.strip().partition(":")
        if not sep:
            raise ValueError(f"Expected key/value in {source}:{line_no}")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        current = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            current[key] = child
            stack.append((indent, child))
        else:
            current[key] = _parse_scalar(value.strip())
    return root


def _parse_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if value.startswith('"') and value.endswith('"'):
        return expand_env_value(value[1:-1])
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return expand_env_value(value)
