# Architecture

`vision-curator` sits between edge package production and model training.

- `thermal-data-engine` produces immutable Phase 2 clip packages.
- `vision-curator` validates, indexes, scores, queues, and releases curated datasets.
- `vision-trainer` consumes immutable dataset releases.

CVAT and FiftyOne are optional integrations. Core validation, scoring, queue generation, and release building must run without them.
