# Updated Proposed Plan — Bootstrap Labeling System

## Current State

The system has now moved from a two-repo edge/training split toward the intended three-layer architecture:

1. **Edge Inference Node**
   - `vision_api`
   - `thermal-data-engine`

2. **Vision Curator**
   - `vision-curator` repo skeleton has been created according to `VISION_CURATOR_REPO_DESIGN.md`

3. **Vision Trainer**
   - `vision-trainer`

This is the correct architectural direction. The immediate priority shifts from designing `vision-curator` to bringing it up as the desktop-side curation control plane.

## 2026-04-30 execution update

### Completed in this wave
- Workspace root-task and live handoffs were initialized for a coordinated four-repo execution slice.
- Repo-specific work packets were written for:
  - `src/vision-curator/docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`
  - `src/vision-trainer/docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`
- Xavier-local implementation advanced in parallel:
  - `vision_api` now emits richer backend/runtime asset provenance in job status and manifest artifacts.
  - `thermal-data-engine` now records structured tracker/runtime provenance in bundle and package metadata and writes `READY.json` markers for combined package roots.
  - the legacy internal IOU tracker was replaced as the default path with a real Ultralytics ByteTrack backend in `thermal-data-engine`.
- End-to-end smoke validation on `incoming/example.mp4` completed successfully with ByteTrack metadata preserved in the emitted run and bundle artifacts.

### In progress / waiting on other nodes
- `vision-curator` desktop execution of ingest, scoring, queue, and draft-release tasks.
- `vision-trainer` desktop execution of curated-release validation and smoke-train preparation.
- Desktop pull of real edge packages into the curator store.

### Explicit human gating points
- CVAT labeling is required before claiming gold negatives, frozen hard-case evaluation slices, or a trustworthy annotation roundtrip.
- Curated-release smoke wiring may proceed before CVAT, but real evaluation quality claims may not.

---

## System-Level Objective

Build a noisy, partial, temporally structured semi-supervised labeling loop for thermal person detection:

```text
Raw thermal videos
    ↓
Edge inference + packaging
    ↓
Raw package store
    ↓
Vision Curator ingest + trust scoring
    ↓
Review queues + CVAT/FiftyOne workflows
    ↓
Curated dataset releases
    ↓
Vision Trainer student training + export
    ↓
Candidate model artifacts
    ↓
Edge deployment validation
    ↺
```

The key principle remains:

> The edge node generates candidate signal.  
> The curator decides what is trusted data.  
> The trainer turns curated data into deployable models.

---

## Repository Responsibilities

## 1. `vision_api` — Edge Runtime Control Plane

### Role
Narrow local FastAPI service on the Xavier NX.

### Responsibilities
- Validate bounded inference requests
- Enforce workspace path boundaries
- Launch offline inference jobs
- Track job status
- Produce stable inference artifacts
- Expose health and GPU/DeepStream telemetry

### Near-Term Work
- Preserve the bounded `vision_api` control-plane surface while downstream repos consume the richer provenance now emitted in edge job artifacts.
- Ensure manifests record:
  - backend implementation
  - model profile
  - tracker backend, if any
  - model artifact path or version

### Status
- Existing service and contract appear structurally sound.
- 2026-04-30 update: backend/runtime asset provenance is now being emitted more explicitly in local job artifacts on the Xavier NX.
- The active local Xavier path has now been smoke-validated end to end with real ByteTrack-backed tracking preserved into downstream artifacts.

---

## 2. `thermal-data-engine` — Edge Package Producer

### Role
Edge-side thermal video capture, triage, and package generation.

### Responsibilities
- Consume raw video or `vision_api` inference job outputs
- Produce Phase 1 Ultralytics-ready packages
- Produce Phase 2 context-rich clip packages
- Preserve track IDs, detections, manifests, and provenance
- Provide basic inspection/OpenClaw tools

### Current Contracts

#### Phase 1 — Direct Training Package
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

#### Phase 2 — Context-Rich Clip Package
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

### Near-Term Work
- Ensure Phase 2 packages contain enough information for `vision-curator` to compute trust scores.
- Implement or finalize desktop-pull sync over SSH/rsync.
- Avoid adding CVAT, FiftyOne, or training concerns here.

### Status
- Clip bundles: done.
- Basic OpenClaw tools: done.
- 2026-04-30 update: package manifests now carry richer runtime/tracker provenance and combined package roots emit `READY.json` completion markers for desktop pull.
- Upload/sync path: still open.
- ByteTrack validation: completed locally, including repo test coverage and an end-to-end smoke run on `incoming/example.mp4`.

