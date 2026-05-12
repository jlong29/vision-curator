# EgoHumans Oracle Import Task Spec

## Purpose
Define the next `vision-curator` task after Codex is restarted with updated sandbox access.

The task is to build the desktop-side hidden-oracle workflow for EgoHumans Lego Assembly calibration. It must keep the Edge Node's pseudo-label packages separate from EgoHumans ground truth while enabling calibration reports, simulated review reveal, and curated release generation.

## Ownership Decision
This work belongs in `vision-curator`, not on the Edge Node.

Reason:
- The Edge Node has already done its correct job: process EgoHumans as unlabeled video, run teacher inference and ByteTrack, preserve frame maps, and emit Phase 2 packages.
- Ground truth must not be used on the Edge Node during pseudo-label generation.
- Hidden oracle labels, reveal sets, trust calibration, and curated releases are desktop curation responsibilities.

## Required Sandbox Access
After restarting Codex, validate these roots before implementation:

Writable:
- `/media/jdl2/DATAPART/YOLO-Data/openclaw`

Read-only:
- `/media/jdl2/DATAPART/YOLO-Data/datasets/egohumans`
- `/home/jdl2/Git/vision-ai/vision_api`
- `/home/jdl2/Git/vision-ai/thermal-data-engine`

The read-only roots are source/reference material by policy. Do not edit, generate files in, or clean files from those paths.

## Phase 1: Sandbox and Input Validation
Run only read-oriented checks except for a tiny write probe under `$OPENCLAW_CURATOR_STORE`.

Suggested checks:

```bash
source ~/openclaw-env.sh

test -d "$OPENCLAW_DATA_ROOT"
test -d "$OPENCLAW_CURATOR_STORE"
test -d /media/jdl2/DATAPART/YOLO-Data/datasets/egohumans
test -d /home/jdl2/Git/vision-ai/vision_api
test -d /home/jdl2/Git/vision-ai/thermal-data-engine

python3 - <<'PY'
from pathlib import Path

paths = [
    Path("/media/jdl2/DATAPART/YOLO-Data/datasets/egohumans"),
    Path("/home/jdl2/Git/vision-ai/vision_api"),
    Path("/home/jdl2/Git/vision-ai/thermal-data-engine"),
]
for path in paths:
    print(path, "readable=", path.is_dir())
PY

mkdir -p "$OPENCLAW_CURATOR_STORE/oracle/egohumans/.write_probe"
rmdir "$OPENCLAW_CURATOR_STORE/oracle/egohumans/.write_probe"
```

Then inspect a small sample of:
- Edge Phase 2 `manifest.json`
- each `clip_manifest.json`
- first lines of each `source_frames.jsonl`
- detection and track table schemas
- EgoHumans annotation/pose files for the relevant Lego Assembly sequence
- `vision_api` EgoHumans conversion scripts
- `thermal-data-engine` Phase 2 package writer/manifest code if package semantics are unclear

Do not bulk traverse the full dataset. Use targeted `find -maxdepth`, `rg`, and small file samples.

## Inputs
The task needs these inputs:

- Edge Phase 2 package root, for example:
  - `$OPENCLAW_RAW_PACKAGE_STORE/phase2/egohumans/<package_id>/`
- EgoHumans source dataset root:
  - `/media/jdl2/DATAPART/YOLO-Data/datasets/egohumans`
- Reference implementation:
  - `/home/jdl2/Git/vision-ai/vision_api`
  - `/home/jdl2/Git/vision-ai/thermal-data-engine`

Known package shape:

```text
<phase2_root>/
├─ manifest.json
├─ READY.json
└─ clips/
   ├─ <sequence>__aria01/
   │  ├─ clip_manifest.json
   │  ├─ clip.mp4
   │  ├─ detections.parquet
   │  ├─ source_frames.jsonl
   │  └─ tracks.parquet
   ├─ <sequence>__aria02/
   └─ <sequence>__aria03/
```

## Output Contract
Write OpenClaw-owned oracle artifacts under:

