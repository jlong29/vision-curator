# TASK_BRIEF.md — Bring Up `vision-curator`

## Objective

Create the initial `vision-curator` repository for desktop-side curation of thermal person detection data.

This repo will consume Phase 2 edge packages from `thermal-data-engine`, score pseudo-label quality, build review queues, and publish small immutable dataset releases for `vision-trainer`.

---

## Scope

### Included

- repo skeleton
- package validation
- package ingest
- curator store layout
- simple trust scoring
- review queue generation
- tiny dataset release builder
- bring-up tests

### Excluded

- YOLO training
- TensorRT export
- edge inference
- live CVAT server automation
- heavy FiftyOne workflows
- full active-learning loop

---

## Required Layout

```text
vision-curator/
├─ AGENTS.md
├─ README.md
├─ pyproject.toml
├─ configs/
├─ docs/
├─ schemas/
├─ src/vision_curator/
└─ tests/
```

Use the design doc as the target layout, but implement only the initial subset needed for bring-up.

---

## Status

Completed on 2026-04-29:

- repo-specific `AGENTS.md` created from `AGENTS_TEMPLATE.md`
- `.agent/` scratch folder created
- original task brief moved to `.agent/TASK_BRIEF.md`
- initial package, CLI, configs, docs, schemas, fixtures, and tests implemented

---

## Implementation Steps

## 1. Create common models

File:

```text
src/vision_curator/common/models.py
```

Include dataclasses or typed models for:

- package record
- clip record
- track score
- review item
- dataset release manifest

## 2. Implement Phase 2 package validation

File:

```text
src/vision_curator/packages/validate.py
```

Validate:

- root `manifest.json` exists
- `clips/` exists
- each clip has:
  - `clip.mp4`
  - `clip_manifest.json`
  - `detections.parquet`
  - `tracks.parquet`

Fail loudly on missing required fields.

## 3. Implement package ingest

File:

```text
src/vision_curator/packages/ingest.py
```

Behavior:

- validate source package
- copy or register package into curator store
- write/update package index
- never mutate source package

## 4. Implement trust scoring

File:

```text
src/vision_curator/scoring/trust.py
```

Initial fields:

- class_trust
- box_trust
- duration_frames
- mean_conf
- min_conf
- bbox_jitter
- edge_fraction
- decision_bucket

Buckets:

- `trusted_full`
- `trusted_class_weak_box`
- `ambiguous`
- `candidate_negative`
- `discard`

## 5. Implement review queue builder

File:

```text
src/vision_curator/review/queues.py
```

Queue kinds:

- hard-case
- ambiguous
- candidate-negative
- random-audit

Output JSONL records under:

```text
<curator_store>/review_queues/<queue_id>.jsonl
```

## 6. Implement dataset release builder

File:

```text
src/vision_curator/releases/build.py
```

Initial release builder can be small and fixture-driven.

It must create:

```text
<release_root>/
├─ dataset.yaml
├─ images/
├─ labels/
├─ splits/
│  ├─ train.txt
│  ├─ val.txt
│  └─ test.txt
├─ manifest.json
└─ provenance/
```

## 7. Implement CLI

File:

```text
src/vision_curator/cli.py
```

Commands:

```bash
validate-package
ingest-package
score-package
build-review-queue
build-release
```

## 8. Add tests

Use stdlib `unittest` unless the repo chooses pytest explicitly.

Required tests:

- valid Phase 2 fixture passes
- missing required file fails
- ingest writes package index
- trust scoring is deterministic
- queue builder writes JSONL
- release builder writes required files

---

## Definition of Done

- [x] repo installs in editable mode
- [x] validation command works on a fixture
- [x] ingest command creates store records
- [x] score command emits trust records
- [x] queue command emits review queue
- [x] release command emits a tiny dataset release
- [x] tests pass

## Verification

- `python -m unittest` — passed, 7 tests.
- `python -m pip install -e .` — passed after allowing network for build dependency resolution.
- `python -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid` — passed.
- `python -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store` — passed.
- `python -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store` — passed.
- `python -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store` — passed.
- `python -m vision_curator.cli build-release --config configs/release/default.yaml --release-id cli_smoke_20260429_2111` — passed.

---

## Notes

Keep CVAT and FiftyOne optional for now. The first repo milestone is contract stability and bring-up tests, not full annotation automation. Though, note the next task is to bring up CVAT and FiftyOne as dependencies.
