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
        self.assertRegex(summary["phase0"]["source"]["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(summary["phase0"]["regression"]["result"], "passed")
        self.assertGreaterEqual(summary["phase0"]["dependency_package_count"], 20)
        self.assertEqual(summary["phase1"]["view_count"], 120)
        self.assertFalse(summary["phase1"]["measurements_are_metric"])
        dataset_depth = summary["phase1"]["depth_anything_v2"]
        self.assertEqual(dataset_depth["coverage"]["object_count"], 24)
        self.assertEqual(dataset_depth["coverage"]["view_count"], 120)
        self.assertTrue(all(dataset_depth["checks"].values()))
        self.assertEqual(dataset_depth["phase1_gate"]["status"], "blocked")
        self.assertFalse(dataset_depth["phase1_gate"]["metric_depth"])
        complete = summary["phase1"]["complete_features"]
        self.assertEqual(complete["coverage"]["object_count"], 24)
        self.assertEqual(complete["coverage"]["view_count"], 120)
        self.assertEqual(complete["runtime"]["repeat_count"], 3)
        self.assertTrue(all(complete["checks"].values()))
        self.assertEqual(
            complete["feature_contract"]["stored_array_count_per_view"], 22
        )
        self.assertTrue(
            complete["reconstruction_contract"]["source_pixel_roundtrip_exact"]
        )
        self.assertEqual(complete["metric_depth"]["status"], "blocked")
        ground_truth = summary["phase1_ground_truth"]
        self.assertEqual(ground_truth["exit_gate"]["status"], "blocked")
        self.assertEqual(ground_truth["exit_gate"]["pending_label_review_count"], 35)
        self.assertEqual(
            ground_truth["depth"]["status"], "machine_proposals_pending_review"
        )
        self.assertFalse(ground_truth["depth"]["metric"])
        self.assertTrue(
            ground_truth["depth_validation"]["checks"][
                "all_three_repeats_identical"
            ]
        )
        self.assertEqual(
            ground_truth["depth_validation"]["metric_depth"]["status"],
            "blocked",
        )
        self.assertEqual(ground_truth["pixel_features"]["view_count"], 5)
        self.assertTrue(
            ground_truth["pixel_features"]["reconstruction_contract"][
                "pixel_exact_roundtrip"
            ]
        )
        self.assertFalse(
            ground_truth["pixel_features"]["depth_contract"][
                "metric_depth_available"
            ]
        )
        geometry = summary["phase3"]["geometry_benchmark"]
        self.assertEqual(geometry["selected_object_count"], 24)
        self.assertEqual(geometry["backends"]["colmap"]["version"], "4.2.1")
        self.assertEqual(geometry["backends"]["vggt"]["status"], "blocked")

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
            self.assertTrue(detail["artifacts"]["phase1_depth_review"])
            self.assertTrue(detail["artifacts"]["phase1_complete_audit"])
            self.assertTrue(detail["artifacts"]["phase3_preview"])
            self.assertTrue(detail["artifacts"]["phase3_stl"])
            self.assertTrue(detail["artifacts"]["phase3_3mf"])
            self.assertTrue(detail["artifacts"]["colmap_report"])
            self.assertEqual(
                detail["geometry_evidence"]["authority"], "machine_hypothesis"
            )
            for view in VIEW_ORDER:
                self.assertTrue(all(detail["artifacts"]["views"][view].values()))
                self.assertEqual(
                    set(detail["views"][view]["features"]),
                    {
                        "foreground_fraction",
                        "edge_fraction",
                        "contour_count",
                        "hole_count",
                        "horizontal_symmetry_iou",
                    },
                )
                self.assertFalse(detail["views"][view]["depth"]["metric"])
                self.assertFalse(
                    detail["views"][view]["depth"]["cross_view_aligned"]
                )
                complete = detail["views"][view]["complete_features"]
                self.assertEqual(complete["feature_count"], 22)
                self.assertEqual(complete["repeat_count"], 3)
                self.assertTrue(complete["repeat_deterministic"])
                self.assertTrue(complete["source_pixel_roundtrip_exact"])
                self.assertFalse(complete["metric"])
                self.assertFalse(complete["cross_view_aligned"])

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
        self.assertTrue(report["claims"]["phase1_relative_depth_proposals_generated"])
        self.assertFalse(report["claims"]["phase1_depth_accuracy_validated"])
        self.assertFalse(report["claims"]["phase2_human_ground_truth_accuracy_validated"])
        self.assertTrue(report["claims"]["phase3_experimental_non_metric"])
        self.assertFalse(report["claims"]["manufacturing_accuracy_validated"])
        self.assertTrue(
            report["benchmark_record"]["code_commit_recorded_in_source_report"]
        )
        self.assertTrue(report["benchmark_record"]["license_manifest_recorded"])
        self.assertTrue(
            report["benchmark_record"]["model_checkpoint_revision_recorded"]
        )
        self.assertTrue(report["benchmark_record"]["peak_memory_recorded"])
        self.assertTrue(report["benchmark_record"]["runtime_recorded"])
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
        environment = self.client.get("/api/artifacts/phase0_environment")
        self.assertEqual(environment.status_code, 200)
        self.assertRegex(
            environment.get_json()["source"]["commit"], r"^[0-9a-f]{40}$"
        )
        environment.close()

    def test_studio_page_exposes_visual_and_metadata_evidence_controls(self) -> None:
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        markup = page.get_data(as_text=True)
        for marker in (
            'id="phase0-summary"',
            'id="phase0-limits"',
            'id="phase1-summary"',
            'id="phase1-depth-status"',
            'id="phase1-deep-summary"',
            'id="dataset-depth-summary"',
            'id="dataset-complete-summary"',
            'data-layer="normalized"',
            'data-layer="mask"',
            'data-layer="edges"',
            'data-layer="depth"',
            'data-layer="depth_uncertainty"',
            'data-layer="depth_ensemble"',
            'data-layer="depth_transform_uncertainty"',
            'data-layer="depth_overlay"',
            'id="phase1-complete-audit"',
            'id="phase3-geometry"',
            'id="phase3-geometry-report"',
            'id="feature-rows"',
            'id="depth-rows"',
        ):
            self.assertIn(marker, markup)
        script = self.client.get("/static/studio.js")
        self.assertEqual(script.status_code, 200)
        javascript = script.get_data(as_text=True)
        self.assertIn('$("#phase0-summary")', javascript)
        self.assertIn('$("#feature-rows")', javascript)
        self.assertIn('$("#phase1-summary")', javascript)
        self.assertIn('$("#phase1-deep-summary")', javascript)
        self.assertIn('$("#dataset-depth-summary")', javascript)
        self.assertIn('$("#dataset-complete-summary")', javascript)
        self.assertIn('$("#phase1-complete-audit")', javascript)
        script.close()
        page.close()

    def test_object_and_asset_routes(self) -> None:
        detail = self.client.get("/api/objects/ring_001")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.get_json()["views"]), 5)
        image = self.client.get("/api/objects/ring_001/assets/source?view=front")
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image.mimetype, "image/png")
        image.close()
        depth = self.client.get("/api/artifacts/phase1_depth_review")
        self.assertEqual(depth.status_code, 200)
        self.assertEqual(depth.mimetype, "image/png")
        depth.close()
        front_audit = self.client.get("/api/artifacts/ring01_front_depth_audit")
        self.assertEqual(front_audit.status_code, 200)
        self.assertEqual(front_audit.mimetype, "image/png")
        front_audit.close()
        pixel_audit = self.client.get("/api/artifacts/ring01_pixel_feature_audit")
        self.assertEqual(pixel_audit.status_code, 200)
        self.assertEqual(pixel_audit.mimetype, "image/png")
        pixel_audit.close()
        dataset_depth = self.client.get(
            "/api/objects/ring_001/assets/depth?view=front"
        )
        self.assertEqual(dataset_depth.status_code, 200)
        self.assertEqual(dataset_depth.mimetype, "image/png")
        dataset_depth.close()
        ensemble = self.client.get(
            "/api/objects/ring_001/assets/depth_ensemble?view=front"
        )
        self.assertEqual(ensemble.status_code, 200)
        self.assertEqual(ensemble.mimetype, "image/png")
        ensemble.close()
        transform_uncertainty = self.client.get(
            "/api/objects/ring_001/assets/depth_transform_uncertainty?view=front"
        )
        self.assertEqual(transform_uncertainty.status_code, 200)
        self.assertEqual(transform_uncertainty.mimetype, "image/png")
        transform_uncertainty.close()
        depth_overlay = self.client.get(
            "/api/objects/ring_001/assets/depth_overlay?view=front"
        )
        self.assertEqual(depth_overlay.status_code, 200)
        self.assertEqual(depth_overlay.mimetype, "image/png")
        depth_overlay.close()
        review = self.client.get(
            "/api/objects/ring_001/assets/phase1_depth_review"
        )
        self.assertEqual(review.status_code, 200)
        self.assertEqual(review.mimetype, "image/jpeg")
        review.close()
        complete_audit = self.client.get(
            "/api/objects/ring_001/assets/phase1_complete_audit"
        )
        self.assertEqual(complete_audit.status_code, 200)
        self.assertEqual(complete_audit.mimetype, "image/png")
        complete_audit.close()
        overview = self.client.get("/api/artifacts/dataset_depth_overview")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(overview.mimetype, "image/jpeg")
        overview.close()
        complete_overview = self.client.get(
            "/api/artifacts/dataset_complete_phase1_overview"
        )
        self.assertEqual(complete_overview.status_code, 200)
        self.assertEqual(complete_overview.mimetype, "image/png")
        complete_overview.close()

    def test_invalid_routes_fail_closed(self) -> None:
        self.assertEqual(self.client.get("/api/objects/ring_999").status_code, 404)
        self.assertEqual(
            self.client.get("/api/objects/ring_001/assets/source?view=../../etc").status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
