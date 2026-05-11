from __future__ import annotations

import argparse
import json

from vision_curator.annotation.cvat_export import export_cvat_task
from vision_curator.annotation.cvat_import import import_cvat_annotations
from vision_curator.common.env import path_from_arg_or_env
from vision_curator.packages.ingest import ingest_package
from vision_curator.packages.validate import validate_phase2_package
from vision_curator.releases.build import build_release
from vision_curator.review.queues import build_review_queue
from vision_curator.scoring.trust import score_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vision-curator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-package")
    validate_parser.add_argument("--phase2", required=True)
    validate_parser.set_defaults(func=_validate_package)

    ingest_parser = subparsers.add_parser("ingest-package")
    ingest_parser.add_argument("--source", required=True)
    ingest_parser.add_argument("--store-root")
    ingest_parser.set_defaults(func=_ingest_package)

    score_parser = subparsers.add_parser("score-package")
    score_parser.add_argument("--package-id", required=True)
    score_parser.add_argument("--store-root")
    score_parser.set_defaults(func=_score_package)

    queue_parser = subparsers.add_parser("build-review-queue")
    queue_parser.add_argument("--queue-kind", required=True, choices=["hard-case", "ambiguous", "candidate-negative", "random-audit"])
    queue_parser.add_argument("--store-root")
    queue_parser.add_argument("--limit", type=int)
    queue_parser.set_defaults(func=_build_review_queue)

    release_parser = subparsers.add_parser("build-release")
    release_parser.add_argument("--config", required=True)
    release_parser.add_argument("--release-id", required=True)
    release_parser.set_defaults(func=_build_release)

    cvat_export_parser = subparsers.add_parser("export-cvat-task")
    cvat_export_parser.add_argument("--queue", required=True)
    cvat_export_parser.add_argument("--store-root")
    cvat_export_parser.add_argument("--task-id")
    cvat_export_parser.set_defaults(func=_export_cvat_task)

    cvat_import_parser = subparsers.add_parser("import-cvat-annotations")
    cvat_import_parser.add_argument("--task-root", required=True)
    cvat_import_parser.add_argument("--store-root")
    cvat_import_parser.set_defaults(func=_import_cvat_annotations)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


def _validate_package(args: argparse.Namespace) -> None:
    result = validate_phase2_package(args.phase2)
    print(json.dumps({"status": "ok", "package_id": result["package_id"], "clip_count": len(result["clips"])}, sort_keys=True))


def _ingest_package(args: argparse.Namespace) -> None:
    store_root = path_from_arg_or_env(args.store_root, "OPENCLAW_CURATOR_STORE")
    record = ingest_package(args.source, store_root)
    print(json.dumps(record.to_dict(), sort_keys=True))


def _score_package(args: argparse.Namespace) -> None:
    store_root = path_from_arg_or_env(args.store_root, "OPENCLAW_CURATOR_STORE")
    scores = score_package(args.package_id, store_root)
    output = store_root / "scores" / args.package_id / "track_scores.parquet"
    print(json.dumps({"package_id": args.package_id, "score_count": len(scores), "output": str(output)}, sort_keys=True))


def _build_review_queue(args: argparse.Namespace) -> None:
    store_root = path_from_arg_or_env(args.store_root, "OPENCLAW_CURATOR_STORE")
    queue_id, output, items = build_review_queue(args.queue_kind, store_root, args.limit)
    print(json.dumps({"queue_id": queue_id, "item_count": len(items), "output": str(output)}, sort_keys=True))


def _build_release(args: argparse.Namespace) -> None:
    release_root = build_release(args.config, args.release_id)
    print(json.dumps({"release_id": args.release_id, "release_root": str(release_root)}, sort_keys=True))


def _export_cvat_task(args: argparse.Namespace) -> None:
    store_root = path_from_arg_or_env(args.store_root, "OPENCLAW_CURATOR_STORE")
    task_root = export_cvat_task(args.queue, store_root, args.task_id)
    print(json.dumps({"task_root": str(task_root)}, sort_keys=True))


def _import_cvat_annotations(args: argparse.Namespace) -> None:
    store_root = path_from_arg_or_env(args.store_root, "OPENCLAW_CURATOR_STORE")
    import_root = import_cvat_annotations(args.task_root, store_root)
    print(json.dumps({"import_root": str(import_root)}, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
