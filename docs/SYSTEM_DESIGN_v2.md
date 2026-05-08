# Updated System Design — OpenClaw Thermal Person Detection Bootstrap Pipeline

## Purpose

Build a modular, hierarchical computer-vision system for thermal human detection using noisy, partial, temporally structured semi-supervision.

The system uses:

1. **Edge Inference Node** on Xavier NX
2. **Vision Curator** on desktop
3. **Vision Trainer** on desktop
4. **Workspace orchestration** above all repos

The design intentionally separates data generation, curation, training, and deployment.

---

## Design Principle

The edge generates signal.

The curator decides what is usable.

The trainer produces candidate models.

The workspace root coordinates high-level task completion.

No single repo should silently absorb the responsibilities of another repo.

---

## Current Repo Roles

## 1. `vision_api` — Xavier NX runtime/control plane

### Mission

`vision_api` is the narrow FastAPI control plane for Xavier-side computer-vision jobs.

### Responsibilities

- Validate typed requests
- Enforce workspace path boundaries
- Launch bounded offline inference jobs
- Track job state
- Emit job artifacts
- Expose health and telemetry

### Non-responsibilities

- Dataset curation
- Training
- Annotation
- Broad shell control
- Desktop orchestration

### Boundary

`vision_api` owns the detector/runtime invocation boundary.

`thermal-data-engine` should call it rather than duplicating runtime logic.

---

## 2. `thermal-data-engine` — Xavier NX edge package producer

### Mission

`thermal-data-engine` turns raw thermal video into structured data packages.

### Responsibilities

- Request detector/runtime jobs from `vision_api`
- Collect detections
- Apply or validate tracking
- Build clip packages
- Write manifests
- Generate inspectable artifacts
- Provide lightweight OpenClaw/CLI inspection
- Spool packages for desktop pull

### Current package outputs

#### Phase 1 — Ultralytics-ready dataset package

```text
<phase1_root>/
├─ dataset.yaml
├─ images/
├─ labels/
├─ manifest.json
└─ splits/
   ├─ train.txt
   └─ val.txt
```

This is the current direct training contract.

#### Phase 2 — context-rich clip package

```text
<phase2_root>/
├─ manifest.json
└─ clips/
   ├─ <package_clip_id>/
   │  ├─ clip.mp4
   │  ├─ clip_manifest.json
   │  ├─ detections.parquet
   │  └─ tracks.parquet
   └─ ...
```

This is the current provenance-rich curation/debug contract.

### Important update

Phase 1 and Phase 2 should coexist.

- Phase 1 supports immediate YOLO training and smoke tests.
- Phase 2 supports curator workflows, annotation, trust scoring, and future dataset releases.

---

## 3. `vision-curator` — desktop curation and annotation repo

### Mission

`vision-curator` is the desktop-side repo that owns package ingestion, pseudo-label trust scoring, review queue generation, CVAT/FiftyOne integration, and curated dataset releases.

### Responsibilities

- Validate raw edge packages
- Ingest immutable package records
- Score class trust and box trust
- Build human review queues
- Export preannotations to CVAT
- Import corrected annotations
- Optionally expose FiftyOne views
- Create immutable dataset releases for `vision-trainer`

### Non-responsibilities

- Running edge inference
- Training YOLO models
- Exporting TensorRT engines
- Promoting models to the NX

---

## 4. `vision-trainer` — desktop training and artifact repo

### Mission

`vision-trainer` trains and evaluates YOLO models using curated releases.

### Responsibilities

- Validate training package contracts
- Run smoke training
- Run full training on 3 GPUs
- Evaluate on frozen gold sets
- Export candidate artifacts
- Produce promotion reports

### Current status

The basic training/evaluation/export repo exists. It should evolve to consume curated dataset releases from `vision-curator` instead of relying only on raw Phase 1 packages.

---

## End-to-End Data Flow

```text
Raw thermal video
    ↓
vision_api runtime job
    ↓
thermal-data-engine package generation
    ├── Phase 1 direct YOLO package
    └── Phase 2 clip/provenance package
    ↓
Desktop pull over SSH / rsync
    ↓
Immutable raw package store
    ↓
vision-curator ingest + trust scoring
    ├── trusted pseudo positives
    ├── ambiguous review candidates
    ├── candidate gold negatives
    └── random audit sample
    ↓
CVAT/FiftyOne review loop
    ↓
Curated dataset release
    ↓
vision-trainer training + evaluation
    ↓
TensorRT / deployment artifact package
    ↓
NX staging slot
    ↓
Smoke test + promotion or rollback
```

---

