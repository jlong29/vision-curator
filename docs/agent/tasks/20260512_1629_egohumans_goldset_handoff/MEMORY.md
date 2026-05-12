# .agent/MEMORY.md (scratch)

**Task:** egohumans-goldset-proposal-handoff
**Last updated:** 2026-05-12

## Goal / status
- Updated `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` as the next-session handoff for creating trainer-ready calibration and headroom releases.

## Repro commands
- `git diff -- docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md`

## Hypotheses + evidence
- Current release builder is generic and not yet EgoHumans namespace/split aware.
- Oracle substrate is complete: six incoming packages validated/imported; 8,227 frame rows and 8,839 oracle labels.

## Decisions (and why)
- Keep the gold-set proposal as the policy/handoff doc rather than scattering next steps across multiple docs.
- Explicitly separate realistic calibration releases from the `oracle_upper_bound` headroom release.

## Gotchas discovered (promote at closeout)
- Next task must not assume `build-release` can already produce EgoHumans release families; release materialization still needs code work.

## Verification run
- Command(s): `git diff -- docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md`
- Outcome(s): diff reviewed; docs-only change.

## Next steps
- Build trainer-ready EgoHumans release families and hand off dataset YAML paths to `vision-trainer`.
