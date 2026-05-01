# .agent/MEMORY.md (scratch)

**Task:** align curator with 2026-04-30 next steps  
**Last updated:** 2026-05-01 02:25 UTC

## Goal / status
- Phase 2 implementation completed against local fixtures.
- No real edge Phase 2 packages were used.
- CVAT true correction roundtrip remains blocked on Dr. Long labeling exported tasks.

## Repro commands
- `python3 -m unittest`
- `python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`
- `python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store`
- `python3 -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store`
- `python3 -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store`
- `python3 -m vision_curator.cli build-review-queue --queue-kind ambiguous --store-root /tmp/vision-curator-smoke-store`
- `python3 -m vision_curator.cli build-review-queue --queue-kind candidate-negative --store-root /tmp/vision-curator-smoke-store`
- `python3 -m vision_curator.cli build-review-queue --queue-kind random-audit --store-root /tmp/vision-curator-smoke-store`
- `python3 -m vision_curator.cli export-cvat-task --queue /tmp/vision-curator-smoke-store/review_queues/hard-case_20260501T022523Z.jsonl --store-root /tmp/vision-curator-smoke-store --task-id smoke_cvat_20260501T022523Z`
- `python3 -m vision_curator.cli import-cvat-annotations --task-root /tmp/vision-curator-smoke-store/annotation_exports/cvat/smoke_cvat_20260501T022523Z --store-root /tmp/vision-curator-smoke-store`
- `python3 -m vision_curator.cli build-release --config configs/release/default.yaml --release-id smoke_release_20260430`

## Hypotheses + evidence
- Handoff objectives can be met with fixture-backed stdlib-only behavior; unit suite now covers ingest, scoring, queues, CVAT exchange boundaries, and release provenance.

## Decisions (and why)
- Preserve raw package immutability by indexing source paths and provenance only; no raw clip copying added.
- Store Phase 2 provenance opportunistically from known manifest fields instead of inventing defaults.
- Keep trust scoring deterministic and transparent; added detection density and area-change fields for later threshold tuning.
- Represent CVAT as local export/import manifests so core tests do not require a live CVAT server.
- Mark default release as `annotation_status: pseudo_only` so trainer consumers do not confuse fixture releases with human-verified data.

## Gotchas discovered (promote at closeout)
- `tests/fixtures/phase2_valid` has no candidate-negative score after scoring, so the smoke `candidate-negative` queue is valid but empty. Candidate-negative behavior is covered with synthetic queue test rows.
- The release smoke command created `build/releases/smoke_release_20260430`; `build/` is ignored and release immutability will reject rerunning the same release id unless the directory is removed manually or a new id is used.

## Verification run
- Command(s): focused unit tests, full `python3 -m unittest`, fixture CLI smoke path, CVAT export/import smoke, release smoke.
- Outcome(s): all unit tests passed: 14 tests OK. CLI smoke commands completed successfully.

## Next steps
- Run closeout procedure: promote stable docs, archive `.agent` scratch files under `docs/agent/tasks/<task_slug>/`, restore scratch templates, and commit.
