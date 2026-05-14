# Closeout — EgoHumans Gold Set Releases

## Summary

Materialized the EgoHumans Lego Assembly calibration release workflow in `vision-curator` and built all five trainer-facing releases under `$OPENCLAW_DATASET_RELEASE_STORE/calibration`.

## Decisions Made

- Added an EgoHumans-specific release builder rather than overloading the generic release builder, because oracle/gold/pseudo namespace policy is calibration-specific.
- Kept global trust bucket semantics stable, but documented and applied stricter EgoHumans pseudo-label selection thresholds for the trusted-track release.
- Treated absolute Edge Node paths as provenance only and used package-local `clip.mp4` extraction plus a curator-side image cache when desktop-readable source images were not available.
- Kept `oracle_upper_bound` as the only full-oracle training release and marked it diagnostic headroom only.

## Outputs

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`
- `oracle_upper_bound`

All five releases share frozen validation/test definitions from:

```text
$OPENCLAW_CURATOR_STORE/oracle/egohumans/splits/split_assignments_v0.jsonl
```

## New / Changed Commands

```bash
python -m vision_curator.cli build-egohumans-splits --store-root "$OPENCLAW_CURATOR_STORE"
python -m vision_curator.cli build-egohumans-release --release-family <family> --release-id <release_id> --store-root "$OPENCLAW_CURATOR_STORE" --release-store "$OPENCLAW_DATASET_RELEASE_STORE"
python -m vision_curator.cli validate-release --release-root "$OPENCLAW_DATASET_RELEASE_STORE/calibration/<release_id>"
```

## Gotchas / Invariants

- Realistic calibration releases must not train from `oracle_hidden`.
- `oracle_upper_bound` is diagnostic headroom only.
- `vision-trainer` expects `dataset.yaml` `names` as a zero-indexed YAML mapping.
- `vision-trainer` expects release `split_policy` and `label_policy` manifest fields as mappings.
- Edge Node absolute paths inside package/oracle provenance are not desktop-readable inputs.
- `gold_plus_trusted_tracks_v0` is intentionally conservative and sparse: 626 train objects versus 1371/1695 val/test oracle eval objects.

## TODOs / Follow-Ups

- In `vision-trainer`, run the full EgoHumans calibration matrix described in `docs/EGOHUMANS_VISION_TRAINER_TASK_SPEC.md`.
- Add non-test oracle precision analysis for trusted-track pseudo labels before relaxing trusted-track thresholds.
- Formalize portable package paths vs Edge-local provenance paths in package contracts and validation.
- Consider a declared variant of `gold_plus_review_revealed_v1` that also includes trusted pseudo labels.
- Improve record-level label lineage in `label_items.jsonl` with source oracle/reveal/detection IDs and source table paths.

## Verification Evidence

- `python3 -m unittest` — 26 tests passed.
- `python3 -m compileall src tests` — passed.
- Validated all six staged EgoHumans Phase 2 package roots.
- Ingested all six package roots.
- Scored all six packages.
- Built review queues from pseudo-label metadata.
- Built frozen split assignments.
- Built and curator-validated all five releases.
- `vision-trainer` release validation passed for all five release roots.
- `vision-trainer` dry-run smoke command preparation passed for all five release roots.

## Trainer Next Step

Use `docs/EGOHUMANS_VISION_TRAINER_TASK_SPEC.md` as the next task specification for `vision-trainer`.
