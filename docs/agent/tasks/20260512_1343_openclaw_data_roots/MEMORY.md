# .agent/MEMORY.md (scratch)

**Task:** plan-openclaw-data-roots  
**Last updated:** 2026-05-11 19:00

## Goal / status
- Add repo support for machine-local OpenClaw data roots and fail-fast env setup prompts.
- Add a next-task specification for EgoHumans oracle import after sandbox refresh.

## Repro commands
- `source ~/openclaw-env.sh`

## Hypotheses + evidence
- Env variables should be the operational interface; explicit CLI paths should still work for tests and one-off smoke commands.

## Decisions (and why)
- Commands that need curator store paths accept explicit `--store-root`, otherwise use `OPENCLAW_CURATOR_STORE`.
- Config values can reference `${OPENCLAW_*}`; missing OpenClaw vars raise an early prompt to source `~/openclaw-env.sh`.
- EgoHumans hidden-oracle production belongs in `vision-curator`, not the Edge Node, because ground truth must stay desktop-side and separate from pseudo-label generation.

## Gotchas discovered (promote at closeout)
- `build-release` depends on config values rather than a direct CLI store argument, so env expansion belongs in config loading.
- The Edge Node package appears to have the needed `source_frames.jsonl`; the next task should still validate actual frame-map content after sandbox refresh.

## Verification run
- `python3 -m unittest tests.test_env_requirements`: passed.
- `python3 -m unittest`: passed.
- `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`: passed.
- `env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-env-smoke-store`: passed.
- `python3 -m compileall src`: passed.

## Next steps
- Apply matching env fail-fast behavior in `vision-trainer`.
- Restart Codex with writable/read roots, then start `add-egohumans-oracle-import` using `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md`.
