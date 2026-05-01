# Task Brief — align curator with 2026-04-30 next steps

## Branch
- `align-curator-next-steps`

## Goal
Bring `vision-curator` into alignment with `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md` by hardening the first useful curation control plane:
- validate and ingest immutable Phase 2 packages,
- produce deterministic and inspectable trust scores,
- build useful review queues with provenance,
- define the CVAT exchange boundary,
- emit a draft curated release contract consumable by `vision-trainer`.

## Success Criteria
- [x] `validate-package` fails loudly on missing required manifest fields and required clip artifacts.
- [x] `ingest-package` writes a canonical package index record containing source path, package id, clip count, clip ids, and key provenance fields available from package metadata.
- [x] Trust scoring is deterministic for the same package and writes class trust, box trust, decision bucket, and tuning feature fields.
- [x] `hard-case`, `ambiguous`, `candidate-negative`, and `random-audit` queues are tested and preserve package id, clip id, run/provenance id when available, and source path.
- [x] Queue ordering reflects queue semantics rather than raw filesystem order.
- [x] CVAT export/import boundaries are represented by docs and/or command/module stubs, with the human labeling gate explicitly documented.
- [x] Release build emits immutable `manifest.json`, `dataset.yaml`, split files, and provenance metadata from a minimal local fixture or smoke dataset.
- [x] Core tests do not require CVAT, FiftyOne, pyarrow, or real edge packages.

## Current State Review
- `src/vision_curator/cli.py` exposes the expected bring-up commands: `validate-package`, `ingest-package`, `score-package`, `build-review-queue`, and `build-release`.
- `src/vision_curator/packages/validate.py` already enforces the Phase 2 package layout and required clip files, but validation coverage should include missing manifest fields and provenance-bearing manifest shapes.
- `src/vision_curator/packages/ingest.py` indexes immutable source paths without copying raw clips, matching repo policy. The current `PackageRecord` captures package id, source path, manifest path, ingest time, clip count, and clip ids, but not additional provenance fields from manifests.
- `src/vision_curator/scoring/trust.py` is deterministic and stdlib-light. It emits the required bucket names plus useful features such as confidence, duration, jitter, and edge fraction. It should be expanded only where needed for inspectability and tests.
- `src/vision_curator/review/queues.py` supports all requested queue kinds, but current `ReviewItem` lacks source path and run/provenance fields, and tests only cover `hard-case`.
- `src/vision_curator/annotation/cvat_export.py` and `src/vision_curator/annotation/cvat_import.py` are documentation-only stubs, so Objective 4 is the largest missing implementation/documentation boundary.
- `src/vision_curator/releases/build.py` already creates immutable release directories with manifest, `dataset.yaml`, splits, and provenance/build config. Release manifest metadata may need clearer annotation/provenance fields for trainer handoff.
- `AGENTS.md` now references task/memory templates under `docs/agent/`, and those template files exist.

## Relevant Files
- `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`: requested objective source.
- `src/vision_curator/cli.py`: canonical command surface.
- `src/vision_curator/common/models.py`: shared records that need provenance/source-path fields.
- `src/vision_curator/packages/validate.py`: Phase 2 boundary checks.
- `src/vision_curator/packages/ingest.py`: package index behavior.
- `src/vision_curator/scoring/trust.py`: trust feature and bucket semantics.
- `src/vision_curator/review/queues.py`: queue selection, ordering, and output records.
- `src/vision_curator/annotation/cvat_export.py`: CVAT export boundary.
- `src/vision_curator/annotation/cvat_import.py`: CVAT import boundary.
- `src/vision_curator/releases/build.py`: release layout and immutability.
- `docs/package_contracts.md`, `docs/review_queues.md`, `docs/dataset_releases.md`, `docs/annotation_policy.md`: durable contract docs.
- `tests/fixtures/phase2_valid`: local Phase 2 smoke fixture.
- `tests/test_validate_phase2.py`, `tests/test_ingest.py`, `tests/test_trust_scoring.py`, `tests/test_review_queue.py`, `tests/test_dataset_release.py`: focused verification surface.

