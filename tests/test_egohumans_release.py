from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vision_curator.common.manifests import read_json, read_jsonl, write_json, write_jsonl
from vision_curator.releases.egohumans import build_egohumans_release, build_split_assignments
from vision_curator.releases.validate import validate_release


class EgoHumansReleaseTests(unittest.TestCase):
    def test_split_assignments_keep_camera_views_together(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store"
            oracle = store / "oracle" / "egohumans"
            frame_rows = []
            for camera in ("aria01", "aria02"):
                for frame_idx in range(4):
                    frame_rows.append(_frame_row("pkg", f"seq__{camera}", "seq", camera, frame_idx, Path(tmp) / f"{camera}_{frame_idx}.jpg"))
            write_jsonl(oracle / "normalized" / "frame_index.jsonl", frame_rows)

            output = build_split_assignments(store, chunk_size=2)
            rows = read_jsonl(output)

            by_unit: dict[str, set[str]] = {}
            for row in rows:
                by_unit.setdefault(row["unit_id"], set()).add(row["split_name"])
            self.assertTrue(by_unit)
            self.assertTrue(all(len(split_names) == 1 for split_names in by_unit.values()))

    def test_gold_only_release_forbids_oracle_train_and_reuses_oracle_for_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = _write_release_fixture(Path(tmp))
            release_store = Path(tmp) / "releases"

            result = build_egohumans_release("gold_only_v0", "gold_only_v0", store, release_store)
            validate_release(result.release_root)

            manifest = read_json(result.release_root / "manifest.json")
            self.assertEqual(manifest["release_family"], "gold_only_v0")
            self.assertTrue(manifest["realistic_calibration_loop"])
            self.assertIn("oracle_hidden", manifest["forbidden_label_namespaces_for_train"])
            self.assertEqual(manifest["label_namespaces_used_for_train"], ["gold_revealed"])
            self.assertEqual(manifest["split_policy"]["name"], "egohumans_split_assignments_v0")
            self.assertEqual(manifest["label_policy"]["release_family"], "gold_only_v0")
            self.assertIn("provenance/label_items.jsonl", manifest["provenance_records"])
            self.assertEqual(manifest["counts_by_split"], {"train": 1, "val": 1, "test": 1})
            self.assertIn("names:\n  0: person\n", (result.release_root / "dataset.yaml").read_text(encoding="utf-8"))
            train_labels = (result.release_root / "labels" / "seq__aria01__frame_000000.txt").read_text(encoding="utf-8")
            val_labels = (result.release_root / "labels" / "seq__aria01__frame_000001.txt").read_text(encoding="utf-8")
            self.assertIn("0 ", train_labels)
            self.assertIn("0 ", val_labels)

    def test_oracle_upper_bound_is_diagnostic_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = _write_release_fixture(Path(tmp))
            release_store = Path(tmp) / "releases"

            result = build_egohumans_release("oracle_upper_bound", "oracle_upper_bound", store, release_store)
            validate_release(result.release_root)

            manifest = read_json(result.release_root / "manifest.json")
            self.assertEqual(manifest["release_family"], "oracle_upper_bound")
            self.assertTrue(manifest["oracle_upper_bound"])
            self.assertFalse(manifest["realistic_calibration_loop"])
            self.assertEqual(manifest["label_namespaces_used_for_train"], ["oracle_hidden"])
            self.assertEqual(manifest["forbidden_label_namespaces_for_train"], [])


def _write_release_fixture(root: Path) -> Path:
    store = root / "store"
    oracle = store / "oracle" / "egohumans"
    image_paths = [root / f"frame_{idx}.jpg" for idx in range(3)]
    for image_path in image_paths:
        image_path.write_bytes(b"fixture image")
    frames = [
        _frame_row("pkg", "seq__aria01", "seq", "aria01", idx, image_paths[idx])
        for idx in range(3)
    ]
    labels = [
        _oracle_label("oracle_0", frames[0], [10, 10, 50, 60]),
        _oracle_label("oracle_1", frames[1], [15, 15, 55, 65]),
        _oracle_label("oracle_2", frames[2], [20, 20, 60, 70]),
    ]
    write_jsonl(oracle / "normalized" / "frame_index.jsonl", frames)
    write_jsonl(oracle / "normalized" / "oracle_labels.jsonl", labels)
    write_jsonl(
        oracle / "reveal_sets" / "gold_seed_v0.jsonl",
        [
            {
                "label_namespace": "gold_revealed",
                "oracle_record_id": "oracle_0",
                "package_id": "pkg",
                "package_clip_id": "seq__aria01",
                "frame_idx": 0,
                "reveal_set": "gold_seed_v0",
            }
        ],
    )
    write_jsonl(
        oracle / "reveal_sets" / "review_revealed_gold_v0.jsonl",
        [
            {
                "label_namespace": "gold_revealed",
                "oracle_record_id": "oracle_0",
                "package_id": "pkg",
                "package_clip_id": "seq__aria01",
                "frame_idx": 0,
                "reveal_set": "review_revealed_gold_v0",
            }
        ],
    )
    write_json(oracle / "source_dataset_manifest.json", {"imported_package_ids": ["pkg"], "label_namespace": "oracle_hidden"})
    write_jsonl(
        oracle / "splits" / "split_assignments_v0.jsonl",
        [
            _split_row("pkg", "seq__aria01", "seq", "aria01", 0, "gold_seed_pool"),
            _split_row("pkg", "seq__aria01", "seq", "aria01", 1, "oracle_val_hidden"),
            _split_row("pkg", "seq__aria01", "seq", "aria01", 2, "oracle_test_hidden"),
        ],
    )
    write_jsonl(
        store / "indexes" / "packages.jsonl",
        [
            {
                "package_id": "pkg",
                "source_path": str(root / "missing_phase2"),
                "manifest_path": str(root / "missing_phase2" / "manifest.json"),
                "ingested_at": "2026-05-12T00:00:00+00:00",
                "clip_count": 1,
                "clip_ids": ["seq__aria01"],
                "run_id": "run",
                "provenance": {},
            }
        ],
    )
    return store


def _frame_row(package_id: str, clip_id: str, sequence: str, camera: str, frame_idx: int, image_path: Path) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_clip_id": clip_id,
        "frame_idx": frame_idx,
        "source_sequence_id": sequence,
        "source_camera_id": camera,
        "source_frame_idx": frame_idx + 1,
        "source_image_path_or_name": str(image_path),
        "width": 100,
        "height": 100,
    }


def _oracle_label(record_id: str, frame: dict[str, object], box: list[int]) -> dict[str, object]:
    return {
        "record_id": record_id,
        "label_namespace": "oracle_hidden",
        "package_id": frame["package_id"],
        "package_clip_id": frame["package_clip_id"],
        "frame_idx": frame["frame_idx"],
        "sequence_id": frame["source_sequence_id"],
        "camera_id": frame["source_camera_id"],
        "source_frame_idx": frame["source_frame_idx"],
        "class_name": "person",
        "box_xyxy": box,
    }


def _split_row(package_id: str, clip_id: str, sequence: str, camera: str, frame_idx: int, split: str) -> dict[str, object]:
    return {
        "split_version": "split_assignments_v0",
        "unit_id": f"{sequence}|{frame_idx}|{frame_idx}",
        "package_id": package_id,
        "package_clip_id": clip_id,
        "sequence_id": sequence,
        "camera_id": camera,
        "frame_start_idx": frame_idx,
        "frame_end_idx": frame_idx,
        "split_name": split,
        "split_rationale": "fixture",
    }


if __name__ == "__main__":
    unittest.main()
