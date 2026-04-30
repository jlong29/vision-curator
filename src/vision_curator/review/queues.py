from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from vision_curator.common.manifests import read_jsonl, write_jsonl
from vision_curator.common.models import ReviewItem
from vision_curator.common.paths import review_queues_dir


QUEUE_KINDS = {"hard-case", "ambiguous", "candidate-negative", "random-audit"}


def build_review_queue(queue_kind: str, store_root: str | Path, limit: int | None = None) -> tuple[str, Path, list[ReviewItem]]:
    if queue_kind not in QUEUE_KINDS:
        raise ValueError(f"Unsupported queue kind {queue_kind!r}; expected one of {sorted(QUEUE_KINDS)}")
    scores = _load_scores(store_root)
    selected = list(_select_scores(queue_kind, scores))
    selected.sort(key=lambda row: (-float(row.get("review_priority", 0.0)), row.get("package_id", ""), row.get("clip_id", ""), row.get("track_id", "")))
    if limit is not None:
        selected = selected[:limit]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    queue_id = f"{queue_kind}_{timestamp}"
    items = [
        ReviewItem(
            review_id=f"{queue_id}:{index:06d}",
            queue_id=queue_id,
            queue_kind=queue_kind,
            package_id=str(row.get("package_id", "")),
            clip_id=str(row.get("clip_id", "")),
            track_id=str(row.get("track_id", "")),
            decision_bucket=str(row.get("decision_bucket", "")),
            reason=_reason(queue_kind, row),
            priority=round(float(row.get("review_priority", 0.0)), 6),
        )
        for index, row in enumerate(selected, start=1)
    ]

    output = review_queues_dir(store_root) / f"{queue_id}.jsonl"
    write_jsonl(output, [item.to_dict() for item in items])
    return queue_id, output, items


def _load_scores(store_root: str | Path) -> list[dict]:
    scores_root = Path(store_root) / "scores"
    if not scores_root.exists():
        return []
    rows: list[dict] = []
    for score_path in sorted(scores_root.glob("*/track_scores.parquet")):
        rows.extend(read_jsonl(score_path))
    return rows


def _select_scores(queue_kind: str, scores: list[dict]) -> Iterable[dict]:
    if queue_kind == "ambiguous":
        return (row for row in scores if row.get("decision_bucket") == "ambiguous")
    if queue_kind == "candidate-negative":
        return (row for row in scores if row.get("decision_bucket") == "candidate_negative")
    if queue_kind == "random-audit":
        return (row for index, row in enumerate(scores) if index % 10 == 0)
    return (
        row
        for row in scores
        if row.get("decision_bucket") in {"ambiguous", "trusted_class_weak_box"}
        or float(row.get("edge_fraction", 0.0)) > 0.0
        or float(row.get("bbox_jitter", 0.0)) >= 0.15
    )


def _reason(queue_kind: str, row: dict) -> str:
    bucket = row.get("decision_bucket")
    if queue_kind == "candidate-negative":
        return "candidate negative audit"
    if queue_kind == "random-audit":
        return "deterministic random audit sample"
    if bucket == "trusted_class_weak_box":
        return "class trusted but box quality weak"
    if bucket == "ambiguous":
        return "ambiguous class or geometry"
    if float(row.get("edge_fraction", 0.0)) > 0.0:
        return "edge truncation"
    return "hard case"
