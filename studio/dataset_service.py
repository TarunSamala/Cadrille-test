"""Read-only service layer for the versioned jewellery dataset artifacts.

The web interface deliberately depends on this module instead of reading files
directly.  That keeps path validation, schema checks and phase-status language
consistent if a different UI or API is added later.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


VIEW_ORDER = ("front", "top", "iso", "lsv", "rsv")
VIEW_LABELS = {
    "front": "Front",
    "top": "Top",
    "iso": "Isometric",
    "lsv": "Left side",
    "rsv": "Right side",
}


class DatasetError(RuntimeError):
    """Base exception for unavailable or invalid dataset state."""


class ObjectNotFoundError(DatasetError):
    """Raised when an object ID is not present in the manifest."""


class AssetNotFoundError(DatasetError):
    """Raised when a requested artifact is unavailable."""


class DatasetRepository:
    """Index the prepared dataset and retained phase artifacts.

    All paths returned by :meth:`asset_path` are checked to remain under the
    repository root.  The service never executes a phase or mutates evidence.
    """

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[1]).resolve()
        self.prepared_root = self.repo_root / "dataset" / "prepared_v1"
        self.phase_root = self.repo_root / "dataset" / "phase_runs" / "v1"

        self.dataset_report = self._read_json(self.prepared_root / "dataset_report.json")
        self.phase_summary = self._read_json(self.phase_root / "summary.json")
        self.audit_report = self._read_json(
            self.phase_root / "phase_audits" / "phase_audit_report.json"
        )
        self.phase3_report = self._read_json(
            self.phase_root / "phase3" / "visual_hull" / "phase3_batch_report.json"
        )
        self.phase1_features = self._read_json(self.phase_root / "phase1_features.json")
        self.phase0_environment = self._read_json(
            self.repo_root / "docs" / "reproducibility" / "environment_manifest.json"
        )
        self.phase0_licenses = self._read_json(
            self.repo_root
            / "docs"
            / "reproducibility"
            / "dependency_license_manifest.json"
        )
        self.records = self._read_manifest(self.prepared_root / "manifest.jsonl")
        self._records_by_id = {record["object_id"]: record for record in self.records}
        self._phase1_by_object = self._index_phase1_features()
        self._phase2_metrics = self._index_phase2_metrics()
        self._phase3_objects = {
            item["object_id"]: item for item in self.phase3_report.get("objects", [])
        }
        self._validate_index()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise DatasetError(f"Required dataset report is missing: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DatasetError(f"Cannot read dataset report: {path}") from exc

    @staticmethod
    def _read_manifest(path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            raise DatasetError(f"Dataset manifest is missing: {path}")
        records: list[dict[str, Any]] = []
        try:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if "object_id" not in record or "views" not in record:
                    raise DatasetError(f"Invalid manifest record on line {line_number}")
                records.append(record)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"Invalid JSON in dataset manifest: {path}") from exc
        return sorted(records, key=lambda record: _natural_key(record["object_id"]))

    def _validate_index(self) -> None:
        expected = int(self.dataset_report.get("object_count", 0))
        if expected != len(self.records):
            raise DatasetError(
                f"Manifest/report object-count mismatch: {len(self.records)} != {expected}"
            )
        for record in self.records:
            missing = set(VIEW_ORDER) - set(record["views"])
            if missing:
                raise DatasetError(f"{record['object_id']} is missing views: {sorted(missing)}")

    def _index_phase2_metrics(self) -> dict[str, dict[str, dict[str, float]]]:
        indexed: dict[str, dict[str, dict[str, float]]] = {}
        for row in self.audit_report.get("views", []):
            indexed.setdefault(row["object_id"], {})[row["view"]] = {
                "iou": float(row["iou"]),
                "dice": float(row["dice"]),
                "boundary_f1_2px": float(row["boundary_f1_2px"]),
            }
        return indexed

    def _index_phase1_features(self) -> dict[str, dict[str, dict[str, Any]]]:
        indexed: dict[str, dict[str, dict[str, Any]]] = {}
        for row in self.phase1_features.get("views", []):
            indexed.setdefault(row["object_id"], {})[row["view"]] = {
                "foreground_fraction": float(row["foreground_fraction"]),
                "edge_fraction": float(row["edge_fraction"]),
                "contour_count": int(row["contour_count"]),
                "hole_count": int(row["hole_count"]),
                "horizontal_symmetry_iou": float(row["horizontal_symmetry_iou"]),
            }
        return indexed

    def _record(self, object_id: str) -> dict[str, Any]:
        try:
            return self._records_by_id[object_id]
        except KeyError as exc:
            raise ObjectNotFoundError(f"Unknown dataset object: {object_id}") from exc

    def _safe_path(self, relative_or_absolute: str | Path) -> Path:
        candidate = Path(relative_or_absolute)
        if not candidate.is_absolute():
            candidate = self.repo_root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.repo_root)
        except ValueError as exc:
            raise AssetNotFoundError("Requested path is outside the project repository") from exc
        if not resolved.is_file():
            raise AssetNotFoundError(f"Artifact is not available: {resolved.name}")
        return resolved

    def summary(self) -> dict[str, Any]:
        split_counts = deepcopy(self.dataset_report.get("split_counts", {}))
        phase3_objects = list(self._phase3_objects.values())
        return {
            "dataset": {
                "name": "STL-1",
                "object_count": len(self.records),
                "image_count": int(self.dataset_report.get("image_count", 0)),
                "views": list(VIEW_ORDER),
                "split_counts": split_counts,
                "prepared_size": int(self.dataset_report.get("image_size", 0)),
                "valid": bool(self.dataset_report.get("dataset_valid", False)),
            },
            "governance": {
                "project": "Lalitha / Image2CAD",
                "bible_release": "BASELINE ARCHITECTURE V1.0",
                "architecture": "evidence-driven jewellery reverse-engineering and CAD",
                "primary_scope": "rings",
                "capture_tier": "A",
                "evidence_class": "PROVEN-IN-PROJECT",
                "claim_level": "coarse non-metric research",
                "authoritative_output": "STEP / exact B-rep",
                "dataset_has_authoritative_step": False,
                "decision": "research_only",
            },
            "phase0": {
                "status": "in_progress",
                "source": deepcopy(self.phase0_environment.get("source", {})),
                "container": deepcopy(self.phase0_environment.get("container", {})),
                "runtime": deepcopy(self.phase0_environment.get("runtime", {})),
                "regression": deepcopy(self.phase0_environment.get("regression", {})),
                "known_limits": deepcopy(
                    self.phase0_environment.get("known_limits", [])
                ),
                "dependency_package_count": int(
                    self.phase0_licenses.get("package_count", 0)
                ),
                "dependency_unknown_license_count": int(
                    self.phase0_licenses.get("unknown_license_count", 0)
                ),
                "legal_status": self.phase0_licenses.get("legal_status"),
            },
            "phase1": {
                "stage": self.phase1_features.get("stage"),
                "view_count": int(self.phase1_features.get("view_count", 0)),
                "measurements_are_metric": bool(
                    self.phase1_features.get("measurements_are_metric", False)
                ),
                "checks": deepcopy(self.phase1_features.get("checks", {})),
            },
            "phase2": {
                "status": "pseudo-label self-consistency benchmark; not human-ground-truth accuracy",
                "test": deepcopy(self.phase_summary.get("test", {})),
                "metrics_by_split": deepcopy(self.audit_report.get("metrics_by_split", {})),
                "selected_threshold": self.phase_summary.get("selected_threshold"),
            },
            "phase3": {
                "status": self.phase3_report.get("phase3_status", "unavailable"),
                "object_count": len(phase3_objects),
                "all_meshes_watertight": bool(
                    self.phase3_report.get("all_meshes_watertight", False)
                ),
                "mean_reprojection_iou_by_split": deepcopy(
                    self.phase3_report.get("mean_reprojection_iou_by_split", {})
                ),
                "manufacturing_accuracy_validated": bool(
                    self.phase3_report.get("manufacturing_accuracy_validated", False)
                ),
                "artifact_authority": "derived research mesh; no authoritative STEP",
                "decision": "research_only",
            },
            "limitations": deepcopy(self.dataset_report.get("limitations", [])),
        }

    def list_objects(self, split: str | None = None) -> list[dict[str, Any]]:
        if split not in {None, "all", "train", "val", "test"}:
            raise DatasetError(f"Invalid split: {split}")
        result = []
        for record in self.records:
            if split not in {None, "all"} and record["split"] != split:
                continue
            phase3 = self._phase3_objects.get(record["object_id"], {})
            result.append(
                {
                    "object_id": record["object_id"],
                    "source_name": record.get("source_object_name", record["object_id"]),
                    "category": record.get("category", "unknown"),
                    "split": record["split"],
                    "view_count": len(record["views"]),
                    "phase3_mean_iou": phase3.get("reprojection", {}).get("mean_iou"),
                    "phase3_available": bool(phase3),
                }
            )
        return result

    def object_detail(self, object_id: str) -> dict[str, Any]:
        record = self._record(object_id)
        phase1 = self._phase1_by_object.get(object_id, {})
        phase2 = self._phase2_metrics.get(object_id, {})
        phase3 = deepcopy(self._phase3_objects.get(object_id))
        views: dict[str, Any] = {}
        for view in VIEW_ORDER:
            metadata = record["views"][view]
            views[view] = {
                "label": VIEW_LABELS[view],
                "source_size_wh": deepcopy(metadata.get("source_size_wh")),
                "prepared_size_wh": deepcopy(metadata.get("prepared_size_wh")),
                "mask_occupancy": metadata.get("mask_occupancy"),
                "camera_calibrated": bool(metadata.get("camera_calibrated", False)),
                "source_sha256": metadata.get("source_sha256"),
                "features": deepcopy(phase1.get(view, {})),
                "metrics": deepcopy(phase2.get(view)),
            }
        return {
            "object_id": object_id,
            "source_name": record.get("source_object_name", object_id),
            "category": record.get("category", "unknown"),
            "split": record["split"],
            "views": views,
            "view_order": list(VIEW_ORDER),
            "phase3": phase3,
            "supervision": deepcopy(record.get("supervision", {})),
            "bible": {
                "capture": {
                    "tier": "A",
                    "view_contract": "five explicitly named research views",
                    "allowed_claims": [
                        "segmentation proposals",
                        "visual proposals",
                        "coarse non-metric reconstruction",
                    ],
                    "forbidden_claim": "manufacturing-accurate geometry",
                },
                "evidence_records": [
                    {
                        "stage": "immutable source views",
                        "evidence_class": "PROVEN-IN-PROJECT",
                        "state": "observed",
                    },
                    {
                        "stage": "normalization, masks and edges",
                        "evidence_class": "PROVEN-IN-PROJECT",
                        "state": "inferred",
                    },
                    {
                        "stage": "foreground, edge, contour, hole and symmetry measurements",
                        "evidence_class": "PROVEN-IN-PROJECT",
                        "state": "measured_non_metric",
                    },
                    {
                        "stage": "visual-hull mesh",
                        "evidence_class": "PROVEN-IN-PROJECT",
                        "state": "inferred",
                    },
                ],
                "gates": {
                    "human_reviewed_image_truth": False,
                    "metric_scale": False,
                    "calibrated_cameras": False,
                    "reviewed_component_graph": False,
                    "authoritative_exact_brep": False,
                    "manufacturing_validation": False,
                },
                "artifact_authority": "No authoritative STEP exists for this dataset object; STL and 3MF are derived research artifacts.",
                "decision": "research_only",
            },
            "artifacts": self.artifact_availability(object_id),
        }

    def artifact_availability(self, object_id: str) -> dict[str, Any]:
        self._record(object_id)
        view_assets = {
            view: {
                kind: self._asset_exists(object_id, kind, view)
                for kind in ("source", "normalized", "mask", "edges", "view_audit")
            }
            for view in VIEW_ORDER
        }
        return {
            "views": view_assets,
            "phase_sheet": self._asset_exists(object_id, "phase_sheet"),
            "phase3_preview": self._asset_exists(object_id, "phase3_preview"),
            "phase3_stl": self._asset_exists(object_id, "phase3_stl"),
            "phase3_3mf": self._asset_exists(object_id, "phase3_3mf"),
            "held_out_review": self._asset_exists(object_id, "held_out_review"),
        }

    def _asset_exists(self, object_id: str, kind: str, view: str | None = None) -> bool:
        try:
            self.asset_path(object_id, kind, view)
        except AssetNotFoundError:
            return False
        return True

    def asset_path(self, object_id: str, kind: str, view: str | None = None) -> Path:
        record = self._record(object_id)
        view_kinds = {
            "source": "source_path",
            "normalized": "image_path",
            "mask": "jewelry_mask_path",
            "edges": "edge_path",
        }
        if kind in view_kinds:
            if view not in VIEW_ORDER:
                raise AssetNotFoundError(f"A valid view is required for {kind}")
            return self._safe_path(record["views"][view][view_kinds[kind]])
        if kind == "view_audit":
            if view not in VIEW_ORDER:
                raise AssetNotFoundError("A valid view is required for view_audit")
            return self._safe_path(
                self.phase_root
                / "phase_audits"
                / object_id
                / "views"
                / f"{object_id}_{view}_audit.png"
            )
        if kind == "phase_sheet":
            return self._safe_path(
                self.phase_root / "phase_audits" / object_id / f"{object_id}_all_phases.png"
            )
        if kind == "held_out_review":
            return self._safe_path(
                self.phase_root / "test_predictions" / f"{object_id}_review.png"
            )

        phase3 = self._phase3_objects.get(object_id)
        if not phase3:
            raise AssetNotFoundError(f"Phase 3 output is unavailable for {object_id}")
        export_keys = {
            "phase3_preview": "preview",
            "phase3_stl": "stl",
            "phase3_3mf": "3mf",
        }
        if kind in export_keys:
            path = phase3.get("exports", {}).get(export_keys[kind])
            if not path:
                raise AssetNotFoundError(f"{kind} is unavailable for {object_id}")
            return self._safe_path(path)
        raise AssetNotFoundError(f"Unknown artifact kind: {kind}")

    def global_asset_path(self, name: str) -> Path:
        allowed = {
            "multiview_overview": "dataset_multiview_overview.png",
            "processing_comparison": "dataset_processing_comparison.png",
            "held_out_comparison": "held_out_prediction_comparison.png",
        }
        reproducibility = {
            "phase0_environment": self.repo_root
            / "docs"
            / "reproducibility"
            / "environment_manifest.json",
            "phase0_licenses": self.repo_root
            / "docs"
            / "reproducibility"
            / "dependency_license_manifest.json",
            "phase0_status": self.repo_root
            / "docs"
            / "reproducibility"
            / "PHASE0_STATUS.md",
        }
        if name in reproducibility:
            return self._safe_path(reproducibility[name])
        try:
            filename = allowed[name]
        except KeyError as exc:
            raise AssetNotFoundError(f"Unknown global artifact: {name}") from exc
        return self._safe_path(self.phase_root / "comparisons" / filename)

    def export_object_report(self, object_id: str) -> dict[str, Any]:
        """Return a portable evidence report without leaking local absolute paths."""

        detail = self.object_detail(object_id)
        detail["schema_version"] = "lalitha_studio_evidence_v1"
        detail["claims"] = {
            "phase2_pseudo_label_self_consistency_measured": True,
            "phase2_human_ground_truth_accuracy_validated": False,
            "phase3_experimental_non_metric": True,
            "metric_reconstruction_validated": False,
            "manufacturing_accuracy_validated": False,
        }
        detail["benchmark_record"] = {
            "capture_tier": "A",
            "input_hashes_recorded": True,
            "code_commit_recorded_in_source_report": bool(
                self.phase0_environment.get("source", {}).get("commit")
            ),
            "model_checkpoint_hash_recorded": False,
            "license_manifest_recorded": True,
            "peak_memory_recorded": False,
            "runtime_recorded": False,
            "random_seed_recorded": False,
            "completeness": "partial",
            "decision": "research_only",
        }
        return detail


def _natural_key(value: str) -> tuple[Any, ...]:
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value))
