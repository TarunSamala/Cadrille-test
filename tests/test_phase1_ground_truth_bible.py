"""Bible Phase 1 checks for Ring01 review and depth proposals."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

import cv2
import numpy as np


class Phase1GroundTruthBibleTest(unittest.TestCase):
    root = Path.cwd()
    workspace = root / "data" / "ring01_ground_truth_v1"

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (cls.workspace / "manifest.json").read_text(encoding="utf-8")
        )
        cls.depth = json.loads(
            (cls.workspace / "depth_anything_v2" / "depth_metadata.json").read_text(
                encoding="utf-8"
            )
        )

    @staticmethod
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_ground_truth_gate_is_honestly_blocked(self) -> None:
        self.assertEqual(self.manifest["status"], "human_review_required")
        gate = self.manifest["exit_gate"]
        self.assertEqual(gate["status"], "blocked")
        self.assertFalse(gate["human_ground_truth_complete"])
        self.assertTrue(gate["physical_scale_missing"])
        self.assertEqual(len(gate["pending_label_reviews"]), 35)
        self.assertEqual(len(gate["pending_component_identities"]), 7)
        self.assertEqual(len(gate["pending_camera_records"]), 5)

    def test_all_five_views_have_binary_review_proposals(self) -> None:
        self.assertEqual(
            set(self.manifest["views"]), {"front", "side", "top", "angled", "back"}
        )
        for record in self.manifest["views"].values():
            source = cv2.imread(str(self.root / record["source"]["path"]))
            self.assertIsNotNone(source)
            for proposal in record["proposals"].values():
                path = self.root / proposal["path"]
                mask = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
                self.assertIsNotNone(mask)
                self.assertEqual(mask.shape[:2], source.shape[:2])
                self.assertTrue(set(np.unique(mask)).issubset({0, 255}))
                self.assertEqual(proposal["sha256"], self.sha256(path))
                self.assertEqual(proposal["authority"], "machine_proposal")

    def test_component_ids_and_review_sheets_exist(self) -> None:
        component_ids = [
            item["component_id"] for item in self.manifest["component_catalog"]
        ]
        self.assertEqual(len(component_ids), len(set(component_ids)))
        self.assertEqual(component_ids.count("stone_001"), 1)
        self.assertEqual(sum(item.startswith("prong_") for item in component_ids), 4)
        for record in self.manifest["views"].values():
            self.assertIsNotNone(cv2.imread(str(self.root / record["review_sheet"])))
        self.assertIsNotNone(
            cv2.imread(str(self.root / self.manifest["review_summary"]))
        )

    def test_depth_anything_output_is_complete_but_non_metric(self) -> None:
        model = self.depth["model"]
        self.assertEqual(model["id"], "depth-anything/Depth-Anything-V2-Small-hf")
        self.assertRegex(model["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(model["license"], "Apache-2.0")
        self.assertEqual(self.depth["device"], "cuda")
        self.assertGreater(self.depth["peak_gpu_memory_bytes"], 0)
        self.assertEqual(self.depth["decision"], "research_only")
        self.assertEqual(set(self.depth["views"]), set(self.manifest["views"]))
        for view, record in self.depth["views"].items():
            self.assertFalse(record["metric"])
            self.assertFalse(record["cross_view_aligned"])
            source_shape = tuple(
                reversed(self.manifest["views"][view]["source"]["size_wh"])
            )
            raw_path = self.root / record["raw_float32_npy"]
            raw = np.load(raw_path)
            self.assertEqual(raw.shape, source_shape)
            self.assertTrue(np.isfinite(raw).all())
            self.assertEqual(record["raw_sha256"], self.sha256(raw_path))
            preview = cv2.imread(str(self.root / record["preview"]))
            uncertainty = cv2.imread(
                str(self.root / record["uncertainty_u16"]), cv2.IMREAD_UNCHANGED
            )
            self.assertEqual(preview.shape[:2], source_shape)
            self.assertEqual(uncertainty.dtype, np.uint16)
        self.assertIsNotNone(
            cv2.imread(str(self.root / self.depth["review_summary"]))
        )

    def test_depth_environment_and_checkpoint_are_pinned(self) -> None:
        requirements = (
            self.root / "requirements-depth.txt"
        ).read_text(encoding="utf-8").splitlines()
        fixed = [line for line in requirements if line and not line.startswith("#")]
        self.assertTrue(
            all(re.match(r"^[A-Za-z0-9_.-]+==[^=<>~]+$", line) for line in fixed)
        )
        dockerfile = (self.root / "Dockerfile.phase1-depth").read_text(
            encoding="utf-8"
        )
        self.assertIn("FROM image2cad-validation:phase0", dockerfile)
        source = (
            self.root / "pipeline" / "infer_depth_anything_v2.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'MODEL_REVISION = "5426e4f0f36572d16453bbda7a8389317b1bef99"',
            source,
        )


if __name__ == "__main__":
    unittest.main()
