from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from vision_curator.packages.validate import validate_phase2_package


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "phase2_valid"


class ValidatePhase2Tests(unittest.TestCase):
    def test_valid_phase2_fixture_passes(self) -> None:
        result = validate_phase2_package(FIXTURE)
        self.assertEqual(result["package_id"], "fixture_phase2_001")
        self.assertEqual(result["run_id"], "fixture_run_001")
        self.assertEqual(result["provenance"]["source_node_id"], "fixture_nx_001")
        self.assertEqual(len(result["clips"]), 1)
        self.assertEqual(result["clips"][0]["source_path"], str(FIXTURE))
        self.assertEqual(result["clips"][0]["run_id"], "fixture_run_001")

    def test_egohumans_phase2_package_clip_id_and_frame_map_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            shutil.copytree(FIXTURE, package)
            (package / "READY.json").write_text('{"status": "ready"}\n', encoding="utf-8")
            (package / "clips" / "clip_001" / "source_frames.jsonl").write_text(
                '{"frame_idx": 0, "source_frame_idx": 100, "source_image_path_or_name": "frame_000100.jpg"}\n',
                encoding="utf-8",
            )
            (package / "manifest.json").write_text(
                """
{
  "package_id": "egohumans_lego_001",
  "dataset_source": "egohumans",
  "activity": "lego_assembly",
  "package_type": "phase2_context_rich_clip_package",
  "producer_repo": "thermal-data-engine",
  "model_profile": "yolo11m",
  "model_artifact_version": "teacher_fixture",
  "detector_backend": "vision_api",
  "tracker_backend": "bytetrack",
  "tracker_config_hash": "fixture_hash",
  "frame_stride": 1,
  "detection_confidence_threshold": 0.1,
  "nms_threshold": 0.7,
  "clip_count": 1,
  "clips": [{"package_clip_id": "clip_001"}]
}
""".lstrip(),
                encoding="utf-8",
            )
            (package / "clips" / "clip_001" / "clip_manifest.json").write_text(
                """
{
  "package_clip_id": "clip_001",
  "source_sequence_id": "lego_seq_001",
  "source_camera_id": "cam_01",
  "start_frame_idx": 100,
  "end_frame_idx": 102,
  "fps": 30,
  "width": 640,
  "height": 512,
  "frame_count": 3,
  "source_frame_map_path": "source_frames.jsonl",
  "detections_path": "detections.parquet",
  "tracks_path": "tracks.parquet"
}
""".lstrip(),
                encoding="utf-8",
            )
            result = validate_phase2_package(package)
            self.assertEqual(result["package_id"], "egohumans_lego_001")
            self.assertEqual(result["clips"][0]["clip_id"], "clip_001")
            self.assertEqual(result["clips"][0]["provenance"]["dataset_source"], "egohumans")
            self.assertEqual(result["clips"][0]["provenance"]["source_sequence_id"], "lego_seq_001")

    def test_egohumans_missing_source_frame_map_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            shutil.copytree(FIXTURE, package)
            (package / "manifest.json").write_text(
                """
{
  "package_id": "egohumans_lego_001",
  "dataset_source": "egohumans",
  "activity": "lego_assembly",
  "package_type": "phase2_context_rich_clip_package",
  "producer_repo": "thermal-data-engine",
  "model_profile": "yolo11m",
  "model_artifact_version": "teacher_fixture",
  "detector_backend": "vision_api",
  "tracker_backend": "bytetrack",
  "tracker_config_hash": "fixture_hash",
  "frame_stride": 1,
  "detection_confidence_threshold": 0.1,
  "nms_threshold": 0.7,
  "clips": [{"package_clip_id": "clip_001"}]
}
""".lstrip(),
                encoding="utf-8",
            )
            (package / "clips" / "clip_001" / "clip_manifest.json").write_text(
                """
{
  "package_clip_id": "clip_001",
  "source_sequence_id": "lego_seq_001",
  "source_camera_id": "cam_01",
  "start_frame_idx": 100,
  "end_frame_idx": 102,
  "fps": 30,
  "width": 640,
  "height": 512,
  "frame_count": 3,
  "source_frame_map_path": "source_frames.jsonl",
  "detections_path": "detections.parquet",
  "tracks_path": "tracks.parquet"
}
""".lstrip(),
                encoding="utf-8",
            )
            with self.assertRaises(FileNotFoundError):
                validate_phase2_package(package)

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            shutil.copytree(FIXTURE, package)
            (package / "clips" / "clip_001" / "tracks.parquet").unlink()
            with self.assertRaises(FileNotFoundError):
                validate_phase2_package(package)

    def test_missing_root_manifest_package_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            shutil.copytree(FIXTURE, package)
            (package / "manifest.json").write_text('{"clips": [{"clip_id": "clip_001"}]}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_phase2_package(package)

    def test_malformed_manifest_clip_entry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            shutil.copytree(FIXTURE, package)
            (package / "manifest.json").write_text(
                '{"package_id": "fixture_phase2_001", "clips": [{"name": "clip_001"}]}\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                validate_phase2_package(package)

    def test_missing_clip_manifest_clip_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            shutil.copytree(FIXTURE, package)
            (package / "clips" / "clip_001" / "clip_manifest.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_phase2_package(package)


if __name__ == "__main__":
    unittest.main()
