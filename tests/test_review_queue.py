from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vision_curator.common.manifests import read_jsonl
from vision_curator.common.manifests import write_jsonl
from vision_curator.common.paths import track_scores_path
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
            self.assertEqual(rows[0]["source_path"], str(FIXTURE))
            self.assertEqual(rows[0]["run_id"], "fixture_run_001")

    def test_all_queue_kinds_preserve_provenance_and_semantic_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_jsonl(
                track_scores_path(tmp, "pkg"),
                [
                    _score("pkg", "clip_001", "trusted", "trusted_full", 0.95, 0.95, 0.0, 0.0, 0.0),
                    _score("pkg", "clip_002", "weak_box", "trusted_class_weak_box", 0.92, 0.30, 0.1, 0.2, 0.8),
                    _score("pkg", "clip_003", "ambig_hi", "ambiguous", 0.58, 0.70, 0.0, 0.0, 0.7),
                    _score("pkg", "clip_004", "ambig_lo", "ambiguous", 0.48, 0.90, 0.0, 0.0, 0.4),
                    _score("pkg", "clip_005", "negative", "candidate_negative", 0.0, 1.0, 0.0, 0.0, 0.2),
                    _score("pkg", "clip_006", "reject", "discard", 0.10, 0.95, 0.0, 0.0, 0.05),
                ],
            )

            hard_case_id, hard_case_output, hard_case_items = build_review_queue("hard-case", tmp)
            ambiguous_id, ambiguous_output, ambiguous_items = build_review_queue("ambiguous", tmp)
            candidate_id, candidate_output, candidate_items = build_review_queue("candidate-negative", tmp)
            random_id, random_output, random_items = build_review_queue("random-audit", tmp)

            self.assertTrue(hard_case_id.startswith("hard-case_"))
            self.assertTrue(ambiguous_id.startswith("ambiguous_"))
            self.assertTrue(candidate_id.startswith("candidate-negative_"))
            self.assertTrue(random_id.startswith("random-audit_"))
            self.assertEqual(hard_case_items[0].track_id, "weak_box")
            self.assertEqual([item.track_id for item in ambiguous_items], ["ambig_hi", "ambig_lo"])
            self.assertEqual([item.track_id for item in candidate_items], ["negative"])
            self.assertEqual([item.track_id for item in random_items], ["trusted"])

            for output in (hard_case_output, ambiguous_output, candidate_output, random_output):
                rows = read_jsonl(output)
                self.assertGreaterEqual(len(rows), 1)
                self.assertEqual(rows[0]["source_path"], "/phase2/pkg")
                self.assertEqual(rows[0]["clip_path"], "/phase2/pkg/clips/clip.mp4")
                self.assertEqual(rows[0]["run_id"], "run_001")
                self.assertEqual(rows[0]["provenance"]["source_node_id"], "nx_001")


def _score(
    package_id: str,
    clip_id: str,
    track_id: str,
    decision_bucket: str,
    class_trust: float,
    box_trust: float,
    edge_fraction: float,
    bbox_jitter: float,
    review_priority: float,
) -> dict:
    return {
        "package_id": package_id,
        "clip_id": clip_id,
        "track_id": track_id,
        "source_path": "/phase2/pkg",
        "clip_path": "/phase2/pkg/clips/clip.mp4",
        "run_id": "run_001",
        "class_trust": class_trust,
        "box_trust": box_trust,
        "duration_frames": 3,
        "frame_count": 3,
        "detection_count": 3,
        "detection_density": 1.0,
        "mean_conf": class_trust,
        "min_conf": class_trust,
        "bbox_jitter": bbox_jitter,
        "area_change": 0.0,
        "edge_fraction": edge_fraction,
        "decision_bucket": decision_bucket,
        "review_priority": review_priority,
        "provenance": {"source_node_id": "nx_001"},
    }


if __name__ == "__main__":
    unittest.main()
