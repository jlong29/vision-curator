## TASK_BRIEF

### Task
- Materialize EgoHumans Lego Assembly trainer-ready calibration releases from the six staged Phase 2 packages while preserving strict label namespace separation.

### Why this update
- The hidden-oracle import substrate exists, but `vision-trainer` still needs immutable YOLO release directories for the calibration ablations described in `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md`.
- This task turns the proposal into executable `vision-curator` release workflow: ingest/score packages, freeze splits, materialize labels/images, validate manifests, and hand off dataset YAMLs.

### Fixed invariants (do not change)
- Never mutate raw Phase 2 package roots.
- Realistic calibration releases must never train from `oracle_hidden`; full oracle labels are allowed only in `oracle_upper_bound`.
- Hidden test labels must not tune trust thresholds, choose review items, accept pseudo labels, or populate realistic training labels.
- All calibration releases must share compatible frozen validation/test split definitions.
- Review queues and pseudo-label selection must use teacher pseudo labels and edge provenance only.
- Dataset releases are immutable; do not overwrite an existing release unless the user explicitly asks for destructive behavior.
- `candidate_negative` remains confirmation-only; no-detection frames are not training negatives without oracle/human reveal.

### Ablation dimensions (new)
- `gold_only_v0`: revealed seed labels only.
- `gold_plus_naive_pseudo_v0`: revealed seed labels plus high-confidence framewise teacher pseudo labels.
- `gold_plus_trusted_tracks_v0`: revealed seed labels plus track-aware `trusted_full` pseudo labels.
- `gold_plus_review_revealed_v1`: revealed seed labels plus simulated review-revealed gold; include trusted pseudo labels only if the policy declares it.
- `oracle_upper_bound`: full oracle training labels for diagnostic headroom only.

### Goal
- Produce validated, immutable, trainer-facing release roots under the calibration dataset release store, each with `dataset.yaml`, YOLO images/labels, split files, manifest/provenance, and auditable label-policy metadata.

### Success criteria
- [x] All six incoming EgoHumans package roots are confirmed, validated, and indexed or already present in the curator package index.
- [x] Trust scores and review queues are produced from pseudo-teacher metadata only.
- [x] `$OPENCLAW_CURATOR_STORE/oracle/egohumans/splits/split_assignments_v0.jsonl` exists and records package/clip/camera/sequence/split/rationale without recomputing random splits in release builders.
- [x] `gold_only_v0`, `gold_plus_naive_pseudo_v0`, `gold_plus_trusted_tracks_v0`, `gold_plus_review_revealed_v1`, and `oracle_upper_bound` release roots are built with common validation/test definitions.
- [x] Every release manifest exposes `release_family`, train/eval namespaces, forbidden train namespaces, source package IDs, source oracle manifest, reveal sets, pseudo policy, `realistic_calibration_loop`, and `oracle_upper_bound`.
- [x] Realistic release manifests include `oracle_hidden` in `forbidden_label_namespaces_for_train`.
- [x] `oracle_upper_bound` is the only release with `oracle_upper_bound: true` and `realistic_calibration_loop: false`.
- [x] Release validation passes and `vision-trainer` can start a packaging/smoke run from the generated `dataset.yaml` paths.
- [x] Document the Edge/desktop path portability issue discovered during release materialization and record the follow-up need to formalize package-relative consumable paths vs Edge-local provenance paths.

