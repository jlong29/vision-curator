# Annotation Policy

CVAT is the intended human annotation tool. `vision-curator` owns exchange packages, imported corrections, canonical curated labels, and provenance.

The bring-up milestone does not automate a live CVAT server.

## CVAT Bring-Up Boundary

`vision-curator` represents the handoff with local exchange folders:

```text
<curator_store>/
├─ annotation_exports/cvat/<task_id>/
│  ├─ manifest.json
│  └─ review_items.jsonl
└─ annotation_imports/cvat/<task_id>/
   ├─ manifest.json
   └─ corrected_annotations.jsonl
```

Export a review queue:

```bash
python -m vision_curator.cli export-cvat-task --queue <queue.jsonl> --store-root <curator_store> --task-id <task_id>
```

At this point Dr. Long labels the selected items in CVAT. The export manifest records `status: blocked_on_human_labeling` and names the expected import file, `corrected_annotations.jsonl`.

Import corrected annotations, or create a zero-count placeholder that marks the parser boundary while labeling is still pending:

```bash
python -m vision_curator.cli import-cvat-annotations --task-root <curator_store>/annotation_exports/cvat/<task_id> --store-root <curator_store>
```

Core tests and smoke workflows must not require a live CVAT server.
