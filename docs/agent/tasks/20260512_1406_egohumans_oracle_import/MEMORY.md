# .agent/MEMORY.md (scratch)

**Task:** egohumans-oracle-import
**Last updated:** 2026-05-12

## Goal / status
- Implemented a hidden-oracle EgoHumans import path and CLI command.
- Unit and compile verification passed.
- Real-package smoke could not run because no EgoHumans Phase 2 manifest was found locally under the configured package roots.

## Repro commands
- `env PYTHONPATH=src python3 -m unittest tests.test_egohumans_oracle`
- `env PYTHONPATH=src python3 -m unittest`
- `env PYTHONPATH=src python3 -m compileall src tests`

## Hypotheses + evidence
- Expected package path from task spec did not contain a manifest: `$OPENCLAW_RAW_PACKAGE_STORE/phase2/egohumans`.
- Targeted OpenClaw and historical `~/openclawInfo` searches also did not find a real EgoHumans Phase 2 package.

## Decisions (and why)
- Added `src/vision_curator/oracle/egohumans.py` instead of mixing oracle behavior into scoring/release code, preserving namespace boundaries.
- Kept `.npy` pose support optional behind `numpy` so core tests stay light while real EgoHumans poses2d files remain supported.
- Generated reveal records as references to `oracle_hidden` record IDs; negatives are only emitted for frames whose oracle pose source was checked.

## Gotchas discovered (promote at closeout)
- Real package path is unresolved in this workspace; fixture tests are the current executable smoke.
- Local EgoHumans oracle labels may be proxy labels derived from poses2d rather than upstream COCO benchmark JSON.

## Verification run
- Command(s): `env PYTHONPATH=src python3 -m unittest tests.test_egohumans_oracle`; `env PYTHONPATH=src python3 -m unittest`; `env PYTHONPATH=src python3 -m compileall src tests`
- Outcome(s): all passed.

## Next steps
- Run the CLI against the first real EgoHumans Phase 2 package once its path is supplied or generated under the configured OpenClaw package store.
