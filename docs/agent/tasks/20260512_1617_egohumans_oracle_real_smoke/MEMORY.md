# .agent/MEMORY.md (scratch)

**Task:** egohumans-oracle-real-package-smoke
**Last updated:** 2026-05-12

## Goal / status
- Goal: run real-package oracle import smoke tests for six EgoHumans Lego Assembly packages to unblock `vision-trainer` model-update work.
- Verified package location: `$OPENCLAW_RAW_PACKAGE_STORE/incoming`.
- Status: completed; real oracle artifacts exist under `$OPENCLAW_CURATOR_STORE/oracle/egohumans`.

## Repro commands
- `source ~/openclaw-env.sh`
- `find "$OPENCLAW_RAW_PACKAGE_STORE/incoming" -maxdepth 2 -name manifest.json -print | sort`
- `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <package_root>`
- `env PYTHONPATH=src python3 -m vision_curator.cli import-egohumans-oracle --phase2 <package_root> --dataset-root /media/jdl2/DATAPART/YOLO-Data/datasets/egohumans --store-root "$OPENCLAW_CURATOR_STORE"`

## Hypotheses + evidence
- Evidence: six incoming package directories exist, each with `manifest.json`:
- `/media/jdl2/DATAPART/YOLO-Data/openclaw/raw_edge_packages/incoming/001_legoassemble_full_package__yolo11_person_v1_bytetrack`
- `/media/jdl2/DATAPART/YOLO-Data/openclaw/raw_edge_packages/incoming/002_legoassemble_full_package__yolo11_person_v1_bytetrack`
- `/media/jdl2/DATAPART/YOLO-Data/openclaw/raw_edge_packages/incoming/003_legoassemble_full_package__yolo11_person_v1_bytetrack`
- `/media/jdl2/DATAPART/YOLO-Data/openclaw/raw_edge_packages/incoming/004_legoassemble_full_package__yolo11_person_v1_bytetrack`
- `/media/jdl2/DATAPART/YOLO-Data/openclaw/raw_edge_packages/incoming/005_legoassemble_full_package__yolo11_person_v1_bytetrack`
- `/media/jdl2/DATAPART/YOLO-Data/openclaw/raw_edge_packages/incoming/006_legoassemble_full_package__yolo11_person_v1_bytetrack`

## Decisions (and why)
- Do not move or delete `incoming`; smoke tests can use explicit package roots there, and raw-package immutability matters more than path tidiness before validation.
- Remember package location in `.agent/MEMORY.md`; promote to durable docs only if smoke confirms this is the stable operational staging path.
- Updated importer to accumulate package outputs in the shared oracle root because the output contract is dataset-level, not one output directory per package.
- Validator now requires EgoHumans package metadata keys to be present but allows null values for real package-writer outputs where the key is explicit but unavailable.

## Gotchas discovered (promote at closeout)
- Real package `pose_member` paths are relative to `dataset_root/<sequence_id>/`, not directly to `dataset_root`.
- Real EgoHumans pose dicts store `keypoints` as NumPy arrays, not plain Python lists.
- Current incoming manifests contain explicit `null` values for `model_artifact_version`, `detection_confidence_threshold`, and `nms_threshold`.

## Verification run
- Command(s): six `validate-package` runs over `$OPENCLAW_RAW_PACKAGE_STORE/incoming/*`; six `import-egohumans-oracle` runs over the same roots; `env PYTHONPATH=src python3 -m unittest`; `env PYTHONPATH=src python3 -m compileall src tests`.
- Outcome(s): validation passed for all six packages; import passed for all six packages; final oracle output has 8,227 frame-index rows, 8,839 oracle labels, 884 gold seed rows, 398 review-revealed rows, 113 gold negative rows, and 0 warnings; all tests and compile checks passed.

## Next steps
- Move to `vision-trainer` once curated release inputs are defined from `gold_revealed` and/or trusted pseudo labels.
