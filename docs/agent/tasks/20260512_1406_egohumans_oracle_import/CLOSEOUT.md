# Closeout — EgoHumans Oracle Import

## Decisions Made
- Added a dedicated `vision_curator.oracle.egohumans` module so hidden-oracle behavior stays out of trust scoring, package ingest, and release construction.
- Added `import-egohumans-oracle` to the CLI with explicit `--phase2`, `--dataset-root`, and `--store-root` inputs.
- Wrote oracle outputs under `<store-root>/oracle/egohumans/` with `oracle_hidden` labels and `gold_revealed` reveal records kept separate.
- Kept `.npy` EgoHumans pose support optional behind `numpy`; fixture coverage uses JSON pose inputs so core tests remain lightweight.
- Emitted gold negatives only for frames whose oracle pose source was actually checked.

## New Invariants / Gotchas
- Local EgoHumans labels may be benchmark-semantics proxy oracle labels derived from `poses2d`, not byte-for-byte upstream COCO benchmark labels.
- No real EgoHumans Phase 2 package manifest was found under the configured OpenClaw package roots during this task, so real-package smoke remains pending.
- Reveal sets reference `oracle_hidden` record IDs; they are not a second global truth copy.

## New / Changed Commands
- `env PYTHONPATH=src python3 -m vision_curator.cli import-egohumans-oracle --phase2 <package_root> --dataset-root <egohumans_root> --store-root <curator_store>`

## Verification Evidence
- `env PYTHONPATH=src python3 -m unittest tests.test_egohumans_oracle` — passed.
- `env PYTHONPATH=src python3 -m unittest` — passed, 23 tests.
- `env PYTHONPATH=src python3 -m compileall src tests` — passed.

## TODOs / Follow-Ups
- Run the CLI against the first real EgoHumans Phase 2 package once its path is supplied or generated under `$OPENCLAW_RAW_PACKAGE_STORE`.
- Add pseudo-vs-oracle calibration metrics in a later task.
- Wire oracle/revealed-gold labels into release families in a later task.
