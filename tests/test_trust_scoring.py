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
        self.assertIn("detection_density", first[0])
        self.assertIn("area_change", first[0])

    def test_required_buckets_are_reachable(self) -> None:
        cases = {
            "trusted_full": [
                {"frame_index": 0, "track_id": "t1", "confidence": 0.9, "x": 10, "y": 10, "w": 20, "h": 40},
                {"frame_index": 1, "track_id": "t1", "confidence": 0.8, "x": 11, "y": 10, "w": 20, "h": 40},
            ],
            "trusted_class_weak_box": [
                {"frame_index": 0, "track_id": "t1", "confidence": 0.9, "x": 0, "y": 10, "w": 20, "h": 40},
                {"frame_index": 1, "track_id": "t1", "confidence": 0.9, "x": 0, "y": 10, "w": 20, "h": 40},
            ],
            "ambiguous": [
                {"frame_index": 0, "track_id": "t1", "confidence": 0.45, "x": 10, "y": 10, "w": 20, "h": 40},
                {"frame_index": 1, "track_id": "t1", "confidence": 0.40, "x": 11, "y": 10, "w": 20, "h": 40},
            ],
            "discard": [
                {"frame_index": 0, "track_id": "t1", "confidence": 0.1, "x": 10, "y": 10, "w": 20, "h": 40},
            ],
        }
        observed = {
            bucket: score_rows("pkg", f"clip_{bucket}", rows)[0].decision_bucket
            for bucket, rows in cases.items()
        }
        observed["candidate_negative"] = score_rows("pkg", "clip_empty", [])[0].decision_bucket
        self.assertEqual(
            observed,
            {
                "trusted_full": "trusted_full",
                "trusted_class_weak_box": "trusted_class_weak_box",
                "ambiguous": "ambiguous",
                "discard": "discard",
                "candidate_negative": "candidate_negative",
            },
        )

    def test_score_package_writes_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ingest_package(FIXTURE, tmp)
            first_scores = [score.to_dict() for score in score_package("fixture_phase2_001", tmp)]
            second_scores = [score.to_dict() for score in score_package("fixture_phase2_001", tmp)]
            rows = read_jsonl(track_scores_path(tmp, "fixture_phase2_001"))
            self.assertEqual(first_scores, second_scores)
            self.assertEqual(len(first_scores), 2)
            self.assertEqual(len(rows), 2)
            self.assertIn("trusted_full", {row["decision_bucket"] for row in rows})
            self.assertEqual(rows[0]["source_path"], str(FIXTURE))
            self.assertEqual(rows[0]["run_id"], "fixture_run_001")
            self.assertEqual(rows[0]["frame_count"], 3)
            self.assertIn("detection_density", rows[0])


if __name__ == "__main__":
    unittest.main()
