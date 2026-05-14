# EgoHumans Vision-Trainer Task Spec

## Purpose

Run the EgoHumans Lego Assembly calibration test matrix in `vision-trainer` using the curated releases produced by `vision-curator`.

This task evaluates the teacher-student curation machinery. It is not evidence of thermal-domain performance.

## Inputs

Release base:

```text
$OPENCLAW_DATASET_RELEASE_STORE/calibration/
```

Releases:

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`
- `oracle_upper_bound`

All releases use common frozen validation/test definitions. Realistic releases do not train from `oracle_hidden`; `oracle_upper_bound` is the only full-oracle training release and is diagnostic headroom only.

## Required Preflight

From `vision-trainer`:

```bash
env | rg '^OPENCLAW_'
```

Validate every release:

```bash
for release_id in \
  gold_only_v0 \
  gold_plus_naive_pseudo_v0 \
  gold_plus_trusted_tracks_v0 \
  gold_plus_review_revealed_v1 \
  oracle_upper_bound
do
  env PYTHONPATH=src python3 -m bootstrap_train.validate_packages \
    --release "$OPENCLAW_DATASET_RELEASE_STORE/calibration/$release_id"
done
```

Confirm command materialization:

```bash
for release_id in \
  gold_only_v0 \
  gold_plus_naive_pseudo_v0 \
  gold_plus_trusted_tracks_v0 \
  gold_plus_review_revealed_v1 \
  oracle_upper_bound
do
  env PYTHONPATH=src python3 -m bootstrap_train.train \
    --config configs/train/curated_release_smoke.yaml \
    --dataset-kind curated_release \
    --dataset-root "$OPENCLAW_DATASET_RELEASE_STORE/calibration/$release_id" \
    --name "${release_id}_smoke" \
    --dry-run
done
```

## Test Matrix

Run at least one smoke training pass for each release, then run the selected full calibration profile for each release.

Minimum matrix:

| Experiment | Release | Purpose |
|---|---|---|
| gold-only baseline | `gold_only_v0` | Measures small revealed-gold baseline |
| naive pseudo baseline | `gold_plus_naive_pseudo_v0` | Tests high-confidence framewise pseudo-label value |
| trusted-track pseudo | `gold_plus_trusted_tracks_v0` | Tests track-aware trust curation |
| review-revealed gold | `gold_plus_review_revealed_v1` | Simulates active review yield |
| oracle headroom | `oracle_upper_bound` | Measures diagnostic headroom only |

If a teacher-only baseline exists in `vision-trainer`, evaluate it on the same frozen validation/test definitions and report it alongside the trained student results.

## Metrics and Reporting

Report:

- training config and model size,
- release root and release manifest ID,
- validation metrics,
- test metrics,
- hard-case/stress metrics if available,
- training time and hardware,
- failure modes or label-policy concerns.

Interpretation requirements:

- Do not use hidden test metrics to tune trust thresholds.
- Treat `oracle_upper_bound` as a diagnostic upper bound, not a deployable workflow.
- Treat `gold_plus_trusted_tracks_v0` as precision-first and sparse: current audit showed 626 train objects versus 1371/1695 val/test oracle eval objects.
- Compare `gold_plus_naive_pseudo_v0` against `gold_plus_trusted_tracks_v0` to determine whether track-aware trust is helping enough to justify lower pseudo-label volume.

## Outputs

Write a trainer-side result summary that includes:

- release ID,
- dataset root,
- dataset YAML path,
- command/config used,
- resulting run directory,
- primary metrics,
- notes on whether the result supports or weakens the curation hypothesis.

The final report should make the next curator decision explicit: keep thresholds, relax thresholds, change trust features, or prioritize review-revealed gold.

## TODOs / Follow-Ups

- Add non-test oracle precision analysis for `trusted_track` pseudo labels before relaxing trusted-track thresholds.
- Confirm whether `gold_plus_review_revealed_v1` should later include trusted pseudo labels as a declared variant.
- Preserve the distinction between Edge-local provenance paths and desktop-readable release paths in any trainer-side reporting.
