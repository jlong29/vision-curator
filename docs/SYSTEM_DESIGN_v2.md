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

### Current status

`vision-curator` now validates and ingests the six staged EgoHumans Lego Assembly Phase 2 packages, scores teacher tracks, builds review queues, maintains hidden-oracle/revealed-gold artifacts, freezes calibration splits, and emits trainer-ready EgoHumans calibration releases.

The current calibration release families are:

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`
- `oracle_upper_bound`

All realistic calibration releases forbid `oracle_hidden` for training. `oracle_upper_bound` is diagnostic headroom only.

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

The basic training/evaluation/export repo exists and can validate the current EgoHumans curated release roots. The next active system task is to run the full calibration matrix over the five release families and report results against the shared frozen validation/test definitions.

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
    ├── realistic calibration releases
    └── diagnostic oracle upper bound
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

Current EgoHumans release materialization uses a frozen split assignment artifact under:

```text
$OPENCLAW_CURATOR_STORE/oracle/egohumans/splits/split_assignments_v0.jsonl
```

The split assignment is sequence-time chunk based, shared across release families, and keeps validation/test definitions stable for trainer comparisons.

Current interpretation caveat: `gold_plus_trusted_tracks_v0` is deliberately precision-first and sparse. It should be evaluated as a conservative trusted-track ablation; threshold relaxation should be based on non-test oracle precision analysis, not hidden test metrics.

---

## Shared Data Stores

Repos should communicate through immutable stores and manifests, not private ad hoc paths.

Edge Node absolute paths are provenance only once packages are pulled to the desktop. Any file that desktop curation or training must read must be represented by a package-local, clip-local, package-relative, or release-relative path. This keeps the multi-machine pipeline portable across the Edge Node and desktop.

Recommended desktop base root on this workstation:

```text
/media/jdl2/DATAPART/YOLO-Data/openclaw/
```

Use an `openclaw/` namespace under the broader YOLO data mount so Codex, `vision-curator`, and `vision-trainer` can be granted a narrow writable root without exposing unrelated datasets.

Recommended desktop layout:

```text
/media/jdl2/DATAPART/YOLO-Data/openclaw/
├─ raw_edge_packages/
│  ├─ incoming/
│  ├─ phase1/
│  ├─ phase2/
│  │  └─ egohumans/
│  └─ manifests/
├─ curator/
│  ├─ indexes/
│  ├─ scores/
│  ├─ review_queues/
│  ├─ annotation_exports/
│  │  └─ cvat/
│  ├─ annotation_imports/
│  │  └─ cvat/
│  ├─ oracle/
│  │  └─ egohumans/
│  ├─ image_cache/
│  │  └─ egohumans/
│  ├─ revealed_gold/
│  └─ decisions/
├─ dataset_releases/
│  ├─ pseudo_only/
│  ├─ calibration/
│  └─ published/
├─ training_runs/
│  ├─ smoke/
│  ├─ calibration/
│  └─ full/
├─ model_artifacts/
│  ├─ candidates/
│  ├─ exported/
│  ├─ promotion_reports/
│  └─ archived/
└─ docs/
```

Recommended environment variables:

```bash
export OPENCLAW_DATA_ROOT=/media/jdl2/DATAPART/YOLO-Data/openclaw
export OPENCLAW_RAW_PACKAGE_STORE="$OPENCLAW_DATA_ROOT/raw_edge_packages"
export OPENCLAW_CURATOR_STORE="$OPENCLAW_DATA_ROOT/curator"
export OPENCLAW_DATASET_RELEASE_STORE="$OPENCLAW_DATA_ROOT/dataset_releases"
export OPENCLAW_TRAINING_RUN_STORE="$OPENCLAW_DATA_ROOT/training_runs"
export OPENCLAW_MODEL_ARTIFACT_STORE="$OPENCLAW_DATA_ROOT/model_artifacts"
```

Shell setup policy:

- Interactive terminals used for `vision-curator` or `vision-trainer` work should run `source ~/openclaw-env.sh` before invoking repo commands.
- Repo scripts that depend on these stores should check required `OPENCLAW_*` variables early and fail fast with a prompt to source `~/openclaw-env.sh`.
- Explicit CLI path arguments remain valid for tests and one-off smoke work, but env variables are the preferred operational interface.

Setup commands:

```bash
export OPENCLAW_DATA_ROOT=/media/jdl2/DATAPART/YOLO-Data/openclaw
export OPENCLAW_RAW_PACKAGE_STORE="$OPENCLAW_DATA_ROOT/raw_edge_packages"
export OPENCLAW_CURATOR_STORE="$OPENCLAW_DATA_ROOT/curator"
export OPENCLAW_DATASET_RELEASE_STORE="$OPENCLAW_DATA_ROOT/dataset_releases"
export OPENCLAW_TRAINING_RUN_STORE="$OPENCLAW_DATA_ROOT/training_runs"
export OPENCLAW_MODEL_ARTIFACT_STORE="$OPENCLAW_DATA_ROOT/model_artifacts"

mkdir -p \
  "$OPENCLAW_RAW_PACKAGE_STORE/incoming" \
  "$OPENCLAW_RAW_PACKAGE_STORE/phase1" \
  "$OPENCLAW_RAW_PACKAGE_STORE/phase2/egohumans" \
  "$OPENCLAW_RAW_PACKAGE_STORE/manifests" \
  "$OPENCLAW_CURATOR_STORE/indexes" \
  "$OPENCLAW_CURATOR_STORE/scores" \
  "$OPENCLAW_CURATOR_STORE/review_queues" \
  "$OPENCLAW_CURATOR_STORE/annotation_exports/cvat" \
  "$OPENCLAW_CURATOR_STORE/annotation_imports/cvat" \
  "$OPENCLAW_CURATOR_STORE/oracle/egohumans" \
  "$OPENCLAW_CURATOR_STORE/revealed_gold" \
  "$OPENCLAW_CURATOR_STORE/decisions" \
  "$OPENCLAW_DATASET_RELEASE_STORE/pseudo_only" \
  "$OPENCLAW_DATASET_RELEASE_STORE/calibration" \
  "$OPENCLAW_DATASET_RELEASE_STORE/published" \
  "$OPENCLAW_TRAINING_RUN_STORE/smoke" \
  "$OPENCLAW_TRAINING_RUN_STORE/calibration" \
  "$OPENCLAW_TRAINING_RUN_STORE/full" \
  "$OPENCLAW_MODEL_ARTIFACT_STORE/candidates" \
  "$OPENCLAW_MODEL_ARTIFACT_STORE/exported" \
  "$OPENCLAW_MODEL_ARTIFACT_STORE/promotion_reports" \
  "$OPENCLAW_MODEL_ARTIFACT_STORE/archived" \
  "$OPENCLAW_DATA_ROOT/docs"
```

Codex sandbox access should grant the narrow shared root, not the full YOLO data mount:

```toml
[sandbox_workspace_write]
writable_roots = ["/media/jdl2/DATAPART/YOLO-Data/openclaw"]
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
