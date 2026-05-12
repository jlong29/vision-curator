# Executive Summary — EgoHumans Calibration Before Thermal Deployment

## Recommendation
Use EgoHumans Lego Assembly as a controlled calibration dataset for the OpenClaw teacher-student self-learning system.

The idea is strong because all labels exist, but the framework can pretend most of them are unavailable. This allows the system to test the exact semi-supervised loop intended for thermal deployment while retaining an oracle for evaluation.

## Key Principle
Do not use full EgoHumans annotations as ordinary training labels.

Instead maintain three label namespaces:
- hidden oracle labels
- revealed gold labels
- teacher pseudo labels

This allows realistic simulation of:
- small gold seed sets
- active review queues
- pseudo-label filtering
- growing gold sets
- model promotion gates

## Edge Node Role
The Xavier Edge Node should process Lego Assembly as if it were unlabeled deployment video:
- run YOLO11m teacher inference
- run ByteTrack
- write Phase 2 packages
- preserve frame mapping
- avoid using ground truth

## Vision Curator Role
The curator should:
- ingest edge packages
- import EgoHumans labels as hidden oracle
- compute trust scores from teacher outputs only
- reveal oracle labels only for selected gold/review items
- publish curated releases for ablation experiments

## Current Curator Readiness
`vision-curator` is ready for the completed Edge Node package outputs when they satisfy the Phase 2 contract in `docs/package_contracts.md`:

- `validate-package` accepts both `clip_id` and `package_clip_id`.
- EgoHumans package validation requires explicit detector/tracker settings and source-frame maps.
- Trust scoring reads edge table columns including `frame_idx` and `x1/y1/x2/y2`.
- Review queues and draft dataset releases can be produced from ingested package records.

The next missing implementation area is the calibration label namespace workflow: hidden oracle import, controlled reveal records, and release manifests that distinguish hidden oracle, revealed gold, and teacher pseudo labels.

## Calibration Experiments
Run at least these:
1. teacher baseline
2. gold-only baseline
3. naive high-confidence pseudo-label baseline
4. track-aware trust pseudo-label release
5. track-aware plus simulated review-revealed gold
6. oracle upper bound

## Headroom Reference Experiment
Because EgoHumans Lego Assembly has labels for the full calibration dataset, run one explicit headroom reference experiment:

- train/evaluate a model using the complete oracle label set under a clearly marked `oracle_upper_bound` release,
- compare that result against the iterative teacher-student self-learning releases,
- report the gap as remaining headroom for the curation loop rather than as a realistic deployment workflow.

This is the only experiment that should train from the complete hidden oracle label set. It must remain separate from gold-only, pseudo-label, and review-revealed releases so oracle labels do not leak into the simulated semi-supervised process.

## Main Questions Answered
- Are trusted pseudo-labels actually precise?
- Do review queues find real errors better than random sampling?
- Does track-aware trust beat naive confidence filtering?
- Does a small growing gold set improve recall?
- Does the student beat both the teacher and gold-only baseline?
- Does the next teacher produce better pseudo labels?
- How much headroom remains between the realistic iterative curation loop and training on the complete oracle label set?

## Main Warning
This validates the machinery, not thermal-domain performance. EgoHumans is an egocentric RGB/multiview dataset, while the deployment target is helmet-mounted monocular thermal video. After this calibration succeeds, repeat with a small thermal gold set.
