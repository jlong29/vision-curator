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
    if "release_family" in manifest:
        _validate_label_namespace_policy(manifest)


def _validate_label_namespace_policy(manifest: dict) -> None:
    train_namespaces = set(manifest.get("label_namespaces_used_for_train", []))
    forbidden_train_namespaces = set(manifest.get("forbidden_label_namespaces_for_train", []))
    release_family = manifest.get("release_family")
    if manifest.get("realistic_calibration_loop"):
        if "oracle_hidden" not in forbidden_train_namespaces:
            raise ValueError("Realistic calibration releases must forbid oracle_hidden for training")
        if "oracle_hidden" in train_namespaces:
            raise ValueError("Realistic calibration releases must not train from oracle_hidden")
    if manifest.get("oracle_upper_bound"):
        if release_family != "oracle_upper_bound":
            raise ValueError("Only oracle_upper_bound may set oracle_upper_bound=true")
        if manifest.get("realistic_calibration_loop"):
            raise ValueError("oracle_upper_bound must not be marked as a realistic calibration loop")
        if "oracle_hidden" not in train_namespaces:
            raise ValueError("oracle_upper_bound must train from oracle_hidden")