## Model and Tracking Strategy

### Edge model

The current edge model is YOLO11m on Xavier NX.

The edge model should be treated as the deployed teacher for package generation unless replaced by a newer promoted model.

### Desktop model

The desktop may train YOLO11m, YOLO11l, or both.

Recommended policy:

- Train YOLO11m for deployability.
- Train YOLO11l for upper-bound evaluation when useful.
- Promote only models that satisfy Xavier runtime constraints.

### Tracking

Tracking must be explicit and verified.

A valid tracked package should record:

- tracker type
- tracker config hash or version
- per-frame track IDs
- per-track summaries

If the current backend is stock DeepStream-only, do not call it ByteTrack unless ByteTrack is actually invoked.

---

## Trust Model

Trust should be split into class trust and box trust.

### Class trust

Question: “Is this a human?”

Signals:

- detector confidence
- track persistence
- detection density
- temporal consistency
- disagreement between models or augmentations when available

### Box trust

Question: “Is this box accurate enough for regression?”

Signals:

- box jitter
- border clipping
- sudden area change
- occlusion indicators
- track fragmentation

### Buckets

| Bucket | Meaning | Use |
|---|---|---|
| `trusted_full` | strong class, strong box | full training supervision |
| `trusted_class_weak_box` | strong class, weak box | classification-only or reduced regression |
| `ambiguous` | uncertain class or geometry | review queue |
| `candidate_negative` | no detector support in a clip/track context | human confirmation or simulated reveal before negative training |
| `discard` | unusable weak signal | discard or low-volume audit only |

---

## Negative Handling

Do not treat “no detection” as “no human.”

Frame states:

1. **Trusted positive** — usable for training
2. **Unknown** — excluded from ordinary supervised training
3. **Gold negative** — manually confirmed no-human clip/frame

This protects the system from incomplete pseudo-labels becoming false negative supervision.

---

## EgoHumans Calibration Policy

EgoHumans Lego Assembly is a calibration dataset for the machinery, not evidence of thermal-domain performance. The Edge Node processes EgoHumans as unlabeled video and must not use ground truth. The desktop side may import ground truth only as a hidden oracle.

During calibration, keep three label namespaces separate:

1. **Hidden oracle labels** — full EgoHumans ground truth used for evaluation and simulated reveal.
2. **Revealed gold labels** — a controlled subset exposed to the curator as if reviewed by a human.
3. **Teacher pseudo labels** — detector/tracker outputs scored by `vision-curator`.

Trust scoring and queue selection must use teacher pseudo labels and edge provenance only. Hidden oracle labels may measure precision/recall or populate explicitly revealed gold sets, but they must not silently influence pseudo-label acceptance.

---

## Shared Data Stores

Repos should communicate through immutable stores and manifests, not private ad hoc paths.

Recommended desktop roots:

```text
/data/openclaw/raw_edge_packages/
/data/openclaw/curator/
/data/openclaw/dataset_releases/
/data/openclaw/training_runs/
/data/openclaw/model_artifacts/
```

Recommended environment variables:

```bash
OPENCLAW_RAW_PACKAGE_STORE=/data/openclaw/raw_edge_packages
OPENCLAW_CURATOR_STORE=/data/openclaw/curator
OPENCLAW_DATASET_RELEASE_STORE=/data/openclaw/dataset_releases
OPENCLAW_TRAINING_RUN_STORE=/data/openclaw/training_runs
OPENCLAW_MODEL_ARTIFACT_STORE=/data/openclaw/model_artifacts
```

---

## Sync Strategy Between NX and Desktop

Because the NX is isolated and accessed over SSH, prefer a desktop-pull workflow.

```text
NX local spool
    ↓  rsync pull from desktop
Desktop raw package store
```

Recommended rules:

- NX writes packages atomically.
- A package is eligible for pull only after a completion marker or complete manifest exists.
- Desktop validates after pull.
- Raw package store is immutable.
- Cleanup on NX happens only after desktop confirms ingest.

---

## Success Metrics

### Edge

- Stable package production
- Verified tracking IDs
- Reliable SSH/rsync transfer
- Useful OpenClaw/CLI inspection

### Curator

- Review queues prioritize hard cases
- Pseudo-label precision is auditable
- Gold eval sets are frozen and versioned
- Dataset releases are reproducible

### Trainer

- Training consumes curated releases cleanly
- Frozen hard-case metrics improve
- Candidate artifacts are packaged with provenance

### Operations

- Promotion and rollback are explicit
- Nudge infrastructure prevents task stalls
- Workspace task completion rolls up from repo-level success criteria
