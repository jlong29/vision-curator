## TASK_BRIEF

### Task
- Execute the workspace packet in `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md` to harden ingest, trust scoring, review queues, and the first draft curated release contract.

### Why this update
- The repo has completed initial bring-up and now needs to become the first useful desktop curation control plane in the thermal bootstrap pipeline.

### Fixed invariants (do not change)
- Raw edge packages are immutable inputs.
- CVAT and FiftyOne remain optional for core tests.
- This repo owns curation and release publication, not training or edge runtime.
- Human CVAT labeling is an explicit dependency for gold data and hard-case freeze quality.

### Goal
- Produce deterministic curation outputs and a draft release contract that `vision-trainer` can validate.

### Success criteria
- [x] Ingest and validation are deterministic and tested.
- [x] Trust scores preserve class trust, box trust, and decision bucket outputs.
- [x] Review queues exist with preserved provenance.
- [x] A first draft curated release manifest is emitted.
- [x] The packet clearly marks what is blocked on CVAT labeling.

### Relevant files (why)
- `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md` — authoritative repo packet for this wave
- `src/vision_curator/packages/validate.py` — package contract enforcement
- `src/vision_curator/packages/ingest.py` — canonical ingest/index boundary
- `src/vision_curator/scoring/trust.py` — deterministic trust outputs
- `src/vision_curator/review/queues.py` — queue generation
- `src/vision_curator/releases/build.py` — first release contract

### Refined Phase 2 Plan
1) Harden ingest and trust-scoring outputs while preserving raw package immutability.
2) Build review queues and a first draft curated release contract.
3) Document the CVAT handoff boundary and report exact blockers.

### Small change sets (execution order)
1) Validation/ingest changes and tests
2) Trust scoring and queue changes and tests
3) Release contract changes and tests/docs

### Verification
- Fast: `python3 -m unittest`
- Targeted: `python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store`
- Full: follow the command list in `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`

### Risks / gotchas
- Do not invent gold labels from pseudo labels.
- Keep the release contract small and explicit before scaling up.

### Decision rule for defaults
- Prefer deterministic, inspectable heuristics over ambitious but opaque scoring logic.

### Deferred work note
- Full CVAT roundtrip completion and frozen hard-case release quality wait on human labeling.
