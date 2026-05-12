# Task Brief: Prep EgoHumans Calibration Readiness

## Goal
Bring `vision-curator` docs and repo state into alignment with:
- `docs/SYSTEM_DESIGN_v2.md`
- `docs/PROPOSED_PLAN_v2.md`
- `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`
- upcoming EgoHumans calibration work described in `docs/EGOHUMANS_CALIBRATION_EXECUTIVE_SUMMARY.md`

## Status
Implementation, docs, and verification complete. Closeout pending.

## Current Understanding
- The repo already implements more than the stale 2026-04-30 handoff says: validation, ingest, deterministic trust scoring, review queues, CVAT helpers, and release builder files exist.
- The v2 system direction is clear: edge packages remain immutable, Phase 2 clip packages are primary, the curator owns trust/review/release artifacts, and training remains outside this repo.
- The new EgoHumans experiment adds a calibration-specific requirement: ingest edge-generated Phase 2 packages while keeping EgoHumans ground truth as a hidden desktop-side oracle, with only selected labels revealed into gold/review namespaces.

## Success Criteria
- Durable docs reflect current repo capability and the v2 system direction.
- Workspace handoff no longer describes already-implemented features as missing.
- Package and workflow docs are ready for EgoHumans edge outputs that include `READY.json`, `source_frames.jsonl`, preview media, and source-frame mapping metadata.
- If code or schemas block these documented contracts, update them minimally and add tests.
- Verification commands are run and recorded.

## Minimal Relevant Files
- `AGENTS.md`: durable agent workflow and repo mission.
- `docs/SYSTEM_DESIGN_v2.md`: target architecture.
- `docs/PROPOSED_PLAN_v2.md`: workspace-level near-term plan.
- `docs/handoffs/WORKSPACE_NEXT_STEPS_20260430.md`: repo-specific execution packet to reconcile with current state.
- `docs/EGOHUMANS_CALIBRATION_EXECUTIVE_SUMMARY.md`: next experiment requirements.
- `docs/EGOHUMANS_EDGE_NODE_PROCESSING_PROPOSAL.md`: expected edge package output shape.
- `docs/package_contracts.md`, `docs/architecture.md`, `docs/dataset_releases.md`, `docs/review_queues.md`, handoff docs: durable operational docs likely needing updates.
- `schemas/phase2_manifest.schema.json`, `src/vision_curator/packages/validate.py`, tests/fixtures if package validation does not accept new explicit fields.

## Plan
1. Compare current docs/code to the handoff and v2 direction. Done.
2. Update stable docs so they describe current capabilities and next EgoHumans workflow accurately. Done.
3. Make minimal schema/validation/test changes if current code rejects the new Phase 2 edge package metadata. Done.
4. Run focused unit tests and CLI smoke commands. Done.
5. Close out with archived task notes, status, and commit. Pending.

## Verification Commands
- `python3 -m unittest`
- `env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 tests/fixtures/phase2_valid`
- `env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source tests/fixtures/phase2_valid --store-root /tmp/vision-curator-smoke-store`
- `env PYTHONPATH=src python3 -m vision_curator.cli score-package --package-id fixture_phase2_001 --store-root /tmp/vision-curator-smoke-store`
- `env PYTHONPATH=src python3 -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /tmp/vision-curator-smoke-store`

## Branch
`prep-egohumans-calibration`
