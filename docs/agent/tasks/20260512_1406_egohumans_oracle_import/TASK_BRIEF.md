## TASK_BRIEF

### Task
- Implement the EgoHumans Lego Assembly hidden-oracle import workflow in `vision-curator`.

### Why this update
- EgoHumans Phase 2 edge packages keep teacher pseudo labels separate from ground truth; the desktop curator now needs an owned import path for hidden oracle labels, deterministic reveal sets, and frame mappings used by later calibration reports and releases.

### Fixed invariants (do not change)
- Do not mutate raw Edge Node packages or EgoHumans source data.
- Preserve exactly three label namespaces: `oracle_hidden`, `gold_revealed`, and `pseudo_teacher`.
- Trust scoring and review queue selection must not read `oracle_hidden`.
- `oracle_upper_bound` is the only later release family allowed to train from full `oracle_hidden` labels.
- Treat local pose-derived EgoHumans boxes as benchmark-semantics proxy oracle labels when upstream COCO benchmark JSON is absent.
- Split by clip or sequence chunk, not random frames; avoid temporal and near-identical multi-view leakage.

### Ablation dimensions
- First-supported release families: `gold_only_v0`, `gold_plus_naive_pseudo_v0`, `gold_plus_trusted_tracks_v0`, `gold_plus_review_revealed_v1`, and `oracle_upper_bound`.
- Reveal set families: seed gold, review-revealed gold, and oracle-confirmed negatives.
- Camera/view policy should be explicit enough to support holding `aria02` out later as a camera-view generalization check.

### Goal
- Add a small, testable `vision_curator.oracle.egohumans` importer and CLI command that reads an EgoHumans Phase 2 package plus source dataset references, writes OpenClaw-owned oracle artifacts under `$OPENCLAW_CURATOR_STORE/oracle/egohumans/`, and documents provenance/namespace boundaries.

### Success criteria
- [x] New CLI command can be invoked as `import-egohumans-oracle --phase2 <package_root> --dataset-root <egohumans_root> --store-root <curator_store>`.
- [x] Import writes `source_dataset_manifest.json`, `normalized/frame_index.jsonl`, `normalized/oracle_labels.jsonl`, `normalized/class_map.json`, and deterministic `reveal_sets/*.jsonl`.
- [x] `frame_index.jsonl` maps package frame identity to source sequence/camera/frame identity from `source_frames.jsonl` and clip manifests.
- [x] `oracle_labels.jsonl` emits normalized `oracle_hidden` person boxes from pose-derived proxy labels, with provenance and clear proxy semantics.
- [x] Reveal sets emit `gold_revealed` records that reference oracle record IDs instead of silently copying labels into global training truth.
- [x] Unit tests cover frame map normalization, pose/keypoint-to-box normalization, deterministic reveal generation, and CLI smoke behavior with tiny fixtures.
- [x] Verification passes with `python3 -m unittest`; real-package smoke was not possible because no local EgoHumans Phase 2 manifest was found under configured OpenClaw or historical `~/openclawInfo` paths.

### Relevant files (why)
- `src/vision_curator/cli.py` — canonical CLI command surface.
- `src/vision_curator/common/models.py` — shared contracts and naming style for structured records.
- `src/vision_curator/packages/validate.py` — Phase 2 package expectations and clip metadata conventions.
- `src/vision_curator/packages/ingest.py` — package manifest/index reading patterns.
- `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md` — task contract for oracle outputs and namespace rules.
- `docs/EGOHUMANS_LEGO_WORKING_SPEC.md` — current EgoHumans label semantics and proxy-label caveats.
- `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` — split/reveal policy.
- `/home/jdl2/Git/vision-ai/vision_api` — read-only reference for EgoHumans pose-to-box conversion rules.
- `/home/jdl2/Git/vision-ai/thermal-data-engine` — read-only reference for Phase 2 writer semantics if needed.
- `tests/` — add focused stdlib `unittest` coverage and small fixtures.

### Refined Phase 2 Plan
1) Inspect existing CLI/package patterns and read-only reference conversion code for EgoHumans frame/pose semantics. Done.
2) Implement an oracle importer module with pure helpers for frame maps, source manifest, pose/proxy label normalization, and reveal-set generation. Done.
3) Wire a conservative CLI command that defaults output to `<store-root>/oracle/egohumans` and fails loudly on missing required package files. Done.
4) Add tiny fixtures and tests for importer helpers plus CLI smoke behavior. Done.
5) Run unit tests, compile check, and a real-package smoke if a local Phase 2 package path is found or supplied. Unit and compile checks done; real package not found.

### Small change sets (execution order)
1) Add importer module and tests for source/frame/label/reveal normalization.
2) Add CLI command and smoke tests.
3) Update `.agent/TASK_BRIEF.md` with implementation decisions and verification results.

### Verification
- Fast: `python3 -m unittest`
- Targeted: `env PYTHONPATH=src python3 -m unittest tests.test_egohumans_oracle`
- CLI smoke: `env PYTHONPATH=src python3 -m vision_curator.cli import-egohumans-oracle --phase2 <package_root> --dataset-root /media/jdl2/DATAPART/YOLO-Data/datasets/egohumans --store-root /tmp/vision-curator-egohumans-smoke`
- Compile: `python3 -m compileall src tests`

Results:
- `env PYTHONPATH=src python3 -m unittest tests.test_egohumans_oracle` — passed.
- `env PYTHONPATH=src python3 -m unittest` — passed, 23 tests.
- `env PYTHONPATH=src python3 -m compileall src tests` — passed.
- Real package smoke deferred: no `manifest.json` found under `$OPENCLAW_RAW_PACKAGE_STORE/phase2/egohumans`, `/media/jdl2/DATAPART/YOLO-Data/openclaw`, or `/home/jdl2/openclawInfo/outputs/egohumans_phase2`.

### Risks / gotchas
- Phase 1 root validation found the expected OpenClaw roots and write access, but no EgoHumans Phase 2 `manifest.json` under `$OPENCLAW_RAW_PACKAGE_STORE/phase2/egohumans` or a targeted OpenClaw search.
- Upstream COCO benchmark JSON may be absent locally, so the first implementation must support proxy oracle boxes derived from visible `poses2d` keypoints and clearly record that provenance.
- EgoHumans source layout may vary between extracted tarballs and conversion outputs; importer should use explicit paths and fail loudly rather than guessing silently.
- Parquet dependencies are optional elsewhere in bring-up; this importer should not require reading detections/tracks for oracle import unless later calibration metrics are added.

### Decision rule for defaults
- Default to deterministic, minimal outputs that preserve provenance and namespace separation; when source labels are absent or ambiguous, write frame index and manifest, emit an empty oracle label file with warnings/errors appropriate to CLI strictness rather than fabricating labels.

### Deferred work note
- This task does not implement full pseudo-vs-oracle calibration metrics, model training releases, CVAT/FiftyOne workflows, or trust-score threshold tuning. It creates the hidden-oracle/reveal-set substrate those later workflows consume.
