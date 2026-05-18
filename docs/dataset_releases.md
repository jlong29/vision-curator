# Dataset Releases

Dataset releases are immutable once published.

Required layout:

```text
<release_root>/
├─ dataset.yaml
├─ images/
├─ labels/
├─ splits/
│  ├─ train.txt
│  ├─ val.txt
│  └─ test.txt
├─ manifest.json
└─ provenance/
   ├─ build_config.json
   └─ source_packages.jsonl
```

`manifest.json` records `source_package_ids`, expanded `source_packages` provenance, `annotation_versions`, `annotation_status`, label policy, split policy, and counts. `annotation_status: pseudo_only` means the release is a smoke or bootstrap artifact and must not be treated as human-verified gold data.

For `vision-trainer` compatibility, `dataset.yaml` should write `names` as a zero-indexed YAML mapping:

```yaml
names:
  0: person
```

`split_policy` and `label_policy` in `manifest.json` should be mappings, not opaque strings.

## EgoHumans Calibration Releases

EgoHumans calibration releases are built with:

```bash
python -m vision_curator.cli build-egohumans-splits --store-root "$OPENCLAW_CURATOR_STORE"
python -m vision_curator.cli build-egohumans-release --release-family <family> --release-id <release_id> --store-root "$OPENCLAW_CURATOR_STORE" --release-store "$OPENCLAW_DATASET_RELEASE_STORE"
python -m vision_curator.cli validate-release --release-root "$OPENCLAW_DATASET_RELEASE_STORE/calibration/<release_id>"
```

Supported release families:

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`
- `oracle_upper_bound`

Realistic calibration releases must forbid `oracle_hidden` for training. `oracle_upper_bound` is the only full-oracle training release and is diagnostic headroom only.
