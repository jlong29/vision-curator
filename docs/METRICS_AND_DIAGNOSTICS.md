# Metrics and Diagnostics

## Trust Scores

`score-package` emits one JSONL-compatible row per scored track under:

```text
<curator_store>/scores/<package_id>/track_scores.parquet
```

The file may be JSONL during bring-up even though the external contract uses a `.parquet` path.

Key fields:

- `class_trust`: confidence that the track is a person.
- `box_trust`: confidence that the geometry is good enough for box regression.
- `detection_density`: detections divided by clip frame count when available.
- `bbox_jitter`: normalized temporal box instability.
- `area_change`: normalized sudden box area change.
- `edge_fraction`: fraction of boxes touching frame boundaries.
- `decision_bucket`: downstream data-use decision.
- `review_priority`: queue ordering signal.

## Decision Buckets

- `trusted_full`: candidate full supervision.
- `trusted_class_weak_box`: class likely valid, box geometry weak.
- `ambiguous`: review candidate.
- `candidate_negative`: no detector support; not a gold negative until confirmed or revealed.
- `discard`: weak signal, discard or low-volume audit only.

## EgoHumans Calibration Diagnostics

For EgoHumans, diagnostics must distinguish:

- teacher pseudo-label precision/recall against hidden oracle labels,
- queue yield against hidden oracle labels,
- revealed-gold growth curves,
- pseudo-only release results,
- oracle upper-bound results.

Hidden oracle labels are diagnostic/evaluation data. They must not influence trust scoring or queue generation unless they are explicitly copied into the revealed-gold namespace.
