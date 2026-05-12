# EgoHumans Lego Assembly — Vision Curator Gold Set Proposal

## Purpose
Use EgoHumans Lego Assembly as a fully labeled calibration dataset while simulating the real OpenClaw semi-supervised workflow.

The curator should treat ground truth as a hidden oracle, not as globally available training truth. This allows calibration of the full teacher-student framework without manual labeling.

## Current Status

As of the real-package oracle smoke on branch `import-egohumans-oracle`, the curator substrate for this proposal exists but the trainer-ready release families still need to be materialized.

Completed:
- Six EgoHumans Lego Assembly Phase 2 packages are staged under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`.
- `validate-package` passes for all six packages.
- `import-egohumans-oracle` runs against all six packages and writes accumulated dataset-level oracle artifacts under `$OPENCLAW_CURATOR_STORE/oracle/egohumans`.
- The imported hidden-oracle artifacts contain:
  - `normalized/frame_index.jsonl`: 8,227 rows
  - `normalized/oracle_labels.jsonl`: 8,839 `oracle_hidden` labels
  - `normalized/oracle_checked_negative_frames.jsonl`: 2,248 rows
  - `reveal_sets/gold_seed_v0.jsonl`: 884 `gold_revealed` rows
  - `reveal_sets/review_revealed_gold_v0.jsonl`: 398 `gold_revealed` rows
  - `reveal_sets/gold_negatives_v0.jsonl`: 113 rows
- `source_dataset_manifest.json` records all six package IDs, all six sequences, `aria01`/`aria02`/`aria03`, and zero import warnings.

Still needed before handing trainer-ready datasets to `vision-trainer`:
- Ingest the six real package roots into the curator package index if not already indexed.
- Score packages and build review queues from `pseudo_teacher` metadata only.
- Define frozen split assignment records for `oracle_test_hidden`, `oracle_val_hidden`, `gold_seed_pool`, and `unlabeled_pool`.
- Convert `oracle_hidden`, `gold_revealed`, and `pseudo_teacher` records into YOLO image/label release directories without namespace leakage.
- Emit release manifests that clearly identify label namespace, label policy, split policy, source package IDs, and whether the release is a realistic calibration release or the diagnostic headroom release.
- Run release validation and a `vision-trainer` packaging smoke before starting training.

## Three Label States
Every frame/clip should be assigned labels under three distinct namespaces:

1. `oracle_hidden`
   - The full EgoHumans annotations.
   - Used only for evaluation, calibration analysis, and simulated human review reveal.

2. `gold_revealed`
   - A small subset of oracle labels revealed to the training framework.
   - Simulates labels that Dr. Long would have manually created in the real thermal pipeline.

3. `pseudo_teacher`
   - Teacher predictions and ByteTrack outputs from the Xavier Edge Node.
   - Used for trust scoring, review queues, and pseudo-label training releases.

Never mix these namespaces silently.

## Core Idea
The experiment should not ask: “How good can we train if we use all EgoHumans labels?”

It should ask: “If we pretend most labels are unavailable, can our curator select useful pseudo labels and a small growing gold set that improves a student model?”

## Recommended Data Splits
Split by clip or sequence chunk, not random frame, to avoid temporal leakage.

Suggested first split:
- `oracle_test_hidden`: 20% of clips, never used for training, threshold tuning, or active selection.
- `oracle_val_hidden`: 10–15% of clips, used for model selection and calibration reporting.
- `gold_seed_pool`: 5–10% of clips revealed as initial gold labels.
- `unlabeled_pool`: remaining clips; labels hidden except when selected for simulated review.

If multiple ego cameras/views are available, avoid putting near-identical simultaneous views of the same moment into both train and test unless the goal is a camera-view generalization test.

The next implementation should persist the split assignment as an explicit artifact, for example:

```text
$OPENCLAW_CURATOR_STORE/oracle/egohumans/splits/split_assignments_v0.jsonl
```

Each row should identify `package_id`, `package_clip_id`, sequence, camera, frame or chunk bounds, split name, and split rationale. Release builders must consume this artifact rather than recomputing random splits.

## Gold Seed Strategy
Create `gold_seed_v0` with a mixture of:
- easy true positives
- hard positives
- false-positive-prone clutter/background cases
- localization-hard cases
- multi-person interaction/occlusion cases
- edge-of-frame and truncated body cases

Do not make the seed set only the hardest failures. The model needs a stable representation of normal positives as well.

## Hard-Case Gold Evaluation Set
Use the oracle to identify a frozen stress-test set before iterative training begins.

Hard-case tags:
- `teacher_false_negative`
- `teacher_false_positive`
- `poor_localization`
- `id_switch_or_fragmentation`
- `occlusion`
- `small_person`
- `edge_truncated`
- `multi_person_overlap`
- `motion_blur_or_egomotion`

This set should be frozen and reported separately from ordinary validation metrics.

## Review Queue Simulation
For calibration, use the curator queue exactly as it will be used in production:

1. Build queues from pseudo-label metadata only.
2. Select clips for review based on trust score, ambiguity, novelty, and audit sampling.
3. “Reveal” EgoHumans oracle annotations only after the item is selected.
4. Store revealed labels as `gold_revealed`, not as global oracle labels.

This simulates a human labeling workflow without requiring manual labeling.

## Trust Scoring Calibration
Use oracle labels to evaluate trust outputs, not to generate them.

For every teacher track, compute:
- class trust score
- box trust score
- decision bucket
- features used by the scorer

Then compare to oracle:
- Did the track match a real person?
- What was its best IoU?
- Did it preserve identity?
- Did it cover all visible frames?
- Did it miss nearby people in the same frame?

## Bucket Calibration Targets
Initial targets:

### `trusted_full`
Use for full pseudo supervision.
- pseudo-label precision target: >= 95%, preferably >= 98%
- median matched IoU: >= 0.75
- low missing-neighbor rate

### `trusted_class_weak_box`
Use for review or reduced-weight/class-only experiments.
- likely person but box stability is weak
- do not use as ordinary YOLO ground truth unless the trainer supports reduced regression weight

### `ambiguous`
Use for review queue.
- expected high review yield
- likely source of recall gains

### `candidate_negative`
Use only for human/oracle confirmation.
- never treat no-detection clips as negative without confirmation

### `discard`
Use for low-value artifacts.
- still sample a tiny fraction for random audits

## Curated Release Types
Produce multiple releases to support ablation:

1. `gold_only_v0`
   - Training labels: `gold_revealed` seed records only.
   - Validation/test labels: hidden oracle evaluation splits only, not used as training truth.
   - Purpose: small-gold baseline.
   - Remaining work: materialize YOLO images/labels from `gold_seed_v0.jsonl` and split assignments.

2. `gold_plus_naive_pseudo_v0`
   - Training labels: `gold_revealed` seed records plus high-confidence framewise `pseudo_teacher` boxes.
   - Purpose: baseline showing whether naive confidence filtering is enough.
   - Remaining work: define the naive confidence threshold and write pseudo-teacher records to release labels without reading oracle labels for selection.

3. `gold_plus_trusted_tracks_v0`
   - Training labels: `gold_revealed` seed records plus `pseudo_teacher` labels whose tracks land in `trusted_full`.
   - Purpose: main track-aware trust curation candidate.
   - Remaining work: run trust scoring on real packages, calibrate trust outputs against oracle for reporting only, and materialize trusted pseudo labels.

4. `gold_plus_review_revealed_v1`
   - Training labels: `gold_seed_v0` plus `review_revealed_gold_v0`, and optionally trusted pseudo labels depending on the experiment variant.
   - Purpose: simulate active review yield after queues are built from pseudo-label metadata.
   - Remaining work: generate review queues first, reveal oracle labels only for selected queue items, and freeze the resulting reveal set.

5. `oracle_upper_bound`
   - Training labels: full `oracle_hidden` labels.
   - Purpose: diagnostic headroom reference only; not part of the realistic loop.
   - Remaining work: build a clearly marked complete-oracle training release using the same hidden validation/test definitions as the realistic releases.

## Release Build Requirements

The current generic `build-release` path can create simple YOLO release directories, but it is not yet aware of EgoHumans label namespaces, oracle/reveal records, pseudo-teacher records, or fixed calibration split assignments. The next implementation should add an EgoHumans-specific release builder or extend the release config schema so each release can declare:

- release family: `gold_only_v0`, `gold_plus_naive_pseudo_v0`, `gold_plus_trusted_tracks_v0`, `gold_plus_review_revealed_v1`, or `oracle_upper_bound`
- allowed training namespaces
- forbidden training namespaces
- source package roots or package IDs
- oracle root: `$OPENCLAW_CURATOR_STORE/oracle/egohumans`
- split assignment artifact
- pseudo-label selection policy, when applicable
- whether full oracle training is allowed

Every release manifest must make these fields inspectable by `vision-trainer` and by later audit:

- `label_namespaces_used_for_train`
- `label_namespaces_used_for_eval`
- `forbidden_label_namespaces_for_train`
- `release_family`
- `realistic_calibration_loop: true|false`
- `oracle_upper_bound: true|false`
- `source_oracle_manifest`
- `source_reveal_sets`
- `source_pseudo_policy`

For all realistic releases, `forbidden_label_namespaces_for_train` must include `oracle_hidden`.

For `oracle_upper_bound`, `oracle_upper_bound` must be `true`, `realistic_calibration_loop` must be `false`, and the manifest must state that the release is diagnostic headroom only.

## Main Calibration Dataset Set

The main calibration experiment should produce at least these trainer-facing releases:

```text
gold_only_v0
gold_plus_naive_pseudo_v0
gold_plus_trusted_tracks_v0
gold_plus_review_revealed_v1
```

All four should use the same frozen validation/test definitions so model comparisons are meaningful. The only difference should be the training label policy. Oracle labels may be used to evaluate and report these releases, but not to choose pseudo labels, tune trust thresholds on test, or populate training labels except through explicit `gold_revealed` reveal records.

## Headroom Dataset Set

The headroom experiment should produce:

```text
oracle_upper_bound
```

This release may train from full `oracle_hidden` labels, but it must use the same frozen validation/test definitions as the realistic calibration releases. Its result should be reported as remaining headroom for the curation loop, not as a deployable semi-supervised workflow.

Do not use `oracle_upper_bound` to:

- tune trust thresholds for realistic releases
- choose review queue items
- accept pseudo labels
- claim realistic deployment performance

## Curator Deliverables
- validated package index for all six incoming Lego packages
- hidden-oracle artifacts under `$OPENCLAW_CURATOR_STORE/oracle/egohumans` — done
- pseudo-label index from Edge packages
- trust score tables for all six packages
- review queues built only from pseudo-label metadata
- frozen split assignment artifact
- revealed-gold labels for selected seed/review items
- trainer-ready release directories for all realistic release families
- trainer-ready `oracle_upper_bound` release for headroom only
- calibration report comparing pseudo labels to oracle without leaking oracle into selection

## Do Not Do
- Do not train from `oracle_hidden` except for the explicit upper-bound baseline.
- Do not use hidden test labels to tune thresholds.
- Do not randomly split adjacent frames across train and test.
- Do not treat unmatched teacher predictions or no-detection frames as negatives without oracle/human confirmation.

## Next Task Handoff

The next `vision-curator` session should complete the release materialization work needed by `vision-trainer`.

Recommended execution order:

1. Confirm the six incoming package roots and oracle output counts.
2. Ingest the six package roots into the curator store.
3. Run trust scoring for each package.
4. Build review queues from pseudo-label metadata only.
5. Create and persist `split_assignments_v0.jsonl`.
6. Build `gold_only_v0` from `gold_seed_v0`.
7. Build `gold_plus_naive_pseudo_v0` from `gold_seed_v0` plus a documented naive pseudo policy.
8. Build `gold_plus_trusted_tracks_v0` from `gold_seed_v0` plus trusted track-aware pseudo labels.
9. Build `gold_plus_review_revealed_v1` from `gold_seed_v0` plus simulated review reveals, optionally with trusted pseudo labels if declared.
10. Build `oracle_upper_bound` from full `oracle_hidden` labels and mark it as diagnostic headroom.
11. Validate every release and produce a short handoff summary for `vision-trainer` with release roots, dataset YAML paths, label policies, and expected experiment interpretation.

Minimum next-task acceptance criteria:

- all release roots are immutable and do not overwrite prior releases
- every release has `dataset.yaml`, YOLO labels, splits, manifest, and provenance
- realistic releases never train from `oracle_hidden`
- `oracle_upper_bound` is the only complete-oracle training release
- all releases share compatible validation/test definitions
- `vision-trainer` can start a smoke training run from the release `dataset.yaml` paths
