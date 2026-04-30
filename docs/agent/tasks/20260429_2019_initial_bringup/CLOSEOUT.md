# Closeout — Initial `vision-curator` Bring-Up

## Summary

Created the initial `vision-curator` repository for desktop-side curation of thermal person detection data.

The repo now includes a Python package skeleton, CLI, configs, durable docs, JSON schemas, fixtures, and stdlib `unittest` coverage for the first bring-up workflow.

## Decisions Made

- Converted `AGENTS_TEMPLATE.md` into repo-specific `AGENTS.md`.
- Moved task working state into `.agent/` and archived it here at closeout.
- Kept CVAT and FiftyOne optional during bring-up.
- Used stdlib `unittest` for the initial test suite.
- Implemented ingest as source package registration in `indexes/packages.jsonl`, rather than copying raw package data, to preserve raw package immutability.
- Used JSON/JSONL fixture-compatible content in `.parquet`-named files during bring-up to avoid a hard pandas/pyarrow dependency before table IO requirements stabilize.
- Made dataset release creation overwrite-protected by default.
- Moved the original design document to `docs/VISION_CURATOR_REPO_DESIGN.md`.

## New Invariants / Gotchas

- Raw Phase 2 packages are immutable inputs.
- Dataset releases are immutable once created.
- Core tests and CLI paths do not require CVAT or FiftyOne.
- Editable install needed network access for isolated build dependency resolution in this environment.

## Commands Added / Verified

```bash
python -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid
python -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store
python -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store
python -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store
python -m vision_curator.cli build-release --config configs/release/default.yaml --release-id cli_smoke_20260429_2111
python -m unittest
```

## Verification Evidence

- `python -m unittest` passed with 7 tests.
- `python -m pip install -e .` passed after network access was allowed.
- CLI smoke checks passed for validate, ingest, score, review queue, and release build.

## Follow-Ups

- Add real parquet IO once pandas/pyarrow dependency policy is decided.
- Bring up optional CVAT and FiftyOne dependencies in the next milestone.
- Expand schemas from stubs into stricter validation contracts as package formats stabilize.
