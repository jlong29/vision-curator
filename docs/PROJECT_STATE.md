# Project State

## Current Operational Workflow

`vision-curator` is the desktop curation control plane between Edge Node package production and `vision-trainer` training.

Current working path:

1. Pull completed Phase 2 package roots from the Edge Node into an immutable raw package store.
2. Validate packages with `validate-package`.
3. Register immutable package paths with `ingest-package`.
4. Compute deterministic class and box trust scores with `score-package`.
5. Build review queues with `build-review-queue`.
6. Optionally export/import CVAT task packages.
7. Build immutable dataset releases with `build-release`.

## Current Readiness

- Phase 2 validation and ingest are implemented for fixture packages and now accept the EgoHumans edge output naming (`package_clip_id`).
- EgoHumans packages require source-frame maps and explicit detector/tracker settings.
- Trust scoring handles the Edge Node table shape (`frame_idx`, `x1/y1/x2/y2`, `track_id`, `confidence`).
- Review queues exist for hard-case, ambiguous, candidate-negative, and random-audit workflows.
- Dataset release building is available for pseudo-only or curated smoke releases.

## Next Work

The next task should process the completed Edge Node EgoHumans Lego Assembly packages:

- validate and ingest real pulled package roots,
- compute trust scores,
- build review queues,
- import/register EgoHumans ground truth as hidden oracle labels,
- reveal a controlled subset as simulated gold labels,
- publish calibration releases for `vision-trainer`.

Hidden oracle, revealed gold, and teacher pseudo labels must stay separate.
