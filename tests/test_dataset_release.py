from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vision_curator.common.manifests import read_jsonl
from vision_curator.releases.build import build_release
from vision_curator.releases.validate import validate_release


SOURCE = Path(__file__).resolve().parent / "fixtures" / "release_source"


class DatasetReleaseTests(unittest.TestCase):
    def test_release_builder_writes_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "release.yaml"
            config.write_text(
                "\n".join(
                    [
                        f"release_store: {Path(tmp) / 'releases'}",
                        f"source_root: {SOURCE}",
                        "source_package_ids: [fixture_phase2_001]",
                        "annotation_versions: [fixture]",
                        "annotation_status: pseudo_only",
                        "split_policy: deterministic_filename_order",
                        "label_policy: curated_yolo",
                        "class_list: [person]",
                        "source_package_provenance:",
                        "  fixture_phase2_001:",
                        "    run_id: fixture_run_001",
                        "    source_node_id: fixture_nx_001",
                    ]
                ),
                encoding="utf-8",
            )
            release_root = build_release(config, "release_001")
            validate_release(release_root)
            manifest = json.loads((release_root / "manifest.json").read_text(encoding="utf-8"))
            source_packages = read_jsonl(release_root / "provenance" / "source_packages.jsonl")
            self.assertEqual(manifest["release_id"], "release_001")
            self.assertEqual(manifest["annotation_status"], "pseudo_only")
            self.assertTrue(manifest["extra"]["pseudo_only"])
            self.assertEqual(manifest["source_packages"][0]["run_id"], "fixture_run_001")
            self.assertEqual(source_packages, manifest["source_packages"])
            self.assertEqual(manifest["counts_by_split"]["train"], 1)
            with self.assertRaises(FileExistsError):
                build_release(config, "release_001")


if __name__ == "__main__":
    unittest.main()