### Relevant files (why)
- `src/vision_curator/cli.py` — canonical command surface; add or extend release/split commands here.
- `src/vision_curator/oracle/egohumans.py` — existing hidden-oracle/reveal artifact format and source counts.
- `src/vision_curator/releases/build.py` — current generic release builder; either extend here or keep it as shared infrastructure.
- `src/vision_curator/releases/manifest.py` — release manifest creation and provenance fields.
- `src/vision_curator/releases/validate.py` — immutable release validation behavior.
- `schemas/dataset_release.schema.json` — external release manifest contract; add EgoHumans namespace/policy fields if needed.
- `src/vision_curator/scoring/trust.py` and `src/vision_curator/scoring/buckets.py` — trust score and bucket semantics used for trusted pseudo-label selection.
- `configs/trust/default.yaml` — default trust threshold home; add EgoHumans policy values if configs support named policies.
- `src/vision_curator/review/queues.py` — review queue generation must remain pseudo-metadata-only.
- `src/vision_curator/packages/ingest.py` and `src/vision_curator/packages/validate.py` — package indexing and Phase 2 package contract.
- `src/vision_curator/common/models.py` — shared records if split assignments or namespace policies need typed dataclasses.
- `configs/release/default.yaml` — existing release config pattern to preserve or extend.
- `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` — task source of truth for release families and leakage rules.
- `docs/SYSTEM_DESIGN_v2.md` — repo boundary and shared store conventions.
- `docs/EGOHUMANS_CALIBRATION_EXECUTIVE_SUMMARY.md` — calibration experiment intent and interpretation.

### Refined Phase 2 Plan
1. Preflight operational artifacts: source environment, confirm six incoming package roots, verify oracle import counts, and validate/index packages without mutating raw inputs.
2. Run or confirm trust scoring for each package and build review queues using pseudo-teacher metadata only.
3. Add a frozen split assignment artifact builder for EgoHumans that splits by clip or sequence chunk, records rationale, and excludes test from tuning/selection/training.
4. Add an EgoHumans calibration release policy layer that declares release family, allowed/forbidden namespaces, oracle/reveal sources, split artifact, pseudo policy, and headroom flags.
5. Materialize YOLO images/labels from `gold_revealed`, selected `pseudo_teacher`, and, for `oracle_upper_bound` only, `oracle_hidden`.
6. Emit manifests/provenance with explicit namespace and policy fields; update schema/validation to reject namespace leakage.
7. Build all five release families under the calibration release store and validate them.
8. Produce a short trainer handoff with release roots, dataset YAML paths, label policies, and experiment interpretation.

### Small change sets (execution order)
1. Split artifact support: add typed split records, builder/CLI, deterministic output, and focused tests.
2. Manifest/schema support: add EgoHumans namespace/policy fields and validation checks for realistic vs. oracle upper-bound releases.
3. Release materialization support: add EgoHumans release builder or config extension, image extraction/linking policy, YOLO label writing, and immutable output checks.
4. Pseudo policy support: implement naive confidence and trusted-track selectors that consume teacher/trust records only.
5. Operational wiring: add configs/CLI examples and targeted tests around leakage prevention and shared split reuse.

### Phase 2 implementation notes
- Added `src/vision_curator/releases/egohumans.py` with deterministic split building, EgoHumans release materialization, namespace policies, pseudo selectors, YOLO label writing, and curator-side image caching under `$OPENCLAW_CURATOR_STORE/image_cache/egohumans`.
- Added CLI commands: `build-egohumans-splits`, `build-egohumans-release`, and `validate-release`.
- Updated release validation to reject realistic releases that train from `oracle_hidden` and to enforce the special `oracle_upper_bound` flags.
- Added parquet support and track-summary scoring support so real staged EgoHumans package tables can be scored.
- Documented EgoHumans calibration trust thresholds in `configs/trust/default.yaml`.
- Added `tests/test_egohumans_release.py` for split-unit consistency, realistic namespace policy, and diagnostic oracle release policy.
- Recorded the Edge/desktop path portability issue as a follow-up: Phase 2 packages should expose package-relative consumable paths, while absolute Edge paths should remain provenance only.

