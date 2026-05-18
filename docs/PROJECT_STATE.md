# Project State

## Current Operational Workflow

`vision-curator` is the desktop curation control plane between Edge Node package production and `vision-trainer` training.

Current working path:

1. Pull completed Phase 2 package roots from the Edge Node into an immutable raw package store.
2. Validate packages with `validate-package`.
3. Register immutable package paths with `ingest-package`.
4. Compute deterministic class and box trust scores with `score-package`.
5. Build review queues with `build-review-queue`.
6. For EgoHumans calibration, import hidden oracle labels with `import-egohumans-oracle`.
7. For EgoHumans calibration, freeze split assignments with `build-egohumans-splits`.
8. Optionally export/import CVAT task packages.
9. Build immutable generic releases with `build-release` or EgoHumans calibration releases with `build-egohumans-release`.
10. Validate releases with `validate-release`, then hand release roots to `vision-trainer`.

## Current Readiness

- Phase 2 validation and ingest are implemented for fixture packages and now accept the EgoHumans edge output naming (`package_clip_id`).
- EgoHumans packages require source-frame maps and explicit detector/tracker settings.
- Trust scoring handles the Edge Node table shape (`frame_idx`, `x1/y1/x2/y2`, `track_id`, `confidence`).
- Review queues exist for hard-case, ambiguous, candidate-negative, and random-audit workflows.
- EgoHumans hidden-oracle import writes normalized frame indexes, proxy oracle labels, class maps, and deterministic reveal-set records under the curator store while preserving `oracle_hidden` vs. `gold_revealed`.
- Dataset release building is available for pseudo-only/curated smoke releases and EgoHumans calibration releases.
- The five EgoHumans trainer-ready calibration releases have been built and validated under `$OPENCLAW_DATASET_RELEASE_STORE/calibration`.
- `vision-trainer` validation and dry-run training command preparation passed for all five EgoHumans release roots.

## Current EgoHumans Calibration Releases

The current release set is:

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`
- `oracle_upper_bound`

All five use the same frozen validation/test definitions from:

`$OPENCLAW_CURATOR_STORE/oracle/egohumans/splits/split_assignments_v0.jsonl`

Hidden oracle, revealed gold, and teacher pseudo labels must stay separate. Realistic releases forbid `oracle_hidden` for training. `oracle_upper_bound` is diagnostic headroom only.

## Next Work

The next task is in `vision-trainer`: run the EgoHumans calibration test matrix over the five release roots and report teacher, gold-only, naive pseudo, trusted-track, review-revealed, and oracle upper-bound outcomes. Use `docs/EGOHUMANS_VISION_TRAINER_TASK_SPEC.md` as the task specification.

## Current EgoHumans Package Location

The six real Lego Assembly Phase 2 packages used for oracle smoke testing are staged under:

`$OPENCLAW_RAW_PACKAGE_STORE/incoming`

Keep this directory as the current immutable staging location until a deliberate archival/promote step is defined. Do not delete `incoming` just to make the package store flatter.

## Path Portability Follow-Up

Edge packages currently preserve some Edge Node absolute paths for source images and source dataset files. Those paths are provenance only on the desktop. Required curator inputs must be package-relative or clip-relative after transfer. Until the contract is tightened, EgoHumans release materialization falls back to extracting frames from immutable `clip.mp4` files and caches them under `$OPENCLAW_CURATOR_STORE/image_cache/egohumans`.
