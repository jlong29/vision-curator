## TASK_BRIEF

### Task
- Run real-package EgoHumans oracle import smoke tests against the six Lego Assembly Phase 2 packages under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`.

### Why this update
- The oracle import workflow is implemented, but the previous task could not find real Phase 2 packages. The user confirmed the raw packages are staged under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`, and the next project goal is moving to `vision-trainer` for a first model update.

### Fixed invariants (do not change)
- Do not mutate, move, or delete raw package files unless explicitly requested after verification.
- Do not use `oracle_hidden` labels for trust scoring or pseudo-label acceptance.
- Keep `oracle_hidden`, `gold_revealed`, and `pseudo_teacher` namespaces separate.
- Treat the `incoming` package paths as valid immutable inputs for smoke testing unless package validation proves otherwise.

### Goal
- Produce real OpenClaw-owned oracle artifacts in the curator store for all six EgoHumans Lego Assembly packages, with enough verification evidence to unblock the next `vision-trainer` model-update work.

### Success criteria
- [x] Verify there are six incoming package roots and each has a root `manifest.json`.
- [x] `validate-package` passes for each incoming package.
- [x] `import-egohumans-oracle` runs successfully for each package against `/media/jdl2/DATAPART/YOLO-Data/datasets/egohumans`.
- [x] Smoke outputs exist under `$OPENCLAW_CURATOR_STORE/oracle/egohumans/`: `source_dataset_manifest.json`, `normalized/frame_index.jsonl`, `normalized/oracle_labels.jsonl`, `normalized/class_map.json`, and `reveal_sets/*.jsonl`.
- [x] Outputs are non-empty where expected: frame index non-empty, oracle labels non-empty if pose files resolve, reveal sets deterministic.
- [x] Record package paths, commands, results, and any blockers in `.agent/MEMORY.md`.

### Relevant files (why)
- `src/vision_curator/cli.py` — CLI entrypoint for validation and oracle import.
- `src/vision_curator/oracle/egohumans.py` — implementation under smoke test.
- `src/vision_curator/packages/validate.py` — package contract validation.
- `.agent/MEMORY.md` — record exact incoming package paths and smoke results for continuity.
- `$OPENCLAW_RAW_PACKAGE_STORE/incoming/*/manifest.json` — real package inputs.
- `/media/jdl2/DATAPART/YOLO-Data/datasets/egohumans` — real source dataset root.

### Refined Phase 2 Plan
1) Summarize incoming package manifests and source-frame-map fields without bulk traversal.
2) Run `validate-package` on all six incoming package roots.
3) Run `import-egohumans-oracle` on all six packages into the curator store.
4) Inspect output counts and sample records.
5) Update `.agent/MEMORY.md` with exact paths, results, and next-step readiness for `vision-trainer`.

### Small change sets (execution order)
1) Update `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` with the smoke plan and verified package roots.
2) If the smoke exposes a small importer bug, make a surgical fix and rerun the failing package before broadening to all six.

### Verification
- Package discovery: `find "$OPENCLAW_RAW_PACKAGE_STORE/incoming" -maxdepth 2 -name manifest.json -print`
- Validation: `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <package_root>`
- Oracle smoke: `env PYTHONPATH=src python3 -m vision_curator.cli import-egohumans-oracle --phase2 <package_root> --dataset-root /media/jdl2/DATAPART/YOLO-Data/datasets/egohumans --store-root "$OPENCLAW_CURATOR_STORE"`
- Output inspection: count lines in `normalized/frame_index.jsonl`, `normalized/oracle_labels.jsonl`, and `reveal_sets/*.jsonl`.

### Risks / gotchas
- Resolved: importer now upserts into one shared `$OPENCLAW_CURATOR_STORE/oracle/egohumans` output root so sequential package imports accumulate.
- Resolved: source frame maps reference `pose_member` paths relative to each extracted sequence subtree, so the importer now checks `dataset_root/<sequence_id>/<pose_member>`.
- Real EgoHumans `.npy` pose loading requires `numpy`.

### Results
- Six incoming packages verified under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`.
- Six `validate-package` runs passed.
- Six `import-egohumans-oracle` runs passed.
- Final oracle output counts: 8,227 frame-index rows; 8,839 `oracle_hidden` labels; 884 `gold_seed_v0` rows; 398 `review_revealed_gold_v0` rows; 113 `gold_negatives_v0` rows; 0 warnings.
- Final `source_dataset_manifest.json` records all six package IDs and sequences.

### Decision rule for defaults
- Keep raw packages under `$OPENCLAW_RAW_PACKAGE_STORE/incoming` for now; do not move/delete them unless the user explicitly decides to promote them after smoke validation. Remember the location in `.agent/MEMORY.md` and, if stable after the run, in `docs/PROJECT_STATE.md`.

### Deferred work note
- This task does not train a model. It prepares and verifies oracle artifacts so `vision-trainer` can consume curated data in the next phase.
