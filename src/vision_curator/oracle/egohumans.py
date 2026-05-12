from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Iterable

from vision_curator.common.manifests import read_json, read_jsonl, write_json, write_jsonl
from vision_curator.packages.validate import validate_phase2_package


LABEL_NAMESPACE_ORACLE = "oracle_hidden"
LABEL_NAMESPACE_GOLD = "gold_revealed"
DATASET_SOURCE = "egohumans"
ACTIVITY = "lego_assembly"
CLASS_MAP = {"0": "person"}
POSE_KEYPOINT_THRESHOLD = 0.5
POSE_MIN_KEYPOINTS = 5
BBOX_PADDING = 1.4
BOX_SOURCE = "benchmark_pose_projection_proxy"
LABEL_SEMANTICS = (
    "Benchmark-semantics proxy oracle labels derived from aligned EgoHumans poses2d "
    "visible keypoints using the upstream-style pose-to-box rule. Viewer/self labels "
    "are excluded when the pose human_name matches the source camera id."
)


def import_egohumans_oracle(
    phase2_root: str | Path,
    dataset_root: str | Path,
    store_root: str | Path,
) -> dict[str, Any]:
    validation = validate_phase2_package(phase2_root)
    phase2_path = Path(phase2_root)
    dataset_path = Path(dataset_root)
    oracle_root = Path(store_root) / "oracle" / "egohumans"
    normalized_root = oracle_root / "normalized"
    reveal_root = oracle_root / "reveal_sets"
    metrics_root = oracle_root / "evaluation" / "metrics_inputs"
    metrics_root.mkdir(parents=True, exist_ok=True)

    frame_rows, source_rows = build_frame_index(validation)
    label_rows, label_warnings, checked_negative_frames = build_oracle_labels(
        frame_rows=frame_rows,
        source_rows=source_rows,
        dataset_root=dataset_path,
        phase2_root=phase2_path,
    )
    reveal_sets = build_reveal_sets(label_rows, checked_negative_frames)
    source_manifest = build_source_dataset_manifest(
        validation=validation,
        dataset_root=dataset_path,
        frame_rows=frame_rows,
        label_count=len(label_rows),
        warnings=label_warnings,
    )

    write_json(oracle_root / "source_dataset_manifest.json", source_manifest)
    write_json(normalized_root / "class_map.json", CLASS_MAP)
    write_jsonl(normalized_root / "frame_index.jsonl", frame_rows)
    write_jsonl(normalized_root / "oracle_labels.jsonl", label_rows)
    for filename, rows in reveal_sets.items():
        write_jsonl(reveal_root / filename, rows)

    return {
        "oracle_root": str(oracle_root),
        "package_id": validation["package_id"],
        "frame_count": len(frame_rows),
        "oracle_label_count": len(label_rows),
        "warnings": label_warnings,
        "outputs": {
            "source_dataset_manifest": str(oracle_root / "source_dataset_manifest.json"),
            "frame_index": str(normalized_root / "frame_index.jsonl"),
            "oracle_labels": str(normalized_root / "oracle_labels.jsonl"),
            "class_map": str(normalized_root / "class_map.json"),
            "gold_seed": str(reveal_root / "gold_seed_v0.jsonl"),
            "review_revealed_gold": str(reveal_root / "review_revealed_gold_v0.jsonl"),
            "gold_negatives": str(reveal_root / "gold_negatives_v0.jsonl"),
        },
    }


