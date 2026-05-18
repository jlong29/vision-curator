from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ClipRecord:
    package_id: str
    clip_id: str
    source_path: str
    clip_path: str
    manifest_path: str
    detections_path: str
    tracks_path: str
    run_id: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PackageRecord:
    package_id: str
    source_path: str
    manifest_path: str
    ingested_at: str
    clip_count: int
    clip_ids: list[str]
    run_id: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrackScore:
    package_id: str
    clip_id: str
    track_id: str
    source_path: str
    clip_path: str
    run_id: str
    class_trust: float
    box_trust: float
    duration_frames: int
    frame_count: int
    detection_count: int
    detection_density: float
    mean_conf: float
    min_conf: float
    bbox_jitter: float
    area_change: float
    edge_fraction: float
    decision_bucket: str
    review_priority: float
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    queue_id: str
    queue_kind: str
    package_id: str
    clip_id: str
    track_id: str
    source_path: str
    clip_path: str
    run_id: str
    decision_bucket: str
    reason: str
    priority: float
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetReleaseManifest:
    release_id: str
    source_package_ids: list[str]
    source_packages: list[dict[str, Any]]
    annotation_versions: list[str]
    annotation_status: str
    split_policy: str | dict[str, Any]
    label_policy: str | dict[str, Any]
    class_list: list[str]
    counts_by_split: dict[str, int]
    counts_by_label_source: dict[str, int]
    created_at: str
    creator: str = "vision-curator"
    tool_version: str = "0.1.0"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data["extra"]:
            data.pop("extra")
        return data
