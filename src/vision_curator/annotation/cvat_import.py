from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vision_curator.common.manifests import read_json, read_jsonl, write_json, write_jsonl
from vision_curator.common.paths import cvat_imports_dir


def import_cvat_annotations(task_root: str | Path, store_root: str | Path) -> Path:
    task = Path(task_root)
    manifest = read_json(task / "manifest.json")
    task_id = str(manifest.get("task_id", task.name))
    corrections_path = task / str(manifest.get("expected_import_file", "corrected_annotations.jsonl"))
    corrected = read_jsonl(corrections_path)

    import_root = cvat_imports_dir(store_root) / task_id
    if import_root.exists():
        raise FileExistsError(f"CVAT import already exists and will not be overwritten: {import_root}")
    import_root.mkdir(parents=True)
    write_jsonl(import_root / "corrected_annotations.jsonl", corrected)

    status = "imported" if corrections_path.exists() else "awaiting_corrected_annotations"
    import_manifest = {
        "task_id": task_id,
        "exchange": "cvat",
        "status": status,
        "source_task_path": str(task),
        "source_corrections_path": str(corrections_path),
        "corrected_annotation_count": len(corrected),
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "corrected_annotations": "corrected_annotations.jsonl",
        "notes": "A zero-count import marks the parser boundary; curated labels require human CVAT output.",
    }
    write_json(import_root / "manifest.json", import_manifest)
    return import_root
