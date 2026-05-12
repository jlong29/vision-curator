## TASK_BRIEF

### Task
- Update `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` to reflect completed oracle-import work and the remaining dataset-release work for `vision-trainer`.

### Why this update
- The EgoHumans hidden-oracle importer and real-package smoke are complete on this branch. The next session should start from an accurate handoff that distinguishes completed curation substrate from remaining release materialization work.

### Fixed invariants (do not change)
- Preserve the three label namespaces: `oracle_hidden`, `gold_revealed`, and `pseudo_teacher`.
- Full `oracle_hidden` labels may train only the explicit `oracle_upper_bound` headroom release.
- Realistic calibration releases may use only `gold_revealed` and/or `pseudo_teacher`.
- Do not move or delete raw packages under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`.

### Goal
- Leave a high-signal policy and execution handoff for creating all EgoHumans calibration datasets and the headroom dataset for `vision-trainer`.

### Success criteria
- [x] Document completed package validation and oracle import smoke counts.
- [x] Document what remains to build `gold_only_v0`, `gold_plus_naive_pseudo_v0`, `gold_plus_trusted_tracks_v0`, `gold_plus_review_revealed_v1`, and `oracle_upper_bound`.
- [x] Make the headroom experiment boundary explicit.
- [x] Identify the code areas the next session must implement or extend.

### Relevant files (why)
- `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` — target policy/handoff doc.
- `docs/EGOHUMANS_CALIBRATION_EXECUTIVE_SUMMARY.md` — experiment framing.
- `docs/EGOHUMANS_ORACLE_IMPORT_TASK_SPEC.md` — oracle import contract and label namespace rules.
- `docs/PROJECT_STATE.md` — current operational state and package location.
- `src/vision_curator/releases/build.py` — current generic release builder; likely extension point.

### Refined Phase 2 Plan
1) Review relevant docs and current release builder behavior. Done.
2) Update the gold-set proposal with completed artifacts, release matrix, remaining implementation tasks, and next-session acceptance criteria. Done.
3) Run a docs diff review and commit the update. In progress.

### Small change sets (execution order)
1) Documentation-only update to `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md`.

### Verification
- Fast: `git diff -- docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md`
- Full: docs-only, no test run required unless code changes are made.

### Risks / gotchas
- Current `build-release` is not yet EgoHumans-label aware; the doc must not imply releases are already trainer-ready.

### Decision rule for defaults
- State current facts from completed smoke runs and defer release-family implementation details to the next task where code can be inspected and changed.

### Deferred work note
- This task does not create the actual dataset releases; it prepares the next-session handoff.
