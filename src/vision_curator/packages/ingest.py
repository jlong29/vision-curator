from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vision_curator.common.manifests import read_jsonl, write_jsonl
from vision_curator.common.models import PackageRecord
from vision_curator.common.paths import packages_index_path
from vision_curator.packages.validate import validate_phase2_package


def ingest_package(source: str | Path, store_root: str | Path) -> PackageRecord:
    validation = validate_phase2_package(source)
    package_id = validation["package_id"]
    root = Path(validation["root"]).resolve()
    record = PackageRecord(
        package_id=package_id,
        source_path=str(root),
        manifest_path=str(root / "manifest.json"),
        ingested_at=datetime.now(timezone.utc).isoformat(),
        clip_count=len(validation["clips"]),
        clip_ids=[clip["clip_id"] for clip in validation["clips"]],
        run_id=validation["run_id"],
        provenance=validation["provenance"],
    )

    index_path = packages_index_path(store_root)
    records = [row for row in read_jsonl(index_path) if row.get("package_id") != package_id]
    records.append(record.to_dict())
    records.sort(key=lambda row: row["package_id"])
    write_jsonl(index_path, records)
    return record


def load_package_record(store_root: str | Path, package_id: str) -> dict:
    for row in read_jsonl(packages_index_path(store_root)):
        if row.get("package_id") == package_id:
            return row
    raise KeyError(f"Package {package_id!r} is not indexed in {packages_index_path(store_root)}")
