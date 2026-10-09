"""Validate the Ring01 image-only reflection correction checkpoint."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import cv2
import numpy as np

from pipeline.image_only_reflection_correction import infer_correction, read_mask


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "ring01_image_only" / "reflection_correction_v1"
BASELINE = ROOT / "data" / "ring01_phase2_refined" / "masks"


class ImageOnlyReflectionCorrectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads((OUTPUT / "report.json").read_text())

    def test_checkpoint_is_image_only_valid_and_uncertainty_marked(self) -> None:
        self.assertEqual(self.report["input_contract"], "images_only")
        self.assertEqual(
            self.report["authority"], "topology_informed_machine_proposal"
        )
        self.assertTrue(self.report["checkpoint_valid"])
        self.assertTrue(all(self.report["checks"].values()))
        self.assertEqual(
            self.report["status"], "correction_proposed_pending_human_review"
        )
        method = self.report["method"]
        self.assertEqual(method["correction_pixel_count"], 376)
        self.assertGreater(
            method["corrected_opening_ellipse_iou"],
            method["baseline_opening_ellipse_iou"],
        )
        self.assertLessEqual(method["max_observed_correction_distance_px"], 6.0)

    def test_corrected_masks_only_add_the_recorded_local_pixels(self) -> None:
        correction = read_mask(
            OUTPUT / "uncertainty" / "ring01_angled_correction.png"
        )
        self.assertEqual(int(np.count_nonzero(correction)), 376)
        for kind in ("jewelry", "metal", "shank"):
            before = read_mask(BASELINE / kind / f"ring01_angled_{kind}.png")
            after = read_mask(
                OUTPUT / "masks" / kind / f"ring01_angled_{kind}.png"
            )
            self.assertFalse(np.any((before > 0) & (after == 0)), kind)
            self.assertTrue(np.all(after[correction > 0] == 255), kind)
        negative_before = read_mask(
            ROOT
            / "data"
            / "ring01_ground_truth_v1"
            / "proposals"
            / "negative_space"
            / "ring01_angled_negative_space_proposal.png"
        )
        negative_after = read_mask(
            OUTPUT
            / "masks"
            / "negative_space"
            / "ring01_angled_negative_space.png"
        )
        self.assertTrue(np.all(negative_after[correction > 0] == 0))
        self.assertFalse(np.any((negative_before == 0) & (negative_after > 0)))

    def test_report_reproduces_from_immutable_inputs_and_artifacts_are_readable(self) -> None:
        jewelry = read_mask(BASELINE / "jewelry" / "ring01_angled_jewelry.png")
        shank = read_mask(BASELINE / "shank" / "ring01_angled_shank.png")
        inference = infer_correction(jewelry, shank)
        method = self.report["method"]
        self.assertEqual(
            inference["correction_pixel_count"], method["correction_pixel_count"]
        )
        self.assertAlmostEqual(
            inference["corrected_opening_ellipse_iou"],
            method["corrected_opening_ellipse_iou"],
            places=12,
        )
        source_path = ROOT / self.report["inputs"]["source"]
        self.assertEqual(
            hashlib.sha256(source_path.read_bytes()).hexdigest(),
            self.report["inputs"]["source_sha256"],
        )
        for relative in (
            self.report["outputs"]["audit"],
            self.report["outputs"]["correction_mask"],
            self.report["outputs"]["uncertainty_mask"],
        ):
            image = cv2.imread(str(ROOT / relative), cv2.IMREAD_UNCHANGED)
            self.assertIsNotNone(image, relative)
            self.assertGreater(image.size, 0, relative)


if __name__ == "__main__":
    unittest.main()
