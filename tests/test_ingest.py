from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vision_curator.common.manifests import read_jsonl
from vision_curator.common.paths import packages_index_path
from vision_curator.packages.ingest import ingest_package


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "phase2_valid"


class IngestTests(unittest.TestCase):
    def test_ingest_writes_package_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = ingest_package(FIXTURE, tmp)
            rows = read_jsonl(packages_index_path(tmp))
            self.assertEqual(record.package_id, "fixture_phase2_001")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["package_id"], "fixture_phase2_001")
            self.assertEqual(rows[0]["clip_count"], 1)
            self.assertEqual(rows[0]["clip_ids"], ["clip_001"])
            self.assertEqual(rows[0]["run_id"], "fixture_run_001")
            self.assertEqual(rows[0]["provenance"]["completion_state"], "complete")
            self.assertEqual(rows[0]["provenance"]["runtime"]["model_id"], "thermal-person-fixture")


if __name__ == "__main__":
    unittest.main()
