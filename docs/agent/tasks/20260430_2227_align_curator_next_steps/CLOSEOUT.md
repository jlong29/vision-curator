# Closeout — Align Curator Next Steps

## Decisions Made
- Preserve raw package immutability by indexing source paths and provenance only; no raw clip copying was added.
- Capture provenance opportunistically from known Phase 2 manifest fields (`run_id`, `runtime`, `tracker`, `source_node_id`, `completion_state`, timestamps) without inventing defaults.
- Keep trust scoring deterministic and stdlib-light while adding inspectable tuning fields: detection count/density, frame count, area change, jitter, edge fraction, class trust, and box trust.
- Represent CVAT as a local exchange boundary with export/import manifests so core workflows do not require a live CVAT server.
- Mark the default fixture release as `annotation_status: pseudo_only` so downstream trainer validation can distinguish smoke data from human-verified data.

## Invariants / Gotchas
- Raw Phase 2 packages remain immutable inputs.
- Dataset releases remain immutable; rerunning the same release id raises `FileExistsError`.
- `tests/fixtures/phase2_valid` has no candidate-negative score, so the fixture smoke `candidate-negative` queue is empty. Candidate-negative behavior is covered by synthetic unit-test score rows.
- True curated/gold labels remain blocked on Dr. Long labeling exported CVAT tasks.

## New / Changed Commands
- `python3 -m vision_curator.cli export-cvat-task --queue <queue.jsonl> --store-root <curator_store> --task-id <task_id>`
- `python3 -m vision_curator.cli import-cvat-annotations --task-root <curator_store>/annotation_exports/cvat/<task_id> --store-root <curator_store>`

## Verification Evidence
- `python3 -m unittest` — 14 tests passed.
- `python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid` — passed.
- `python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store` — wrote provenance-bearing package index record.
- `python3 -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store` — wrote 2 score records.
- `python3 -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store` — wrote 1 review item.
- `python3 -m vision_curator.cli build-review-queue --queue-kind ambiguous --store-root /tmp/vision-curator-smoke-store` — wrote 1 review item.
- `python3 -m vision_curator.cli build-review-queue --queue-kind candidate-negative --store-root /tmp/vision-curator-smoke-store` — wrote 0 review items for the current fixture.
- `python3 -m vision_curator.cli build-review-queue --queue-kind random-audit --store-root /tmp/vision-curator-smoke-store` — wrote 1 review item.
- `python3 -m vision_curator.cli export-cvat-task --queue /tmp/vision-curator-smoke-store/review_queues/hard-case_20260501T022523Z.jsonl --store-root /tmp/vision-curator-smoke-store --task-id smoke_cvat_20260501T022523Z` — wrote CVAT export manifest.
- `python3 -m vision_curator.cli import-cvat-annotations --task-root /tmp/vision-curator-smoke-store/annotation_exports/cvat/smoke_cvat_20260501T022523Z --store-root /tmp/vision-curator-smoke-store` — wrote zero-count import placeholder.
- `python3 -m vision_curator.cli build-release --config configs/release/default.yaml --release-id smoke_release_20260430` — wrote ignored smoke release under `build/releases/smoke_release_20260430`.

## TODOs / Follow-Ups
- Pull completed real Phase 2 packages from the NX spool and validate ingest against actual edge manifests.
- Export a selected queue to CVAT for Dr. Long, then import corrected annotations once labeling is complete.
- Hand the pseudo-only smoke release or first labeled release to `vision-trainer` for downstream validation.
