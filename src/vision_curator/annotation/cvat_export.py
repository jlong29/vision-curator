from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vision_curator.common.manifests import read_jsonl, write_json, write_jsonl
from vision_curator.common.paths import cvat_exports_dir


def export_cvat_task(queue_path: str | Path, store_root: str | Path, task_id: str | None = None) -> Path:
    queue = Path(queue_path)
    items = read_jsonl(queue)
    if not items:
        raise ValueError(f"Cannot export empty review queue to CVAT: {queue}")

    resolved_task_id = task_id or queue.stem
    task_root = cvat_exports_dir(store_root) / resolved_task_id
    if task_root.exists():
        raise FileExistsError(f"CVAT export task already exists and will not be overwritten: {task_root}")
    task_root.mkdir(parents=True)

    items_path = task_root / "review_items.jsonl"
    write_jsonl(items_path, items)

    manifest = {
        "task_id": resolved_task_id,
        "exchange": "cvat",
        "status": "blocked_on_human_labeling",
        "human_labeling_required": True,
        "labeling_owner": "Dr. Long",
        "queue_id": str(items[0].get("queue_id", "")),
        "queue_kind": str(items[0].get("queue_kind", "")),
        "source_queue_path": str(queue),
        "item_count": len(items),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "review_items": "review_items.jsonl",
        "expected_import_file": "corrected_annotations.jsonl",
        "import_contract": {
            "format": "jsonl",
            "required_fields": ["review_id", "package_id", "clip_id", "annotations"],
            "notes": "Place corrected CVAT-derived annotations in corrected_annotations.jsonl before import.",
        },
    }
    write_json(task_root / "manifest.json", manifest)
    return task_root
