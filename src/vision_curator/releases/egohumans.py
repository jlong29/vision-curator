from __future__ import annotations

import hashlib
import json
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from vision_curator.common.manifests import read_json, read_jsonl, write_json, write_jsonl
from vision_curator.common.models import DatasetReleaseManifest
from vision_curator.common.paths import packages_index_path, track_scores_path
from vision_curator.oracle.egohumans import LABEL_NAMESPACE_GOLD, LABEL_NAMESPACE_ORACLE
from vision_curator.packages.validate import validate_phase2_package


LABEL_NAMESPACE_PSEUDO = "pseudo_teacher"
REALISTIC_RELEASE_FAMILIES = {
    "gold_only_v0",
    "gold_plus_naive_pseudo_v0",
    "gold_plus_trusted_tracks_v0",
    "gold_plus_review_revealed_v1",
}
ALL_RELEASE_FAMILIES = sorted([*REALISTIC_RELEASE_FAMILIES, "oracle_upper_bound"])
TRAIN_ELIGIBLE_SPLITS = {"gold_seed_pool", "unlabeled_pool"}
EVAL_SPLITS = {"oracle_val_hidden", "oracle_test_hidden"}
NAIVE_CONFIDENCE_THRESHOLD = 0.85
TRUSTED_CLASS_THRESHOLD = 0.90
TRUSTED_BOX_THRESHOLD = 0.80
TRUSTED_MIN_TRACK_LENGTH = 3
TRUSTED_MIN_MEAN_CONF = 0.70
TRUSTED_MAX_EDGE_FRACTION = 0.15
TRUSTED_MAX_JITTER = 0.20


@dataclass(frozen=True)
class BuildResult:
    release_root: Path
    dataset_yaml: Path
    manifest: dict[str, Any]


