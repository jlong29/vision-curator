# Closeout — EgoHumans Oracle Real-Package Smoke

## Decisions Made
- Kept raw packages under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`; do not delete or flatten that directory until a deliberate archival/promote step is defined.
- Updated validation to require EgoHumans package metadata keys to be present while allowing explicit `null` values emitted by the real package writer.
- Updated oracle import to accumulate package outputs into the shared dataset-level `$OPENCLAW_CURATOR_STORE/oracle/egohumans` root.
- Updated pose resolution for real packages: `pose_member` paths resolve through `dataset_root/<sequence_id>/<pose_member>`.
- Updated pose normalization to accept NumPy array keypoints from real EgoHumans `.npy` files.

## New Invariants / Gotchas
- The six real Lego Assembly Phase 2 package roots are staged under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`.
- Real package manifests currently contain explicit `null` for `model_artifact_version`, `detection_confidence_threshold`, and `nms_threshold`.
- Final oracle smoke outputs are accumulated across all six packages and are safe to rerun because rows are upserted.

## New / Changed Commands
- Validate one package: `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <package_root>`
- Import one package: `env PYTHONPATH=src python3 -m vision_curator.cli import-egohumans-oracle --phase2 <package_root> --dataset-root /media/jdl2/DATAPART/YOLO-Data/datasets/egohumans --store-root "$OPENCLAW_CURATOR_STORE"`

## Verification Evidence
- Six incoming package roots found, each with `manifest.json`.
- Six `validate-package` runs passed.
- Six `import-egohumans-oracle` runs passed.
- Final curator oracle counts:
  - `normalized/frame_index.jsonl`: 8,227 rows
  - `normalized/oracle_labels.jsonl`: 8,839 rows
  - `normalized/oracle_checked_negative_frames.jsonl`: 2,248 rows
  - `reveal_sets/gold_seed_v0.jsonl`: 884 rows
  - `reveal_sets/review_revealed_gold_v0.jsonl`: 398 rows
  - `reveal_sets/gold_negatives_v0.jsonl`: 113 rows
- `source_dataset_manifest.json` records all six package IDs, all six sequences, `aria01/aria02/aria03`, and zero warnings.
- `env PYTHONPATH=src python3 -m unittest` — passed, 23 tests.
- `env PYTHONPATH=src python3 -m compileall src tests` — passed.

## TODOs / Follow-Ups
- Define curated release inputs for the first `vision-trainer` update from `gold_revealed` and/or trusted pseudo labels.
- Decide whether `$OPENCLAW_RAW_PACKAGE_STORE/incoming` remains the long-term staging convention or whether validated packages get promoted to a separate immutable archive path.
