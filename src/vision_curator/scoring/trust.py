from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from vision_curator.common.manifests import read_json
from vision_curator.common.models import TrackScore
from vision_curator.common.paths import track_scores_path
from vision_curator.common.manifests import write_jsonl
from vision_curator.packages.ingest import load_package_record
from vision_curator.packages.validate import validate_phase2_package


def score_package(package_id: str, store_root: str | Path) -> list[TrackScore]:
    package_record = load_package_record(store_root, package_id)
    validation = validate_phase2_package(package_record["source_path"])
    scores: list[TrackScore] = []
    for clip in validation["clips"]:
        scores.extend(_score_clip(package_id, clip))

    output = track_scores_path(store_root, package_id)
    write_jsonl(output, [score.to_dict() for score in scores])
    return scores


def score_rows(
    package_id: str,
    clip_id: str,
    rows: list[dict[str, Any]],
    frame_width: int = 640,
    frame_height: int = 512,
) -> list[TrackScore]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("track_id", "unknown"))].append(row)
    if not grouped:
        return [
            TrackScore(
                package_id=package_id,
                clip_id=clip_id,
                track_id="no_detection",
                class_trust=0.0,
                box_trust=1.0,
                duration_frames=0,
                mean_conf=0.0,
                min_conf=0.0,
                bbox_jitter=0.0,
                edge_fraction=0.0,
                decision_bucket="candidate_negative",
                review_priority=0.2,
            )
        ]
    return [
        _score_track(package_id, clip_id, track_id, track_rows, frame_width, frame_height)
        for track_id, track_rows in sorted(grouped.items())
    ]


def _score_clip(package_id: str, clip: dict[str, Any]) -> list[TrackScore]:
    clip_manifest = read_json(clip["manifest_path"])
    frame_width = int(clip_manifest.get("frame_width", clip_manifest.get("width", 640)))
    frame_height = int(clip_manifest.get("frame_height", clip_manifest.get("height", 512)))
    rows = _read_rows(clip["detections_path"])
    if not rows:
        rows = _read_rows(clip["tracks_path"])
    return score_rows(package_id, clip["clip_id"], rows, frame_width, frame_height)


def _score_track(
    package_id: str,
    clip_id: str,
    track_id: str,
    rows: list[dict[str, Any]],
    frame_width: int,
    frame_height: int,
) -> TrackScore:
    ordered = sorted(rows, key=lambda row: int(float(row.get("frame_index", row.get("frame", 0)))))
    confidences = [_float(row.get("confidence", row.get("conf", row.get("score", 0.0)))) for row in ordered]
    boxes = [_box(row) for row in ordered]
    duration_frames = len({int(float(row.get("frame_index", row.get("frame", index)))) for index, row in enumerate(ordered)})

    mean_conf = mean(confidences) if confidences else 0.0
    min_conf = min(confidences) if confidences else 0.0
    bbox_jitter = _bbox_jitter(boxes, frame_width, frame_height)
    edge_fraction = _edge_fraction(boxes, frame_width, frame_height)
    class_trust = _clamp(0.7 * mean_conf + 0.3 * min_conf + min(duration_frames, 30) / 300)
    box_trust = _clamp(1.0 - bbox_jitter * 2.0 - edge_fraction * 0.4)
    decision_bucket = _bucket(class_trust, box_trust, duration_frames)
    review_priority = round(_review_priority(class_trust, box_trust, edge_fraction, decision_bucket), 6)

    return TrackScore(
        package_id=package_id,
        clip_id=clip_id,
        track_id=track_id,
        class_trust=round(class_trust, 6),
        box_trust=round(box_trust, 6),
        duration_frames=duration_frames,
        mean_conf=round(mean_conf, 6),
        min_conf=round(min_conf, 6),
        bbox_jitter=round(bbox_jitter, 6),
        edge_fraction=round(edge_fraction, 6),
        decision_bucket=decision_bucket,
        review_priority=review_priority,
    )


def _read_rows(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)
    text = target.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        value = json.loads(text)
        if not isinstance(value, list):
            raise ValueError(f"Expected list in tabular fixture file: {target}")
        return [_normalize_row(row, target) for row in value]
    if text.startswith("{"):
        return [_normalize_row(json.loads(line), target) for line in text.splitlines() if line.strip()]
    with target.open("r", encoding="utf-8", newline="") as fh:
        return [_normalize_row(row, target) for row in csv.DictReader(fh)]


def _normalize_row(row: Any, source: Path) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError(f"Expected object row in {source}: {row!r}")
    return row


def _box(row: dict[str, Any]) -> tuple[float, float, float, float]:
    if isinstance(row.get("bbox"), list) and len(row["bbox"]) == 4:
        return tuple(_float(value) for value in row["bbox"])  # type: ignore[return-value]
    return (
        _float(row.get("x", row.get("bbox_x", 0.0))),
        _float(row.get("y", row.get("bbox_y", 0.0))),
        _float(row.get("w", row.get("width", row.get("bbox_w", 0.0)))),
        _float(row.get("h", row.get("height", row.get("bbox_h", 0.0)))),
    )


def _bbox_jitter(boxes: list[tuple[float, float, float, float]], frame_width: int, frame_height: int) -> float:
    if len(boxes) < 2:
        return 0.0
    values: list[float] = []
    diagonal = math.hypot(frame_width, frame_height)
    for previous, current in zip(boxes, boxes[1:]):
        px, py, pw, ph = previous
        cx, cy, cw, ch = current
        prev_center = (px + pw / 2, py + ph / 2)
        cur_center = (cx + cw / 2, cy + ch / 2)
        center_delta = math.hypot(cur_center[0] - prev_center[0], cur_center[1] - prev_center[1]) / diagonal
        prev_area = max(pw * ph, 1.0)
        cur_area = max(cw * ch, 1.0)
        area_delta = abs(cur_area - prev_area) / max(prev_area, cur_area)
        values.append(center_delta + area_delta)
    return _clamp(mean(values))


def _edge_fraction(boxes: list[tuple[float, float, float, float]], frame_width: int, frame_height: int) -> float:
    if not boxes:
        return 0.0
    edge_count = 0
    for x, y, w, h in boxes:
        if x <= 0 or y <= 0 or x + w >= frame_width or y + h >= frame_height:
            edge_count += 1
    return edge_count / len(boxes)


def _bucket(class_trust: float, box_trust: float, duration_frames: int) -> str:
    if duration_frames == 0:
        return "candidate_negative"
    if class_trust >= 0.75 and box_trust >= 0.70:
        return "trusted_full"
    if class_trust >= 0.75:
        return "trusted_class_weak_box"
    if class_trust < 0.20 and duration_frames <= 1:
        return "discard"
    return "ambiguous"


def _review_priority(class_trust: float, box_trust: float, edge_fraction: float, decision_bucket: str) -> float:
    if decision_bucket == "trusted_full":
        return 0.0
    if decision_bucket == "candidate_negative":
        return 0.2
    if decision_bucket == "discard":
        return 0.05
    return _clamp((1.0 - class_trust) * 0.7 + (1.0 - box_trust) * 0.8 + edge_fraction * 0.4)


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
