# Workspace Next Steps — `vision-curator`

## Context
This packet is the desktop-side `vision-curator` execution slice for the workspace root task **Bootstrap vision next wave across edge, curator, and trainer**.

Read first:
- `AGENTS.md`
- `docs/architecture.md`
- `docs/package_contracts.md`
- `docs/review_queues.md`
- `docs/dataset_releases.md`
- `docs/annotation_policy.md`
- workspace: `docs/SYSTEM_DESIGN_v1.md`
- workspace: `docs/PROPOSED_PLAN_v1.md`

## Mission for this wave
Turn the initial curator bring-up into the first useful curation control plane:
1. ingest immutable raw edge packages,
2. compute deterministic trust outputs,
3. generate review queues,
4. define the CVAT exchange boundary clearly,
5. publish a first draft curated release that `vision-trainer` can validate.

Do not move training into this repo. Do not mutate raw packages. Do not require FiftyOne or CVAT for core tests.

## What the edge node is doing in parallel
The Xavier NX node is updating:
- `vision_api` job metadata so backend/runtime provenance is explicit,
- `thermal-data-engine` package manifests so tracker/runtime provenance and package completion state are explicit.

Assume Phase 2 packages remain the primary input. Prefer consuming package manifests and track/detection artifacts rather than inventing side channels.

## Concrete objectives

### Objective 1, harden Phase 2 ingest as the authoritative raw-package boundary
Acceptance:
- `validate-package` fails loudly on missing manifest fields or required clip artifacts.
- `ingest-package` records a canonical package index entry with source path, package id, clip count, and key provenance fields.
- At least one unit test exercises package ingestion from a realistic Phase 2 fixture.

Suggested implementation shape:
- Tighten `src/vision_curator/packages/validate.py`
- Extend `src/vision_curator/packages/ingest.py`
- Keep immutable source-path registration; do not copy raw clips into the curator store unless the task explicitly changes that policy.

### Objective 2, make trust scoring deterministic and inspectable
Acceptance:
- Trust scoring writes reproducible output for the same package.
- Output separates at least these concepts: class trust, box trust, decision bucket.
- The scoring path records enough feature fields that later threshold tuning is possible without re-ingesting raw packages.

Suggested heuristics for v1:
- class trust from confidence, track duration, detection density
- box trust from jitter, edge clipping, sudden area change if available
- bucket mapping to:
  - `trusted_full`
  - `trusted_class_weak_box`
  - `ambiguous`
  - `candidate_negative`
  - `discard`

Keep this deterministic and stdlib-light. Do not wait for fancy modeling.

### Objective 3, build review queues that are actually useful
Acceptance:
- At least these queue kinds work and are tested:
  - `hard-case`
  - `ambiguous`
  - `candidate-negative`
  - `random-audit`
- Queue records preserve provenance back to package id, clip id, run id, and source path.
- Queue ordering reflects the queue’s semantics rather than arbitrary file order.

Recommended prioritization:
- `hard-case`: low box trust but likely real person
- `ambiguous`: weak class confidence or fragmented track behavior
- `candidate-negative`: likely no-human clips that still need human confirmation
- `random-audit`: low-volume sampling from trusted positives and rejects

### Objective 4, define the CVAT handoff explicitly
Acceptance:
- A durable doc or command surface describes how a review queue becomes a CVAT export task.
- The packet clearly marks the point where Dr. Long must label data in CVAT.
- The repo can represent imported corrected annotations, even if the full roundtrip is still a stub.

Minimum acceptable for this wave:
- export manifest or stubbed task package for a small review queue
- import placeholder contract or parser boundary
- explicit note of what is blocked on human labeling

### Objective 5, publish a draft curated release contract for `vision-trainer`
Acceptance:
- A release build path emits a manifest that `vision-trainer` can validate.
- The release preserves source package provenance and annotation/version metadata.
- The release can be built from a minimal local fixture or tiny smoke dataset.

Recommended release contents for now:
- `manifest.json`
- `dataset.yaml`
- split files
- provenance records
- clear label-policy and split-policy metadata

Do not wait for a large real dataset before defining the contract.

## Human-in-the-loop gates
These are real dependencies, not optional footnotes.

### Gate A, desktop package pull
Before meaningful curation on real data:
- desktop pulls completed Phase 2 packages from the NX spool
- pulled packages are validated locally

### Gate B, CVAT labeling
After review queues exist:
- Dr. Long labels a selected queue in CVAT
- corrected annotations are imported back into `vision-curator`
- only then can gold negatives and frozen hard-case slices become trustworthy

### Gate C, release publication for trainer
After at least one labeling pass or a clearly-labeled pseudo-only smoke release:
- publish the first curated release
- hand it to `vision-trainer`

## Parallelism guidance
Can run now, in parallel with the NX work:
- Objective 1 ingest hardening
- Objective 2 trust scoring
- Objective 3 review queue generation
- Objective 5 draft release contract

Should wait for real pulled edge packages if possible:
- end-to-end ingest against real Phase 2 outputs
- final provenance field locking

Requires Dr. Long / CVAT:
- Objective 4 true annotation roundtrip
- gold-negative confirmation
- frozen hard-case eval split

## Verification
Minimum:
```bash
python3 -m unittest
python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid
python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store
python3 -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store
python3 -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store
```

If you add release validation/build:
```bash
python3 -m vision_curator.cli build-release --config configs/release/default.yaml --release-id smoke_release_20260430
```

## Definition of done for this wave
This packet is complete when:
- package ingest and trust scoring are deterministic and tested,
- review queues exist with preserved provenance,
- the CVAT dependency boundary is explicit,
- a first curated release manifest exists for downstream validation,
- repo-local notes are updated so the trainer agent can consume the result cleanly.

## Deliver back to workspace
Report:
- files changed
- commands run
- whether real edge packages were used or only fixtures
- exact blocker status for CVAT labeling
- exact release path or manifest shape handed to `vision-trainer`
