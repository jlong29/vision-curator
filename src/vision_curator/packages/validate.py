from __future__ import annotations

from pathlib import Path
from typing import Any

from vision_curator.common.manifests import read_json
from vision_curator.common.models import ClipRecord


REQUIRED_CLIP_FILES = ("clip.mp4", "clip_manifest.json", "detections.parquet", "tracks.parquet")
PROVENANCE_FIELDS = (
    "run_id",
    "runtime_id",
    "runtime",
    "tracker_id",
    "tracker",
    "detector_id",
    "detector",
    "model_id",
    "model_version",
    "source_node_id",
    "edge_node_id",
    "package_state",
    "completion_state",
    "created_at",
    "completed_at",
)


def validate_phase2_package(phase2_root: str | Path) -> dict[str, Any]:
    root = Path(phase2_root)
    if not root.exists():
        raise FileNotFoundError(f"Phase 2 package does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Phase 2 package is not a directory: {root}")

    manifest_path = root / "manifest.json"
    clips_dir = root / "clips"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing required root manifest: {manifest_path}")
    if not clips_dir.is_dir():
        raise FileNotFoundError(f"Missing required clips directory: {clips_dir}")

    manifest = read_json(manifest_path)
    package_id = manifest.get("package_id")
    if not isinstance(package_id, str) or not package_id:
        raise ValueError(f"Root manifest must include non-empty string field 'package_id': {manifest_path}")
    if "clips" not in manifest or not isinstance(manifest["clips"], list):
        raise ValueError(f"Root manifest must include list field 'clips': {manifest_path}")
    if not manifest["clips"]:
        raise ValueError(f"Root manifest clips list must not be empty: {manifest_path}")

    package_provenance = _provenance(manifest)
    expected_clip_ids = {_clip_id(item) for item in manifest["clips"]}
    clip_entries = {_clip_id(item): item for item in manifest["clips"]}
    actual_clip_dirs = {path.name for path in clips_dir.iterdir() if path.is_dir()}
    missing_dirs = sorted(expected_clip_ids - actual_clip_dirs)
    if missing_dirs:
        raise FileNotFoundError(f"Manifest clips missing directories under {clips_dir}: {missing_dirs}")

    clip_records: list[ClipRecord] = []
    for clip_id in sorted(expected_clip_ids):
        clip_dir = clips_dir / clip_id
        for filename in REQUIRED_CLIP_FILES:
            required = clip_dir / filename
            if not required.is_file():
                raise FileNotFoundError(f"Missing required clip file: {required}")
        clip_manifest = read_json(clip_dir / "clip_manifest.json")
        manifest_clip_id = clip_manifest.get("clip_id")
        if not isinstance(manifest_clip_id, str) or not manifest_clip_id:
            raise ValueError(f"Clip manifest must include non-empty string field 'clip_id': {clip_dir / 'clip_manifest.json'}")
        if manifest_clip_id != clip_id:
            raise ValueError(f"Clip manifest clip_id {manifest_clip_id!r} does not match directory {clip_id!r}")
        clip_provenance = {
            **package_provenance,
            **_provenance(clip_entries[clip_id] if isinstance(clip_entries[clip_id], dict) else {}),
            **_provenance(clip_manifest),
        }
        clip_records.append(
            ClipRecord(
                package_id=package_id,
                clip_id=clip_id,
                source_path=str(root),
                clip_path=str(clip_dir / "clip.mp4"),
                manifest_path=str(clip_dir / "clip_manifest.json"),
                detections_path=str(clip_dir / "detections.parquet"),
                tracks_path=str(clip_dir / "tracks.parquet"),
                run_id=str(clip_provenance.get("run_id", "")),
                provenance=clip_provenance,
            )
        )

    return {
        "package_id": package_id,
        "root": str(root),
        "manifest": manifest,
        "run_id": str(package_provenance.get("run_id", "")),
        "provenance": package_provenance,
        "clips": [clip.to_dict() for clip in clip_records],
    }


def _clip_id(item: Any) -> str:
    if isinstance(item, str) and item:
        return item
    if isinstance(item, dict) and isinstance(item.get("clip_id"), str) and item["clip_id"]:
        return item["clip_id"]
    raise ValueError(f"Manifest clips entries must be clip_id strings or objects with clip_id: {item!r}")


def _provenance(data: dict[str, Any]) -> dict[str, Any]:
    return {field: data[field] for field in PROVENANCE_FIELDS if field in data}
