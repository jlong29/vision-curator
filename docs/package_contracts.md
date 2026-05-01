# Package Contracts

## Phase 2 Input

```text
<phase2_root>/
├─ manifest.json
└─ clips/
   └─ <package_clip_id>/
      ├─ clip.mp4
      ├─ clip_manifest.json
      ├─ detections.parquet
      └─ tracks.parquet
```

The root manifest must include `package_id` and a non-empty `clips` list. Each clip manifest must include `clip_id`.

`vision-curator` indexes raw packages by immutable source path. It does not copy or mutate raw clips during ingest. When present, provenance fields such as `run_id`, `runtime`, `tracker`, `source_node_id`, `completion_state`, and timestamps are preserved in the curator package index and propagated into score and review records.

During bring-up, test fixtures store JSON/JSONL content in `.parquet`-named files to avoid a hard pyarrow dependency. The external contract remains a track/detection table at those paths.
