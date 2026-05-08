# Task Memory

## Gotchas discovered
- The 2026-04-30 handoff was stale: current code already has validation, ingest, trust scoring, review queues, CVAT command boundaries, and release building.
- The Edge Node EgoHumans proposal uses `package_clip_id`, `frame_idx`, and `x1/y1/x2/y2`; existing code only handled `clip_id`, `frame_index`, and `x/y/w/h`.
- EgoHumans calibration needs source-frame maps to align teacher pseudo labels to hidden oracle annotations without leaking oracle labels into scoring.

## Decisions
- Keep generic Phase 2 validation backward compatible with existing fixture packages.
- Add stricter validation only when `dataset_source` is `egohumans`.
- Preserve expanded edge provenance fields through package/clip records.
- Treat hidden oracle, revealed gold, and teacher pseudo labels as separate namespaces in docs.

## Verification run
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