def build_split_assignments(
    store_root: str | Path,
    output_path: str | Path | None = None,
    chunk_size: int = 100,
) -> Path:
    oracle_root = Path(store_root) / "oracle" / "egohumans"
    frame_rows = read_jsonl(oracle_root / "normalized" / "frame_index.jsonl")
    if not frame_rows:
        raise FileNotFoundError(f"No EgoHumans frame index found under {oracle_root}")
    output = Path(output_path) if output_path else oracle_root / "splits" / "split_assignments_v0.jsonl"
    chunks: dict[tuple[str, int], dict[str, Any]] = {}
    for row in frame_rows:
        sequence_id = str(row.get("source_sequence_id") or row.get("sequence_id") or "")
        frame_idx = _int(row.get("frame_idx"))
        chunk_start = (frame_idx // chunk_size) * chunk_size
        chunk_end = chunk_start + chunk_size - 1
        key = (sequence_id, chunk_start)
        chunk = chunks.setdefault(
            key,
            {
                "sequence_id": sequence_id,
                "chunk_start_frame_idx": chunk_start,
                "chunk_end_frame_idx": chunk_end,
                "frames": [],
            },
        )
        chunk["frames"].append(row)

    ordered_chunks = sorted(chunks.values(), key=lambda item: _stable_key(_chunk_unit_id(item)))
    split_by_unit: dict[str, str] = {}
    counts = _split_counts(len(ordered_chunks))
    split_plan = (
        ["oracle_test_hidden"] * counts["oracle_test_hidden"]
        + ["oracle_val_hidden"] * counts["oracle_val_hidden"]
        + ["gold_seed_pool"] * counts["gold_seed_pool"]
    )
    split_plan.extend(["unlabeled_pool"] * (len(ordered_chunks) - len(split_plan)))
    for chunk, split_name in zip(ordered_chunks, split_plan):
        split_by_unit[_chunk_unit_id(chunk)] = split_name

    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for frame_row in frame_rows:
        sequence_id = str(frame_row.get("source_sequence_id") or frame_row.get("sequence_id") or "")
        frame_idx = _int(frame_row.get("frame_idx"))
        chunk_start = (frame_idx // chunk_size) * chunk_size
        grouped[(str(frame_row["package_id"]), str(frame_row["package_clip_id"]), chunk_start)].append(frame_row)
        unit_id = _chunk_unit_id(
            {
                "sequence_id": sequence_id,
                "chunk_start_frame_idx": chunk_start,
                "chunk_end_frame_idx": chunk_start + chunk_size - 1,
            }
        )
        split_by_unit.setdefault(unit_id, "unlabeled_pool")

    for (package_id, package_clip_id, chunk_start), frames in sorted(grouped.items()):
        first = frames[0]
        unit_id = _chunk_unit_id(
            {
                "sequence_id": str(first.get("source_sequence_id") or first.get("sequence_id") or ""),
                "chunk_start_frame_idx": chunk_start,
                "chunk_end_frame_idx": chunk_start + chunk_size - 1,
            }
        )
        rows.append(
            {
                "split_version": "split_assignments_v0",
                "unit_id": unit_id,
                "package_id": package_id,
                "package_clip_id": package_clip_id,
                "sequence_id": str(first.get("source_sequence_id") or first.get("sequence_id") or ""),
                "camera_id": str(first.get("source_camera_id") or first.get("camera_id") or ""),
                "frame_start_idx": min(_int(row.get("frame_idx")) for row in frames),
                "frame_end_idx": max(_int(row.get("frame_idx")) for row in frames),
                "split_name": split_by_unit[unit_id],
                "split_rationale": "deterministic sequence-time chunk split; simultaneous camera views share a unit_id",
            }
        )
    write_jsonl(output, rows)
    return output


def build_egohumans_release(
    release_family: str,
    release_id: str,
    store_root: str | Path,
    release_store: str | Path,
    split_assignments_path: str | Path | None = None,
) -> BuildResult:
    if release_family not in ALL_RELEASE_FAMILIES:
        raise ValueError(f"Unsupported EgoHumans release family: {release_family}")
    store = Path(store_root)
    release_root = Path(release_store) / release_id
    if release_root.exists():
        raise FileExistsError(f"Dataset release already exists and will not be overwritten: {release_root}")
    oracle_root = store / "oracle" / "egohumans"
    split_path = Path(split_assignments_path) if split_assignments_path else oracle_root / "splits" / "split_assignments_v0.jsonl"
    if not split_path.is_file():
        raise FileNotFoundError(f"Missing split assignments: {split_path}")

    frame_rows = read_jsonl(oracle_root / "normalized" / "frame_index.jsonl")
    oracle_labels = read_jsonl(oracle_root / "normalized" / "oracle_labels.jsonl")
    gold_seed = read_jsonl(oracle_root / "reveal_sets" / "gold_seed_v0.jsonl")
    review_gold = read_jsonl(oracle_root / "reveal_sets" / "review_revealed_gold_v0.jsonl")
    split_rows = read_jsonl(split_path)
    if not frame_rows:
        raise FileNotFoundError(f"No frame index rows found under {oracle_root}")

    package_context = _load_package_context(store)
    frame_by_key = {_frame_key(row): row for row in frame_rows}
    split_by_frame = _split_lookup(split_rows)
    source_packages = _source_package_records(store)
    oracle_by_id = {str(row["record_id"]): row for row in oracle_labels}

    label_items: list[dict[str, Any]] = []
    label_items.extend(_eval_oracle_items(oracle_labels, split_by_frame))
    if release_family == "oracle_upper_bound":
        label_items.extend(_oracle_train_items(oracle_labels, split_by_frame))
    else:
        label_items.extend(_gold_items(gold_seed, oracle_by_id, split_by_frame))
        if release_family == "gold_plus_review_revealed_v1":
            label_items.extend(_gold_items(review_gold, oracle_by_id, split_by_frame))
        if release_family == "gold_plus_naive_pseudo_v0":
            label_items.extend(_naive_pseudo_items(package_context, split_by_frame))
        if release_family == "gold_plus_trusted_tracks_v0":
            label_items.extend(_trusted_pseudo_items(store, package_context, split_by_frame))

    image_cache_root = store / "image_cache" / "egohumans"
    _write_release_tree(release_root, label_items, frame_by_key, package_context, image_cache_root)
    class_list = ["person"]
    dataset_yaml = _dataset_yaml(release_root, class_list)
    (release_root / "dataset.yaml").write_text(dataset_yaml, encoding="utf-8")
    counts_by_split = _counts_by_split(label_items)
    counts_by_label_source = _counts_by_label_source(label_items)
    policy = _release_policy(release_family, split_path, oracle_root)
    manifest = DatasetReleaseManifest(
        release_id=release_id,
        source_package_ids=[str(row["package_id"]) for row in source_packages],
        source_packages=source_packages,
        annotation_versions=["egohumans_goldset_v0"],
        annotation_status="oracle_upper_bound" if release_family == "oracle_upper_bound" else "calibration",
        split_policy={
            "name": "egohumans_split_assignments_v0",
            "artifact": str(split_path),
            "train_eligible_splits": sorted(TRAIN_ELIGIBLE_SPLITS),
            "eval_splits": sorted(EVAL_SPLITS),
        },
        label_policy={
            "release_family": release_family,
            "target_class": "person",
            "allowed_train_namespaces": policy["label_namespaces_used_for_train"],
            "forbidden_train_namespaces": policy["forbidden_label_namespaces_for_train"],
            "source_pseudo_policy": policy["source_pseudo_policy"],
        },
        class_list=class_list,
        counts_by_split=counts_by_split,
        counts_by_label_source=counts_by_label_source,
        created_at=datetime.now(timezone.utc).isoformat(),
        extra=policy,
    ).to_dict()
    manifest.update(policy)
    manifest["provenance_records"] = ["provenance/label_items.jsonl", "provenance/source_packages.jsonl"]
    write_json(release_root / "manifest.json", manifest)
    write_json(release_root / "provenance" / "build_policy.json", policy)
    write_jsonl(release_root / "provenance" / "source_packages.jsonl", source_packages)
    write_jsonl(release_root / "provenance" / "label_items.jsonl", label_items)
    return BuildResult(release_root=release_root, dataset_yaml=release_root / "dataset.yaml", manifest=manifest)


def _release_policy(release_family: str, split_path: Path, oracle_root: Path) -> dict[str, Any]:
    realistic = release_family in REALISTIC_RELEASE_FAMILIES
    train_namespaces = [LABEL_NAMESPACE_ORACLE] if release_family == "oracle_upper_bound" else [LABEL_NAMESPACE_GOLD]
    pseudo_policy: dict[str, Any] | None = None
    if release_family == "gold_plus_naive_pseudo_v0":
        train_namespaces.append(LABEL_NAMESPACE_PSEUDO)
        pseudo_policy = {"policy_name": "naive_confidence", "confidence_threshold": NAIVE_CONFIDENCE_THRESHOLD}
    if release_family == "gold_plus_trusted_tracks_v0":
        train_namespaces.append(LABEL_NAMESPACE_PSEUDO)
        pseudo_policy = {
            "policy_name": "trusted_tracks",
            "class_trust_threshold": TRUSTED_CLASS_THRESHOLD,
            "box_trust_threshold": TRUSTED_BOX_THRESHOLD,
            "min_track_length": TRUSTED_MIN_TRACK_LENGTH,
            "min_mean_conf": TRUSTED_MIN_MEAN_CONF,
            "max_edge_fraction": TRUSTED_MAX_EDGE_FRACTION,
            "max_bbox_jitter": TRUSTED_MAX_JITTER,
        }
    return {
        "release_family": release_family,
        "label_namespaces_used_for_train": train_namespaces,
        "label_namespaces_used_for_eval": [LABEL_NAMESPACE_ORACLE],
        "forbidden_label_namespaces_for_train": [LABEL_NAMESPACE_ORACLE] if realistic else [],
        "realistic_calibration_loop": realistic,
        "oracle_upper_bound": release_family == "oracle_upper_bound",
        "source_oracle_manifest": str(oracle_root / "source_dataset_manifest.json"),
        "source_reveal_sets": (
            ["gold_seed_v0.jsonl", "review_revealed_gold_v0.jsonl"]
            if release_family == "gold_plus_review_revealed_v1"
            else ["gold_seed_v0.jsonl"]
        ),
        "source_pseudo_policy": pseudo_policy,
        "split_assignment_artifact": str(split_path),
        "diagnostic_headroom_only": release_family == "oracle_upper_bound",
    }


def _eval_oracle_items(oracle_labels: list[dict[str, Any]], split_by_frame: dict[tuple[str, str, int], str]) -> list[dict[str, Any]]:
    return [
        _label_item(row, LABEL_NAMESPACE_ORACLE, "oracle_eval", split_by_frame[_frame_key(row)])
        for row in oracle_labels
        if split_by_frame.get(_frame_key(row)) in EVAL_SPLITS
    ]


def _oracle_train_items(oracle_labels: list[dict[str, Any]], split_by_frame: dict[tuple[str, str, int], str]) -> list[dict[str, Any]]:
    return [
        _label_item(row, LABEL_NAMESPACE_ORACLE, "oracle_upper_bound_train", "train")
        for row in oracle_labels
        if split_by_frame.get(_frame_key(row)) in TRAIN_ELIGIBLE_SPLITS
    ]


def _gold_items(
    reveal_rows: list[dict[str, Any]],
    oracle_by_id: dict[str, dict[str, Any]],
    split_by_frame: dict[tuple[str, str, int], str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for reveal in reveal_rows:
        if split_by_frame.get(_frame_key(reveal)) not in TRAIN_ELIGIBLE_SPLITS:
            continue
        oracle = oracle_by_id.get(str(reveal.get("oracle_record_id")))
        if not oracle:
            continue
        items.append(_label_item(oracle, LABEL_NAMESPACE_GOLD, str(reveal.get("reveal_set") or "gold_revealed"), "train"))
    return items


def _naive_pseudo_items(
    package_context: dict[tuple[str, str], dict[str, Any]],
    split_by_frame: dict[tuple[str, str, int], str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for context in package_context.values():
        for row in _read_table(context["detections_path"]):
            if split_by_frame.get(_frame_key(row)) not in TRAIN_ELIGIBLE_SPLITS:
                continue
            if _float(row.get("confidence", row.get("conf", 0.0))) < NAIVE_CONFIDENCE_THRESHOLD:
                continue
            item = _pseudo_item(row, "naive_confidence", context)
            if item:
                items.append(item)
    return items


def _trusted_pseudo_items(
    store_root: Path,
    package_context: dict[tuple[str, str], dict[str, Any]],
    split_by_frame: dict[tuple[str, str, int], str],
) -> list[dict[str, Any]]:
    trusted_tracks: set[tuple[str, str, str]] = set()
    for package_id in sorted({key[0] for key in package_context}):
        for row in read_jsonl(track_scores_path(store_root, package_id)):
            if _is_trusted_track(row):
                trusted_tracks.add((str(row["package_id"]), str(row["clip_id"]), str(row["track_id"])))
    items: list[dict[str, Any]] = []
    for context in package_context.values():
        for row in _read_table(context["detections_path"]):
            track_id = str(row.get("track_id", ""))
            if (str(row.get("package_id")), str(row.get("package_clip_id")), track_id) not in trusted_tracks:
                continue
            if split_by_frame.get(_frame_key(row)) not in TRAIN_ELIGIBLE_SPLITS:
                continue
            item = _pseudo_item(row, "trusted_track", context)
            if item:
                items.append(item)
    return items


def _label_item(row: dict[str, Any], namespace: str, label_source: str, split_name: str) -> dict[str, Any]:
    return {
        "item_id": _stable_id(namespace, label_source, str(row.get("record_id", ""))),
        "package_id": str(row["package_id"]),
        "package_clip_id": str(row["package_clip_id"]),
        "frame_idx": _int(row["frame_idx"]),
        "label_namespace": namespace,
        "label_source": label_source,
        "split": _release_split_name(split_name),
        "class_id": 0,
        "class_name": "person",
        "box_xyxy": [float(value) for value in row["box_xyxy"]],
    }


def _pseudo_item(row: dict[str, Any], label_source: str, context: dict[str, Any]) -> dict[str, Any] | None:
    box = _source_space_box(row, context.get("frame_metadata", {}).get(_int(row.get("frame_idx")), {}))
    if box is None:
        return None
    return {
        "item_id": _stable_id(LABEL_NAMESPACE_PSEUDO, label_source, str(row.get("det_id", "")), str(row.get("frame_idx", ""))),
        "package_id": str(row["package_id"]),
        "package_clip_id": str(row["package_clip_id"]),
        "frame_idx": _int(row["frame_idx"]),
        "label_namespace": LABEL_NAMESPACE_PSEUDO,
        "label_source": label_source,
        "split": "train",
        "class_id": 0,
        "class_name": "person",
        "box_xyxy": box,
        "teacher_confidence": _float(row.get("confidence", row.get("conf", 0.0))),
        "track_id": row.get("track_id"),
    }


def _write_release_tree(
    release_root: Path,
    label_items: list[dict[str, Any]],
    frame_by_key: dict[tuple[str, str, int], dict[str, Any]],
    package_context: dict[tuple[str, str], dict[str, Any]],
    image_cache_root: Path,
) -> None:
    images_dir = release_root / "images"
    labels_dir = release_root / "labels"
    splits_dir = release_root / "splits"
    provenance_dir = release_root / "provenance"
    for directory in (images_dir, labels_dir, splits_dir, provenance_dir):
        directory.mkdir(parents=True, exist_ok=False)
    items_by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in label_items:
        items_by_image[_image_name(item)].append(item)
    split_images: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    extractor = _FrameExtractor()
    try:
        for image_name, items in sorted(items_by_image.items()):
            first = items[0]
            frame_row = frame_by_key[_frame_key(first)]
            context = package_context.get((first["package_id"], first["package_clip_id"]), {})
            _materialize_image(images_dir / image_name, frame_row, context, extractor, image_cache_root)
            lines = [_yolo_line(item, frame_row) for item in items]
            (labels_dir / f"{Path(image_name).stem}.txt").write_text("".join(lines), encoding="utf-8")
            split_images[first["split"]].append(image_name)
    finally:
        extractor.close()
    for split_name, image_names in split_images.items():
        (splits_dir / f"{split_name}.txt").write_text("".join(f"images/{name}\n" for name in sorted(set(image_names))), encoding="utf-8")


def _materialize_image(
    target: Path,
    frame_row: dict[str, Any],
    context: dict[str, Any],
    extractor: "_FrameExtractor",
    image_cache_root: Path,
) -> None:
    cache_path = image_cache_root / target.name
    if cache_path.is_file():
        shutil.copy2(cache_path, target)
        return
    source = Path(str(frame_row.get("source_image_path_or_name") or ""))
    if source.is_file():
        shutil.copy2(source, target)
        _cache_image(target, cache_path)
        return
    if str(frame_row.get("source_image_path_or_name") or "").startswith("images/"):
        candidate = Path(str(context.get("source_path", ""))) / str(frame_row["source_image_path_or_name"])
        if candidate.is_file():
            shutil.copy2(candidate, target)
            _cache_image(target, cache_path)
            return
    clip_path = Path(str(context.get("clip_path", "")))
    if clip_path.is_file():
        extractor.extract(clip_path, _int(frame_row.get("frame_idx")), target)
        _cache_image(target, cache_path)
        return
    raise FileNotFoundError(f"Could not materialize image for frame {_frame_key(frame_row)}")


def _cache_image(source: Path, cache_path: Path) -> None:
    if cache_path.exists():
        return
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, cache_path)


class _FrameExtractor:
    def __init__(self) -> None:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Extracting release images from clips requires OpenCV") from exc
        self._cv2 = cv2
        self._captures: dict[Path, Any] = {}

    def extract(self, clip_path: Path, frame_idx: int, target: Path) -> None:
        capture = self._captures.get(clip_path)
        if capture is None:
            capture = self._cv2.VideoCapture(str(clip_path))
            if not capture.isOpened():
                raise ValueError(f"Could not open clip for image extraction: {clip_path}")
            self._captures[clip_path] = capture
        capture.set(self._cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = capture.read()
        if not ok:
            raise ValueError(f"Could not read frame {frame_idx} from {clip_path}")
        if not self._cv2.imwrite(str(target), frame):
            raise ValueError(f"Could not write release image: {target}")

    def close(self) -> None:
        for capture in self._captures.values():
            capture.release()
        self._captures.clear()


def _yolo_line(item: dict[str, Any], frame_row: dict[str, Any]) -> str:
    width = max(_float(frame_row.get("width")), 1.0)
    height = max(_float(frame_row.get("height")), 1.0)
    x1, y1, x2, y2 = _clamp_box(item["box_xyxy"], width, height)
    x_center = ((x1 + x2) / 2.0) / width
    y_center = ((y1 + y2) / 2.0) / height
    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height
    return f"{item['class_id']} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n"


def _source_space_box(row: dict[str, Any], frame_metadata: dict[str, Any]) -> list[float] | None:
    if not all(key in row for key in ("x1", "y1", "x2", "y2")):
        return None
    x1, y1, x2, y2 = (_float(row["x1"]), _float(row["y1"]), _float(row["x2"]), _float(row["y2"]))
    transform = frame_metadata.get("transform") if isinstance(frame_metadata, dict) else None
    if isinstance(transform, dict):
        scale = _float(transform.get("scale")) or 1.0
        pad_x = _float(transform.get("pad_x"))
        pad_y = _float(transform.get("pad_y"))
        x1, x2 = (x1 - pad_x) / scale, (x2 - pad_x) / scale
        y1, y2 = (y1 - pad_y) / scale, (y2 - pad_y) / scale
    width = _float(frame_metadata.get("width") or frame_metadata.get("source_width") or 0.0)
    height = _float(frame_metadata.get("height") or frame_metadata.get("source_height") or 0.0)
    if width > 0 and height > 0:
        return _clamp_box([x1, y1, x2, y2], width, height)
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y2]


def _load_package_context(store_root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    context: dict[tuple[str, str], dict[str, Any]] = {}
    for package in _source_package_records(store_root):
        source_path = Path(str(package.get("source_path", "")))
        if not source_path.is_dir():
            continue
        validation = validate_phase2_package(source_path)
        for clip in validation["clips"]:
            clip_manifest = read_json(clip["manifest_path"])
            source_frame_map = Path(str(clip_manifest.get("source_frame_map_path", "source_frames.jsonl")))
            source_frame_map_path = source_frame_map if source_frame_map.is_absolute() else Path(clip["manifest_path"]).parent / source_frame_map
            source_frames = _read_source_frames(source_frame_map_path)
            context[(validation["package_id"], clip["clip_id"])] = {
                "source_path": str(source_path),
                "clip_path": clip["clip_path"],
                "detections_path": clip["detections_path"],
                "tracks_path": clip["tracks_path"],
                "frame_metadata": source_frames,
            }
    return context


def _source_package_records(store_root: Path) -> list[dict[str, Any]]:
    return sorted(read_jsonl(packages_index_path(store_root)), key=lambda row: str(row.get("package_id", "")))


def _read_source_frames(path: Path) -> dict[int, dict[str, Any]]:
    return {_int(row.get("frame_idx")): row for row in read_jsonl(path)}


def _read_table(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)
    if target.suffix == ".parquet" and not _looks_textual(target):
        try:
            import pandas as pd  # type: ignore
        except ImportError as exc:
            raise RuntimeError(f"Reading parquet table requires pandas/pyarrow: {target}") from exc
        return [dict(row) for row in pd.read_parquet(target).to_dict(orient="records")]
    text = target.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        value = json.loads(text)
        if not isinstance(value, list):
            raise ValueError(f"Expected list in {target}")
        return [row for row in value if isinstance(row, dict)]
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _split_lookup(split_rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str, int], str]:
    lookup: dict[tuple[str, str, int], str] = {}
    for row in split_rows:
        for frame_idx in range(_int(row["frame_start_idx"]), _int(row["frame_end_idx"]) + 1):
            lookup[(str(row["package_id"]), str(row["package_clip_id"]), frame_idx)] = str(row["split_name"])
    return lookup


def _is_trusted_track(row: dict[str, Any]) -> bool:
    return (
        str(row.get("decision_bucket")) == "trusted_full"
        and _float(row.get("class_trust")) >= TRUSTED_CLASS_THRESHOLD
        and _float(row.get("box_trust")) >= TRUSTED_BOX_THRESHOLD
        and _int(row.get("duration_frames")) >= TRUSTED_MIN_TRACK_LENGTH
        and _float(row.get("mean_conf")) >= TRUSTED_MIN_MEAN_CONF
        and _float(row.get("edge_fraction")) <= TRUSTED_MAX_EDGE_FRACTION
        and _float(row.get("bbox_jitter")) <= TRUSTED_MAX_JITTER
    )


def _counts_by_split(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"train": 0, "val": 0, "test": 0}
    for image_name in {_image_name(item) for item in items}:
        split = next(item["split"] for item in items if _image_name(item) == image_name)
        counts[split] += 1
    return counts


def _counts_by_label_source(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[str(item["label_source"])] = counts.get(str(item["label_source"]), 0) + 1
    return counts


def _dataset_yaml(release_root: Path, class_list: list[str]) -> str:
    names = "".join(f"  {index}: {name}\n" for index, name in enumerate(class_list))
    return (
        f"path: {release_root}\n"
        "train: splits/train.txt\n"
        "val: splits/val.txt\n"
        "test: splits/test.txt\n"
        "names:\n"
        f"{names}"
    )


def _split_counts(total: int) -> dict[str, int]:
    if total <= 0:
        return {"oracle_test_hidden": 0, "oracle_val_hidden": 0, "gold_seed_pool": 0}
    test_count = max(1, round(total * 0.20))
    val_count = max(1, round(total * 0.15)) if total >= 3 else 0
    gold_count = max(1, round(total * 0.10)) if total >= 4 else 0
    while test_count + val_count + gold_count >= total and gold_count > 0:
        gold_count -= 1
    return {"oracle_test_hidden": test_count, "oracle_val_hidden": val_count, "gold_seed_pool": gold_count}


def _chunk_unit_id(row: dict[str, Any]) -> str:
    return "|".join(str(row[key]) for key in ("sequence_id", "chunk_start_frame_idx", "chunk_end_frame_idx"))


def _frame_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return (str(row["package_id"]), str(row["package_clip_id"]), _int(row["frame_idx"]))


def _release_split_name(split_name: str) -> str:
    if split_name == "oracle_val_hidden":
        return "val"
    if split_name == "oracle_test_hidden":
        return "test"
    return "train"


def _image_name(row: dict[str, Any]) -> str:
    return f"{row['package_clip_id']}__frame_{_int(row['frame_idx']):06d}.jpg"


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"egohumans_{digest}"


def _stable_key(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _looks_textual(path: Path) -> bool:
    with path.open("rb") as fh:
        return fh.read(1) in (b"{", b"[")


def _clamp_box(values: list[float], width: float, height: float) -> list[float]:
    x1, y1, x2, y2 = [float(value) for value in values]
    x1 = min(max(0.0, x1), width)
    x2 = min(max(0.0, x2), width)
    y1 = min(max(0.0, y1), height)
    y2 = min(max(0.0, y2), height)
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid box after clamping: {[x1, y1, x2, y2]}")
    return [x1, y1, x2, y2]


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
