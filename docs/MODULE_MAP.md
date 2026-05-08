# Module Map

## CLI
- `src/vision_curator/cli.py` is the command surface.

## Package Boundary
- `src/vision_curator/packages/validate.py` validates Phase 2 package roots and normalizes clip records.
- `src/vision_curator/packages/ingest.py` writes immutable source-path package index records.
- `schemas/phase2_manifest.schema.json` documents the durable root manifest shape.

## Scoring
- `src/vision_curator/scoring/trust.py` computes deterministic track scores.
- `src/vision_curator/scoring/buckets.py` records bucket constants.
- `src/vision_curator/scoring/jitter.py` contains geometry helpers.

## Review
- `src/vision_curator/review/queues.py` builds review queue JSONL files from scored tracks.
- `src/vision_curator/review/hard_cases.py` and `src/vision_curator/review/sampler.py` hold review helpers.

## Annotation
- `src/vision_curator/annotation/cvat_export.py` creates CVAT task package stubs from review queues.
- `src/vision_curator/annotation/cvat_import.py` imports corrected annotation packages.
- `src/vision_curator/annotation/yolo_roundtrip.py` handles YOLO-format exchange helpers.

## Releases
- `src/vision_curator/releases/build.py` builds immutable release directories.
- `src/vision_curator/releases/validate.py` validates release shape.
- `schemas/dataset_release.schema.json` documents the release manifest contract.

## Optional Views
- `src/vision_curator/fiftyone/views.py` is optional and must not be required for core validation, scoring, queue, or release tests.
