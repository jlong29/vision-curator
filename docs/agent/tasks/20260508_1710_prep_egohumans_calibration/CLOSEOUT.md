# Closeout: Prep EgoHumans Calibration Readiness

## Decisions Made
- Kept generic Phase 2 validation backward compatible with existing fixture packages.
- Added stricter validation only for `dataset_source: egohumans`, because oracle-backed calibration requires source-frame alignment.
- Preserved expanded edge provenance fields through validation and ingest so downstream scores, queues, and releases can trace detector/tracker settings.
- Documented hidden oracle, revealed gold, and teacher pseudo labels as separate namespaces to prevent label leakage during calibration.
- Kept `.agent/` tracked for this repo and updated `AGENTS.md` so active task templates remain versioned while task-specific notes are archived at closeout.

## Gotchas / Invariants
- The 2026-04-30 handoff was stale relative to current code; the repo already had validation, ingest, scoring, review queues, CVAT command boundaries, and release building.
- Edge EgoHumans outputs use `package_clip_id`, `frame_idx`, and `x1/y1/x2/y2`; the repo previously favored `clip_id`, `frame_index`, and `x/y/w/h`.
- `candidate_negative` is not a gold negative until confirmed by human labeling or an explicit EgoHumans simulated reveal.

## New / Changed Commands
- No new CLI command names.
- Existing validation now accepts EgoHumans-style packages:
  - `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <pulled_egohumans_phase2_package>`

## TODOs / Follow-Ups
- Implement hidden oracle import/register workflow for EgoHumans annotations.
- Implement controlled reveal records for simulated gold labels.
- Extend release manifests/configs to identify hidden oracle, revealed gold, and teacher pseudo label provenance.
- Run the workflow on real pulled Edge Node package roots.

## Verification Evidence
- `python3 -m unittest tests.test_validate_phase2`: passed.
- `python3 -m unittest tests.test_trust_scoring`: passed.
- `python3 -m unittest`: passed, 17 tests.
- `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`: passed.
- `env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store`: passed.
- `env PYTHONPATH=src python3 -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store`: passed, 2 scores.
- `env PYTHONPATH=src python3 -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store`: passed, 1 item.
- `env PYTHONPATH=src python3 -m vision_curator.cli build-release --config configs/release/default.yaml --release-id smoke_release_20260508_2109`: passed.
- `python3 -m json.tool schemas/phase2_manifest.schema.json`: passed.
- `python3 -m compileall src`: passed.
