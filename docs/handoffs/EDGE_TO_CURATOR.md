# Edge to Curator Handoff

`thermal-data-engine` hands off completed Phase 2 package roots. `vision-curator` treats those package roots as immutable inputs and records source paths plus provenance in its curator store.

For generic Phase 2 packages, each root must contain `manifest.json`, `clips/`, and required clip files. For EgoHumans calibration packages, the root must also preserve source-frame mapping metadata described in `docs/package_contracts.md` and `docs/EGOHUMANS_EDGE_NODE_PROCESSING_PROPOSAL.md`.

Desktop acceptance commands:

```bash
env PYTHONPATH=src python3 -m vision_curator.cli validate-package --phase2 <phase2_package>
env PYTHONPATH=src python3 -m vision_curator.cli ingest-package --source <phase2_package> --store-root <curator_store>
env PYTHONPATH=src python3 -m vision_curator.cli score-package --package-id <package_id> --store-root <curator_store>
```

Ground-truth labels must not be included in edge pseudo-label packages. For EgoHumans, ground truth is imported separately on the desktop as hidden oracle data.
