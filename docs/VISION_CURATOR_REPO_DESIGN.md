# Vision Curator Repo Design

## Repo Name

Recommended name:

```text
vision-curator
```

## Mission

`vision-curator` is the desktop-side curation and annotation repo for the thermal person detection bootstrap pipeline.

It consumes raw edge packages from `thermal-data-engine`, scores pseudo-label quality, builds human review queues, coordinates CVAT/FiftyOne workflows, and emits immutable dataset releases for `vision-trainer`.

---

## Non-Goals

`vision-curator` must not:

- run Xavier edge inference
- own `vision_api` runtime logic
- train YOLO models
- export TensorRT engines
- mutate raw edge packages
- silently invent missing labels

---

## Input Contracts

## Phase 2 clip package — primary input

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

This is the preferred input for curation because it preserves temporal context and tracking metadata.

## Phase 1 training package — secondary input

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

This can be audited or used for compatibility checks, but it should not replace Phase 2 for curation workflows.

---

## Output Contracts

## 1. Curator package index

```text
<curator_store>/indexes/packages.jsonl
```

One record per ingested package.

## 2. Track score table

```text
<curator_store>/scores/<package_id>/track_scores.parquet
```

Contains class trust, box trust, review priority, and decision bucket.

## 3. Review queues

```text
<curator_store>/review_queues/<queue_id>.jsonl
```

Queue types:

- hard-case review
- ambiguous review
- candidate gold negative
- disagreement review
- random audit

## 4. Annotation exchange packages

```text
<curator_store>/annotation_exports/cvat/<task_id>/
<curator_store>/annotation_imports/cvat/<task_id>/
```

## 5. Dataset releases for `vision-trainer`

```text
<dataset_release_store>/<release_id>/
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

Dataset releases are immutable once published.

---

## Recommended Repo Layout

```text
vision-curator/
├─ AGENTS.md
├─ README.md
├─ pyproject.toml
├─ configs/
│  ├─ curator/default.yaml
│  ├─ trust/default.yaml
│  ├─ review/default.yaml
│  └─ release/default.yaml
├─ docs/
│  ├─ architecture.md
│  ├─ package_contracts.md
│  ├─ annotation_policy.md
│  ├─ review_queues.md
│  ├─ dataset_releases.md
│  └─ handoffs/
│     ├─ EDGE_TO_CURATOR.md
│     └─ CURATOR_TO_TRAINER.md
├─ schemas/
│  ├─ phase2_manifest.schema.json
│  ├─ review_item.schema.json
│  └─ dataset_release.schema.json
├─ src/
│  └─ vision_curator/
│     ├─ __init__.py
│     ├─ cli.py
│     ├─ common/
│     │  ├─ models.py
│     │  ├─ paths.py
│     │  ├─ manifests.py
│     │  └─ config.py
│     ├─ packages/
│     │  ├─ validate.py
│     │  ├─ ingest.py
│     │  └─ index.py
│     ├─ scoring/
│     │  ├─ trust.py
│     │  ├─ jitter.py
│     │  └─ buckets.py
│     ├─ review/
│     │  ├─ queues.py
│     │  ├─ sampler.py
│     │  └─ hard_cases.py
│     ├─ annotation/
│     │  ├─ cvat_export.py
│     │  ├─ cvat_import.py
│     │  └─ yolo_roundtrip.py
│     ├─ fiftyone/
│     │  └─ views.py
│     └─ releases/
│        ├─ build.py
│        ├─ validate.py
│        └─ manifest.py
├─ tests/
│  ├─ test_validate_phase2.py
│  ├─ test_ingest.py
│  ├─ test_trust_scoring.py
│  ├─ test_review_queue.py
│  ├─ test_dataset_release.py
│  └─ fixtures/
└─ .agent/
   ├─ TASK_BRIEF.md
   └─ MEMORY.md
```

---

## CLI Surface

Use a small CLI that supports bring-up and later automation.

```bash
python -m vision_curator.cli validate-package --phase2 /path/to/phase2_package

