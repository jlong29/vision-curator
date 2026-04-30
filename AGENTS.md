# AGENTS.md — vision-curator

You are an AI coding agent operating inside the `vision-curator` repository.

This file is always-on guidance. Keep it short, stable, and high-signal. Task-specific state belongs in `.agent/TASK_BRIEF.md`, `.agent/MEMORY.md`, or other `.agent/` scratch artifacts, not here.

---

## Mission
`vision-curator` is the desktop-side curation and annotation repo for the thermal person detection bootstrap pipeline.

It consumes immutable raw edge packages from `thermal-data-engine`, scores pseudo-label quality, builds human review queues, coordinates optional CVAT/FiftyOne exchange workflows, and emits immutable dataset releases for `vision-trainer`.

This repo does not run edge inference, own `vision_api` runtime logic, train YOLO models, export TensorRT engines, mutate raw packages, or silently invent missing labels.

## Source of Truth
When docs and code disagree, trust these files:
- `src/vision_curator/cli.py` — canonical command surface
- `src/vision_curator/common/models.py` — shared data contracts
- `src/vision_curator/packages/validate.py` — Phase 2 package validation contract
- `src/vision_curator/packages/ingest.py` — curator store package indexing behavior
- `src/vision_curator/scoring/trust.py` — trust score and decision bucket semantics
- `src/vision_curator/review/queues.py` — review queue record/output behavior
- `src/vision_curator/releases/build.py` — dataset release layout and immutability behavior
- `schemas/` and `docs/package_contracts.md` — durable external contracts

Additional repo-specific rules:
- Phase 2 clip packages are the primary input; Phase 1 training packages are compatibility/audit inputs only.
- Never mutate raw edge packages.
- Dataset releases are immutable once published; do not overwrite an existing release unless the user explicitly asks for destructive behavior.
- Keep CVAT and FiftyOne optional for core tests and bring-up workflows.
- Prefer explicit metadata and provenance over inferred or silent defaults.

---

## Repo Map

### High-Signal Code
- `src/vision_curator/` — core package
  - `cli.py` — user-facing CLI entrypoint
  - `common/` — dataclasses, config helpers, paths, manifests
  - `packages/` — Phase 2 validation, ingest, package index
  - `scoring/` — trust scoring, jitter, bucket decisions
  - `review/` — review queue generation and sampling
  - `annotation/` — CVAT/YOLO exchange helpers; optional at bring-up
  - `fiftyone/` — optional visualization helpers
  - `releases/` — immutable dataset release builder/validator/manifest
- `configs/` — default curator, trust, review, and release config
- `schemas/` — JSON schemas for manifests, review items, and releases
- `docs/` — architecture, contracts, annotation policy, handoffs, release rules
- `tests/` — unit tests and small fixtures

### Large/Noisy Dirs
Avoid broad traversal unless explicitly needed:
- external Phase 2 package roots
- curator stores (`indexes/`, `scores/`, `review_queues/`, `annotation_exports/`, `annotation_imports/`)
- dataset release stores
- `.agent/logs/`

Use targeted commands (`rg`, `find -maxdepth`, `ls`) and keep outputs small.

---

## Core Workflow

### Prepare
```bash
python -m pip install -e .
```

### Validate / Ingest / Score
```bash
python -m vision_curator.cli validate-package --phase2 /path/to/phase2_package
python -m vision_curator.cli ingest-package --source /path/to/phase2_package --store-root /data/openclaw/curator
python -m vision_curator.cli score-package --package-id <package_id> --store-root /data/openclaw/curator
```

### Review Queues
```bash
python -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /data/openclaw/curator
```

### Dataset Releases
```bash
python -m vision_curator.cli build-release --config configs/release/default.yaml --release-id <release_id>
```

### Tests
Run the fastest meaningful check first:
```bash
python -m unittest
```

Optional packaging smoke:
```bash
python -m pip install -e .
python -m vision_curator.cli --help
```

---

## Metadata Contracts

### Phase 2 Package Input
```text
<phase2_root>/
├─ manifest.json
└─ clips/
   └─ <package_clip_id>/
      ├─ clip.mp4
      ├─ clip_manifest.json
      ├─ detections.parquet
      └─ tracks.parquet
```

