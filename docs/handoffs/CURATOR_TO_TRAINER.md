# Curator to Trainer Handoff

`vision-trainer` consumes immutable dataset release directories produced by `vision-curator`.

Release manifests describe source packages, annotation versions, split policy, label policy, class list, counts, creation time, and tool version.

## Current EgoHumans Calibration Handoff

Release roots are under:

```text
$OPENCLAW_DATASET_RELEASE_STORE/calibration/
```

Current release IDs:

| Release | Training policy | Interpretation |
|---|---|---|
| `gold_only_v0` | `gold_revealed` seed labels only | Small-gold baseline |
| `gold_plus_naive_pseudo_v0` | gold seed plus high-confidence framewise teacher pseudo labels | Naive pseudo-label baseline |
| `gold_plus_trusted_tracks_v0` | gold seed plus `trusted_full` track-aware pseudo labels | Precision-first trusted-track ablation |
| `gold_plus_review_revealed_v1` | gold seed plus simulated review-revealed gold | Active-review simulation |
| `oracle_upper_bound` | full `oracle_hidden` training labels | Diagnostic headroom only |

All five share frozen validation/test definitions. Realistic releases forbid `oracle_hidden` for training. `oracle_upper_bound` must not be interpreted as a realistic semi-supervised workflow.

## Validation Commands

From `vision-trainer`:

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

Dry-run training command preparation:

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

## Notes for Trainer Interpretation

- `gold_plus_trusted_tracks_v0` is very sparse under the current precision-first threshold policy: 626 train objects versus 1371/1695 val/test oracle eval objects.
- `gold_plus_naive_pseudo_v0` is the high-volume pseudo-label baseline.
- Validation/test labels are hidden-oracle evaluation labels and should be used for metrics, not for threshold tuning on the hidden test split.
- Trainer dry runs may materialize `.ultralytics_dataset.yaml` and `.ultralytics_splits/` inside release roots; these are trainer shims and not curator release contract files.
