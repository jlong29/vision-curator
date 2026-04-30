# vision-curator

Desktop-side curation and annotation tools for the thermal person detection bootstrap pipeline.

`vision-curator` consumes Phase 2 edge packages from `thermal-data-engine`, validates and indexes them, scores pseudo-label trust, builds human review queues, and emits immutable dataset releases for `vision-trainer`.

## Quick Start

```bash
python -m pip install -e .
python -m unittest
```

Validate and ingest a Phase 2 package:

```bash
python -m vision_curator.cli validate-package --phase2 /path/to/phase2_package
python -m vision_curator.cli ingest-package --source /path/to/phase2_package --store-root /data/openclaw/curator
```

Score and build a review queue:

```bash
python -m vision_curator.cli score-package --package-id <package_id> --store-root /data/openclaw/curator
python -m vision_curator.cli build-review-queue --queue-kind hard-case --store-root /data/openclaw/curator
```

Build a tiny dataset release:

```bash
python -m vision_curator.cli build-release --config configs/release/default.yaml --release-id <release_id>
```

CVAT and FiftyOne are intentionally optional during bring-up.
