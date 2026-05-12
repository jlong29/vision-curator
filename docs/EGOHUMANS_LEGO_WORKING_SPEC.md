# EgoHumans Lego Working Spec

Status: active durable workspace reference  
Last updated: 2026-05-05

## Purpose
This doc captures the current learned spec for working with the EgoHumans Lego Assembly data inside this workspace, especially for edge-node calibration experiments.

It is meant to prevent us from relearning the same facts each time we touch the dataset.

## Scope
Primary current sequence:
- `~/openclawInfo/datasets/egohumans/005_legoassemble.tar.gz`

Related reference repo:
- `~/openclawInfo/repos/egohumans`

Primary active repo for edge-side work:
- `src/vision_api`

## Core interpretation
Use EgoHumans Lego Assembly as a calibration dataset for the OpenClaw teacher-student system, but treat it as deployment-like edge input.

That means:
- edge-side tooling should process the data as if it were unlabeled deployment video
- ground-truth annotations must not be used on the edge to generate pseudo labels
- ground truth, when needed, belongs in desktop-side hidden-oracle evaluation workflows

## What the uploaded tarballs are, and are not
The uploaded `camera_ready` tarballs are not full canonical benchmark exports.

Important consequence:
- the tarballs do **not** include the exported upstream benchmark COCO json files
- therefore local edge-side conversion currently uses aligned `processed_data/poses2d/...` as a proxy label source
- raw `processed_data/bboxes/...` should **not** be treated as canonical ground truth

## Current label semantics rule
For local reviewable package generation in `vision_api`:
- use upstream benchmark-style semantics as closely as possible
- exclude viewer/self labels
- honor upstream sequence config rules such as `INVALID_ARIAS`
- derive boxes from visible pose keypoints using the benchmark-style pose-to-box rule

This is a useful benchmark-semantics proxy, not a byte-for-byte canonical benchmark dump.

## Sequence-specific rule for `005_legoassemble`
Reference config:
- `~/openclawInfo/repos/egohumans/egohumans/configs/legoassemble/005_legoassemble.yaml`

Observed current facts:
- `INVALID_ARIAS: []`
- upstream `SMPL.ARIA_NAME_LIST` includes `aria01`, `aria02`, `aria03`

Interpretation:
- `aria02` is **not** upstream-invalid for `005_legoassemble`
- if we exclude `aria02`, that must be justified by practical usability or calibration-fit concerns, not by claiming upstream forbids it

## Current practical usability judgment
Based on prior saved validation artifacts:
- `aria01` and `aria03` are the strongest current baseline streams for full-package benchmarking
- `aria02` is still potentially usable, but is much sparser in the previously saved upstream-semantics validation artifact
- do not describe `aria02` as categorically unusable unless a fresh pipeline run proves it

## Current artifact families
### 1) Proxy-label conversion packages
Used for dataset/package inspection and benchmark preparation.

Examples:
- `~/openclawInfo/outputs/egohumans_conversion/005_legoassemble_upstream_semantics/`
- `~/openclawInfo/outputs/egohumans_conversion/005_legoassemble_full_package/`

### 2) Benchmark videoized evaluation artifacts
Used to run the deployed edge detector against the packaged EgoHumans images.

Examples:
- `~/openclawInfo/datasets/benchmarks/005_legoassemble_full_package_benchmark/`
- `~/openclawInfo/outputs/benchmarks/005_legoassemble_full_package/yolo11_person_v1/`

### 3) Dedicated Phase 2 edge packages
These are the desired richer packaging outputs for calibration and curator ingestion.

Expected shape:
```text
<phase2_root>/
├─ manifest.json
├─ READY.json
└─ clips/
   └─ <package_clip_id>/
      ├─ clip.mp4
      ├─ clip_manifest.json
      ├─ detections.parquet
      ├─ tracks.parquet
      ├─ source_frames.jsonl
      └─ preview.mp4   # optional but preferred
```

## Current compliance truth
Be precise here.

The historical `vision_api` EgoHumans work already validated:
- proxy-label conversion
- benchmark-video construction
- deployed-detector scoring against the proxy package

That is useful and still valid.

But it is not the same as a fully proposal-compliant Phase 2 edge package.

## Working distinction that must be preserved
### Proxy benchmark package
Good for:
- package review
- detector scoring
- calibration baselines
- workflow debugging

Not enough by itself for:
- full Phase 2 curator-ready ingestion
- explicit raw edge provenance contract
- tracker-rich package semantics

### Phase 2 edge package
Should preserve:
- source sequence and camera identity
- explicit frame-to-source mapping
- raw or low-threshold detector outputs
- explicit tracker backend identity
- completion marker and inspectable artifacts

## Current edge-side policy
When implementing or modifying EgoHumans edge-side workflows:
- prefer explicit artifacts over hidden transformations
- preserve source frame mapping
- preserve the exact model profile and runtime settings used
- keep tracker provenance explicit
- never call the tracker `bytetrack` unless the implementation truly uses ByteTrack
- do not mutate the original EgoHumans tarball contents
- for large EgoHumans tarballs, extract the tarball first and then run conversion against the extracted directory tree; avoid archive-backed conversion as the default path because it is dramatically slower and more interruption-prone

## Current rerun baseline
Useful existing commands in `src/vision_api`:
- `python3 scripts/inspect_egohumans_archive.py ~/openclawInfo/datasets/egohumans/005_legoassemble.tar.gz --output-dir <dir>`
- `python3 scripts/convert_egohumans_subset.py ~/openclawInfo/datasets/egohumans/005_legoassemble.tar.gz --subset-key 02_lego/005_legoassemble --output-dir <dir> ...`
- `PYTHONPATH=. .venv/bin/python scripts/evaluate_dataset_package.py --package-manifest <manifest> --benchmark-dir <dir> --results-dir <dir>`

## Calibration-use guidance
When using Lego for calibration experiments:
- keep hidden oracle labels conceptually separate from edge pseudo labels
- use the saved full-package benchmark as a baseline reference point
- prefer honest provenance over forced compliance language
- if a package uses a simple tracker or no tracker, say so explicitly

## Current Phase 2 tracker status
As of 2026-05-05, the dedicated EgoHumans Phase 2 path in `src/vision_api` now engages the already-validated thermal-data-engine ByteTrack backend for real package generation.

Concrete artifact:
- `~/openclawInfo/outputs/egohumans_phase2/005_legoassemble_full_package__yolo11_person_v1_bytetrack/manifest.json`

Current observed result on the saved Lego full package:
- `tracker_backend = ultralytics_bytetrack_v1`
- `2` stream clips
- `18,743` detections
- `108` tracks total

Important consequence:
- the workspace should no longer describe the dedicated Phase 2 path as inherently limited to the simple IOU fallback
- if the fallback path is used in a test or degraded environment, that should be called out explicitly for that run only

## What to update when we learn more
Update this doc when any of the following become true:
- `aria02` is promoted into the standard full-package calibration set
- the ByteTrack-backed EgoHumans Phase 2 path changes materially
- the package contract changes materially
- we move from proxy-label benchmark packages to a more canonical label source
