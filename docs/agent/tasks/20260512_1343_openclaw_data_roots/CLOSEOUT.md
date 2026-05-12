# Closeout: OpenClaw Data Roots and EgoHumans Oracle Spec

## Decisions Made
- Use `/media/jdl2/DATAPART/YOLO-Data/openclaw` as the shared OpenClaw data root.
- Keep Codex write access narrow: writable OpenClaw root only, with EgoHumans dataset and sibling repos as read-only roots after session restart.
- Use `source ~/openclaw-env.sh` as the terminal setup mechanism rather than adding OpenClaw variables to global shell startup.
- Keep EgoHumans hidden-oracle production in `vision-curator`, not the Edge Node, to preserve the separation between pseudo-label generation and oracle evaluation.
- Treat the full-oracle `oracle_upper_bound` run as a diagnostic headroom reference, not as part of the realistic teacher-student loop.

## Invariants / Gotchas
- Raw edge packages remain immutable after desktop pull.
- `vision-curator` may write curator outputs and releases, but must not train models.
- `vision-trainer` consumes curated releases and writes training/model artifacts.
- Hidden oracle, revealed gold, and teacher pseudo labels must never be mixed silently.
- The Edge Node packages appear to include `source_frames.jsonl`, but the next task still must validate actual frame-map contents after sandbox refresh.
- `build-release` depends on config values, so env expansion belongs in config loading.

## New / Changed Commands
- Source shared env before repo work:
  - `source ~/openclaw-env.sh`
- Preferred Codex config shape:
  - writable root: `/media/jdl2/DATAPART/YOLO-Data/openclaw`
  - read-only roots: EgoHumans dataset, `vision_api`, `thermal-data-engine`

## Durable Docs Added / Updated
- `docs/EGOHUMANS_LEGO_WORKING_SPEC.md`
- `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md`
- `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md`
- `docs/EGOHUMANS_CALIBRATION_EXECUTIVE_SUMMARY.md`

## TODOs / Follow-Ups
- Restart Codex after updating `~/.codex/config.toml`.
- Start the next task from `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md`.
- Validate sandbox access before reading real EgoHumans/package inputs.
- Implement `add-egohumans-oracle-import` in `vision-curator`.
- Apply analogous env fail-fast behavior in `vision-trainer`.

## Verification Evidence
- Prior env/config implementation verification recorded in task memory:
  - `python3 -m unittest tests.test_env_requirements`: passed.
  - `python3 -m unittest`: passed.
  - `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`: passed.
  - `env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-env-smoke-store`: passed.
  - `python3 -m compileall src`: passed.
- Final changes in this closeout slice are documentation/task-spec updates only.
