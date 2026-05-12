# EgoHumans Lego Assembly — Vision Curator Gold Set Proposal

## Purpose
Use EgoHumans Lego Assembly as a fully labeled calibration dataset while simulating the real OpenClaw semi-supervised workflow.

The curator should treat ground truth as a hidden oracle, not as globally available training truth. This allows calibration of the full teacher-student framework without manual labeling.

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
   - only `gold_revealed` labels

2. `gold_plus_naive_pseudo_v0`
   - gold plus high-confidence framewise pseudo labels
   - used as a baseline to show why track-aware curation matters

3. `gold_plus_trusted_tracks_v0`
   - gold plus trusted track-aware pseudo labels

4. `gold_plus_review_revealed_v1`
   - gold seed plus labels revealed through simulated review queues

5. `oracle_upper_bound`
   - full labels, for upper-bound comparison only; not part of the realistic loop

## Curator Deliverables
- validated package index
- oracle label import under hidden namespace
- pseudo-label index from edge packages
- trust score tables
- review queues
- revealed-gold labels for selected queue items
- curated release manifests
- calibration report comparing pseudo labels to oracle

## Do Not Do
- Do not train from `oracle_hidden` except for the explicit upper-bound baseline.
- Do not use hidden test labels to tune thresholds.
- Do not randomly split adjacent frames across train and test.
- Do not treat unmatched teacher predictions or no-detection frames as negatives without oracle/human confirmation.
