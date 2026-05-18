# Updated Proposed Plan — Bootstrap Labeling System

## 2026-05-14 progress note

`vision-curator` has completed the EgoHumans Lego Assembly calibration release materialization task. The six staged Phase 2 packages were validated, ingested, scored, and used to build review queues. Hidden oracle, revealed gold, and teacher pseudo labels are separated, frozen split assignments exist, and five trainer-ready releases now exist under `$OPENCLAW_DATASET_RELEASE_STORE/calibration`:

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`
- `oracle_upper_bound`

Curator validation, `vision-trainer` release validation, and `vision-trainer` dry-run command preparation passed for all five release roots.

The immediate active task has moved to `vision-trainer`: run the EgoHumans calibration test matrix described in `docs/EGOHUMANS_VISION_TRAINER_TASK_SPEC.md` and report results across the shared frozen validation/test definitions. Two curator follow-ups remain important: formalize portable package paths versus Edge-local provenance paths, and analyze trusted-track pseudo-label precision on non-test oracle data before relaxing thresholds.

## Current State

The system has now moved from a two-repo edge/training split toward the intended three-layer architecture:

1. **Edge Inference Node**
   - `vision_api`
   - `thermal-data-engine`

2. **Vision Curator**
   - `vision-curator` now owns package validation, ingest, trust scoring, review queues, hidden-oracle import, frozen EgoHumans calibration splits, and trainer-ready release materialization.

3. **Vision Trainer**
   - `vision-trainer`

This is the correct architectural direction. The immediate priority has shifted from bringing up `vision-curator` to using the curated EgoHumans releases in `vision-trainer`.

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
- `vision-trainer` execution of the EgoHumans calibration training matrix.
- Analysis of trusted-track pseudo-label precision against hidden oracle labels on non-test calibration data.
- Contract cleanup for portable package-relative paths versus Edge-local provenance paths.

### Explicit human gating points
- CVAT labeling is required before claiming gold negatives, frozen hard-case evaluation slices, or a trustworthy annotation roundtrip.
- EgoHumans simulated reveal can support calibration experiments before CVAT, but it validates the machinery rather than thermal-domain performance.

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
The repo now has a working EgoHumans calibration release workflow. It validates and ingests real staged Phase 2 packages, scores real package tables, builds review queues, freezes split assignments, and emits trainer-ready release roots.

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
- `build-egohumans-splits`
- `build-egohumans-release`
- `validate-release`

### Completed EgoHumans Execution Work
1. Validated and ingested six staged EgoHumans Phase 2 package roots without mutating them.
2. Scored teacher detections/tracks with deterministic class and box trust.
3. Generated hard-case, ambiguous, candidate-negative, and random-audit queues.
4. Registered EgoHumans ground truth as hidden oracle labels for calibration only.
5. Used controlled reveal sets for seed/review gold labels.
6. Built frozen split assignments shared across release families.
7. Published five calibration releases that `vision-trainer` validates.

### Current Calibration Output
Trainer-ready YOLO release roots now live under:

```text
$OPENCLAW_DATASET_RELEASE_STORE/calibration/
├─ gold_only_v0/
├─ gold_plus_naive_pseudo_v0/
├─ gold_plus_trusted_tracks_v0/
├─ gold_plus_review_revealed_v1/
└─ oracle_upper_bound/
```

### Status
- Repo skeleton: done.
- Bring-up tests: done for current local fixtures.
- Phase 2 package validation and ingest: done for fixtures and staged EgoHumans real packages.
- Trust scoring: deterministic first pass done and exercised against real EgoHumans package tables.
- Review queues: deterministic first pass done.
- CVAT export/import boundaries: present, still human-labeling dependent for real gold claims.
- Dataset release builder/validator: generic path plus EgoHumans calibration path done.
- Frozen EgoHumans validation/test split assignment: done.
- Thermal-domain frozen hard-case eval set: still blocked on thermal gold labeling.

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
- Run the EgoHumans calibration matrix over the five curated release roots.
- Keep direct Phase 1 ingestion as a bootstrap/smoke path.
- Report release-level metrics with release IDs, dataset roots, run directories, validation/test metrics, and interpretation notes.
- Compare naive high-confidence pseudo labels against trusted-track pseudo labels and review-revealed gold.

### Status
- Basic train/eval setup: done.
- Phase 1 direct training path: done.
- Curated release validation path: done for current EgoHumans release roots.
- Curated release dry-run training command preparation: done for current EgoHumans release roots.
- Full EgoHumans calibration training matrix: next.
- TensorRT export: not done.
- Promotion workflow: not done.

---

## Shared Data Store Plan

## Data Store Principle

The shared store should be outside all repos. Repos should reference it through config and environment variables.

Recommended root:

```text
/media/jdl2/DATAPART/YOLO-Data/openclaw/
```

Use environment variables:

```bash
export OPENCLAW_DATA_ROOT=/media/jdl2/DATAPART/YOLO-Data/openclaw
export OPENCLAW_RAW_PACKAGE_STORE="$OPENCLAW_DATA_ROOT/raw_edge_packages"
export OPENCLAW_CURATOR_STORE="$OPENCLAW_DATA_ROOT/curator"
export OPENCLAW_DATASET_RELEASE_STORE="$OPENCLAW_DATA_ROOT/dataset_releases"
export OPENCLAW_TRAINING_RUN_STORE="$OPENCLAW_DATA_ROOT/training_runs"
export OPENCLAW_MODEL_ARTIFACT_STORE="$OPENCLAW_DATA_ROOT/model_artifacts"
```

## Suggested Layout

```text
openclaw/
├─ raw_edge_packages/
│  ├─ incoming/
│  ├─ phase1/
│  └─ phase2/
├─ curator/
│  ├─ indexes/
│  ├─ scores/
│  ├─ review_queues/
│  ├─ annotation_exports/
│  ├─ annotation_imports/
│  ├─ oracle/
│  ├─ image_cache/
│  └─ decisions/
├─ dataset_releases/
│  ├─ pseudo_only/
│  ├─ calibration/
│  └─ published/
├─ training_runs/
├─ model_artifacts/
└─ docs/
```

## Repo Access Pattern

### `thermal-data-engine`
Writes:
- `raw_edge_packages/phase1/`
- `raw_edge_packages/phase2/`

### `vision-curator`
Reads:
- `raw_edge_packages/phase1/`
- `raw_edge_packages/phase2/`

Writes:
- `curator/indexes/`
- `curator/scores/`
- `curator/review_queues/`
- `curator/annotation_exports/`
- `curator/annotation_imports/`
- `curator/oracle/`
- `curator/image_cache/`
- `dataset_releases/`

### `vision-trainer`
Reads:
- `dataset_releases/`

Writes:
- `training_runs/`
- `model_artifacts/candidates/`

### Edge Deployment Tools
Read:
- `model_artifacts/candidates/`
- `model_artifacts/exported/`
- `model_artifacts/promotion_reports/`

Push to Xavier NX staging slot by explicit deployment action.

---

## Sync Strategy

Because the Xavier NX is isolated and reachable from the desktop over SSH, use **desktop-pull sync**.

### Recommended Pattern
From desktop:

```bash
rsync -avh --partial --progress \
  xavier:~/.openclaw/workspace/outputs/thermal_data_engine/bundles/ \
  "$OPENCLAW_RAW_PACKAGE_STORE/phase2/"