python -m vision_curator.cli ingest-package \
  --source /path/to/phase2_package \
  --store-root /data/openclaw/curator

python -m vision_curator.cli score-package \
  --package-id <package_id> \
  --store-root /data/openclaw/curator

python -m vision_curator.cli build-review-queue \
  --queue-kind hard-case \
  --store-root /data/openclaw/curator

python -m vision_curator.cli export-cvat \
  --queue-id <queue_id> \
  --output-root /data/openclaw/curator/annotation_exports/cvat

python -m vision_curator.cli import-cvat \
  --task-id <task_id> \
  --source /path/to/cvat_export

python -m vision_curator.cli build-release \
  --config configs/release/default.yaml \
  --release-id <release_id>
```

---

## Trust Scoring

Trust is split into two axes.

### Class trust

Question: “Is this a human?”

Signals:

- mean confidence
- min confidence
- confidence quantiles
- track duration
- detection density
- thermal/scene heuristics when available

### Box trust

Question: “Is this box good enough for bounding-box regression?”

Signals:

- IoU jitter across adjacent frames
- area oscillation
- edge clipping
- missing-frame rate
- sudden center jumps

### Decision buckets

| Bucket | Criteria | Action |
|---|---|---|
| trusted_full | high class, high box | include as pseudo label |
| trusted_class_weak_box | high class, weak box | review or weak/reduced supervision |
| ambiguous | uncertain class or geometry | human review |
| candidate_negative | no detection but useful for audit | negative review queue |
| discard | low value | ignore |

---

## Review Queue Strategy

### Hard-case queue

Prioritize:

- low-resolution humans
- partial humans
- edge truncation
- hot clutter
- multiple people
- crossing tracks
- high ego-motion

### Ambiguous queue

Prioritize:

- persistent low-confidence detections
- high-jitter tracks
- broken tracks
- detector/tracker disagreement

### Candidate gold-negative queue

Prioritize:

- no detections but high motion or thermal activity
- representative normal no-human clips

### Random audit queue

Small random sample from all package classes to detect silent failure modes.

---

## CVAT Workflow

Initial implementation should support export/import without requiring full CVAT automation.

### Export

Create a package containing:

- clips
- preannotations
- task manifest
- review reason metadata

### Import

Accept corrected annotations and convert them into canonical curated labels.

### Policy

CVAT is the human annotation tool. `vision-curator` owns the exchange package and canonical annotation store.

---

## FiftyOne Workflow

FiftyOne should be optional at bring-up.

Initial use:

- load scored clips
- visualize trusted/ambiguous buckets
- inspect false positives and hard cases
- later support embedding/novelty mining

Do not make FiftyOne a hard dependency for core tests.

---

## Dataset Release Rules

A dataset release is immutable once published.

A release manifest must include:

- release_id
- source package IDs
- annotation versions
- split policy
- label policy
- class list
- counts by split
- counts by label source
- creation timestamp
- creator/tool version

Training wrappers may create temporary files for Ultralytics compatibility, but they must not mutate the release contract.

---

## Bring-Up Tests

Minimum tests for initial repo:

1. Validate minimal Phase 2 fixture package
2. Reject package missing required files
3. Ingest package into curator store
4. Compute deterministic trust score for synthetic tracks
5. Build review queue from scored tracks
6. Build tiny dataset release from fixture annotations
7. Validate release manifest fields
8. Confirm release is immutable or at least overwrite-protected by default

Heavy CVAT/FiftyOne integration tests can be skipped initially or mocked.

---

## First Implementation Milestone

### Deliverables

- repo skeleton
- package validators
- curator store layout
- ingestion command
- simple trust scorer
- review queue builder
- tiny dataset release builder
- tests passing with fixtures

### Non-deliverables

- live CVAT server automation
- FiftyOne embedding mining
- full active-learning loop

---

## AGENTS.md Guidance Summary

The repo agent should know:

- this is desktop-side only
- raw packages are immutable
- dataset releases are immutable
- `vision-trainer` consumes releases
- `thermal-data-engine` produces raw packages
- no training code belongs here
- no edge runtime code belongs here