```text
$OPENCLAW_CURATOR_STORE/oracle/egohumans/
├─ source_dataset_manifest.json
├─ normalized/
│  ├─ oracle_labels.jsonl
│  ├─ frame_index.jsonl
│  └─ class_map.json
├─ reveal_sets/
│  ├─ gold_seed_v0.jsonl
│  ├─ review_revealed_gold_v0.jsonl
│  └─ gold_negatives_v0.jsonl
└─ evaluation/
   └─ metrics_inputs/
```

`source_dataset_manifest.json` must record:
- canonical dataset root
- source tarball or extracted sequence identity when known
- reference repo/script versions or commit SHAs when available
- EgoHumans sequence/activity/camera IDs
- label semantics statement
- provenance that these labels are benchmark-semantics proxy oracle labels when applicable

`oracle_labels.jsonl` should contain one normalized object per visible person box:
- `label_namespace: "oracle_hidden"`
- `dataset_source: "egohumans"`
- `activity: "lego_assembly"`
- `sequence_id`
- `camera_id`
- `source_frame_idx`
- `source_image_path_or_name`
- `class_name: "person"`
- `box_xyxy`
- `box_source`
- `visibility_or_keypoint_metadata` when available
- `provenance`

`frame_index.jsonl` should map Edge package frames to source identity:
- `package_id`
- `package_clip_id`
- `frame_idx`
- `source_sequence_id`
- `source_camera_id`
- `source_frame_idx`
- `source_image_path_or_name`

Reveal sets must contain `label_namespace: "gold_revealed"` and reference the corresponding `oracle_hidden` record IDs. They are not copies of global training truth; they simulate labels a human would have revealed through seed selection or review.

## Label Namespace Rules
Preserve exactly three namespaces:

- `oracle_hidden`
  - Full EgoHumans oracle/proxy labels.
  - Evaluation, calibration analysis, and simulated reveal only.
  - Never used by trust scoring.

- `gold_revealed`
  - Small controlled subset copied/revealed from oracle labels.
  - Simulates human-created labels.
  - Eligible for gold-only and gold-plus-pseudo releases.

- `pseudo_teacher`
  - Edge detector and ByteTrack outputs.
  - Used for trust scoring, queue generation, and pseudo-label releases.

Never silently mix these namespaces.

## Label Semantics
Follow `docs/EGOHUMANS_LEGO_WORKING_SPEC.md` and the `vision_api` implementation:

- Use upstream benchmark-style semantics as closely as possible.
- Exclude viewer/self labels.
- Honor sequence config rules such as `INVALID_ARIAS`.
- For current local tarballs, upstream COCO benchmark JSON may be absent.
- If canonical benchmark labels are unavailable, derive proxy oracle boxes from aligned `processed_data/poses2d/...` visible keypoints using the benchmark-style pose-to-box rule.
- Do not treat raw `processed_data/bboxes/...` as canonical ground truth.
- Document clearly when outputs are proxy benchmark-semantics oracle labels rather than byte-for-byte upstream benchmark labels.

## Split and Gold Set Policy
Use `docs/EGOHUMANS_VISION_CURATOR_GOLDSET_PROPOSAL.md` as the policy reference.

Required split concepts:
- `oracle_test_hidden`: frozen hidden test clips, not used for training, threshold tuning, or active selection.
- `oracle_val_hidden`: hidden validation clips used for calibration reporting/model selection.
- `gold_seed_pool`: small revealed seed set.
- `unlabeled_pool`: remaining clips; oracle stays hidden unless selected for simulated review.

Split by clip or sequence chunk, not random frame, to avoid temporal leakage.

If multiple ego cameras/views represent near-identical simultaneous moments, avoid placing those near-identical views across train/test unless explicitly testing camera-view generalization.

Gold seed `v0` should include:
- easy true positives
- hard positives
- false-positive-prone clutter/background cases
- localization-hard cases
- multi-person interaction/occlusion cases
- edge-of-frame/truncated body cases
- normal positives, not only hardest failures

## Review Simulation Policy
Simulated review must follow the production order:

