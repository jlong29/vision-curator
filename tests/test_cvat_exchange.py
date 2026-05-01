from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vision_curator.annotation.cvat_export import export_cvat_task
from vision_curator.annotation.cvat_import import import_cvat_annotations
from vision_curator.common.manifests import read_json, read_jsonl, write_jsonl


class CvatExchangeTests(unittest.TestCase):
    def test_export_writes_task_manifest_and_review_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_path = Path(tmp) / "review_queues" / "hard-case_001.jsonl"
            write_jsonl(queue_path, [_review_item()])

            task_root = export_cvat_task(queue_path, tmp, "task_001")

            manifest = read_json(task_root / "manifest.json")
            rows = read_jsonl(task_root / "review_items.jsonl")
            self.assertEqual(manifest["task_id"], "task_001")
            self.assertEqual(manifest["status"], "blocked_on_human_labeling")
            self.assertTrue(manifest["human_labeling_required"])
            self.assertEqual(manifest["labeling_owner"], "Dr. Long")
            self.assertEqual(manifest["expected_import_file"], "corrected_annotations.jsonl")
            self.assertEqual(rows[0]["review_id"], "review_001")
            with self.assertRaises(FileExistsError):
                export_cvat_task(queue_path, tmp, "task_001")

    def test_import_represents_placeholder_and_corrected_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_path = Path(tmp) / "review_queues" / "hard-case_001.jsonl"
            write_jsonl(queue_path, [_review_item()])
            task_root = export_cvat_task(queue_path, tmp, "task_001")

            placeholder_root = import_cvat_annotations(task_root, tmp)
            placeholder = read_json(placeholder_root / "manifest.json")
            self.assertEqual(placeholder["status"], "awaiting_corrected_annotations")
            self.assertEqual(placeholder["corrected_annotation_count"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            queue_path = Path(tmp) / "review_queues" / "hard-case_001.jsonl"
            write_jsonl(queue_path, [_review_item()])
            task_root = export_cvat_task(queue_path, tmp, "task_002")
            write_jsonl(
                task_root / "corrected_annotations.jsonl",
                [{"review_id": "review_001", "package_id": "pkg", "clip_id": "clip", "annotations": []}],
            )

            import_root = import_cvat_annotations(task_root, tmp)
            manifest = read_json(import_root / "manifest.json")
            corrected = read_jsonl(import_root / "corrected_annotations.jsonl")
            self.assertEqual(manifest["status"], "imported")
            self.assertEqual(manifest["corrected_annotation_count"], 1)
            self.assertEqual(corrected[0]["review_id"], "review_001")


def _review_item() -> dict:
    return {
        "review_id": "review_001",
        "queue_id": "hard-case_001",
        "queue_kind": "hard-case",
        "package_id": "pkg",
        "clip_id": "clip",
        "track_id": "track",
        "source_path": "/phase2/pkg",
        "clip_path": "/phase2/pkg/clips/clip/clip.mp4",
        "run_id": "run_001",
        "decision_bucket": "ambiguous",
        "reason": "hard case",
        "priority": 0.8,
        "provenance": {"source_node_id": "nx_001"},
    }


if __name__ == "__main__":
    unittest.main()
