from __future__ import annotations

from pathlib import Path

from vision_curator.common.manifests import read_json, read_jsonl


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
    manifest = read_json(root / "manifest.json")
    for field in ("source_packages", "annotation_status"):
        if field not in manifest:
            raise ValueError(f"Release manifest missing required field: {field}")
    source_packages = read_jsonl(root / "provenance" / "source_packages.jsonl")
    if manifest["source_packages"] != source_packages:
        raise ValueError("Release manifest source_packages must match provenance/source_packages.jsonl")
