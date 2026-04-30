from __future__ import annotations

from pathlib import Path


REQUIRED_RELEASE_PATHS = (
    "dataset.yaml",
    "images",
    "labels",
    "splits/train.txt",
    "splits/val.txt",
    "splits/test.txt",
    "manifest.json",
    "provenance",
)


def validate_release(release_root: str | Path) -> None:
    root = Path(release_root)
    for relative in REQUIRED_RELEASE_PATHS:
        path = root / relative
        if not path.exists():
            raise FileNotFoundError(f"Missing required release path: {path}")
