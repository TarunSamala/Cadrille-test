"""Regression tests for the read-only STL-1 dataset backend."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from studio.dataset_service import (
    AssetNotFoundError,
    DatasetRepository,
    ObjectNotFoundError,
    VIEW_ORDER,
)


class DatasetStudioServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = DatasetRepository(Path.cwd())

    def test_summary_uses_all_twenty_four_five_view_objects(self) -> None:
        summary = self.repository.summary()
        self.assertEqual(summary["dataset"]["object_count"], 24)
        self.assertEqual(summary["dataset"]["image_count"], 120)
        self.assertEqual(summary["dataset"]["views"], list(VIEW_ORDER))
        self.assertTrue(summary["dataset"]["valid"])
        self.assertEqual(summary["governance"]["capture_tier"], "A")
        self.assertEqual(summary["governance"]["decision"], "research_only")
        self.assertEqual(
            summary["governance"]["authoritative_output"], "STEP / exact B-rep"
        )

    def test_object_filters_preserve_object_level_splits(self) -> None:
        self.assertEqual(len(self.repository.list_objects("train")), 18)
        self.assertEqual(len(self.repository.list_objects("val")), 3)
        self.assertEqual(len(self.repository.list_objects("test")), 3)
        self.assertEqual(len(self.repository.list_objects("all")), 24)

    def test_every_object_exposes_real_view_and_phase_artifacts(self) -> None:
        for item in self.repository.list_objects():
            detail = self.repository.object_detail(item["object_id"])
            self.assertEqual(detail["view_order"], list(VIEW_ORDER))
            self.assertEqual(detail["bible"]["capture"]["tier"], "A")
            self.assertEqual(detail["bible"]["decision"], "research_only")
            self.assertFalse(any(detail["bible"]["gates"].values()))
            self.assertTrue(detail["artifacts"]["phase_sheet"])
            self.assertTrue(detail["artifacts"]["phase3_preview"])
            self.assertTrue(detail["artifacts"]["phase3_stl"])
            self.assertTrue(detail["artifacts"]["phase3_3mf"])
            for view in VIEW_ORDER:
                self.assertTrue(all(detail["artifacts"]["views"][view].values()))

    def test_test_objects_expose_held_out_review_sheets(self) -> None:
        for item in self.repository.list_objects("test"):
            self.assertTrue(
                self.repository.object_detail(item["object_id"])["artifacts"][
                    "held_out_review"
                ]
            )

    def test_export_report_keeps_accuracy_claims_honest(self) -> None:
        report = self.repository.export_object_report("ring_001")
        self.assertTrue(report["claims"]["phase2_pseudo_label_self_consistency_measured"])
        self.assertFalse(report["claims"]["phase2_human_ground_truth_accuracy_validated"])
        self.assertTrue(report["claims"]["phase3_experimental_non_metric"])
        self.assertFalse(report["claims"]["manufacturing_accuracy_validated"])
        self.assertEqual(report["benchmark_record"]["completeness"], "partial")
        self.assertEqual(report["benchmark_record"]["decision"], "research_only")
        json.dumps(report)

    def test_unknown_object_and_asset_are_rejected(self) -> None:
        with self.assertRaises(ObjectNotFoundError):
            self.repository.object_detail("ring_999")
        with self.assertRaises(AssetNotFoundError):
            self.repository.asset_path("ring_001", "../../etc/passwd")
        with self.assertRaises(AssetNotFoundError):
            self.repository.asset_path("ring_001", "source", "../../front")


try:
    import flask  # noqa: F401
except ImportError:
    flask = None


@unittest.skipIf(flask is None, "Flask is an optional Studio dependency")
class DatasetStudioApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from studio.app import create_app

        app = create_app(Path.cwd())
        app.config.update(TESTING=True)
        cls.client = app.test_client()

    def test_health_and_summary_routes(self) -> None:
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["objects"], 24)
        summary = self.client.get("/api/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.get_json()["dataset"]["image_count"], 120)

    def test_object_and_asset_routes(self) -> None:
        detail = self.client.get("/api/objects/ring_001")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.get_json()["views"]), 5)
        image = self.client.get("/api/objects/ring_001/assets/source?view=front")
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image.mimetype, "image/png")
        image.close()

    def test_invalid_routes_fail_closed(self) -> None:
        self.assertEqual(self.client.get("/api/objects/ring_999").status_code, 404)
        self.assertEqual(
            self.client.get("/api/objects/ring_001/assets/source?view=../../etc").status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
