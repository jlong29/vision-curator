# Review Queues

Supported initial queue kinds:

- `hard-case`
- `ambiguous`
- `candidate-negative`
- `random-audit`

Queues are written as JSONL files under `<curator_store>/review_queues/`.

Each review item preserves `package_id`, `clip_id`, `track_id`, `source_path`, `clip_path`, `run_id`, `decision_bucket`, `priority`, and provenance when available.

Initial ordering semantics:

- `hard-case`: likely person tracks with weak geometry first.
- `ambiguous`: highest review priority first, then class trust closest to the uncertain boundary.
- `candidate-negative`: highest review priority first.
- `random-audit`: deterministic low-volume sample from trusted positives and rejects.
