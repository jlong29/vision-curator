# .agent/MEMORY.md (scratch)

**Task:** bring up vision-curator
**Last updated:** 2026-04-29 17:12

## Goal / status
- Initial `vision-curator` bring-up is implemented and verified.

## Repro commands
- `python -m unittest`
- `python -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`
- `python -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store`
- `python -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store`
- `python -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store`
- `python -m vision_curator.cli build-release --config configs/release/default.yaml --release-id cli_smoke_20260429_2111`

## Hypotheses + evidence
- Pending.

## Decisions (and why)
- Keep CVAT/FiftyOne optional during bring-up, per design doc.
- Use stdlib `unittest` initially, per task brief.
- Register source packages in the curator store index instead of copying raw packages; this preserves raw package immutability and avoids expensive duplicate storage.
- Use JSON/JSONL fixture-compatible content in `.parquet`-named score/input files for bring-up to avoid a hard pyarrow/pandas dependency before table IO requirements stabilize.

## Gotchas discovered (promote at closeout)
- This directory was not initialized as a git repository when bring-up started.
- `python -m pip install -e .` needed network access for isolated build dependencies.

## Verification run
- Command(s): `python -m unittest`; editable install; CLI validate/ingest/score/build-review-queue/build-release smoke commands.
- Outcome(s): all passed.

## Next steps
- Bring up real parquet IO and optional CVAT/FiftyOne dependencies in the next milestone.
