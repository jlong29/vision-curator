# Workspace Next Steps — `vision-curator`

## Context
This packet started as the desktop-side execution slice for **Bootstrap vision next wave across edge, curator, and trainer**. It has now been reconciled with the v2 system plan and the completed Xavier Edge Node EgoHumans package run.

Read first:
- `AGENTS.md`
- `docs/architecture.md`
- `docs/package_contracts.md`
- `docs/review_queues.md`
- `docs/dataset_releases.md`
- `docs/annotation_policy.md`
- `docs/SYSTEM_DESIGN_v2.md`
- `docs/PROPOSED_PLAN_v2.md`
- `docs/EGOHUMANS_CALIBRATION_EXECUTIVE_SUMMARY.md`
- `docs/EGOHUMANS_EDGE_NODE_PROCESSING_PROPOSAL.md`

## Current State
The original bring-up objectives are no longer all future work. The repo now has:

- Phase 2 package validation and immutable source-path ingest.
- Canonical package index records under `<curator_store>/indexes/packages.jsonl`.
- Deterministic trust scoring with separate `class_trust`, `box_trust`, feature fields, and decision buckets.
- Review queue generation for `hard-case`, `ambiguous`, `candidate-negative`, and `random-audit`.
- CVAT export/import command boundaries that remain optional for core tests.
- Immutable draft dataset release building and validation.

The important remaining work is not repo skeleton bring-up; it is real data execution and EgoHumans calibration artifact production.

## Mission for the Next Task
Consume the completed Edge Node EgoHumans Lego Assembly Phase 2 outputs and produce the curation artifacts needed for training experiments:

1. validate and ingest pulled edge packages,
2. compute trust scores from teacher outputs only,
3. build review queues,
4. import or register EgoHumans ground truth as hidden oracle labels,
5. reveal a controlled subset as gold labels,
6. publish pseudo-only and oracle/revealed-gold calibration releases for `vision-trainer`,
7. record provenance so ablations can compare teacher, gold-only, naive pseudo, track-aware pseudo, review-revealed, and oracle upper-bound runs.

Do not move training into this repo. Do not mutate raw packages. Do not require CVAT or FiftyOne for core tests.

## Edge Package Expectations
The edge output should follow `docs/EGOHUMANS_EDGE_NODE_PROCESSING_PROPOSAL.md`.

Expected package-level fields include:
- `dataset_source: egohumans`
- `activity: lego_assembly`
- `package_type`
- `producer_repo`
- `model_profile`
- `model_artifact_version`
- `detector_backend`
- `tracker_backend: bytetrack`
- `tracker_config_hash`
- `frame_stride`
- `detection_confidence_threshold`
- `nms_threshold`
- `clips`

Expected clip-level fields include:
- `package_clip_id`
- `source_sequence_id`
- `source_camera_id`
- `start_frame_idx`, `end_frame_idx`
- `fps`, `width`, `height`, `frame_count`
- `source_frame_map_path`
- `detections_path`
- `tracks_path`

`source_frame_map_path` must resolve locally. It is the bridge between edge pseudo labels and hidden EgoHumans oracle annotations.

## Human-in-the-Loop Gates
These remain real dependencies.

### Gate A, Desktop Package Pull
Before real curation:
- pull completed Phase 2 packages from the NX spool,
- validate each package locally,
- keep the raw package roots immutable.

### Gate B, CVAT or Simulated Reveal
Before claiming gold negatives or frozen hard-case slices:
- label selected queues in CVAT, or
- for EgoHumans calibration only, reveal a controlled oracle subset as simulated human labels.

Hidden oracle labels must not leak into trust scoring or pseudo-label selection.

### Gate C, Release Publication for Trainer
After trust scoring and any chosen reveal policy:
- publish at least one pseudo-only smoke release,
- publish calibration releases with explicit `annotation_status`, `label_policy`, source package provenance, and oracle/reveal metadata,
- hand release roots to `vision-trainer`.

## Verification
Minimum local fixture checks:

```bash
python3 -m unittest
env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid
env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store
env PYTHONPATH=src python3 -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store
env PYTHONPATH=src python3 -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store
env PYTHONPATH=src python3 -m vision_curator.cli build-release --config configs/release/default.yaml --release-id smoke_release_20260430
```

For real EgoHumans packages, add:

```bash
env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <pulled_egohumans_phase2_package>
env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source <pulled_egohumans_phase2_package> --store-root <curator_store>
env PYTHONPATH=src python3 -m vision_curator.cli score-package --package-id <package_id> --store-root <curator_store>
```

## Deliver Back to Workspace
Report:
- raw package roots used,
- package IDs ingested,
- trust score output paths,
- review queue IDs and item counts,
- whether labels are hidden oracle, revealed gold, or teacher pseudo labels,
- release paths and manifest shapes handed to `vision-trainer`,
- blocker status for CVAT labeling or simulated reveal policy.
