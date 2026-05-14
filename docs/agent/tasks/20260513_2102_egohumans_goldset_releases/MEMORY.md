# .agent/MEMORY.md (scratch)

**Task:** egohumans-goldset-releases  
**Last updated:** 2026-05-12 22:00

## Goal / status
- Built trainer-ready EgoHumans calibration releases for all five planned families.
- Paused before Phase 4 closeout per user request.

## Repro commands
- `python3 -m unittest`
- `python3 -m compileall src tests`
- `python3 -m vision_curator.cli build-egohumans-splits --store-root "$OPENCLAW_CURATOR_STORE" --chunk-size 100`
- `python3 -m vision_curator.cli build-egohumans-release --release-family <family> --release-id <family> --store-root "$OPENCLAW_CURATOR_STORE" --release-store "$OPENCLAW_DATASET_RELEASE_STORE"`
- `python3 -m vision_curator.cli validate-release --release-root "$OPENCLAW_DATASET_RELEASE_STORE"/calibration/<family>`
- From `vision-trainer`: `env PYTHONPATH=src python3 -m bootstrap_train.validate_packages --release "$OPENCLAW_DATASET_RELEASE_STORE"/calibration/<family>`
- From `vision-trainer`: `env PYTHONPATH=src python3 -m bootstrap_train.train --config configs/train/curated_release_smoke.yaml --dataset-kind curated_release --dataset-root "$OPENCLAW_DATASET_RELEASE_STORE"/calibration/<family> --name <family>_smoke --dry-run`

## Hypotheses + evidence
- Initial release writer failed `vision-trainer` validation because `split_policy`/`label_policy` were strings and `dataset.yaml` used inline `names`; changed EgoHumans writer to manifest mappings and multiline names.

## Decisions (and why)
- Added EgoHumans-specific release builder instead of overloading generic `build-release`, because namespace policy and oracle leakage rules are calibration-specific.
- Kept scorer bucket semantics stable, but documented stricter EgoHumans pseudo-selection thresholds and applied them in the trusted-track release selector.
- Used a curator-side image cache for extracted frames because source image paths point to edge locations and repeated video extraction was slow.
- Treat Edge-local absolute paths as provenance only. Desktop workflows should consume package-local/relative artifacts after transfer.

## Gotchas discovered (promote at closeout)
- `vision-trainer` curated-release contract requires manifest `split_policy` and `label_policy` to be mappings.
- `vision-trainer` curated-release contract requires `dataset.yaml` `names` as a zero-indexed YAML mapping, not inline `{0: person}`.
- EgoHumans oracle `source_image_path_or_name` can point to NX-local paths; desktop release materialization must fall back to extracting frames from `clip.mp4`.
- `vision-trainer` dry-run creates `.ultralytics_dataset.yaml` and `.ultralytics_splits/` inside release roots; these were removed after verification to keep release roots clean.
- Phase 2 packages need a clearer portability contract: required curator inputs should be package-relative or clip-relative, while absolute Edge paths should be named and treated as origin/provenance paths.
- Follow-up docs/validation target: `docs/package_contracts.md`, `docs/SYSTEM_DESIGN_v2.md`, and package validation should formalize portable paths vs provenance paths.
- `gold_plus_trusted_tracks_v0` is intentionally conservative but may be too sparse for training usefulness: audit showed train has 626 objects (`gold_seed_v0=574`, `trusted_track=52`) while val/test have 1371/1695 oracle eval objects. Document this as an interpretation caveat and consider non-test oracle precision analysis before relaxing trusted-track thresholds.

## Verification run
- Command(s): see `.agent/TASK_BRIEF.md` verification evidence.
- Outcome(s): Curator tests, compile checks, curator release validation, trainer release validation, and trainer dry-runs all passed.

## Next steps
- User review against the checklist in `.agent/TASK_BRIEF.md`.
- During closeout, promote the path portability gotcha to durable docs.
- During closeout, promote the trusted-track sparsity caveat to durable docs/handoff notes.
- After review approval, perform Phase 4 closeout/archive/commit procedure.