### Initial trust and pseudo-label policy choices
- Naive pseudo baseline: accept framewise teacher detections with detector confidence `>= 0.85`, valid positive-area boxes, and frames assigned to train-eligible pools only. Rationale: this is intentionally simple and precision-biased so it is a meaningful baseline against track-aware trust without using oracle feedback for selection.
- `trusted_full`: require `class_trust >= 0.90`, `box_trust >= 0.80`, minimum track length `>= 3` frames, average detector confidence `>= 0.70`, border-clipped frame rate `<= 0.15`, and normalized box jitter `<= 0.20` if those features are available. Rationale: the proposal targets at least 95% pseudo-label precision and median matched IoU at least 0.75; these thresholds favor reliable supervision over recall.
- `trusted_class_weak_box`: require `class_trust >= 0.90` and `0.55 <= box_trust < 0.80`. Rationale: likely-person tracks are useful for review or reduced-regression experiments, but should not become ordinary YOLO box labels unless the trainer explicitly supports reduced box loss.
- `ambiguous`: route tracks with `0.45 <= class_trust < 0.90` or `0.40 <= box_trust < 0.55` to review queues. Rationale: this range should have high review yield without polluting training labels.
- `candidate_negative`: assign only to clip/frame contexts with no usable teacher support after package-aware grouping; never train as negative until confirmed by `gold_revealed`/oracle reveal. Rationale: no detection is unknown, not proof of no person.
- `discard`: use for invalid geometry, very short one-frame tracks below threshold, `class_trust < 0.45`, or `box_trust < 0.40`; still allow a tiny random audit sample. Rationale: keep low-value artifacts out of training while monitoring for systematic scorer blind spots.

### Verification
- Fast: `python -m unittest`
- Targeted: `python -m vision_curator.cli validate-package --phase2 <one_egohumans_phase2_package>`
- Targeted: `python -m vision_curator.cli ingest-package --source <one_egohumans_phase2_package> --store-root "$OPENCLAW_CURATOR_STORE"`
- Targeted: `python -m vision_curator.cli score-package --package-id <package_id> --store-root "$OPENCLAW_CURATOR_STORE"`
- Targeted: `python -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root "$OPENCLAW_CURATOR_STORE"`
- Targeted: release validation command for each generated release root, using the existing or newly added validator CLI.
- Full: build all five EgoHumans calibration releases, validate manifests/schema, and run a `vision-trainer` packaging/smoke command against each `dataset.yaml`.

### Verification evidence
- `python3 -m unittest` — 26 tests passed.
- `python3 -m compileall src tests` — passed.
- Validated all six staged package roots under `$OPENCLAW_RAW_PACKAGE_STORE/incoming`.
- Ingested all six staged package roots into `$OPENCLAW_CURATOR_STORE/indexes/packages.jsonl`.
- Scored all six packages: score counts were 147, 143, 156, 141, 106, and 99.
- Built review queues: hard-case 200, ambiguous 200, candidate-negative 0, random-audit 12.
- Built split artifact: `$OPENCLAW_CURATOR_STORE/oracle/egohumans/splits/split_assignments_v0.jsonl` with 95 rows, 33 sequence-time units, and 0 multi-split units.
- Built and curator-validated all releases under `$OPENCLAW_DATASET_RELEASE_STORE/calibration`:
  - `gold_only_v0`
  - `gold_plus_naive_pseudo_v0`
  - `gold_plus_trusted_tracks_v0`
  - `gold_plus_review_revealed_v1`
  - `oracle_upper_bound`
- `vision-trainer` validation passed for all five releases with `env PYTHONPATH=src python3 -m bootstrap_train.validate_packages --release <release_root>`.
- `vision-trainer` dry-run smoke command passed for all five releases with `env PYTHONPATH=src python3 -m bootstrap_train.train --config configs/train/curated_release_smoke.yaml --dataset-kind curated_release --dataset-root <release_root> --name <release_id>_smoke --dry-run`.

