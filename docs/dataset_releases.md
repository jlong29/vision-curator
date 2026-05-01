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
