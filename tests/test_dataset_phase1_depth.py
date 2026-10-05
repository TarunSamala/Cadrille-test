"""Regression gates for the STL-1 Depth Anything V2 Phase 1 benchmark."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

import cv2
import numpy as np


class DatasetPhase1DepthTest(unittest.TestCase):
    root = Path.cwd()
    output = root / "dataset" / "phase_runs" / "v1" / "phase1_depth_anything_v2"

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads((cls.output / "report.json").read_text(encoding="utf-8"))

    @staticmethod
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_model_source_and_inputs_are_pinned(self) -> None:
        model = self.report["model"]
        self.assertEqual(model["id"], "depth-anything/Depth-Anything-V2-Small-hf")
        self.assertRegex(model["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(model["license"], "Apache-2.0")
        source = self.report["source"]
        self.assertRegex(source["commit"], r"^[0-9a-f]{40}$")
        for path_key, hash_key in (
            ("prepared_manifest", "prepared_manifest_sha256"),
            ("phase1_feature_report", "phase1_feature_report_sha256"),
            ("pipeline", "pipeline_sha256"),
        ):
            path = self.root / source[path_key]
            self.assertTrue(path.is_file())
            self.assertEqual(source[hash_key], self.sha256(path))

    def test_all_objects_and_views_have_readable_depth_evidence(self) -> None:
        coverage = self.report["coverage"]
        self.assertEqual(coverage["object_count"], 24)
        self.assertEqual(coverage["view_count"], 120)
        self.assertTrue(all(self.report["checks"].values()))
        self.assertEqual(len(self.report["objects"]), 24)
        seen = set()
        for item in self.report["objects"]:
            self.assertEqual(set(item["views"]), {"front", "top", "iso", "lsv", "rsv"})
            self.assertIsNotNone(cv2.imread(str(self.root / item["review_sheet"])))
            for view, record in item["views"].items():
                seen.add((item["object_id"], view))
                self.assertFalse(record["metric"])
                self.assertFalse(record["cross_view_aligned"])
                self.assertRegex(record["raw_float32_sha256"], r"^[0-9a-f]{64}$")
                for key in ("depth_u16", "uncertainty_u16"):
                    image = cv2.imread(
                        str(self.root / record[key]), cv2.IMREAD_UNCHANGED
                    )
                    self.assertIsNotNone(image)
                    self.assertEqual(image.shape, (768, 768))
                    self.assertEqual(image.dtype, np.uint16)
                self.assertGreaterEqual(record["mean_flip_error_over_depth_span"], 0)
                self.assertGreaterEqual(record["p95_flip_error_over_depth_span"], 0)
        self.assertEqual(len(seen), 120)

    def test_report_does_not_claim_depth_or_cad_accuracy(self) -> None:
        self.assertEqual(self.report["status"], "completed_research_only")
        self.assertEqual(self.report["decision"], "research_only")
        self.assertFalse(self.report["metrics"]["accuracy_metric"])
        gate = self.report["phase1_gate"]
        self.assertEqual(gate["status"], "blocked")
        for key in (
            "human_reviewed_masks",
            "reviewed_component_identities",
            "calibrated_cameras",
            "physical_scale",
            "metric_depth",
            "cross_view_consistent_depth",
        ):
            self.assertFalse(gate[key])
        limitations = " ".join(self.report["limitations"]).lower()
        self.assertIn("no human depth", limitations)
        self.assertIn("not accuracy", limitations)

    def test_gpu_runtime_and_summary_are_recorded(self) -> None:
        runtime = self.report["runtime"]
        self.assertEqual(runtime["device"], "cuda")
        self.assertGreater(runtime["total_seconds"], 0)
        self.assertGreater(runtime["peak_gpu_memory_bytes"], 0)
        overall = self.report["metrics"]["overall"]
        self.assertTrue(all(np.isfinite(value) for value in overall.values()))
        self.assertLessEqual(overall["median"], overall["p95"])
        self.assertLessEqual(overall["p95"], overall["max"])


if __name__ == "__main__":
    unittest.main()