### Release counts
- `gold_only_v0`: train 567, val 904, test 1098 images; label sources `gold_seed_v0=574`, `oracle_eval=3066`.
- `gold_plus_naive_pseudo_v0`: train 3707, val 904, test 1098 images; label sources `gold_seed_v0=574`, `naive_confidence=4962`, `oracle_eval=3066`.
- `gold_plus_trusted_tracks_v0`: train 613, val 904, test 1098 images; label sources `gold_seed_v0=574`, `trusted_track=52`, `oracle_eval=3066`.
- `gold_plus_review_revealed_v1`: train 820, val 904, test 1098 images; label sources `gold_seed_v0=574`, `review_revealed_gold_v0=263`, `oracle_eval=3066`.
- `oracle_upper_bound`: train 3977, val 904, test 1098 images; label sources `oracle_upper_bound_train=5773`, `oracle_eval=3066`.

### User review checklist
- [ ] Confirm all realistic release policies forbid `oracle_hidden` for training.
- [ ] Confirm `oracle_upper_bound` is clearly marked diagnostic-only and is the only release allowed to train from full oracle labels.
- [ ] Confirm split assignments are frozen, clip/chunk based, and shared across all release families.
- [ ] Confirm trust/pseudo-label thresholds are documented with precision-first rationale.
- [ ] Confirm review-revealed labels come from selected review items, not a silent full-oracle dump.
- [ ] Confirm generated release manifests expose label namespaces, split policy, source package IDs, reveal sets, pseudo policy, and headroom flags.
- [ ] Confirm validation commands pass or any remaining blockers are explicitly documented.
- [ ] Confirm trainer handoff information includes release roots, `dataset.yaml` paths, and intended experiment interpretation.
- [ ] Confirm the Edge/desktop path portability follow-up is captured: desktop workflows must not require access to Edge-local absolute paths after package transfer.

### Risks / gotchas
- Oracle artifacts are allowed for evaluation and explicit reveal only; accidental use in pseudo selection is the highest-risk failure mode.
- Split assignment must avoid temporal/camera leakage; frame-random splits are not acceptable.
- Existing generic release builder may not express namespace policy cleanly; an EgoHumans-specific builder may be safer than overloading generic config too early.
- Parquet availability may affect score ingestion; keep optional dependency behavior compatible with current bring-up rules.
- Image materialization needs a stable policy: prefer deterministic extraction or links/copies that do not mutate package roots and are valid for trainer consumption.
- Review-revealed labels must be tied to selected queue items; do not simply dump all oracle labels into `gold_revealed`.
- `vision-trainer` requires `dataset.yaml` `names` as a multiline zero-indexed mapping and release `split_policy`/`label_policy` as manifest mappings.
- Source image paths in the imported oracle records point to edge-machine locations, so release materialization extracts frames from immutable `clip.mp4` files and caches them in the curator store.
- Running `vision-trainer` dry-runs materializes `.ultralytics_dataset.yaml` and `.ultralytics_splits/` inside each release root; these were removed after verification to keep release roots clean.
- Durable follow-up: update package contracts/design docs and validation so required curator inputs use package-relative or clip-relative paths; keep absolute Edge paths only as provenance/audit metadata.
- Interpretation caveat: `gold_plus_trusted_tracks_v0` is very sparse under the conservative trusted-track policy. Audit showed train has 626 objects while val/test have 1371/1695 oracle eval objects; document this in handoff notes and analyze non-test precision before relaxing thresholds.

### Decision rule for defaults
- Defaults should be conservative, precision-first, and auditable. If oracle validation reporting shows `trusted_full` precision below 95% on non-test calibration data, tighten class/box thresholds by 0.03-0.05 or add stricter track-length/jitter gates. If precision is at least 98% but pseudo-label volume is too small for a useful ablation, relax only non-oracle-test thresholds incrementally and document the change in `.agent/MEMORY.md`.

### Deferred work note
- This task does not train YOLO models, export TensorRT engines, promote models, mutate edge packages, or claim thermal-domain performance. EgoHumans results validate the curation machinery only; thermal deployment still needs a small thermal gold set.