---

## 3. `vision-curator` — Desktop Curation Control Plane

### Role
Desktop-side curation, review, audit, and dataset release repo.

### Updated Status
The repo skeleton and first useful curation workflow now exist. The task has shifted from bring-up to running real edge packages through the curator and producing calibration/training artifacts.

### Responsibilities
- Ingest raw Phase 1 and Phase 2 packages from the shared package store
- Validate package contracts without mutating upstream artifacts
- Build a canonical curation index
- Compute class trust and box trust
- Build review queues
- Export selected clips/tasks to CVAT
- Import reviewed annotations
- Integrate or inspect with FiftyOne
- Maintain frozen hard-case eval sets
- Publish curated dataset releases for `vision-trainer`

### Current CLI Surface
- `validate-package`
- `ingest-package`
- `score-package`
- `build-review-queue`
- `export-cvat-task`
- `import-cvat-annotations`
- `build-release`

### Immediate Execution Work
1. Pull completed Phase 2 edge packages into the desktop raw package store.
2. Validate and ingest real package roots without mutating them.
3. Score teacher detections/tracks with deterministic class and box trust.
4. Generate hard-case, ambiguous, candidate-negative, and random-audit queues.
5. Register EgoHumans ground truth as hidden oracle labels for calibration only.
6. Reveal a controlled subset as simulated gold/review labels.
7. Publish pseudo-only and calibration releases that `vision-trainer` can validate.

### First Useful Output
A curation release with this shape:

```text
<curated_release_root>/
├─ release_manifest.json
├─ datasets/
│  ├─ gold_hard_train/
│  ├─ gold_hard_val/
│  ├─ gold_hard_test/
│  ├─ pseudo_strong_train/
│  └─ gold_negative_train/
├─ review_queues/
│  ├─ hard_cases.jsonl
│  ├─ ambiguous.jsonl
│  ├─ random_audit.jsonl
│  └─ candidate_negatives.jsonl
└─ provenance/
   ├─ source_packages.jsonl
   └─ curation_decisions.jsonl
```

### Status
- Repo skeleton: done.
- Bring-up tests: done for current local fixtures.
- Phase 2 package validation and ingest: done for fixture packages; ready for real Edge Node package validation.
- Trust scoring: deterministic first pass done.
- Review queues: deterministic first pass done.
- CVAT export/import boundaries: present, still human-labeling dependent for real gold claims.
- Dataset release builder/validator: draft path done.
- Frozen hard-case eval set: blocked on CVAT labeling or EgoHumans simulated reveal policy.

---

## 4. `vision-trainer` — Desktop Training and Artifact Producer

### Role
Train, evaluate, export, and package model artifacts from curated datasets.

### Responsibilities
- Consume curated releases from `vision-curator`
- Validate package/release contracts
- Run YOLO training/evaluation
- Export candidate model artifacts
- Produce promotion reports
- Avoid reimplementing edge runtime or curation logic

### Near-Term Work
- Update `vision-trainer` to treat `vision-curator` releases as the preferred input contract.
- Keep direct Phase 1 ingestion as a bootstrap/smoke path.
- Add release-level validation once `vision-curator` publishes its first release manifest.
- Clarify whether `docs/handoffs/EDGE_TO_DESKTOP.md` should describe:
  - edge → raw package store → curator, or
  - edge → trainer direct bootstrap only.

### Status
- Basic train/eval setup: done.
- Phase 1 direct training path: done.
- Curated release input path: not done.
- TensorRT export: not done.
- Promotion workflow: not done.

---

## Shared Data Store Plan

## Data Store Principle

The shared store should be outside all repos. Repos should reference it through config and environment variables.

Recommended root:

```text
/data/thermal_vision/
```

or, if staying under OpenClaw workspace:

```text
~/.openclaw/workspace/vision_data/
```

## Suggested Layout

```text
vision_data/
├─ raw_packages/
│  ├─ phase1/
│  └─ phase2/
├─ curation/
│  ├─ indexes/
│  ├─ review_queues/
│  ├─ cvat_exports/
│  ├─ cvat_imports/
│  └─ curated_releases/
├─ trainer/
│  ├─ runs/
│  ├─ evals/
│  └─ artifacts/
└─ deployment/
   ├─ candidates/
   ├─ staged/
   └─ promoted/
```

