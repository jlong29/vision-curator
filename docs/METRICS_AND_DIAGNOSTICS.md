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

### Current Release Interpretation Notes

The current `gold_plus_trusted_tracks_v0` release is intentionally conservative. Its training set has 626 objects (`gold_seed_v0=574`, `trusted_track=52`), while validation and test have 1371 and 1695 oracle-evaluation objects respectively. Treat this as a precision-first ablation; it may be too sparse for training usefulness.

Before relaxing trusted-track thresholds, compare trusted pseudo labels against hidden oracle labels on non-test calibration data. Do not use the hidden test split to tune thresholds.

### Release Count Snapshot

- `gold_only_v0`: train 567, val 904, test 1098 images; label sources `gold_seed_v0=574`, `oracle_eval=3066`.
- `gold_plus_naive_pseudo_v0`: train 3707, val 904, test 1098 images; label sources `gold_seed_v0=574`, `naive_confidence=4962`, `oracle_eval=3066`.
- `gold_plus_trusted_tracks_v0`: train 613, val 904, test 1098 images; label sources `gold_seed_v0=574`, `trusted_track=52`, `oracle_eval=3066`.
- `gold_plus_review_revealed_v1`: train 820, val 904, test 1098 images; label sources `gold_seed_v0=574`, `review_revealed_gold_v0=263`, `oracle_eval=3066`.
- `oracle_upper_bound`: train 3977, val 904, test 1098 images; label sources `oracle_upper_bound_train=5773`, `oracle_eval=3066`.
