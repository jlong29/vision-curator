from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vision_curator.common.manifests import read_jsonl
from vision_curator.common.paths import track_scores_path
from vision_curator.packages.ingest import ingest_package
from vision_curator.scoring.trust import score_package, score_rows


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "phase2_valid"


class TrustScoringTests(unittest.TestCase):
    def test_trust_scoring_is_deterministic(self) -> None:
        rows = [
            {"frame_index": 0, "track_id": "t1", "confidence": 0.9, "x": 10, "y": 10, "w": 20, "h": 40},
            {"frame_index": 1, "track_id": "t1", "confidence": 0.8, "x": 11, "y": 10, "w": 20, "h": 40},
        ]
        first = [score.to_dict() for score in score_rows("pkg", "clip", rows)]
        second = [score.to_dict() for score in score_rows("pkg", "clip", rows)]
        self.assertEqual(first, second)
        self.assertEqual(first[0]["decision_bucket"], "trusted_full")

    def test_score_package_writes_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ingest_package(FIXTURE, tmp)
            scores = score_package("fixture_phase2_001", tmp)
            rows = read_jsonl(track_scores_path(tmp, "fixture_phase2_001"))
            self.assertEqual(len(scores), 2)
            self.assertEqual(len(rows), 2)
            self.assertIn("trusted_full", {row["decision_bucket"] for row in rows})


if __name__ == "__main__":
    unittest.main()
