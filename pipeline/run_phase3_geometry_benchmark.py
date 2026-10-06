"""Run the Bible Phase 3/B2 camera and geometry evidence benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.vggt_geometry_adapter import probe_vggt, run_vggt_object


VIEW_ORDER = ("front", "top", "iso", "lsv", "rsv")
BIBLE_PREREQUISITE_BLOCKERS = (
    "human_reviewed_image_truth_missing",
    "known_physical_dimension_missing",
    "calibrated_camera_truth_missing",
    "paired_cad_or_scan_truth_missing",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.run(
            ("git", "-C", str(root), "rev-parse", "HEAD"),
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _manifest(path: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return sorted(records, key=lambda row: int(row["object_id"].split("_")[-1]))


def _database_counts(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    with sqlite3.connect(path) as database:
        for table in ("images", "keypoints", "descriptors", "matches", "two_view_geometries"):
            count, rows = database.execute(
                f"SELECT COUNT(*), COALESCE(SUM(rows), 0) FROM {table}"
                if table != "images" else "SELECT COUNT(*), 0 FROM images"
            ).fetchone()
            result[f"{table}_records"] = int(count)
            if table != "images":
                result[f"{table}_rows"] = int(rows)
                nonempty = database.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE rows > 0"
                ).fetchone()[0]
                result[f"{table}_nonempty_records"] = int(nonempty)
    return result


def _prepare_colmap_images(root: Path, record: dict[str, Any], images_dir: Path) -> list[Path]:
    images_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for view in VIEW_ORDER:
        source = root / record["views"][view]["image_path"]
        suffix = source.suffix.lower() or ".png"
        target = images_dir / f"{view}{suffix}"
        shutil.copy2(source, target)
        paths.append(target)
    return paths


def _camera_records(reconstruction: Any) -> list[dict[str, Any]]:
    records = []
    for image_id in reconstruction.reg_image_ids():
        image = reconstruction.image(image_id)
        camera = reconstruction.camera(image.camera_id)
        records.append({
            "image_id": int(image_id),
            "image_name": image.name,
            "camera_model": camera.model_name,
            "intrinsic_matrix": camera.calibration_matrix().tolist(),
            "cam_from_world": image.cam_from_world().matrix().tolist(),
            "projection_center": image.projection_center().tolist(),
        })
    return sorted(records, key=lambda item: item["image_name"])


def _run_colmap_object(root: Path, record: dict[str, Any], output_root: Path, force: bool) -> dict[str, Any]:
    import pycolmap

    object_id = record["object_id"]
    object_dir = output_root / "colmap" / object_id
    if object_dir.exists() and force:
        shutil.rmtree(object_dir)
    object_dir.mkdir(parents=True, exist_ok=True)
    images_dir = object_dir / "images"
    sparse_dir = object_dir / "sparse"
    database_path = object_dir / "database.db"
    image_paths = _prepare_colmap_images(root, record, images_dir)
    started = time.perf_counter()
    try:
        extraction_options = pycolmap.FeatureExtractionOptions()
        extraction_options.num_threads = 4
        matching_options = pycolmap.FeatureMatchingOptions()
        matching_options.num_threads = 4
        pycolmap.extract_features(
            database_path, images_dir,
            image_names=[path.name for path in image_paths],
            camera_mode=pycolmap.CameraMode.PER_IMAGE,
            extraction_options=extraction_options,
            device=pycolmap.Device.cpu,
        )
        pycolmap.match_exhaustive(
            database_path,
            matching_options=matching_options,
            device=pycolmap.Device.cpu,
        )
        sparse_dir.mkdir(parents=True, exist_ok=True)
        reconstructions = pycolmap.incremental_mapping(database_path, images_dir, sparse_dir)
        best = max(
            reconstructions.values(),
            key=lambda value: (value.num_reg_images(), value.num_points3D()),
            default=None,
        )
        counts = _database_counts(database_path)
        if best:
            status = "completed_with_sparse_model"
        elif counts["two_view_geometries_nonempty_records"] == 0:
            status = "completed_without_verified_matches"
        else:
            status = "completed_without_sparse_model"
        result: dict[str, Any] = {
            "object_id": object_id,
            "split": record["split"],
            "backend": "colmap_pycolmap",
            "backend_version": pycolmap.__version__,
            "status": status,
            "authority": "machine_hypothesis",
            "metric": False,
            "cross_view_validated": False,
            "camera_calibrated_against_truth": False,
            "image_count": len(image_paths),
            "input_images": [
                {"view": view, "path": _repo_path(path, root), "sha256": _sha256(path)}
                for view, path in zip(VIEW_ORDER, image_paths)
            ],
            "database": counts,
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "prerequisite_blockers": list(BIBLE_PREREQUISITE_BLOCKERS),
            "decision": "research_only",
        }
        if best:
            ply_path = object_dir / f"{object_id}_sparse_points.ply"
            best.export_PLY(ply_path)
            result["sparse_model"] = {
                "registered_images": int(best.num_reg_images()),
                "points3d": int(best.num_points3D()),
                "observations": int(best.compute_num_observations()),
                "mean_track_length": float(best.compute_mean_track_length()),
                "mean_observations_per_registered_image": float(best.compute_mean_observations_per_reg_image()),
                "mean_reprojection_error_px": float(best.compute_mean_reprojection_error()),
                "cameras": _camera_records(best),
                "ply": _repo_path(ply_path, root),
            }
        else:
            result["sparse_model"] = None
    except Exception as exc:  # Preserve failed experiments as evidence.
        result = {
            "object_id": object_id,
            "split": record["split"],
            "backend": "colmap_pycolmap",
            "backend_version": pycolmap.__version__,
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "authority": "machine_hypothesis",
            "metric": False,
            "cross_view_validated": False,
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "prerequisite_blockers": list(BIBLE_PREREQUISITE_BLOCKERS),
            "decision": "research_only",
        }
    report_path = object_dir / "colmap_report.json"
    result["report"] = _repo_path(report_path, root)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    output = args.output_dir.resolve()
    report_path = output / "report.json"
    if report_path.exists() and not args.force:
        raise FileExistsError(f"{report_path} exists; use --force to rerun explicitly")
    records = _manifest(root / "dataset" / "prepared_v1" / "manifest.jsonl")
    if len(records) != 24 or any(set(item["views"]) != set(VIEW_ORDER) for item in records):
        raise ValueError("STL-1 must contain 24 complete five-view objects")
    if args.objects:
        selected = set(args.objects)
        records = [item for item in records if item["object_id"] in selected]
        missing = selected - {item["object_id"] for item in records}
        if missing:
            raise ValueError(f"Unknown object ids: {sorted(missing)}")
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    colmap_results: list[dict[str, Any]] = []
    colmap_backend: dict[str, Any] = {"status": "not_requested"}
    if args.backend in {"colmap", "all"}:
        try:
            import pycolmap

            colmap_backend = {"status": "available", "version": pycolmap.__version__, "device": "cpu"}
            for record in records:
                result = _run_colmap_object(root, record, output, args.force)
                colmap_results.append(result)
                print(f"COLMAP {record['object_id']}: {result['status']}", flush=True)
        except ImportError:
            colmap_backend = {"status": "blocked", "blockers": ["pycolmap_not_installed"]}

    vggt_probe = {"status": "not_requested"}
    vggt_results: list[dict[str, Any]] = []
    if args.backend in {"vggt", "all"}:
        vggt_probe = probe_vggt(
            args.vggt_checkpoint,
            args.vggt_license_id,
            args.allow_noncommercial_research,
        )
        if vggt_probe["status"] == "ready":
            for record in records:
                image_paths = [root / record["views"][view]["image_path"] for view in VIEW_ORDER]
                result = run_vggt_object(
                    image_paths,
                    output / "vggt" / record["object_id"],
                    args.vggt_checkpoint,
                    args.vggt_license_id,
                    args.vggt_device,
                    args.vggt_save_dense,
                    args.allow_noncommercial_research,
                )
                result["object_id"] = record["object_id"]
                result["split"] = record["split"]
                result["decision"] = "research_only"
                result["prerequisite_blockers"] = list(BIBLE_PREREQUISITE_BLOCKERS)
                vggt_results.append(result)

    completed_models = [row for row in colmap_results if row["status"] == "completed_with_sparse_model"]
    database_totals = {
        field: sum(row.get("database", {}).get(field, 0) for row in colmap_results)
        for field in (
            "images_records", "keypoints_records", "keypoints_rows",
            "matches_records", "matches_rows", "two_view_geometries_records",
            "matches_nonempty_records", "two_view_geometries_rows",
            "two_view_geometries_nonempty_records",
        )
    }
    report = {
        "schema_version": "phase3_geometry_benchmark_v1",
        "stage": "phase3_b2_camera_and_geometry_evidence",
        "created_at": _utc_now(),
        "code_commit": _git_commit(root),
        "dataset": "STL-1",
        "selected_object_count": len(records),
        "selected_view_count": len(records) * len(VIEW_ORDER),
        "backends": {"colmap": colmap_backend, "vggt": vggt_probe},
        "colmap": {
            "objects": colmap_results,
            "completed_sparse_model_count": len(completed_models),
            "database_totals": database_totals,
            "registered_all_five_views_count": sum(
                row.get("sparse_model", {}).get("registered_images") == 5
                for row in completed_models
            ),
        },
        "vggt": {"objects": vggt_results},
        "bible_gate": {
            "phase": "Phase 3 - camera and geometry evidence benchmark",
            "benchmark": "B2",
            "status": "research_only_blocked_from_promotion",
            "blockers": list(BIBLE_PREREQUISITE_BLOCKERS),
            "next_after_reviewed_b2": "Phase 4 - universal component and constraint graph",
        },
        "claims": {
            "camera_pose_accuracy_validated": False,
            "metric_depth_validated": False,
            "geometry_accuracy_validated": False,
            "manufacturing_accuracy_validated": False,
        },
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "decision": "research_only",
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=Path("dataset/phase_runs/v1/phase3_geometry_benchmark_v1"))
    parser.add_argument("--backend", choices=("colmap", "vggt", "all"), default="all")
    parser.add_argument("--objects", nargs="*")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--vggt-checkpoint", type=Path)
    parser.add_argument("--vggt-license-id")
    parser.add_argument("--vggt-device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--vggt-save-dense", action="store_true")
    parser.add_argument("--allow-noncommercial-research", action="store_true")
    args = parser.parse_args()
    report = run(args)
    print(json.dumps({
        "stage": report["stage"],
        "selected_object_count": report["selected_object_count"],
        "backends": report["backends"],
        "colmap_completed_sparse_model_count": report["colmap"]["completed_sparse_model_count"],
        "bible_gate": report["bible_gate"],
    }, indent=2))


if __name__ == "__main__":
    main()
