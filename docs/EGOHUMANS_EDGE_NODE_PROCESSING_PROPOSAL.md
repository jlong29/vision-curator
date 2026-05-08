# EgoHumans Lego Assembly — Xavier Edge Node Processing Proposal

## Purpose
Process the EgoHumans Lego Assembly subset exactly as if it were deployment data: mostly unlabeled video entering the edge pipeline, producing pseudo-label packages and tracking metadata for desktop curation.

The edge node must not use ground-truth annotations during this run. Ground truth should remain a hidden oracle on the desktop side.

## Processing Goals
1. Produce Phase 2 context-rich clip packages with ByteTrack metadata.
2. Preserve exact frame mapping back to EgoHumans source frames.
3. Preserve low-threshold detections so the curator can calibrate trust thresholds.
4. Produce inspectable preview overlays for QA.
5. Emit package metadata sufficient for downstream evaluation against hidden oracle labels.

## Recommended Edge Inputs
Use the already validated Lego Assembly image sequences converted to video, or process image sequences through a video-compatible wrapper.

For every processed video, preserve:
- EgoHumans sequence name
- activity: `lego_assembly`
- camera/view id
- source image directory
- frame index mapping
- original image filename per output frame
- fps used for video reconstruction
- model profile
- detector version
- tracker backend and tracker config

## Detection and Tracking Settings
Use the current deployed teacher model, e.g. YOLO11m, and the real ByteTrack backend.

Recommended initial settings:
- `frame_stride = 1`
- detection confidence threshold low enough to retain candidate weak positives, e.g. `0.05–0.15`
- standard NMS, but record NMS threshold in metadata
- track every frame
- do not discard low-confidence tracks before writing raw detection and track artifacts

Rationale: the curator can always filter later, but it cannot recover detections that the edge node discarded before packaging.

## Required Phase 2 Package Shape
```text
<phase2_root>/
├─ manifest.json
├─ READY.json
└─ clips/
   ├─ <package_clip_id>/
   │  ├─ clip.mp4
   │  ├─ clip_manifest.json
   │  ├─ detections.parquet
   │  ├─ tracks.parquet
   │  ├─ source_frames.jsonl
   │  └─ preview.mp4              # optional but recommended
   └─ ...
```

## Required Fields

### Package Manifest
- `package_id`
- `dataset_source = egohumans`
- `activity = lego_assembly`
- `package_type = phase2_context_rich_clip_package`
- `created_at`
- `producer_repo = thermal-data-engine`
- `vision_api_job_id`, if applicable
- `model_profile`
- `model_artifact_version`
- `detector_backend`
- `tracker_backend = bytetrack`
- `tracker_config_hash`
- `frame_stride`
- `detection_confidence_threshold`
- `nms_threshold`
- `clip_count`

### Clip Manifest
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

### Detections Table
Minimum columns:
- `package_id`
- `package_clip_id`
- `frame_idx`
- `source_frame_idx`
- `source_image_path_or_name`
- `det_id`
- `track_id`
- `class_id`
- `class_name`
- `confidence`
- `x1`, `y1`, `x2`, `y2`

### Tracks Table
Minimum columns:
- `package_id`
- `package_clip_id`
- `track_id`
- `class_name`
- `start_frame_idx`
- `end_frame_idx`
- `duration_frames`
- `frames_present`
- `detection_density`
- `mean_confidence`
- `min_confidence`
- `max_confidence`
- `bbox_area_mean`
- `bbox_area_std`
- `bbox_jitter_mean`
- `edge_fraction`

## Verification Before Desktop Pull
Run these checks before declaring the package ready:
1. `READY.json` exists only after all package files are complete.
2. Every clip has `clip.mp4`, `clip_manifest.json`, `detections.parquet`, and `tracks.parquet`.
3. `tracks.parquet` contains persistent `track_id` values.
4. Manifest explicitly records `tracker_backend = bytetrack`.
5. A preview overlay confirms that boxes and track IDs visually align with people.
6. The frame map allows exact alignment to EgoHumans ground-truth annotations on the desktop.

## Do Not Do
- Do not import or use EgoHumans ground truth on the Xavier for pseudo-label generation.
- Do not pre-filter down to only high-confidence detections.
- Do not call the output “gold” or “ground truth.”
- Do not mutate the source EgoHumans files.
- Do not train on the Xavier.

## Deliverable to Desktop
A completed Phase 2 package in the raw package store, ready for `vision-curator` ingestion and oracle-backed calibration.

## Desktop Acceptance in `vision-curator`
On the desktop, `vision-curator` treats the delivered package root as immutable. The acceptance path is:

```bash
env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <pulled_egohumans_phase2_package>
env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source <pulled_egohumans_phase2_package> --store-root <curator_store>
env PYTHONPATH=src python3 -m vision_curator.cli score-package --package-id <package_id> --store-root <curator_store>
```

Validation requires `source_frame_map_path` for EgoHumans clips so hidden oracle labels can later align to teacher pseudo labels without using ground truth during edge processing.