def build_frame_index(validation: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frame_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    package_id = validation["package_id"]
    for clip in validation["clips"]:
        clip_manifest_path = Path(clip["manifest_path"])
        clip_root = clip_manifest_path.parent
        clip_manifest = read_json(clip_manifest_path)
        clip_id = str(clip_manifest.get("package_clip_id") or clip_manifest.get("clip_id") or clip["clip_id"])
        frame_map_path = _resolve_existing_path(clip_root, clip_manifest["source_frame_map_path"])
        for fallback_idx, source_row in enumerate(read_jsonl(frame_map_path)):
            frame_idx = _int_or_default(source_row.get("frame_idx"), fallback_idx)
            source_frame_idx = _int_or_default(
                source_row.get("source_frame_idx"),
                _int_or_default(clip_manifest.get("start_frame_idx"), 0) + frame_idx,
            )
            source_image = _first_present(
                source_row,
                ("source_image_path_or_name", "source_image_path", "source_image_file", "image_path", "rgb_member"),
            )
            row = {
                "package_id": str(source_row.get("package_id") or package_id),
                "package_clip_id": str(source_row.get("package_clip_id") or clip_id),
                "frame_idx": frame_idx,
                "source_sequence_id": str(
                    source_row.get("source_sequence_id")
                    or source_row.get("sequence_id")
                    or clip_manifest.get("source_sequence_id")
                    or ""
                ),
                "source_camera_id": str(
                    source_row.get("source_camera_id")
                    or source_row.get("camera_id")
                    or source_row.get("stream_id")
                    or clip_manifest.get("source_camera_id")
                    or ""
                ),
                "source_frame_idx": source_frame_idx,
                "source_image_path_or_name": str(source_image or ""),
            }
            width = source_row.get("width") or clip_manifest.get("width") or clip_manifest.get("frame_width")
            height = source_row.get("height") or clip_manifest.get("height") or clip_manifest.get("frame_height")
            if width is not None:
                row["width"] = _int_or_default(width, 0)
            if height is not None:
                row["height"] = _int_or_default(height, 0)
            frame_rows.append(row)
            source_rows.append({**source_row, **row})
    frame_rows.sort(key=lambda row: (row["package_clip_id"], row["frame_idx"]))
    source_rows.sort(key=lambda row: (row["package_clip_id"], row["frame_idx"]))
    return frame_rows, source_rows


def build_oracle_labels(
    frame_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    dataset_root: str | Path,
    phase2_root: str | Path,
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    labels: list[dict[str, Any]] = []
    warnings: list[str] = []
    checked_negative_frames: list[dict[str, Any]] = []
    for frame_row, source_row in zip(frame_rows, source_rows):
        width = _int_or_default(frame_row.get("width"), 0)
        height = _int_or_default(frame_row.get("height"), 0)
        pose_ref = _first_present(source_row, ("oracle_pose_path", "pose_path", "pose_member"))
        if not pose_ref:
            warnings.append(_frame_warning(frame_row, "missing pose reference"))
            continue
        pose_path = _resolve_source_path(str(pose_ref), dataset_root=Path(dataset_root), phase2_root=Path(phase2_root))
        if pose_path is None:
            warnings.append(_frame_warning(frame_row, f"pose reference not found: {pose_ref}"))
            continue
        pose_entries = _load_pose_entries(pose_path)
        frame_labels = list(_labels_from_pose_entries(frame_row, pose_entries, width=width, height=height, pose_ref=str(pose_ref)))
        if frame_labels:
            labels.extend(frame_labels)
        else:
            checked_negative_frames.append(frame_row)
    labels.sort(key=lambda row: row["record_id"])
    return labels, warnings, checked_negative_frames


def build_reveal_sets(
    oracle_labels: list[dict[str, Any]],
    checked_negative_frames: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    sorted_labels = sorted(oracle_labels, key=lambda row: _stable_key(row["record_id"]))
    seed_count = _bounded_count(len(sorted_labels), fraction=0.10, minimum=1)
    review_count = _bounded_count(max(0, len(sorted_labels) - seed_count), fraction=0.05, minimum=1)
    gold_seed = [
        _gold_reveal_record(row, "gold_seed_v0", "deterministic_seed_sample")
        for row in sorted_labels[:seed_count]
    ]
    review_revealed = [
        _gold_reveal_record(row, "review_revealed_gold_v0", "deterministic_review_simulation_sample")
        for row in sorted_labels[seed_count : seed_count + review_count]
    ]
    negative_count = _bounded_count(len(checked_negative_frames), fraction=0.05, minimum=1)
    gold_negatives = [
        _gold_negative_record(row, "gold_negatives_v0")
        for row in sorted(checked_negative_frames, key=lambda row: _stable_key(_frame_identity(row)))[:negative_count]
    ]
    return {
        "gold_seed_v0.jsonl": gold_seed,
        "review_revealed_gold_v0.jsonl": review_revealed,
        "gold_negatives_v0.jsonl": gold_negatives,
    }


def build_source_dataset_manifest(
    validation: dict[str, Any],
    dataset_root: Path,
    frame_rows: list[dict[str, Any]],
    label_count: int,
    warnings: list[str],
) -> dict[str, Any]:
    manifest = validation["manifest"]
    sequences = sorted({row["source_sequence_id"] for row in frame_rows if row.get("source_sequence_id")})
    cameras = sorted({row["source_camera_id"] for row in frame_rows if row.get("source_camera_id")})
    return {
        "dataset_source": DATASET_SOURCE,
        "activity": manifest.get("activity") or ACTIVITY,
        "canonical_dataset_root": str(dataset_root.resolve()),
        "source_package_manifest_path": manifest.get("source_package_manifest_path"),
        "source_benchmark_manifest_path": manifest.get("source_benchmark_manifest_path"),
        "source_sequence_ids": sequences,
        "source_camera_ids": cameras,
        "package_id": validation["package_id"],
        "label_namespace": LABEL_NAMESPACE_ORACLE,
        "label_semantics": LABEL_SEMANTICS,
        "box_source": BOX_SOURCE,
        "provenance": {
            "vision_curator_importer": "vision_curator.oracle.egohumans",
            "vision_api_reference": "/home/jdl2/Git/vision-ai/vision_api/scripts/convert_egohumans_subset.py",
            "vision_api_commit": _git_head(Path("/home/jdl2/Git/vision-ai/vision_api")),
            "thermal_data_engine_commit": _git_head(Path("/home/jdl2/Git/vision-ai/thermal-data-engine")),
            "pose_keypoint_threshold": POSE_KEYPOINT_THRESHOLD,
            "pose_min_keypoints": POSE_MIN_KEYPOINTS,
            "bbox_padding": BBOX_PADDING,
        },
        "counts": {
            "frames": len(frame_rows),
            "oracle_labels": label_count,
            "warnings": len(warnings),
        },
        "warnings": warnings,
    }


def _labels_from_pose_entries(
    frame_row: dict[str, Any],
    pose_entries: Iterable[dict[str, Any]],
    width: int,
    height: int,
    pose_ref: str,
) -> Iterable[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    for pose_entry in pose_entries:
        if not isinstance(pose_entry, dict):
            continue
        identity = _annotation_identity(pose_entry)
        if identity in seen:
            continue
        seen.add(identity)
        human_name = pose_entry.get("human_name")
        if human_name is not None and str(human_name) == str(frame_row.get("source_camera_id")):
            continue
        bbox = bbox_from_pose_keypoints(pose_entry, width=width, height=height)
        if bbox is None:
            continue
        x1, y1, x2, y2, confidence, selected_count, visible_count = bbox
        record_id = _oracle_record_id(frame_row, identity)
        yield {
            "record_id": record_id,
            "label_namespace": LABEL_NAMESPACE_ORACLE,
            "dataset_source": DATASET_SOURCE,
            "activity": ACTIVITY,
            "package_id": frame_row["package_id"],
            "package_clip_id": frame_row["package_clip_id"],
            "frame_idx": frame_row["frame_idx"],
            "sequence_id": frame_row["source_sequence_id"],
            "camera_id": frame_row["source_camera_id"],
            "source_frame_idx": frame_row["source_frame_idx"],
            "source_image_path_or_name": frame_row["source_image_path_or_name"],
            "class_name": "person",
            "box_xyxy": [x1, y1, x2, y2],
            "box_source": BOX_SOURCE,
            "visibility_or_keypoint_metadata": {
                "human_name": human_name,
                "human_id": pose_entry.get("human_id"),
                "visible_keypoint_count": visible_count,
                "selected_keypoint_count": selected_count,
                "selected_keypoint_score_mean": confidence,
            },
            "provenance": {
                "source_pose_path_or_member": pose_ref,
                "label_semantics": LABEL_SEMANTICS,
                "pose_keypoint_threshold": POSE_KEYPOINT_THRESHOLD,
                "pose_min_keypoints": POSE_MIN_KEYPOINTS,
                "bbox_padding": BBOX_PADDING,
            },
        }


def bbox_from_pose_keypoints(entry: dict[str, Any], width: int, height: int) -> list[float] | None:
    keypoints = entry.get("keypoints")
    if not isinstance(keypoints, list):
        return None
    visible_count = 0
    selected: list[tuple[float, float, float]] = []
    for point in keypoints:
        if not isinstance(point, (list, tuple)) or len(point) < 3:
            continue
        x, y, score = float(point[0]), float(point[1]), float(point[2])
        if score > 0:
            visible_count += 1
        if score <= POSE_KEYPOINT_THRESHOLD:
            continue
        if x < 0 or y < 0 or x > float(width) or y > float(height):
            continue
        selected.append((x, y, score))
    if len(selected) < POSE_MIN_KEYPOINTS:
        return None
    x_values = [point[0] for point in selected]
    y_values = [point[1] for point in selected]
    x1, x2 = min(x_values), max(x_values)
    y1, y2 = min(y_values), max(y_values)
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    scale_x = (x2 - x1) * BBOX_PADDING
    scale_y = (y2 - y1) * BBOX_PADDING
    if scale_x <= 0.0 or scale_y <= 0.0:
        return None
    box = _clamp_bbox_to_frame(
        [
            center_x - (scale_x / 2.0),
            center_y - (scale_y / 2.0),
            center_x + (scale_x / 2.0),
            center_y + (scale_y / 2.0),
        ],
        width=width,
        height=height,
    )
    if box[2] <= box[0] or box[3] <= box[1]:
        return None
    confidence = sum(point[2] for point in selected) / float(len(selected))
    return [box[0], box[1], box[2], box[3], confidence, len(selected), visible_count]


def _load_pose_entries(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    elif path.suffix == ".npy":
        try:
            import numpy as np  # type: ignore
        except ImportError as exc:
            raise RuntimeError(f"Reading EgoHumans .npy pose files requires numpy: {path}") from exc
        payload = np.load(path, allow_pickle=True).tolist()
    else:
        raise ValueError(f"Unsupported pose annotation format: {path}")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("annotations", "poses", "people", "entries"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError(f"Expected pose annotation list/object in {path}")


def _resolve_source_path(value: str, dataset_root: Path, phase2_root: Path) -> Path | None:
    raw = Path(value)
    candidates = [raw] if raw.is_absolute() else [dataset_root / raw, phase2_root / raw]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _resolve_existing_path(base: Path, value: str) -> Path:
    path = Path(value)
    candidate = path if path.is_absolute() else base / path
    if not candidate.is_file():
        raise FileNotFoundError(f"Missing required file: {candidate}")
    return candidate


def _gold_reveal_record(row: dict[str, Any], reveal_set: str, reason: str) -> dict[str, Any]:
    return {
        "reveal_id": _stable_id("gold", reveal_set, row["record_id"]),
        "label_namespace": LABEL_NAMESPACE_GOLD,
        "dataset_source": DATASET_SOURCE,
        "activity": row["activity"],
        "reveal_set": reveal_set,
        "selection_reason": reason,
        "oracle_record_id": row["record_id"],
        "source_label_namespace": LABEL_NAMESPACE_ORACLE,
        "package_id": row["package_id"],
        "package_clip_id": row["package_clip_id"],
        "frame_idx": row["frame_idx"],
        "sequence_id": row["sequence_id"],
        "camera_id": row["camera_id"],
        "source_frame_idx": row["source_frame_idx"],
        "class_name": row["class_name"],
        "provenance": {
            "policy": "deterministic initial reveal set; not global training truth",
        },
    }


def _gold_negative_record(row: dict[str, Any], reveal_set: str) -> dict[str, Any]:
    return {
        "reveal_id": _stable_id("gold-negative", reveal_set, _frame_identity(row)),
        "label_namespace": LABEL_NAMESPACE_GOLD,
        "dataset_source": DATASET_SOURCE,
        "activity": ACTIVITY,
        "reveal_set": reveal_set,
        "selection_reason": "oracle_checked_no_visible_person_labels",
        "oracle_record_id": None,
        "source_label_namespace": LABEL_NAMESPACE_ORACLE,
        "package_id": row["package_id"],
        "package_clip_id": row["package_clip_id"],
        "frame_idx": row["frame_idx"],
        "sequence_id": row["source_sequence_id"],
        "camera_id": row["source_camera_id"],
        "source_frame_idx": row["source_frame_idx"],
        "class_name": "negative_frame",
        "provenance": {
            "policy": "negative only after oracle pose source was checked for this frame",
        },
    }


def _annotation_identity(entry: dict[str, Any]) -> tuple[str, str]:
    if entry.get("human_name") not in (None, ""):
        return ("human_name", str(entry["human_name"]))
    return ("human_id", str(entry.get("human_id", "")))


def _oracle_record_id(frame_row: dict[str, Any], identity: tuple[str, str]) -> str:
    return _stable_id(
        "oracle",
        frame_row["source_sequence_id"],
        frame_row["source_camera_id"],
        str(frame_row["source_frame_idx"]),
        identity[0],
        identity[1],
    )


def _frame_identity(row: dict[str, Any]) -> str:
    return "|".join(
        str(row.get(key, ""))
        for key in ("package_id", "package_clip_id", "frame_idx", "source_sequence_id", "source_camera_id", "source_frame_idx")
    )


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _stable_key(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _bounded_count(total: int, fraction: float, minimum: int) -> int:
    if total <= 0:
        return 0
    return min(total, max(minimum, int(math.ceil(total * fraction))))


def _clamp_bbox_to_frame(bbox_xyxy: list[float], width: int, height: int) -> list[float]:
    x1, y1, x2, y2 = [float(value) for value in bbox_xyxy[:4]]
    return [
        min(max(0.0, x1), float(width)),
        min(max(0.0, y1), float(height)),
        min(max(0.0, x2), float(width)),
        min(max(0.0, y2), float(height)),
    ]


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _frame_warning(frame_row: dict[str, Any], message: str) -> str:
    return f"{frame_row.get('package_clip_id')}:{frame_row.get('frame_idx')}: {message}"


def _git_head(repo_root: Path) -> str | None:
    if not repo_root.is_dir():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None

