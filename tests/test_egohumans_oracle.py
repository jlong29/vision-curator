from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from vision_curator.cli import main
from vision_curator.common.manifests import read_json, read_jsonl
from vision_curator.oracle.egohumans import bbox_from_pose_keypoints, import_egohumans_oracle


class EgoHumansOracleImportTests(unittest.TestCase):
    def test_bbox_from_pose_keypoints_matches_upstream_padding_rule(self) -> None:
        entry = {
            "keypoints": [
                [10, 20, 0.9],
                [20, 30, 0.8],
                [30, 40, 0.7],
                [40, 50, 0.6],
                [50, 60, 0.95],
            ]
        }
        bbox = bbox_from_pose_keypoints(entry, width=100, height=80)
        self.assertIsNotNone(bbox)
        self.assertEqual(bbox[:4], [2.0, 12.0, 58.0, 68.0])
        self.assertAlmostEqual(bbox[4], 0.79)
        self.assertEqual(bbox[5], 5)
        self.assertEqual(bbox[6], 5)

    def test_import_writes_frame_index_oracle_labels_and_reveal_sets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phase2 = _write_phase2_package(root)
            dataset = _write_dataset(root)
            store = root / "store"

            result = import_egohumans_oracle(phase2, dataset, store)

            oracle_root = store / "oracle" / "egohumans"
            self.assertEqual(result["frame_count"], 2)
            self.assertEqual(result["oracle_label_count"], 1)
            self.assertTrue((oracle_root / "source_dataset_manifest.json").is_file())
            self.assertEqual(read_json(oracle_root / "normalized" / "class_map.json"), {"0": "person"})

            frame_rows = read_jsonl(oracle_root / "normalized" / "frame_index.jsonl")
            self.assertEqual(len(frame_rows), 2)
            self.assertEqual(frame_rows[0]["package_clip_id"], "005_legoassemble__aria01")
            self.assertEqual(frame_rows[0]["source_camera_id"], "aria01")
            self.assertEqual(frame_rows[0]["source_frame_idx"], 100)

            labels = read_jsonl(oracle_root / "normalized" / "oracle_labels.jsonl")
            self.assertEqual(len(labels), 1)
            self.assertEqual(labels[0]["label_namespace"], "oracle_hidden")
            self.assertEqual(labels[0]["class_name"], "person")
            self.assertEqual(labels[0]["box_source"], "benchmark_pose_projection_proxy")
            self.assertEqual(labels[0]["visibility_or_keypoint_metadata"]["human_name"], "person_a")
            self.assertEqual(labels[0]["box_xyxy"], [2.0, 12.0, 58.0, 68.0])

            gold_seed = read_jsonl(oracle_root / "reveal_sets" / "gold_seed_v0.jsonl")
            self.assertEqual(len(gold_seed), 1)
            self.assertEqual(gold_seed[0]["label_namespace"], "gold_revealed")
            self.assertEqual(gold_seed[0]["oracle_record_id"], labels[0]["record_id"])

            gold_negatives = read_jsonl(oracle_root / "reveal_sets" / "gold_negatives_v0.jsonl")
            self.assertEqual(len(gold_negatives), 1)
            self.assertEqual(gold_negatives[0]["class_name"], "negative_frame")
            self.assertIsNone(gold_negatives[0]["oracle_record_id"])

            manifest = read_json(oracle_root / "source_dataset_manifest.json")
            self.assertEqual(manifest["label_namespace"], "oracle_hidden")
            self.assertIn("proxy oracle labels", manifest["label_semantics"])

    def test_cli_import_egohumans_oracle_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phase2 = _write_phase2_package(root)
            dataset = _write_dataset(root)
            store = root / "store"

            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "import-egohumans-oracle",
                        "--phase2",
                        str(phase2),
                        "--dataset-root",
                        str(dataset),
                        "--store-root",
                        str(store),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue((store / "oracle" / "egohumans" / "normalized" / "oracle_labels.jsonl").is_file())


def _write_phase2_package(root: Path) -> Path:
    phase2 = root / "phase2"
    clip = phase2 / "clips" / "005_legoassemble__aria01"
    clip.mkdir(parents=True)
    (clip / "clip.mp4").write_bytes(b"fixture")
    (clip / "detections.parquet").write_bytes(b"fixture")
    (clip / "tracks.parquet").write_bytes(b"fixture")
    (phase2 / "READY.json").write_text('{"ready": true}\n', encoding="utf-8")
    _write_json(
        phase2 / "manifest.json",
        {
            "package_id": "005_legoassemble__phase2__fixture",
            "dataset_source": "egohumans",
            "activity": "lego_assembly",
            "package_type": "phase2_context_rich_clip_package",
            "producer_repo": "vision_api",
            "model_profile": "fixture_model",
            "model_artifact_version": "fixture_artifact",
            "detector_backend": "fixture_detector",
            "tracker_backend": "ultralytics_bytetrack_v1",
            "tracker_config_hash": "fixture_hash",
            "frame_stride": 1,
            "detection_confidence_threshold": 0.001,
            "nms_threshold": 0.7,
            "source_package_manifest_path": str(root / "source_package" / "manifest.json"),
            "source_benchmark_manifest_path": str(root / "benchmark" / "benchmark_manifest.json"),
            "clips": [{"package_clip_id": "005_legoassemble__aria01"}],
        },
    )
    _write_json(
        clip / "clip_manifest.json",
        {
            "package_clip_id": "005_legoassemble__aria01",
            "source_sequence_id": "005_legoassemble",
            "source_camera_id": "aria01",
            "start_frame_idx": 100,
            "end_frame_idx": 101,
            "fps": 30,
            "width": 100,
            "height": 80,
            "frame_count": 2,
            "source_frame_map_path": "source_frames.jsonl",
            "detections_path": "detections.parquet",
            "tracks_path": "tracks.parquet",
        },
    )
    _write_jsonl(
        clip / "source_frames.jsonl",
        [
            {
                "frame_idx": 0,
                "source_frame_idx": 100,
                "source_image_path": "images/000100.jpg",
                "pose_member": "poses/000100.json",
                "width": 100,
                "height": 80,
            },
            {
                "frame_idx": 1,
                "source_frame_idx": 101,
                "source_image_path": "images/000101.jpg",
                "pose_member": "poses/000101.json",
                "width": 100,
                "height": 80,
            },
        ],
    )
    return phase2


def _write_dataset(root: Path) -> Path:
    dataset = root / "dataset"
    poses = dataset / "poses"
    poses.mkdir(parents=True)
    _write_json(
        poses / "000100.json",
        [
            {
                "human_name": "aria01",
                "human_id": "viewer",
                "keypoints": [[1, 1, 0.9], [2, 2, 0.9], [3, 3, 0.9], [4, 4, 0.9], [5, 5, 0.9]],
            },
            {
                "human_name": "person_a",
                "human_id": "1",
                "keypoints": [
                    [10, 20, 0.9],
                    [20, 30, 0.8],
                    [30, 40, 0.7],
                    [40, 50, 0.6],
                    [50, 60, 0.95],
                ],
            },
        ],
    )
    _write_json(poses / "000101.json", [])
    return dataset


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
