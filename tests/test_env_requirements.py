from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vision_curator.cli import main
from vision_curator.common.config import load_simple_config


class EnvRequirementTests(unittest.TestCase):
    def test_cli_without_store_root_prompts_for_openclaw_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "source ~/openclaw-env.sh"):
                main(["build-review-queue", "--queue-kind", "hard-case"])

    def test_config_expands_openclaw_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "release.yaml"
            config.write_text("release_store: ${OPENCLAW_DATASET_RELEASE_STORE}/pseudo_only\n", encoding="utf-8")
            with patch.dict(os.environ, {"OPENCLAW_DATASET_RELEASE_STORE": "/tmp/releases"}, clear=True):
                loaded = load_simple_config(config)
            self.assertEqual(loaded["release_store"], "/tmp/releases/pseudo_only")

    def test_config_with_missing_openclaw_env_prompts_for_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "release.yaml"
            config.write_text("release_store: ${OPENCLAW_DATASET_RELEASE_STORE}/pseudo_only\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(RuntimeError, "source ~/openclaw-env.sh"):
                    load_simple_config(config)


if __name__ == "__main__":
    unittest.main()
