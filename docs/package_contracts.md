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

The root manifest must include `package_id` and a `clips` list. Each clip manifest must include `clip_id`.

During bring-up, test fixtures store JSON/JSONL content in `.parquet`-named files to avoid a hard pyarrow dependency. The external contract remains a track/detection table at those paths.
