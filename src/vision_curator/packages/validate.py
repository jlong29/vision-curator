from __future__ import annotations

from pathlib import Path
from typing import Any

from vision_curator.common.manifests import read_json
from vision_curator.common.models import ClipRecord


REQUIRED_CLIP_FILES = ("clip.mp4", "clip_manifest.json", "detections.parquet", "tracks.parquet")
PROVENANCE_FIELDS = (
    "dataset_source",
    "activity",
    "package_type",
    "run_id",
    "vision_api_job_id",
    "runtime_id",
    "runtime",
    "tracker_id",
    "tracker",
    "tracker_backend",
    "tracker_config_hash",
    "detector_id",
    "detector",
    "detector_backend",
    "model_id",
    "model_version",
    "model_profile",
    "model_artifact_version",
    "producer_repo",
    "source_node_id",
    "edge_node_id",
    "source_sequence_id",
    "source_camera_id",
    "source_frame_map_path",
    "frame_stride",
    "detection_confidence_threshold",
    "nms_threshold",
    "package_state",
    "completion_state",
    "created_at",
    "completed_at",
)
EGOHUMANS_REQUIRED_PACKAGE_FIELDS = (
    "dataset_source",
    "activity",
    "package_type",
    "producer_repo",
    "model_profile",
    "model_artifact_version",
    "detector_backend",
    "tracker_backend",
    "tracker_config_hash",
    "frame_stride",
    "detection_confidence_threshold",
    "nms_threshold",
)
EGOHUMANS_REQUIRED_CLIP_FIELDS = (
    "source_sequence_id",
    "source_camera_id",
    "start_frame_idx",
    "end_frame_idx",
    "fps",
    "width",
    "height",
    "frame_count",
    "source_frame_map_path",
    "detections_path",
    "tracks_path",
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
    if manifest.get("dataset_source") == "egohumans":
        _require_keys(manifest, EGOHUMANS_REQUIRED_PACKAGE_FIELDS, manifest_path)

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
        if manifest.get("dataset_source") == "egohumans":
            _require_fields(clip_manifest, EGOHUMANS_REQUIRED_CLIP_FIELDS, clip_dir / "clip_manifest.json")
            _require_relative_file(clip_dir, clip_manifest["source_frame_map_path"], "source frame map")
        manifest_clip_id = clip_manifest.get("clip_id", clip_manifest.get("package_clip_id"))
        if not isinstance(manifest_clip_id, str) or not manifest_clip_id:
            raise ValueError(
                "Clip manifest must include non-empty string field 'clip_id' or "
                f"'package_clip_id': {clip_dir / 'clip_manifest.json'}"
            )
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
    if isinstance(item, dict) and isinstance(item.get("package_clip_id"), str) and item["package_clip_id"]:
        return item["package_clip_id"]
    raise ValueError(f"Manifest clips entries must be clip_id strings or objects with clip_id/package_clip_id: {item!r}")


def _provenance(data: dict[str, Any]) -> dict[str, Any]:
    return {field: data[field] for field in PROVENANCE_FIELDS if field in data}


def _require_fields(data: dict[str, Any], fields: tuple[str, ...], path: Path) -> None:
    missing = [field for field in fields if field not in data or data[field] in ("", None)]
    if missing:
        raise ValueError(f"Missing required fields in {path}: {missing}")


def _require_keys(data: dict[str, Any], fields: tuple[str, ...], path: Path) -> None:
    missing = [field for field in fields if field not in data]
    if missing:
        raise ValueError(f"Missing required fields in {path}: {missing}")


def _require_relative_file(base: Path, value: Any, description: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing {description} path in {base / 'clip_manifest.json'}")
    path = Path(value)
    candidate = path if path.is_absolute() else base / path
    if not candidate.is_file():
        raise FileNotFoundError(f"Missing required {description}: {candidate}")