## Repo Access Pattern

### `thermal-data-engine`
Writes:
- `raw_packages/phase1/`
- `raw_packages/phase2/`

### `vision-curator`
Reads:
- `raw_packages/phase1/`
- `raw_packages/phase2/`

Writes:
- `curation/indexes/`
- `curation/review_queues/`
- `curation/cvat_exports/`
- `curation/cvat_imports/`
- `curation/curated_releases/`

### `vision-trainer`
Reads:
- `curation/curated_releases/`

Writes:
- `trainer/runs/`
- `trainer/evals/`
- `trainer/artifacts/`
- `deployment/candidates/`

### Edge Deployment Tools
Read:
- `deployment/candidates/`
- `deployment/staged/`
- `deployment/promoted/`

Push to Xavier NX staging slot by explicit deployment action.

---

## Sync Strategy

Because the Xavier NX is isolated and reachable from the desktop over SSH, use **desktop-pull sync**.

### Recommended Pattern
From desktop:

```bash
rsync -avh --partial --progress \
  xavier:~/.openclaw/workspace/outputs/thermal_data_engine/bundles/ \
  /data/thermal_vision/raw_packages/phase2/
```

For Phase 1:

```bash
rsync -avh --partial --progress \
  xavier:~/.openclaw/workspace/outputs/thermal_data_engine/phase1_packages/ \
  /data/thermal_vision/raw_packages/phase1/
```

### Rules
- NX writes local packages first.
- Desktop pulls completed packages.
- Desktop validates after pull.
- NX never owns the canonical data store.
- Avoid deleting remote data during early bring-up.

---

## Updated Milestones

## Milestone 0 — Workspace Workflow Alignment

### Deliverables
- Root `AGENTS.md` says every high-level task begins as a workspace task.
- `ACTIVE_TASK.md` supports root tasks even when implementation is single-repo.
- Cron nudge is documented as workspace task infrastructure.
- Remove or deprecate duplicate/conflicting workflow docs.
- Templates match live workflow docs.

### Status
Partially addressed in design docs; implementation status depends on current workspace edits.

### Priority
High, because this governs how agents coordinate all following work.

---

## Milestone 1 — Edge Capture + Triage

### Deliverables
- YOLO11m inference path on NX
- Tracking path validated as ByteTrack or explicitly documented otherwise
- Phase 1 package generation
- Phase 2 package generation
- Basic OpenClaw inspection tools
- Desktop-pull sync path over SSH/rsync

### Status
- Inference/package generation: mostly done.
- OpenClaw tools: done.
- Tracking validation: not done.
- Desktop-pull sync: not done.

### Next Tasks
1. Add backend/tracker metadata to manifests if missing.
2. Run a short video through the pipeline and verify persistent `track_id` output.
3. Confirm tracker config path/name in logs and manifests.
4. Add `rsync` pull script on desktop.
5. Add post-sync validation command.

---

## Milestone 2 — Vision Curator Bring-Up

### Deliverables
- Repo skeleton verified
- Environment and import tests pass
- Package validators implemented or stubbed cleanly
- Phase 1 and Phase 2 ingestion commands
- Canonical curation index
- Initial trust scoring
- Initial review queue generation
- First curated release manifest

### Status
- Repo skeleton: done.
- 2026-04-30 update: a concrete desktop execution packet now exists at `src/vision-curator/docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`.
- Everything else: next.

### Next Tasks
1. Pull and validate completed Edge Node EgoHumans Phase 2 packages.
2. Ingest package roots into the immutable curator index.
3. Score teacher detections/tracks from edge table fields.
4. Generate queue JSONL files:
   - hard cases
   - ambiguous tracks
   - random audit
   - candidate negatives
5. Register hidden EgoHumans oracle labels without leaking them into trust scoring.
6. Publish first pseudo-only and calibration release manifests.

---

## Milestone 3 — Annotation + Audit Loop

### Deliverables
- CVAT export path
- CVAT import path
- FiftyOne inspection path
- Frozen hard-case eval set v1
- Gold-negative confirmation workflow
- Annotation policy doc

### Status
Partially done. CVAT export/import command boundaries exist, but real human labeling remains a gate. EgoHumans calibration may use simulated reveal from hidden oracle labels as a controlled substitute for some experiments.

