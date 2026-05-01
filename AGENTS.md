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

## Working agreement (four-phase execution)
### Phase 1 — Plan + Task Definition (read-only)
Goal: build repo-aware understanding and produce **one** task artifact.

Rules:
- Do not edit code or tracked files in this phase.
- Use ≤10 shell commands and keep output concise (avoid long listings).
- Restate goal + success criteria.
- Identify the minimal relevant files and why.
- Propose a plan + verification commands.

**Phase 1 output (the only artifact):**
- Create a branch for the task using a short name reflecting the goal of the task e.g. `add-oAuth`, `fix-callbacks`
- Write the plan to: `.agent/TASK_BRIEF.md`

`.agent/` is **untracked** and exists specifically for this ephemeral brief. The brief may be updated in Phase 2.

At the end of Phase 1:
- Ensure `.agent/TASK_BRIEF.md` is up to date.

Notes:
  - A template for `.agent/TASK_BRIEF.md` is already available and it is copied from `docs/agent/TASK_BRIEF_TEMPLATE.md`

### Phase 2 — Implement + Learn (write + verify, no git history operations)
Goal: Execute the plan developed in Phase 1 and memorialized in `.agent/TASK_BRIEF.md`

Rules:
- You may edit files, but do NOT run:
  `git merge`/`rebase`, `git reset --hard`, `git clean -fd`
- Keep diffs minimal; no broad “format-only” changes unless requested.
- After each coherent edit set:
  1) state intent + files touched
  2) apply changes
  3) run verification and report results
  4) show diff summary and key hunks

## Phase 3 — Debug mode
Goal: Review the output of Phase 2 and thoroughly test until all outputs are predictable and functional.

When debugging bugs introduced during Phase 2, follow this strict loop:
1) Reproduce the failure with the exact command provided.
2) Minimize the repro (smallest failing command/test).
3) Propose 1–2 hypotheses and what evidence would confirm each.
4) Add a targeted regression test when feasible.
5) Make a **surgical** fix (minimal files), re-run the failing test(s), then broaden coverage.
6) Update `.agent/TASK_BRIEF.md` with what changed and why; if possible, run `/compact` if context is getting large.

## Phase 4 — Task completion / closeout procedure
Goal: Summary successful completed work and clean up.

When the task is complete (as defined in `.agent/TASK_BRIEF.md`), the agent should:
1) Review this `AGENTS.md`.
2) Produce a **closeout summary** (short, high-signal), using `.agent/MEMORY.md` and `.agent/TASK_BRIEF.md` as the sources of truth:
   - Decisions made (and why)
   - New invariants/gotchas discovered
   - New/changed commands (CLI flags, scripts)
   - TODOs / follow-ups
   - Verification evidence (commands run)
3) Update repo docs **only when the information is stable and reusable**:
   - Update `AGENTS.md` for durable workflow/invariants only.
   - Create or Update `docs/PROJECT_STATE.md` for “current operational workflow.”
   - Create or Update `docs/MODULE_MAP.md` if module boundaries/entrypoints changed.
   - Create or Update `docs/METRICS_AND_DIAGNOSTICS.md` if diagnostics/metrics interpretation changed.
   - Finish with `git status` and commit message(s)
   - commit code
4) Follow the procedure defined in `Cleanup at task closeout` (defined below)

### Cleanup at task closeout
At completion:
1. Summarize “gotchas / decisions / commands / TODOs” and promote them to durable docs (see `Task completion / closeout procedure`).
2. Create a folder `docs/agent/tasks/<task_slug>` under `docs/agent/tasks`
  - e.g. <task_slug> = YYYYMMDD_HHMM_<short_topic>
3. Move `.agent/TASK_BRIEF.md` to `docs/agent/tasks/<task_slug>/`
4. Move `.agent/MEMORY.md`to `docs/agent/tasks/<task_slug>/`
5. Empty `.agent/logs/` (or delete the directory contents)
6. Write the closeout into `docs/agent/tasks/<task_slug>/CLOSEOUT.md`
7. Verify: `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` exist (templates), `.agent/logs/` empty, and archive folder contains `TASK_BRIEF.md`, `MEMORY.md`, and `CLOSEOUT.md`

---

## `.agent/` folder policy (scratch only)

`.agent/` is **untracked** and is intended as **scratch space only**. It should be safe to delete at any time, and it should be **cleared at task closeout**.

### Purpose
1) **Task Related documents** most notably TASK_BRIEF.md
2) **User-provided artifacts for debugging** (logs, traces, perf output) that the agent should inspect.
3) **Agent working memory externalization** when the chat context window is under pressure.

> Policy: when the agent learns a new *gotcha* during Phase 2, it should record it in `.agent/MEMORY.md` and only promote it to durable docs during closeout.

### Flat structure (preferred)
- `.agent/TASK_BRIEF.md` — compact task description, success criteria, and progress notes
- `.agent/MEMORY.md` — compact running notes related to the work process rather than the task definition itself
- `.agent/logs/` — log files and small extracted snippets

### `.agent/TASK_BRIEF.md`
During Phase 2 this document may be updated to reflect changes in:

- **Goal / status**
- **Decisions (and why)**
- **Next steps**

### `.agent/MEMORY.md` format (keep it small)
Maintain **≤ 200 lines** when possible. Use bullets. Suggested headings:

- **A valuable research url cache**
- **Repro commands**
- **Hypotheses + evidence**
- **Failed experiments and ideas**
- **Gotchas discovered**  ← (promote these during closeout)
- **Verification run** (commands + outcomes)

Notes:
  - A template for `.agent/MEMORY.md` is already available and it is copied from `docs/agent/MEMORY_TEMPLATE.md`

### Log naming convention
Store logs as:

- `.agent/logs/YYYYMMDD_HHMM_<topic>.log`

The agent may create filtered snippets alongside logs, e.g.:

- `.agent/logs/YYYYMMDD_HHMM_<topic>__excerpt.log`
- `.agent/logs/YYYYMMDD_HHMM_<topic>__grep_<pattern>.log`

Keep snippets **small** (e.g., ≤ 500 lines). Do not copy huge logs.

### When to externalize to `.agent/`
Externalize (write/update `.agent/MEMORY.md`) when any of these is true:
- The plan has evolved materially beyond Phase 1.
- Debugging involves multiple hypotheses or long traces.
- The session is getting long (check `/status` or a token status line).
- The agent is about to run `/compact`.

After externalizing:
- Update `.agent/MEMORY.md`
- Then run `/compact` to keep interactive context focused.

---

## Docs policy (protect the context window)
Do NOT read the entire docs tree by default.

Open docs only when needed, in this priority order:
1) The repo’s current workflow / operational workflow doc
2) The repo’s module / architecture map doc
3) The repo’s metrics / diagnostics doc
4) The repo’s experiment log / change log / results log

Treat these as historical unless explicitly requested:
- old specs
- old work plans
- archived project-state headers
- other superseded planning docs

If the repo does not yet have durable docs in these roles, ask the user which files are intended to fill them.
