## TASK_BRIEF

### Task
- Design and document the desktop OpenClaw data-root layout under `/media/jdl2/DATAPART/YOLO-Data/`, plus the Codex access plan for `vision-curator` and `vision-trainer`.

### Status
- `docs/SYSTEM_DESIGN_v2.md` now documents the concrete `/media/jdl2/DATAPART/YOLO-Data/openclaw` layout, environment variables, setup commands, and narrow Codex writable root.
- CLI/config instrumentation now prompts for `source ~/openclaw-env.sh` when OpenClaw store env vars are needed but missing.
- `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md` now defines the next task: validate refreshed sandbox access, then implement EgoHumans hidden-oracle import and reveal-set generation.

### Why this update
- The next EgoHumans calibration task will need stable machine-local stores for raw edge packages, curator indexes/scores/queues, dataset releases, training runs, and model artifacts.
- These directories live outside the repo sandbox, so access must be explicit and consistent with Codex sandbox policy.

### Fixed invariants (do not change)
- Raw edge packages are immutable after desktop pull.
- `vision-curator` may read raw packages and write curator outputs/releases, but must not train models.
- `vision-trainer` may read curated releases and write training/model outputs, but should not mutate raw packages or curator indexes.
- Dataset releases are immutable once published.
- Hidden oracle, revealed gold, and teacher pseudo labels must remain separate for EgoHumans calibration.

### Proposed Data Root
- Base: `/media/jdl2/DATAPART/YOLO-Data/openclaw`

### Proposed Environment Variables
- `OPENCLAW_RAW_PACKAGE_STORE=/media/jdl2/DATAPART/YOLO-Data/openclaw/raw_edge_packages`
- `OPENCLAW_CURATOR_STORE=/media/jdl2/DATAPART/YOLO-Data/openclaw/curator`
- `OPENCLAW_DATASET_RELEASE_STORE=/media/jdl2/DATAPART/YOLO-Data/openclaw/dataset_releases`
- `OPENCLAW_TRAINING_RUN_STORE=/media/jdl2/DATAPART/YOLO-Data/openclaw/training_runs`
- `OPENCLAW_MODEL_ARTIFACT_STORE=/media/jdl2/DATAPART/YOLO-Data/openclaw/model_artifacts`

### Proposed Directory Layout
```text
/media/jdl2/DATAPART/YOLO-Data/openclaw/
├─ raw_edge_packages/
│  ├─ incoming/
│  ├─ phase1/
│  ├─ phase2/
│  │  └─ egohumans/
│  └─ manifests/
├─ curator/
│  ├─ indexes/
│  ├─ scores/
│  ├─ review_queues/
│  ├─ annotation_exports/
│  │  └─ cvat/
│  ├─ annotation_imports/
│  │  └─ cvat/
│  ├─ oracle/
│  │  └─ egohumans/
│  ├─ revealed_gold/
│  └─ decisions/
├─ dataset_releases/
│  ├─ pseudo_only/
│  ├─ calibration/
│  └─ published/
├─ training_runs/
│  ├─ smoke/
│  ├─ calibration/
│  └─ full/
├─ model_artifacts/
│  ├─ candidates/
│  ├─ exported/
│  ├─ promotion_reports/
│  └─ archived/
└─ docs/
   └─ README.md
```

### Access Plan
- Prefer adding one writable root for both repos:
  - `/media/jdl2/DATAPART/YOLO-Data/openclaw`
- This is narrower and cleaner than granting `/media/jdl2/DATAPART/YOLO-Data/`.
- If using repo-local Codex config, create/update `.codex/config.toml` in each repo with:
```toml
[sandbox_workspace_write]
writable_roots = ["/media/jdl2/DATAPART/YOLO-Data/openclaw"]
```
- If a global Codex config is used for both repos, use the same writable root there instead of duplicating config.
- For commands that must create the external directories before config is active, request explicit escalation rather than trying to bypass the sandbox.

### Relevant Files (why)
- `docs/SYSTEM_DESIGN_v2.md` — defines shared store roots and data flow.
- `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md` — next-task handoff for sandbox validation and oracle dataset production.
- `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` — gold/reveal/split policy for the oracle importer task.
- `docs/EGOHUMANS_LEGO_WORKING_SPEC.md` — EgoHumans source semantics and edge-package facts.
- `docs/PROJECT_STATE.md` — current operational workflow should name the chosen machine-local root.
- `docs/handoffs/EDGE_TO_CURATOR.md` — should point the edge pull target at the raw package store.
- `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md` — should include the chosen env vars before real EgoHumans package ingest.
- `configs/curator/default.yaml`, `configs/release/default.yaml` — may need defaults or examples updated to use env-driven stores.
- `AGENTS.md` — may need a short durable note that this repo uses tracked `.agent/` and external OpenClaw data roots by explicit sandbox config.

### Refined Phase 2 Plan
1) Confirm the user wants the `openclaw/` namespace under `/media/jdl2/DATAPART/YOLO-Data/`. Done.
2) Add durable docs for the data root layout and env vars. Done for `docs/SYSTEM_DESIGN_v2.md`.
3) Update curator configs/examples to reference the selected paths through env vars or documented shell exports. Done.
4) Add matching guidance for `vision-trainer`. Done in `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md` by specifying downstream release families.
5) Optionally create the external directories only after permission is granted.
6) Write a next-task spec for sandbox validation and EgoHumans oracle import. Done.

### Small Change Sets (execution order)
1) Documentation: add/update project state, handoffs, and a data-root README section.
2) Config examples: align curator/release config examples with the env var layout.
3) Access setup: add `.codex/config.toml` only if the user wants repo-local Codex config committed.
4) Verification: run unit tests and CLI smoke using temporary or approved external roots.

### Verification
- Fast: `python3 -m unittest`
- Config smoke: `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`
- External write smoke, after permission: ingest/score/queue against `$OPENCLAW_CURATOR_STORE`

### Verification run
- `python3 -m unittest tests.test_env_requirements`: passed.
- `python3 -m unittest`: passed.
- `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`: passed.
- `env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-env-smoke-store`: passed.
- `python3 -m compileall src`: passed.

### Risks / gotchas
- `/media/jdl2/DATAPART/YOLO-Data/` may be removable-media mounted; permissions and mount availability should be checked before long runs.
- Granting the broader YOLO-Data root would expose unrelated datasets; prefer the narrower `openclaw` subroot.
- Repo-local `.codex/config.toml` may be machine-specific; if committed, keep it limited to this machine path and document that it is local-operational config.

### Decision rule for defaults
- Use environment variables as the public interface.
- Use repo-local or global Codex sandbox config only to grant filesystem access, not as application configuration.
- Keep raw package stores append-only/immutable by policy; enforce destructive operations through explicit user approval.

### Deferred work note
- This task does not process EgoHumans packages yet.
- This task does not create external directories until the user grants access/escalation or config is in place.
