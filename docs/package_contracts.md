# Package Contracts

## Phase 2 Input

```text
<phase2_root>/
├─ manifest.json
├─ READY.json                 # optional generic marker; expected for completed edge spools
└─ clips/
   └─ <package_clip_id>/
      ├─ clip.mp4
      ├─ clip_manifest.json
      ├─ detections.parquet
      └─ tracks.parquet
```

The root manifest must include `package_id` and a non-empty `clips` list. Clip IDs may be represented as `clip_id` or `package_clip_id`; the latter is the preferred edge-package name when source-dataset frame identity matters.

`vision-curator` indexes raw packages by immutable source path. It does not copy or mutate raw clips during ingest. When present, provenance fields such as `run_id`, `dataset_source`, `activity`, `runtime`, `tracker`, `model_profile`, `detector_backend`, `tracker_backend`, `tracker_config_hash`, `source_node_id`, `completion_state`, and timestamps are preserved in the curator package index and propagated into score and review records.

During bring-up, test fixtures store JSON/JSONL content in `.parquet`-named files to avoid a hard pyarrow dependency. The external contract remains a track/detection table at those paths.

## Path Portability Rule

Phase 2 packages are portable immutable units. After desktop transfer, required curator inputs must be readable from package-local, clip-local, package-relative, or clip-relative paths.

Absolute paths from the Edge Node may be preserved only as provenance/audit metadata. They must not be the only way for desktop workflows to read required inputs.

Recommended field naming:

- `*_path` for package-relative or clip-relative paths that the curator should dereference.
- `source_*_path`, `origin_*_path`, or `edge_*_path` for historical Edge/source-machine provenance that may not exist on the desktop.

Current compatibility note: some EgoHumans oracle/source records include Edge-local image paths. `vision-curator` therefore materializes releases from package-local `clip.mp4` frames and caches extracted images under `$OPENCLAW_CURATOR_STORE/image_cache/egohumans`.

## EgoHumans Calibration Package Requirements

For `dataset_source: egohumans`, validation is intentionally stricter because source-frame alignment is required for oracle-backed calibration. The package manifest must include:

- `dataset_source: egohumans`
- `activity`, expected initially as `lego_assembly`
- `package_type`
- `producer_repo`
- `model_profile`
- `model_artifact_version`
- `detector_backend`
- `tracker_backend`, expected as `bytetrack` for the completed edge run
- `tracker_config_hash`
- `frame_stride`
- `detection_confidence_threshold`
- `nms_threshold`
- `clips`

Each EgoHumans clip manifest must include:

- `package_clip_id`
- `source_sequence_id`
- `source_camera_id`
- `start_frame_idx`
- `end_frame_idx`
- `fps`
- `width`, `height`
- `frame_count`
- `source_frame_map_path`
- `detections_path`
- `tracks_path`

`source_frame_map_path` must resolve to an existing JSONL file inside the clip directory. Ground-truth EgoHumans annotations are not part of the edge package and must not be used during edge pseudo-label generation; they are imported on the desktop as hidden oracle data for calibration.

## Detection and Track Tables

The scoring path accepts the current fixture aliases and the edge proposal columns:

- frame identity: `frame_idx`, `frame_index`, or `frame`
- boxes: either `bbox`, `x/y/w/h`, or `x1/y1/x2/y2`
- confidence: `confidence`, `conf`, or `score`
- grouping: `track_id`

For EgoHumans packages, `source_frame_idx` and `source_image_path_or_name` should be present so review and oracle-evaluation code can align pseudo labels to hidden annotations.

`source_image_path_or_name` is alignment/provenance metadata unless it is explicitly package-relative and present after transfer. Curator release builders must not require that field to point to a desktop-readable absolute path.