Validation must fail loudly on missing required files or required manifest fields.

### Curator Store Outputs
- `<curator_store>/indexes/packages.jsonl` — one record per ingested package.
- `<curator_store>/scores/<package_id>/track_scores.parquet` — initial bring-up may use JSONL-compatible content behind this contract if parquet dependencies are intentionally avoided.
- `<curator_store>/review_queues/<queue_id>.jsonl` — review items for hard-case, ambiguous, candidate-negative, disagreement, or random-audit workflows.
- `<curator_store>/annotation_exports/cvat/<task_id>/` and `<curator_store>/annotation_imports/cvat/<task_id>/` — CVAT exchange packages.
- `<dataset_release_store>/<release_id>/` — immutable release consumed by `vision-trainer`.

### Trust Buckets
Preserve these bucket names unless the user explicitly changes the contract:
- `trusted_full`
- `trusted_class_weak_box`
- `ambiguous`
- `candidate_negative`
- `discard`

---

## Coding/Style Conventions
- Python package source lives under `src/vision_curator`.
- Keep dependencies light for bring-up; use stdlib and optional imports where practical.
- Use stdlib `unittest` unless the repo deliberately adopts pytest.
- Prefer minimal, localized diffs; avoid broad formatting-only changes unless requested.
- Follow existing local style in touched files if no formatter/linter is configured.

---

## Working Agreement

### Phase 1 — Plan + Task Definition
Goal: build repo-aware understanding and produce or update `.agent/TASK_BRIEF.md`.

Rules:
- Read only until the goal, success criteria, relevant files, plan, and verification are clear.
- Keep command output concise.
- If the user has explicitly authorized implementation, proceed after updating `.agent/TASK_BRIEF.md`; otherwise stop and ask before editing tracked files.
- Run `/compact` before continuing only when context pressure justifies it.

### Phase 2 — Implement + Learn
Goal: execute the plan in `.agent/TASK_BRIEF.md`.

Rules:
- You may edit files, but do not run `git commit`, `git push`, `git merge`, `git rebase`, `git reset --hard`, or `git clean -fd` unless explicitly requested.
- Keep diffs minimal and scoped to the task.
- After coherent edit sets, state intent, apply changes, run verification, and report results.
- Record durable gotchas in `.agent/MEMORY.md`; promote them to docs only at closeout.

### Phase 3 — Debug Mode
When debugging:
1. Reproduce the failure with the exact command provided.
2. Minimize the repro.
3. Propose 1–2 hypotheses and the evidence for each.
4. Add a targeted regression test when feasible.
5. Make a surgical fix, rerun failing tests, then broaden coverage.
6. Update `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` when the plan changes materially.

### Phase 4 — Closeout
When the task is complete:
1. Use `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` as closeout sources of truth.
2. Summarize decisions, invariants/gotchas, changed commands, TODOs, and verification evidence.
3. Update durable docs only when information is stable and reusable.
4. Archive scratch notes under `docs/agent/tasks/<task_slug>/` if the repo has adopted task archives.
5. Reset `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` to templates and leave `.agent/logs/` empty.

---

## `.agent/` Folder Policy (Scratch Only)

`.agent/` is untracked scratch space. It should be safe to delete at any time and should be cleared at task closeout.

Preferred structure:
- `.agent/TASK_BRIEF.md` — compact task description, success criteria, progress notes, and next steps.
- `.agent/MEMORY.md` — compact running notes for process discoveries and gotchas.
- `.agent/logs/` — logs and small extracted snippets.

Log naming convention:
```text
.agent/logs/YYYYMMDD_HHMM_<topic>.log
```

Keep `.agent/MEMORY.md` under 200 lines when possible. Suggested headings:
- Goal / status
- Repro commands
- Hypotheses + evidence
- Decisions (and why)
- Gotchas discovered
- Verification run
- Next steps

Promote durable knowledge from `.agent/MEMORY.md` into docs during closeout; do not let scratch files become permanent documentation.

---

## Docs Policy
Do not read the entire docs tree by default.

Open docs only when needed, in this priority order:
1. Current workflow / operational workflow doc
2. Module / architecture map doc
3. Metrics / diagnostics doc
4. Experiment log / change log / results log

Treat archived plans and old specs as historical unless explicitly requested.
