"""Contracts for canonical Bible Phase 2 paired jewellery data."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipeline.bible_phase_2_paired_benchmark import (
    SCHEMA_VERSION,
    validate_dataset,
)


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_valid_object(dataset_root: Path, object_id: str = "ring_001") -> dict:
    object_root = dataset_root / "objects" / object_id
    rgb_root = object_root / "capture" / "rgb"
    rgb_root.mkdir(parents=True)
    filenames = []
    for index in range(8):
        filename = f"view_{index:02d}.png"
        (rgb_root / filename).write_bytes(b"retained-image-evidence")
        filenames.append(filename)
    write_json(
        object_root / "capture" / "camera_metadata.json",
        {
            "views": [
                {"view_id": f"view_{index:02d}", "filename": filename}
                for index, filename in enumerate(filenames)
            ],
            "calibration_status": "unknown_but_explicit",
        },
    )
    write_json(
        object_root / "truth" / "measured_dimensions.json",
        {
            "measurements": [
                {
                    "name": "inner_diameter",
                    "value_mm": 17.2,
                    "source": "digital_caliper",
                    "uncertainty_mm": 0.05,
                }
            ]
        },
    )
    (object_root / "truth" / "production.step").write_text(
        "ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n",
        encoding="ascii",
    )
    write_json(
        object_root / "annotations" / "component_graph.json",
        {
            "nodes": [
                {
                    "id": "shank_001",
                    "type": "shank",
                    "provenance_state": "observed",
                }
            ],
            "edges": [],
        },
    )
    write_json(
        object_root / "provenance.json",
        {
            "source": "project_capture",
            "rights_holder": "test-rights-holder",
            "capture_owner": "test-capture-owner",
            "cad_owner": "test-cad-owner",
            "license_or_agreement": "test-agreement-record",
            "consent_record": "test-consent-record",
            "permitted_uses": ["research"],
        },
    )
    return {"object_id": object_id, "design_family": "solitaire", "split": "train"}


class BiblePhase2PairedBenchmarkTest(unittest.TestCase):
    def test_checked_in_registry_is_honestly_collection_blocked(self) -> None:
        report = validate_dataset(ROOT / "dataset" / "paired_cad_v1")
        retained = json.loads(
            (ROOT / "dataset" / "paired_cad_v1" / "report.json").read_text()
        )
        self.assertEqual(report, retained)
        self.assertEqual(report["status"], "collection_required")
        self.assertEqual(report["object_count"], 0)
        self.assertFalse(report["requirements"]["pilot_object_count_at_least_20"])
        self.assertEqual(
            report["accuracy_claim"],
            "none_until_paired_truth_is_collected_and_benchmarked",
        )

    def test_complete_object_contract_is_accepted_without_passing_dataset_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset_root = Path(temporary)
            entry = build_valid_object(dataset_root)
            write_json(
                dataset_root / "manifest.json",
                {
                    "schema_version": SCHEMA_VERSION,
                    "splits": {
                        "locked": False,
                        "assignments": {
                            "train": [entry["object_id"]],
                            "validation": [],
                            "test": [],
                        },
                    },
                    "objects": [entry],
                },
            )
            report = validate_dataset(dataset_root)
            self.assertEqual(report["valid_object_count"], 1)
            self.assertTrue(report["objects"][0]["valid"])
            self.assertTrue(report["objects"][0]["production_step_valid"])
            self.assertTrue(report["objects"][0]["legal_provenance_valid"])
            self.assertEqual(report["status"], "collection_required")

    def test_missing_production_cad_fails_the_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset_root = Path(temporary)
            entry = build_valid_object(dataset_root)
            (dataset_root / "objects" / entry["object_id"] / "truth" / "production.step").unlink()
            write_json(
                dataset_root / "manifest.json",
                {
                    "schema_version": SCHEMA_VERSION,
                    "splits": {
                        "locked": False,
                        "assignments": {
                            "train": [entry["object_id"]],
                            "validation": [],
                            "test": [],
                        },
                    },
                    "objects": [entry],
                },
            )
            report = validate_dataset(dataset_root)
            self.assertEqual(report["valid_object_count"], 0)
            self.assertIn("production_step_missing", report["objects"][0]["issues"])

    def test_ring01_reflection_exception_remains_open_and_non_approving(self) -> None:
        notes = json.loads(
            (
                ROOT
                / "data"
                / "ring01_ground_truth_v1"
                / "review"
                / "ring01_review_notes.json"
            ).read_text()
        )
        self.assertEqual(
            notes["open_issues"][0]["status"],
            "correction_proposed_pending_human_review",
        )
        self.assertEqual(notes["open_issues"][0]["phenomenon"], "specular_reflection")
        self.assertIn("remains blocked", notes["gate_effect"])


if __name__ == "__main__":
    unittest.main()
