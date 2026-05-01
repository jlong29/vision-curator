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
