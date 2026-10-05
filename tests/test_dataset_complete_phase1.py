"""Regression gates for complete STL-1 Phase 1 pixel and depth evidence."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import cv2
import numpy as np


class DatasetCompletePhase1Test(unittest.TestCase):
    root = Path.cwd()
    output = (
        root / "dataset" / "phase_runs" / "v1" / "phase1_complete_features_v1"
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads((cls.output / "report.json").read_text(encoding="utf-8"))

    @staticmethod
    def array_sha256(values: np.ndarray) -> str:
        return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()

    def test_all_objects_views_and_three_runs_pass(self) -> None:
        self.assertEqual(self.report["coverage"]["object_count"], 24)
        self.assertEqual(self.report["coverage"]["view_count"], 120)
        self.assertEqual(
            self.report["coverage"]["view_order"],
            ["front", "top", "iso", "lsv", "rsv"],
        )
        self.assertTrue(all(self.report["checks"].values()))
        self.assertEqual(len(self.report["objects"]), 24)
        views = []
        for item in self.report["objects"]:
            self.assertEqual(set(item["views"]), {"front", "top", "iso", "lsv", "rsv"})
            for view, record in item["views"].items():
                views.append((item["object_id"], view))
                self.assertEqual(record["repeat_count"], 3)
                self.assertTrue(record["repeat_deterministic"])
                self.assertEqual(len(set(record["repeat_raw_sha256"])), 1)
                self.assertEqual(record["repeat_max_abs_difference"], [0.0, 0.0])
                self.assertFalse(record["view_contract"]["camera_pose_known"])
        self.assertEqual(len(views), 120)

    def test_feature_contract_is_pixel_level_and_honest(self) -> None:
        contract = self.report["feature_contract"]
        self.assertEqual(contract["stored_array_count_per_view"], 22)
        self.assertIn("source_rgb_u8", contract["lossless_pixels"])
        self.assertIn("gradient_magnitude_f32", contract["differential_geometry"])
        self.assertIn("relative_depth_raw_f32", contract["relative_depth"])
        self.assertIn("individual_stones", contract["unavailable_component_truth"])
        reconstruction = self.report["reconstruction_contract"]
        self.assertTrue(reconstruction["source_pixel_roundtrip_exact"])
        self.assertTrue(reconstruction["normalized_pixels_retained_exactly"])
        self.assertFalse(reconstruction["semantic_features_alone_reconstruct_exact_rgb"])

    def test_metric_and_cross_view_geometry_are_not_claimed(self) -> None:
        self.assertEqual(self.report["status"], "completed_research_only")
        self.assertEqual(self.report["decision"], "research_only")
        self.assertEqual(self.report["metric_depth"]["status"], "blocked")
        self.assertIsNone(self.report["metric_depth"]["unit"])
        self.assertIn(
            "blocked",
            self.report["depth_validation"]["cross_view_geometry"],
        )
        for item in self.report["objects"]:
            for record in item["views"].values():
                self.assertFalse(record["metric"])
                self.assertFalse(record["cross_view_aligned"])

    def test_depth_bias_and_flip_diagnostics_are_finite(self) -> None:
        validation = self.report["depth_validation"]
        self.assertTrue(validation["all_repeats_identical"])
        for name in ("horizontal_flip_error", "vertical_flip_error"):
            self.assertTrue(
                all(np.isfinite(value) for value in validation[name].values())
            )
        self.assertGreater(validation["vertical_flip_error"]["mean"], 0)
        for view in ("front", "top", "iso", "lsv", "rsv"):
            values = validation["top_bottom_absolute_bias_by_view"][view]
            self.assertTrue(np.isfinite(values["raw"]["mean"]))
            self.assertTrue(np.isfinite(values["regularized"]["mean"]))
        self.assertNotIn("improved", json.dumps(validation).lower())

    def test_versioned_audits_and_overview_are_readable(self) -> None:
        overview = cv2.imread(str(self.root / self.report["overview"]))
        self.assertIsNotNone(overview)
        self.assertGreater(overview.shape[0], 500)
        for item in self.report["objects"]:
            audit = cv2.imread(str(self.root / item["audit_sheet"]))
            self.assertIsNotNone(audit, item["object_id"])
            self.assertGreater(audit.shape[0], 500)

    def test_local_matrix_cache_matches_hash_manifest_when_present(self) -> None:
        sample_ids = {"ring_001", "ring_007", "ring_024"}
        checked = 0
        for item in self.report["objects"]:
            if item["object_id"] not in sample_ids:
                continue
            for record in item["views"].values():
                bundle = self.root / record["bundle"]
                if not bundle.is_file():
                    continue
                with np.load(bundle) as arrays:
                    self.assertEqual(len(arrays.files), 22)
                    self.assertEqual(arrays["normalized_rgb_u8"].shape, (768, 768, 3))
                    self.assertEqual(
                        self.array_sha256(arrays["source_rgb_u8"]),
                        record["features"]["source_rgb_u8"]["sha256"],
                    )
                    self.assertEqual(
                        self.array_sha256(arrays["relative_depth_raw_f32"]),
                        record["features"]["relative_depth_raw_f32"]["sha256"],
                    )
                checked += 1
        if checked == 0:
            self.skipTest("reproducible local NPZ matrix cache is not present")
        self.assertEqual(checked, 15)


if __name__ == "__main__":
    unittest.main()