1. Build queues from pseudo-label metadata only.
2. Select review items from trust score, ambiguity, novelty, and audit sampling.
3. Reveal EgoHumans oracle labels only after selection.
4. Store revealed labels as `gold_revealed`.

## Calibration Outputs
The importer should enable later reports that compare teacher pseudo labels to oracle labels:

- pseudo precision for `trusted_full`
- matched IoU distributions
- missing-neighbor rate
- review queue yield
- hard-case tags:
  - `teacher_false_negative`
  - `teacher_false_positive`
  - `poor_localization`
  - `id_switch_or_fragmentation`
  - `occlusion`
  - `small_person`
  - `edge_truncated`
  - `multi_person_overlap`
  - `motion_blur_or_egomotion`

Initial bucket targets:
- `trusted_full`: precision >= 95%, preferably >= 98%; median matched IoU >= 0.75.
- `candidate_negative`: use only after oracle/human confirmation.
- `discard`: sample a tiny fraction for random audits.

## Release Families Enabled Later
The oracle/reveal workflow should support these release families:

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`
- `oracle_upper_bound`

`oracle_upper_bound` is the only release allowed to train from full `oracle_hidden` labels, and it must be marked as an upper-bound comparison outside the realistic loop.

## Headroom Reference Calibration
The calibration plan must include an explicit headroom reference experiment.

Because EgoHumans Lego Assembly has complete oracle labels, publish an `oracle_upper_bound` release that trains from the full oracle label set and evaluate it against the same hidden validation/test definitions used for the realistic runs. Compare this result to:

- `gold_only_v0`
- `gold_plus_naive_pseudo_v0`
- `gold_plus_trusted_tracks_v0`
- `gold_plus_review_revealed_v1`

The difference between the oracle-trained result and the iterative teacher-student results is the headroom left for the curation loop. This reference is diagnostic only. It must not be used for trust threshold tuning, review selection, pseudo-label acceptance, or any claim about the realistic semi-supervised workflow.

Implementation implications:
- `source_dataset_manifest.json` and release manifests must clearly mark `oracle_upper_bound` as a complete-oracle training release.
- `oracle_upper_bound` may read from `oracle_hidden`; other realistic releases may only use `gold_revealed` and `pseudo_teacher`.
- Metrics reports should show the oracle headroom gap separately from ordinary validation metrics.

## Implementation Plan
1. Validate sandbox and input paths after Codex restart.
2. Read package manifests and frame maps.
3. Inspect `vision_api` EgoHumans conversion logic and identify the pose-to-box rule.
4. Implement a small `vision_curator.oracle.egohumans` module.
5. Add CLI command or subcommand for oracle import, likely:
   - `import-egohumans-oracle --phase2 <package_root> --dataset-root <egohumans_root> --store-root <curator_store>`
6. Normalize oracle labels and frame index into `$OPENCLAW_CURATOR_STORE/oracle/egohumans/normalized/`.
7. Add deterministic split/reveal-set generation.
8. Add tiny fixtures and unit tests.
9. Run an end-to-end smoke on one real package with small sampled outputs.

## Verification
Minimum:

```bash
python3 -m unittest
env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <egohumans_phase2_package>
env PYTHONPATH=src python3 -m vision_curator.cli import-egohumans-oracle --phase2 <egohumans_phase2_package> --dataset-root /media/jdl2/DATAPART/YOLO-Data/datasets/egohumans
```

Expected smoke outputs:
- `source_dataset_manifest.json`
- non-empty `normalized/frame_index.jsonl`
- non-empty `normalized/oracle_labels.jsonl` if labels exist for sampled frames
- deterministic reveal-set files

## Open Questions for Phase 1
- What is the exact canonical local path for the Phase 2 package to process first?
- Are EgoHumans source files extracted under `/media/jdl2/DATAPART/YOLO-Data/datasets/egohumans`, or are tarballs still the main source?
- Which sequence should be first: `001_legoassemble`, `005_legoassemble`, or both?
- Should `aria02` be included in the first calibration split, or held as a separate camera-view/generalization check?
