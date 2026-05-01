from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from vision_curator.common.config import load_simple_config
from vision_curator.common.manifests import write_json, write_jsonl
from vision_curator.common.models import DatasetReleaseManifest


def build_release(config_path: str | Path, release_id: str) -> Path:
    config = load_simple_config(config_path)
    release_store = Path(str(config.get("release_store", "releases")))
    release_root = release_store / release_id
    if release_root.exists():
        raise FileExistsError(f"Dataset release already exists and will not be overwritten: {release_root}")

    images_dir = release_root / "images"
    labels_dir = release_root / "labels"
    splits_dir = release_root / "splits"
    provenance_dir = release_root / "provenance"
    for directory in (images_dir, labels_dir, splits_dir, provenance_dir):
        directory.mkdir(parents=True, exist_ok=False)

    source_root = Path(str(config.get("source_root", ""))) if config.get("source_root") else None
    images = _copy_tree_files(source_root / "images", images_dir) if source_root else []
    _copy_tree_files(source_root / "labels", labels_dir) if source_root else []

    split_map = _split_images(images)
    for split, split_images in split_map.items():
        split_file = splits_dir / f"{split}.txt"
        split_file.write_text("".join(f"images/{image.name}\n" for image in split_images), encoding="utf-8")

    class_list = [str(item) for item in config.get("class_list", ["person"])]
    dataset_yaml = _dataset_yaml(release_root, class_list)
    (release_root / "dataset.yaml").write_text(dataset_yaml, encoding="utf-8")
    source_packages = _source_package_records(config)
    annotation_status = str(config.get("annotation_status", "unknown"))

    manifest = DatasetReleaseManifest(
        release_id=release_id,
        source_package_ids=[str(item) for item in config.get("source_package_ids", [])],
        source_packages=source_packages,
        annotation_versions=[str(item) for item in config.get("annotation_versions", ["fixture"])],
        annotation_status=annotation_status,
        split_policy=str(config.get("split_policy", "deterministic_filename_order")),
        label_policy=str(config.get("label_policy", "curated_yolo")),
        class_list=class_list,
        counts_by_split={split: len(paths) for split, paths in split_map.items()},
        counts_by_label_source={str(config.get("label_policy", "curated_yolo")): len(images)},
        created_at=datetime.now(timezone.utc).isoformat(),
        extra={
            "pseudo_only": annotation_status == "pseudo_only",
        },
    )
    write_json(release_root / "manifest.json", manifest.to_dict())
    write_json(provenance_dir / "build_config.json", config)
    write_jsonl(provenance_dir / "source_packages.jsonl", source_packages)
    return release_root


def _copy_tree_files(source: Path, destination: Path) -> list[Path]:
    if not source.exists():
        return []
    copied: list[Path] = []
    for path in sorted(source.iterdir()):
        if not path.is_file():
            continue
        target = destination / path.name
        shutil.copy2(path, target)
        copied.append(target)
    return copied


def _split_images(images: list[Path]) -> dict[str, list[Path]]:
    if not images:
        return {"train": [], "val": [], "test": []}
    train: list[Path] = []
    val: list[Path] = []
    test: list[Path] = []
    for index, image in enumerate(sorted(images, key=lambda item: item.name)):
        if index % 10 == 8:
            val.append(image)
        elif index % 10 == 9:
            test.append(image)
        else:
            train.append(image)
    return {"train": train, "val": val, "test": test}


def _source_package_records(config: dict) -> list[dict]:
    provenance = config.get("source_package_provenance", {})
    if not isinstance(provenance, dict):
        provenance = {}

    records: list[dict] = []
    for package_id in [str(item) for item in config.get("source_package_ids", [])]:
        record = {"package_id": package_id}
        package_provenance = provenance.get(package_id, {})
        if isinstance(package_provenance, dict):
            record.update(package_provenance)
        records.append(record)
    return records


def _dataset_yaml(release_root: Path, class_list: list[str]) -> str:
    names = ", ".join(f"{index}: {name}" for index, name in enumerate(class_list))
    return (
        f"path: {release_root}\n"
        "train: splits/train.txt\n"
        "val: splits/val.txt\n"
        "test: splits/test.txt\n"
        f"names: {{{names}}}\n"
    )
