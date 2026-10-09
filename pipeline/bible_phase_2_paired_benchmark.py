"""Validate the canonical Bible Phase 2 paired jewellery benchmark.

This module validates evidence that actually exists. It never fabricates CAD,
metric dimensions, capture calibration, component truth, or legal provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "lalitha_bible_phase2_paired_benchmark_v1"
OBJECT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
SCAN_SUFFIXES = {".stl", ".obj", ".ply", ".glb", ".gltf", ".3mf"}
PROVENANCE_STATES = {"observed", "inferred", "designed", "unknown"}
REQUIRED_SPLITS = ("train", "validation", "test")


class Phase2ContractError(RuntimeError):
    """Raised when the benchmark root or manifest cannot be trusted."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Phase2ContractError(f"Required JSON is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise Phase2ContractError(f"Invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Phase2ContractError(f"Expected a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_json(path: Path, issues: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        issues.append(f"missing_{label}")
        return {}
    try:
        return _read_json(path)
    except Phase2ContractError:
        issues.append(f"invalid_{label}")
        return {}


def _validate_dimensions(document: dict[str, Any], issues: list[str]) -> int:
    measurements = document.get("measurements", [])
    if not isinstance(measurements, list) or not measurements:
        issues.append("no_physical_measurements")
        return 0
    valid = 0
    names: set[str] = set()
    for index, item in enumerate(measurements):
        if not isinstance(item, dict):
            issues.append(f"measurement_{index}_invalid")
            continue
        name = str(item.get("name", "")).strip()
        value = item.get("value_mm")
        source = str(item.get("source", "")).strip()
        uncertainty = item.get("uncertainty_mm")
        if not name or name in names:
            issues.append(f"measurement_{index}_name_invalid")
            continue
        if not isinstance(value, (int, float)) or value <= 0:
            issues.append(f"measurement_{index}_value_invalid")
            continue
        if not source:
            issues.append(f"measurement_{index}_source_missing")
            continue
        if uncertainty is not None and (
            not isinstance(uncertainty, (int, float)) or uncertainty < 0
        ):
            issues.append(f"measurement_{index}_uncertainty_invalid")
            continue
        names.add(name)
        valid += 1
    return valid


def _validate_provenance(document: dict[str, Any], issues: list[str]) -> bool:
    required_text = (
        "source",
        "rights_holder",
        "capture_owner",
        "cad_owner",
        "license_or_agreement",
        "consent_record",
    )
    for field in required_text:
        if not str(document.get(field, "")).strip():
            issues.append(f"provenance_{field}_missing")
    uses = document.get("permitted_uses", [])
    if not isinstance(uses, list) or "research" not in uses:
        issues.append("provenance_research_use_not_permitted")
    return not any(issue.startswith("provenance_") for issue in issues)


def _validate_component_graph(document: dict[str, Any], issues: list[str]) -> int:
    nodes = document.get("nodes", [])
    edges = document.get("edges", [])
    if not isinstance(nodes, list) or not nodes:
        issues.append("component_graph_has_no_nodes")
        return 0
    ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            issues.append(f"component_node_{index}_invalid")
            continue
        node_id = str(node.get("id", "")).strip()
        kind = str(node.get("type", "")).strip()
        state = node.get("provenance_state")
        if not node_id or node_id in ids:
            issues.append(f"component_node_{index}_id_invalid")
            continue
        if not kind:
            issues.append(f"component_node_{index}_type_missing")
        if state not in PROVENANCE_STATES:
            issues.append(f"component_node_{index}_provenance_invalid")
        ids.add(node_id)
    if not isinstance(edges, list):
        issues.append("component_edges_invalid")
    else:
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                issues.append(f"component_edge_{index}_invalid")
                continue
            if edge.get("source") not in ids or edge.get("target") not in ids:
                issues.append(f"component_edge_{index}_endpoint_invalid")
            if not str(edge.get("relationship", "")).strip():
                issues.append(f"component_edge_{index}_relationship_missing")
    return len(ids)


def _validate_step(path: Path, issues: list[str]) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        issues.append("production_step_missing")
        return False
    try:
        header = path.read_bytes()[:4096].upper()
    except OSError:
        issues.append("production_step_unreadable")
        return False
    if b"ISO-10303-21" not in header:
        issues.append("production_step_header_invalid")
        return False
    return True


def validate_object(dataset_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    object_id = str(entry.get("object_id", ""))
    if not OBJECT_ID_PATTERN.fullmatch(object_id):
        return {"object_id": object_id, "valid": False, "issues": ["object_id_invalid"]}

    object_root = (dataset_root / "objects" / object_id).resolve()
    objects_root = (dataset_root / "objects").resolve()
    try:
        object_root.relative_to(objects_root)
    except ValueError as exc:
        raise Phase2ContractError(f"Object path escaped dataset root: {object_id}") from exc
    if not object_root.is_dir():
        return {"object_id": object_id, "valid": False, "issues": ["object_directory_missing"]}

    design_family = str(entry.get("design_family", "")).strip()
    split = entry.get("split")
    if not design_family:
        issues.append("design_family_missing")
    if split not in REQUIRED_SPLITS:
        issues.append("split_invalid")

    rgb_root = object_root / "capture" / "rgb"
    images = sorted(
        path for path in rgb_root.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and path.stat().st_size > 0
    ) if rgb_root.is_dir() else []
    if not 8 <= len(images) <= 12:
        issues.append("guided_view_count_outside_8_to_12")

    camera = _required_json(
        object_root / "capture" / "camera_metadata.json", issues, "camera_metadata"
    )
    camera_views = camera.get("views", [])
    camera_filenames = {
        item.get("filename") for item in camera_views if isinstance(item, dict)
    } if isinstance(camera_views, list) else set()
    image_names = {path.name for path in images}
    if camera_filenames != image_names:
        issues.append("camera_metadata_view_mismatch")

    dimensions = _required_json(
        object_root / "truth" / "measured_dimensions.json",
        issues,
        "measured_dimensions",
    )
    measurement_count = _validate_dimensions(dimensions, issues) if dimensions else 0

    provenance = _required_json(object_root / "provenance.json", issues, "provenance")
    legal_provenance_valid = _validate_provenance(provenance, issues) if provenance else False

    graph = _required_json(
        object_root / "annotations" / "component_graph.json",
        issues,
        "component_graph",
    )
    component_count = _validate_component_graph(graph, issues) if graph else 0

    step_path = object_root / "truth" / "production.step"
    step_valid = _validate_step(step_path, issues)
    scan_files = sorted(
        path for path in (object_root / "truth").glob("scan_mesh.*")
        if path.suffix.lower() in SCAN_SUFFIXES and path.is_file() and path.stat().st_size > 0
    )

    hashes = {
        str(path.relative_to(dataset_root)): _sha256(path)
        for path in [*images, step_path, *scan_files]
        if path.is_file()
    }
    return {
        "object_id": object_id,
        "design_family": design_family,
        "split": split,
        "valid": not issues,
        "issues": sorted(set(issues)),
        "view_count": len(images),
        "measurement_count": measurement_count,
        "component_count": component_count,
        "production_step_valid": step_valid,
        "legal_provenance_valid": legal_provenance_valid,
        "has_scan_truth": bool(scan_files),
        "file_hashes": hashes,
    }


def validate_dataset(dataset_root: Path) -> dict[str, Any]:
    dataset_root = dataset_root.resolve()
    manifest = _read_json(dataset_root / "manifest.json")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise Phase2ContractError("Unsupported Phase 2 manifest schema")
    objects = manifest.get("objects", [])
    if not isinstance(objects, list):
        raise Phase2ContractError("manifest.objects must be a list")
    ids = [str(item.get("object_id", "")) for item in objects if isinstance(item, dict)]
    if len(ids) != len(objects) or len(ids) != len(set(ids)):
        raise Phase2ContractError("Object records must be objects with unique object_id values")

    results = [validate_object(dataset_root, entry) for entry in objects]
    valid_results = [item for item in results if item["valid"]]
    families = {item["design_family"] for item in valid_results if item["design_family"]}
    scan_count = sum(bool(item["has_scan_truth"]) for item in valid_results)
    legal_count = sum(bool(item["legal_provenance_valid"]) for item in valid_results)

    splits = manifest.get("splits", {})
    assignments = splits.get("assignments", {}) if isinstance(splits, dict) else {}
    split_lists = {
        name: assignments.get(name, []) if isinstance(assignments, dict) else []
        for name in REQUIRED_SPLITS
    }
    split_ids = [object_id for values in split_lists.values() for object_id in values]
    split_disjoint = len(split_ids) == len(set(split_ids))
    split_complete = set(split_ids) == set(ids)
    split_names_match = all(
        item.get("object_id") in split_lists.get(item.get("split"), [])
        for item in results
    )
    split_locked = bool(splits.get("locked", False)) if isinstance(splits, dict) else False

    requirements = {
        "pilot_object_count_at_least_20": len(valid_results) >= 20,
        "several_design_families_at_least_3": len(families) >= 3,
        "all_objects_have_legal_provenance": bool(valid_results)
        and legal_count == len(valid_results),
        "scan_subset_present": scan_count >= 1,
        "object_level_split_complete_and_disjoint": split_disjoint
        and split_complete
        and split_names_match,
        "test_split_locked": split_locked and bool(split_lists["test"]),
    }
    blockers = [name for name, passed in requirements.items() if not passed]
    return {
        "schema_version": SCHEMA_VERSION,
        "bible_phase": "Phase 2 - Real Paired Benchmark",
        "status": "pass" if not blockers else "collection_required",
        "decision": "phase2_exit_gate_passed" if not blockers else "phase2_infrastructure_ready_data_blocked",
        "object_count": len(results),
        "valid_object_count": len(valid_results),
        "invalid_object_count": len(results) - len(valid_results),
        "design_family_count": len(families),
        "scan_truth_object_count": scan_count,
        "legal_provenance_object_count": legal_count,
        "capture_contract": {
            "tier": "B",
            "guided_view_count_min": 8,
            "guided_view_count_max": 12,
            "production_step_required": True,
            "physical_measurement_required": True,
            "component_graph_required": True,
        },
        "split": {
            "locked": split_locked,
            "complete": split_complete,
            "disjoint": split_disjoint,
            "entry_assignments_match": split_names_match,
            "counts": {name: len(values) for name, values in split_lists.items()},
        },
        "requirements": requirements,
        "blockers": blockers,
        "objects": results,
        "accuracy_claim": "none_until_paired_truth_is_collected_and_benchmarked",
    }


def write_report(dataset_root: Path, report: dict[str, Any]) -> Path:
    path = dataset_root / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-root", type=Path, default=Path("dataset/paired_cad_v1")
    )
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    report = validate_dataset(args.dataset_root)
    if not args.check_only:
        write_report(args.dataset_root, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