### Next Tasks
1. Export selected review queues to CVAT when human labeling is desired.
2. Import corrected labels back into `vision-curator`.
3. For EgoHumans, implement hidden-oracle import plus controlled reveal records.
4. Create initial hard-case validation split after labels are confirmed or explicitly simulated.
5. Add audit reports for pseudo-label precision against hidden oracle labels.

---

## Milestone 4 — Curated Training Release → Vision Trainer

### Deliverables
- Curated release contract finalized
- `vision-trainer` consumes curated releases
- Direct Phase 1 training remains available as bootstrap path
- Evaluation reports distinguish:
  - gold validation
  - pseudo-label training set
  - hard-case test set

### Status
Partially enabled. `vision-curator` can build immutable draft releases; downstream curated-release training remains a `vision-trainer` task.
- 2026-04-30 update: a concrete desktop execution packet now exists at `src/vision-trainer/docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`.

### Next Tasks
1. Hand `vision-trainer` a real or fixture curated release root.
2. Add/verify release validator in `vision-trainer`.
3. Add training config that targets curated release paths.
4. Run single-GPU smoke training on a minimal curated release.
5. Scale to 3-GPU run only after smoke pass.

---

## Milestone 5 — Export + Promotion Back to Edge

### Deliverables
- TensorRT export workflow
- Candidate model package
- Promotion report
- Staging deployment to Xavier NX
- Edge smoke test
- Rollback path

### Status
Not done.

### Next Tasks
1. Implement export target(s): ONNX first if needed, TensorRT after.
2. Define model package manifest.
3. Add desktop-side promotion candidate directory.
4. Add Xavier staging deploy script.
5. Add edge smoke-test command through `vision_api` or OpenClaw tool.

---

## Milestone 6 — Active Learning Loop

### Deliverables
- Disagreement mining
- Random audits
- Drift/novelty sampling
- Model comparison tooling
- Periodic review queue refresh

### Status
Not done.

### Next Tasks
1. Compare old vs new model outputs on same Phase 2 clips.
2. Mine high-disagreement clips.
3. Add random audits to every curation batch.
4. Track review yield over time.
5. Use review outcomes to tune edge clip-selection policy.

---

## Updated Success Criteria

## Edge-Side
- NX produces valid Phase 1 and Phase 2 packages.
- Tracking backend is explicit and validated.
- Desktop can pull packages reliably over SSH/rsync.
- Edge tools return actionable summaries.

## Curator-Side
- `vision-curator` ingests raw packages without mutating upstream artifacts.
- Trust scores and review queues are reproducible.
- CVAT/FiftyOne workflows are connected to curated records.
- Frozen hard-case eval set v1 exists.
- Curated releases are immutable and versioned.

## Trainer-Side
- `vision-trainer` consumes curated releases.
- Gold hard-case metrics are reported separately from pseudo-label training metrics.
- Model artifacts preserve provenance back to curated release and source packages.

## Operational
- New model artifacts can be staged, tested, promoted, and rolled back.
- Human review is focused on hard or uncertain cases.
- Each high-level system task has workspace-level tracking and a nudge path.

---

## Immediate Recommended Active Task

Now that the Edge Node has completed EgoHumans package processing, the next workspace task should be:

> Run completed EgoHumans Phase 2 packages through `vision-curator`, build trust scores and review queues, register hidden oracle labels, reveal a controlled gold subset, and publish calibration releases for `vision-trainer`.

### Active Repo
`src/vision-curator`

### Supporting Repos
- `src/thermal-data-engine` for source package contracts
- `src/vision-trainer` for downstream curated release expectations

### First Definition of Done
- `vision-curator` tests pass.
- It validates and ingests pulled EgoHumans Phase 2 package roots.
- It writes canonical package index entries with edge provenance preserved.
- It computes class/box trust metrics from Phase 2 detections/tracks.
- It produces review queue JSONL files for the required queue kinds.
- It keeps hidden oracle, revealed gold, and teacher pseudo labels separate.
- It emits curated release manifests consumable by `vision-trainer`.

---

## Notes for Coding Agents

- Do not move curation logic into `thermal-data-engine`.
- Do not move training logic into `vision-curator`.
- Do not make `vision-trainer` parse raw edge packages as its preferred long-term path.
- Use the shared data root by config/env var, not hardcoded repo-relative paths.
- Preserve provenance fields everywhere.
- Treat missing or malformed manifests as hard validation failures.
- Keep Phase 1 direct training support as a bootstrap path, but make curated releases the intended long-term interface.
