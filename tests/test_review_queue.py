from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vision_curator.common.manifests import read_jsonl
from vision_curator.packages.ingest import ingest_package
from vision_curator.review.queues import build_review_queue
from vision_curator.scoring.trust import score_package


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "phase2_valid"


class ReviewQueueTests(unittest.TestCase):
    def test_queue_builder_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ingest_package(FIXTURE, tmp)
            score_package("fixture_phase2_001", tmp)
            queue_id, output, items = build_review_queue("hard-case", tmp)
            rows = read_jsonl(output)
            self.assertTrue(queue_id.startswith("hard-case_"))
            self.assertEqual(len(items), len(rows))
            self.assertGreaterEqual(len(rows), 1)
            self.assertEqual(rows[0]["queue_kind"], "hard-case")


if __name__ == "__main__":
    unittest.main()