```

For Phase 1:

```bash
rsync -avh --partial --progress \
  xavier:~/.openclaw/workspace/outputs/thermal_data_engine/phase1_packages/ \
  "$OPENCLAW_RAW_PACKAGE_STORE/phase1/"
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
- Tracking validation: done for the current ByteTrack/EgoHumans staged package path; keep backend metadata explicit in each manifest.
- Desktop-pull sync: manual/staged package transfer works; durable rsync helper and post-sync validation remain open.

### Next Tasks
1. Formalize portable path checks so package-local artifacts are consumable on desktop and Edge-local absolute paths remain provenance only.
2. Add an `rsync` pull helper on desktop.
3. Add a post-sync validation command.
4. Keep backend/tracker metadata explicit in package manifests and logs.

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
- Done for current EgoHumans calibration bring-up.
- Real staged EgoHumans package roots validated/ingested/scored.
- Review queues and frozen split assignments built.
- Five calibration release roots produced and validated.

### Next Tasks
1. Add non-test oracle precision diagnostics for trusted pseudo labels.
2. Improve record-level lineage in `label_items.jsonl`.
3. Formalize path portability validation for package-relative consumable paths vs Edge-local provenance paths.
4. Preserve CVAT/FiftyOne workflows for thermal gold review.

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
3. Use the current EgoHumans hidden-oracle and controlled-reveal records for calibration reporting.
4. Create the initial thermal hard-case validation split after labels are confirmed.
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
Enabled for EgoHumans calibration. `vision-curator` has built five trainer-ready releases, and `vision-trainer` validation/dry-run preparation succeeds for all five. Running the full training matrix remains a `vision-trainer` task.

### Next Tasks
1. Run smoke training for all five EgoHumans release roots.
2. Run the full calibration matrix.
3. Report metrics by release ID and dataset root.
4. Compare naive pseudo, trusted-track pseudo, review-revealed, and oracle upper-bound outcomes.
5. Feed results back into curator trust-threshold and review-priority decisions.

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
- EgoHumans frozen calibration eval exists; thermal hard-case eval set v1 remains the human-labeling target.
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

Now that `vision-curator` has published the EgoHumans calibration releases, the next workspace task should be:

> Run the EgoHumans calibration training matrix in `vision-trainer` using the five curated release roots and report the results against the frozen validation/test definitions.

### Active Repo
`src/vision-trainer`

### Supporting Repos
- `src/vision-curator` for release manifests, label policy, and curation diagnostics
- `src/thermal-data-engine` / `vision_api` for source package provenance

### First Definition of Done
- `vision-trainer` validates all five release roots.
- Smoke training runs for all five release roots.
- Full calibration runs complete for the planned matrix.
- Results report metrics for `gold_only_v0`, `gold_plus_naive_pseudo_v0`, `gold_plus_trusted_tracks_v0`, `gold_plus_review_revealed_v1`, and `oracle_upper_bound`.
- The report treats `oracle_upper_bound` as diagnostic headroom only.
- The report notes that `gold_plus_trusted_tracks_v0` is sparse and should not be judged only by final training accuracy without pseudo-label precision analysis.

---

## Notes for Coding Agents

- Do not move curation logic into `thermal-data-engine`.
- Do not move training logic into `vision-curator`.
- Do not make `vision-trainer` parse raw edge packages as its preferred long-term path.
- Use the shared data root by config/env var, not hardcoded repo-relative paths.
- Preserve provenance fields everywhere.
- Treat missing or malformed manifests as hard validation failures.
- Keep Phase 1 direct training support as a bootstrap path, but make curated releases the intended long-term interface.
- Treat Edge Node absolute paths as provenance only; desktop workflows should consume package-local or release-local paths.
