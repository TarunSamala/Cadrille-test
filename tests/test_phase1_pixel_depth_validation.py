"""Strict gates for Ring01 pixel features and repeated depth validation."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import cv2
import numpy as np


class Phase1PixelDepthValidationTest(unittest.TestCase):
    root = Path.cwd()
    workspace = root / "data" / "ring01_ground_truth_v1"

    @classmethod
    def setUpClass(cls) -> None:
        cls.depth = json.loads(
            (cls.workspace / "depth_validation_v1" / "report.json").read_text(
                encoding="utf-8"
            )
        )
        cls.features = json.loads(
            (cls.workspace / "pixel_features_v1" / "report.json").read_text(
                encoding="utf-8"
            )
        )

    @staticmethod
    def array_sha256(values: np.ndarray) -> str:
        return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()

    def test_three_runs_are_identical_for_every_view(self) -> None:
        self.assertTrue(all(self.depth["checks"].values()))
        self.assertEqual(set(self.depth["views"]), {"front", "side", "top", "angled", "back"})
        for record in self.depth["views"].values():
            self.assertEqual(record["repeat_count"], 3)
            self.assertTrue(record["repeat_deterministic"])
            self.assertEqual(len(record["repeat_raw_sha256"]), 3)
            self.assertEqual(len(set(record["repeat_raw_sha256"])), 1)
            self.assertEqual(record["repeat_max_abs_difference"], [0.0, 0.0])

    def test_front_vertical_bias_is_measured_and_only_partially_reduced(self) -> None:
        front = self.depth["views"]["front"]
        raw_object = abs(
            front["whole_object_distribution"]["top_minus_bottom_mean"]
        )
        corrected_object = abs(
            front["regularized_whole_object_distribution"][
                "top_minus_bottom_mean"
            ]
        )
        raw_stone = abs(front["stone_distribution"]["top_minus_bottom_mean"])
        corrected_stone = abs(
            front["regularized_stone_distribution"]["top_minus_bottom_mean"]
        )
        self.assertGreater(raw_object, 0.08)
        self.assertGreater(raw_stone, 0.17)
        self.assertLess(corrected_object, raw_object)
        self.assertLess(corrected_stone, raw_stone)
        self.assertGreater(corrected_stone, 0.10)
        self.assertGreater(
            front["vertical_flip_error_over_depth_span"],
            front["horizontal_flip_error_over_depth_span"],
        )

    def test_metric_depth_and_camera_pose_remain_blocked(self) -> None:
        metric = self.depth["metric_depth"]
        self.assertEqual(metric["status"], "blocked")
        self.assertIsNone(metric["unit"])
        self.assertIsNone(metric["millimetres_per_depth_unit"])
        for record in self.depth["views"].values():
            self.assertFalse(record["metric"])
            self.assertFalse(record["cross_view_aligned"])
            self.assertFalse(record["view_contract"]["camera_pose_known"])

    def test_feature_bundles_roundtrip_every_source_pixel_exactly(self) -> None:
        self.assertEqual(self.features["view_count"], 5)
        self.assertTrue(
            self.features["reconstruction_contract"]["pixel_exact_roundtrip"]
        )
        self.assertFalse(
            self.features["reconstruction_contract"][
                "semantic_features_alone_reconstruct_exact_rgb"
            ]
        )
        for view, record in self.features["views"].items():
            self.assertTrue(record["pixel_roundtrip_exact"])
            source = cv2.cvtColor(
                cv2.imread(str(self.root / record["source"])), cv2.COLOR_BGR2RGB
            )
            reconstructed = cv2.cvtColor(
                cv2.imread(str(self.root / record["reconstructed_image"])),
                cv2.COLOR_BGR2RGB,
            )
            self.assertTrue(np.array_equal(source, reconstructed), view)
            self.assertEqual(
                record["source_pixel_sha256"], self.array_sha256(source)
            )
            self.assertEqual(
                record["reconstructed_pixel_sha256"],
                self.array_sha256(reconstructed),
            )

    def test_feature_arrays_have_expected_shape_type_and_hash(self) -> None:
        required = {
            "rgb_u8",
            "rgb_linear_f32",
            "gradient_magnitude_f32",
            "gradient_angle_radians_f32",
            "laplacian_f32",
            "local_contrast_f32",
            "canny_u8",
            "mask_jewelry_u8",
            "mask_stone_visible_u8",
            "mask_prongs_u8",
            "relative_depth_raw_f32",
            "relative_depth_regularized_f32",
            "relative_depth_normalized_u16",
            "relative_depth_uncertainty_u16",
        }
        for record in self.features["views"].values():
            with np.load(self.root / record["bundle"]) as bundle:
                self.assertTrue(required.issubset(bundle.files))
                height, width = reversed(record["size_wh"])
                for name in bundle.files:
                    values = bundle[name]
                    self.assertEqual(values.shape[:2], (height, width), name)
                    self.assertTrue(np.isfinite(values).all(), name)
                    metadata = record["features"][name]
                    self.assertEqual(metadata["shape"], list(values.shape))
                    self.assertEqual(metadata["dtype"], str(values.dtype))
                    self.assertEqual(metadata["sha256"], self.array_sha256(values))

    def test_visual_audits_are_readable(self) -> None:
        for path in (
            self.depth["front_photo_with_depth"],
            self.depth["front_audit"],
            self.depth["all_views_audit"],
            self.features["audit_sheet"],
        ):
            self.assertIsNotNone(cv2.imread(str(self.root / path)))


if __name__ == "__main__":
    unittest.main()