## Implementation Plan
1. Harden Phase 2 validation and ingest.
   - Add tests for missing root manifest fields, malformed clip entries, missing clip manifest `clip_id`, and realistic provenance fields.
   - Extend package/clip records conservatively with manifest provenance fields when present, without inventing silent defaults.
   - Preserve immutable source-path registration and no raw package mutation/copying.

2. Make trust scoring more inspectable without changing the bucket contract.
   - Keep scoring deterministic and stdlib-light.
   - Ensure output has stable feature fields for later threshold tuning.
   - Add tests covering each required decision bucket and repeatability of full package scoring output.

3. Improve review queue usefulness and provenance.
   - Extend review queue records with source path and available run/provenance identifiers.
   - Add tests for `hard-case`, `ambiguous`, `candidate-negative`, and `random-audit`.
   - Tighten per-kind ordering rules so queue semantics are explicit and deterministic.

4. Define the CVAT handoff boundary.
   - Add a minimal CVAT export manifest/task package builder or a CLI-visible stub if the command surface remains intentionally small.
   - Add an import placeholder/parser boundary that can represent corrected annotations without needing a live CVAT server.
   - Update durable docs to mark the exact point where Dr. Long labels data in CVAT and what remains blocked on human labeling.

5. Strengthen the draft release contract for `vision-trainer`.
   - Ensure release manifests preserve source package provenance, annotation/version metadata, label policy, split policy, and pseudo-only vs curated status.
   - Keep release immutability behavior.
   - Add or update fixture-backed release tests and validation checks.

6. Close out per `AGENTS.md`.
   - Run verification.
   - Promote only stable workflow/contracts to durable docs.
   - Archive `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` under `docs/agent/tasks/<task_slug>/`.
   - Empty `.agent/logs/`, restore `.agent` templates if needed, write `CLOSEOUT.md`, finish with `git status`, and commit.

## Verification Plan
- [x] `python3 -m unittest`
- [x] `python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`
- [x] `python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store`
- [x] `python3 -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store`
- [x] `python3 -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store`
- [x] `python3 -m vision_curator.cli build-review-queue --queue-kind ambiguous --store-root /tmp/vision-curator-smoke-store`
- [x] `python3 -m vision_curator.cli build-review-queue --queue-kind candidate-negative --store-root /tmp/vision-curator-smoke-store`
- [x] `python3 -m vision_curator.cli build-review-queue --queue-kind random-audit --store-root /tmp/vision-curator-smoke-store`
- [x] `python3 -m vision_curator.cli export-cvat-task --queue /tmp/vision-curator-smoke-store/review_queues/hard-case_20260501T022523Z.jsonl --store-root /tmp/vision-curator-smoke-store --task-id smoke_cvat_20260501T022523Z`
- [x] `python3 -m vision_curator.cli import-cvat-annotations --task-root /tmp/vision-curator-smoke-store/annotation_exports/cvat/smoke_cvat_20260501T022523Z --store-root /tmp/vision-curator-smoke-store`
- [x] `python3 -m vision_curator.cli build-release --config configs/release/default.yaml --release-id smoke_release_20260430`

## Constraints / Non-Goals
- Do not run edge inference, train models, export TensorRT engines, or move trainer behavior into this repo.
- Do not mutate raw Phase 2 packages.
- Do not make CVAT, FiftyOne, pyarrow, or real edge package availability required for core tests.
- Do not overwrite existing dataset releases unless explicitly requested.
- Treat real desktop package pull, CVAT labeling, and trainer handoff as external gates unless fixtures are sufficient for smoke validation.

## Open Questions / Blockers
- No real edge packages have been reviewed in this Phase 1 pass; planned work should use fixtures unless the user provides/pulls completed NX packages.
- CVAT true roundtrip remains blocked on Dr. Long labeling selected queues.
- The fixture smoke dataset has no candidate-negative row, so the candidate-negative smoke queue is empty. Candidate-negative queue behavior is covered by unit tests with synthetic score rows.
