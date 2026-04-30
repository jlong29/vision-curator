from __future__ import annotations

from pathlib import Path


def indexes_dir(store_root: str | Path) -> Path:
    return Path(store_root) / "indexes"


def packages_index_path(store_root: str | Path) -> Path:
    return indexes_dir(store_root) / "packages.jsonl"


def scores_dir(store_root: str | Path, package_id: str) -> Path:
    return Path(store_root) / "scores" / package_id


def track_scores_path(store_root: str | Path, package_id: str) -> Path:
    return scores_dir(store_root, package_id) / "track_scores.parquet"


def review_queues_dir(store_root: str | Path) -> Path:
    return Path(store_root) / "review_queues"
