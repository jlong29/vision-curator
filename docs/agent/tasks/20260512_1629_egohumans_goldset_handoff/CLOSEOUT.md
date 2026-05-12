# Closeout — EgoHumans Gold Set Handoff

## Decisions Made
- Updated `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` as the durable handoff for the next release-materialization task.
- Recorded completed oracle-import facts in the proposal: six validated/imported packages, 8,227 frame-index rows, 8,839 oracle labels, reveal-set counts, and zero warnings.
- Made the remaining dataset families explicit: `gold_only_v0`, `gold_plus_naive_pseudo_v0`, `gold_plus_trusted_tracks_v0`, `gold_plus_review_revealed_v1`, and `oracle_upper_bound`.
- Clarified that the current generic `build-release` path is not yet EgoHumans namespace/split aware.

## New Invariants / Gotchas
- Realistic calibration releases must not train from `oracle_hidden`; only `oracle_upper_bound` may train from full oracle labels.
- All main calibration releases and the headroom release should share compatible frozen validation/test definitions.
- The next session must create an explicit split assignment artifact before materializing releases.

## New / Changed Commands
- None. Documentation-only task.

## Verification Evidence
- Reviewed relevant EgoHumans docs, project state, module map, and release builder behavior.
- Reviewed `git diff -- docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md`.

## TODOs / Follow-Ups
- Implement EgoHumans-specific release materialization.
- Validate each release and hand off release roots plus `dataset.yaml` paths to `vision-trainer`.
