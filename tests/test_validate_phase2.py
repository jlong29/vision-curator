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
        self.assertEqual(len(result["clips"]), 1)

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            shutil.copytree(FIXTURE, package)
            (package / "clips" / "clip_001" / "tracks.parquet").unlink()
            with self.assertRaises(FileNotFoundError):
                validate_phase2_package(package)


if __name__ == "__main__":
    unittest.main()
