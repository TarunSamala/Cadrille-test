"""Run the non-metric Depth Anything V2 Phase 1 benchmark on STL-1."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

from pipeline.infer_depth_anything_v2 import (
    MODEL_ID,
    MODEL_LICENSE,
    MODEL_REVISION,
    align_prediction,
    colorize,
    infer,
    robust_normalize,
    sha256,
)


VIEW_ORDER = ("front", "top", "iso", "lsv", "rsv")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_commit(root: Path) -> str | None:
    try:
        return subprocess.run(
            ("git", "-C", str(root), "rev-parse", "HEAD"),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        git_dir = root / ".git"
        head_path = git_dir / "HEAD"
        if not head_path.is_file():
            return None
        head = head_path.read_text(encoding="utf-8").strip()
        if not head.startswith("ref: "):
            return head if len(head) == 40 else None
        reference = head.removeprefix("ref: ")
        loose_ref = git_dir / reference
        if loose_ref.is_file():
            return loose_ref.read_text(encoding="utf-8").strip()
        packed_refs = git_dir / "packed-refs"
        if packed_refs.is_file():
            for line in packed_refs.read_text(encoding="utf-8").splitlines():
                if line and not line.startswith(("#", "^")):
                    commit, name = line.split(" ", 1)
                    if name == reference:
                        return commit
        return None


def read_manifest(path: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return sorted(records, key=lambda item: int(item["object_id"].split("_")[-1]))


def array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def image_panel(image: np.ndarray, title: str, size: int = 190) -> np.ndarray:
    resized = cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    canvas = np.full((size + 30, size, 3), 245, np.uint8)
    canvas[30:] = resized
    cv2.putText(
        canvas,
        title,
        (7, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.43,
        (28, 34, 42),
        1,
        cv2.LINE_AA,
    )
    return canvas


def phase1_evidence(source: np.ndarray, mask: np.ndarray, edges: np.ndarray) -> np.ndarray:
    evidence = source.copy()
    evidence[mask == 0] = (
        evidence[mask == 0].astype(np.float32) * 0.2 + 245.0 * 0.8
    ).astype(np.uint8)
    evidence[edges > 0] = (30, 130, 245)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(evidence, contours, -1, (40, 190, 80), 2, cv2.LINE_AA)
    return evidence


def review_sheet(rows: list[tuple[str, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]) -> np.ndarray:
    rendered = []
    for view, source, evidence, depth, uncertainty in rows:
        rendered.append(
            cv2.hconcat(
                [
                    image_panel(source, f"{view.upper()} NORMALIZED"),
                    image_panel(evidence, "PHASE 1 MASK + EDGES"),
                    image_panel(depth, "RELATIVE DEPTH"),
                    image_panel(uncertainty, "FLIP UNCERTAINTY"),
                ]
            )
        )
    return cv2.vconcat(rendered)


def overview_sheet(cells: list[tuple[str, np.ndarray, np.ndarray]]) -> np.ndarray:
    rendered = []
    for object_id, source, depth in cells:
        left = image_panel(source, object_id.upper(), 135)
        right = image_panel(depth, "ISO DEPTH", 135)
        rendered.append(cv2.hconcat((left, right)))
    rows = []
    for offset in range(0, len(rendered), 4):
        group = rendered[offset : offset + 4]
        while len(group) < 4:
            group.append(np.full_like(rendered[0], 245))
        rows.append(cv2.hconcat(group))
    return cv2.vconcat(rows)


def aggregate(records: list[dict[str, Any]], field: str) -> dict[str, float]:
    values = np.asarray([float(item[field]) for item in records], dtype=np.float64)
    return {
        "mean": round(float(values.mean()), 6),
        "median": round(float(np.median(values)), 6),
        "p95": round(float(np.percentile(values, 95)), 6),
        "max": round(float(values.max()), 6),
    }


def grouped_aggregate(records: list[dict[str, Any]], key: str, field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record[key])].append(record)
    return {name: aggregate(values, field) for name, values in sorted(groups.items())}


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    manifest_path = root / "dataset" / "prepared_v1" / "manifest.jsonl"
    feature_path = root / "dataset" / "phase_runs" / "v1" / "phase1_features.json"
    output = root / "dataset" / "phase_runs" / "v1" / "phase1_depth_anything_v2"
    report_path = output / "report.json"
    if report_path.exists() and not args.force:
        raise FileExistsError(f"{report_path} exists; use --force to rerun explicitly")

    records = read_manifest(manifest_path)
    if len(records) != 24 or any(set(item["views"]) != set(VIEW_ORDER) for item in records):
        raise ValueError("STL-1 prepared manifest must contain 24 complete five-view objects")
    phase1_features = json.loads(feature_path.read_text(encoding="utf-8"))
    if not all(phase1_features.get("checks", {}).values()):
        raise ValueError("Existing dataset Phase 1 feature checks are not all passing")

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    device = torch.device(
        "cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu"
    )
    processor = AutoImageProcessor.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_files_only=args.local_files_only,
        use_fast=False,
    )
    model = AutoModelForDepthEstimation.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_files_only=args.local_files_only,
    ).to(device).eval()

    depth_root = output / "depth_u16"
    uncertainty_root = output / "uncertainty_u16"
    review_root = output / "reviews"
    for directory in (depth_root, uncertainty_root, review_root):
        directory.mkdir(parents=True, exist_ok=True)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()

    all_views: list[dict[str, Any]] = []
    object_reports = []
    overview_cells = []
    started = time.perf_counter()
    for object_index, object_record in enumerate(records, 1):
        object_id = object_record["object_id"]
        split = object_record["split"]
        (depth_root / object_id).mkdir(parents=True, exist_ok=True)
        (uncertainty_root / object_id).mkdir(parents=True, exist_ok=True)
        rows = []
        view_reports: dict[str, Any] = {}
        for view in VIEW_ORDER:
            view_record = object_record["views"][view]
            image_path = root / view_record["image_path"]
            mask_path = root / view_record["jewelry_mask_path"]
            edge_path = root / view_record["edge_path"]
            image = Image.open(image_path).convert("RGB")
            source = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            edges = cv2.imread(str(edge_path), cv2.IMREAD_GRAYSCALE)
            if mask is None or edges is None or mask.shape != source.shape[:2]:
                raise ValueError(f"Invalid Phase 1 evidence for {object_id}:{view}")
            mask = np.where(mask > 127, 255, 0).astype(np.uint8)

            view_started = time.perf_counter()
            depth = infer(image, processor, model, device)
            flipped = infer(image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), processor, model, device)
            aligned_flip = align_prediction(depth, np.fliplr(flipped).copy(), mask)
            uncertainty = np.abs(depth - aligned_flip)
            normalized, low, high = robust_normalize(depth, mask)
            normalized_uncertainty, uncertainty_low, uncertainty_high = robust_normalize(uncertainty, mask)
            depth_span = max(high - low, 1e-6)
            masked_uncertainty = uncertainty[mask > 0]
            normalized_mean_error = float(masked_uncertainty.mean() / depth_span)
            normalized_p95_error = float(np.percentile(masked_uncertainty, 95) / depth_span)

            depth_path = depth_root / object_id / f"{view}.png"
            uncertainty_path = uncertainty_root / object_id / f"{view}.png"
            depth_u16 = np.where(mask > 0, np.round(normalized * 65535), 0).astype(np.uint16)
            uncertainty_u16 = np.where(
                mask > 0, np.round(normalized_uncertainty * 65535), 0
            ).astype(np.uint16)
            if not cv2.imwrite(str(depth_path), depth_u16):
                raise OSError(f"Cannot write {depth_path}")
            if not cv2.imwrite(str(uncertainty_path), uncertainty_u16):
                raise OSError(f"Cannot write {uncertainty_path}")

            depth_preview = colorize(normalized, mask)
            uncertainty_preview = colorize(normalized_uncertainty, mask)
            evidence = phase1_evidence(source, mask, edges)
            rows.append((view, source, evidence, depth_preview, uncertainty_preview))
            if view == "iso":
                overview_cells.append((object_id, source, depth_preview))

            result = {
                "object_id": object_id,
                "split": split,
                "view": view,
                "authority": "machine_proposal",
                "metric": False,
                "cross_view_aligned": False,
                "image_path": view_record["image_path"],
                "image_sha256": sha256(image_path),
                "mask_path": view_record["jewelry_mask_path"],
                "mask_authority": "pseudo_background_difference",
                "depth_u16": str(depth_path.relative_to(root)),
                "uncertainty_u16": str(uncertainty_path.relative_to(root)),
                "raw_float32_sha256": array_sha256(depth),
                "robust_depth_range": {"p02": float(low), "p98": float(high)},
                "robust_uncertainty_range": {
                    "p02": float(uncertainty_low),
                    "p98": float(uncertainty_high),
                },
                "mean_flip_error_over_depth_span": round(normalized_mean_error, 6),
                "p95_flip_error_over_depth_span": round(normalized_p95_error, 6),
                "runtime_seconds": round(time.perf_counter() - view_started, 6),
            }
            all_views.append(result)
            view_reports[view] = result

        review_path = review_root / f"{object_id}_review.jpg"
        if not cv2.imwrite(
            str(review_path),
            review_sheet(rows),
            (cv2.IMWRITE_JPEG_QUALITY, 92),
        ):
            raise OSError(f"Cannot write {review_path}")
        object_reports.append(
            {
                "object_id": object_id,
                "source_name": object_record.get("source_object_name", object_id),
                "split": split,
                "status": "machine_proposals_complete_human_review_missing",
                "review_sheet": str(review_path.relative_to(root)),
                "views": view_reports,
            }
        )
        print(f"[{object_index:02d}/24] {object_id} complete", flush=True)

    overview_path = output / "dataset_depth_overview.jpg"
    if not cv2.imwrite(
        str(overview_path), overview_sheet(overview_cells), (cv2.IMWRITE_JPEG_QUALITY, 92)
    ):
        raise OSError(f"Cannot write {overview_path}")

    expected_views = len(records) * len(VIEW_ORDER)
    runtime = time.perf_counter() - started
    ranking = sorted(all_views, key=lambda item: item["mean_flip_error_over_depth_span"], reverse=True)
    report = {
        "schema_version": "lalitha_stl1_phase1_depth_v1",
        "created_at_utc": utc_now(),
        "phase": "Phase 1 dataset depth proposal benchmark",
        "status": "completed_research_only",
        "decision": "research_only",
        "source": {
            "dataset": "STL-1",
            "prepared_manifest": str(manifest_path.relative_to(root)),
            "prepared_manifest_sha256": sha256(manifest_path),
            "phase1_feature_report": str(feature_path.relative_to(root)),
            "phase1_feature_report_sha256": sha256(feature_path),
            "commit": git_commit(root),
            "pipeline": "pipeline/infer_dataset_depth_anything_v2.py",
            "pipeline_sha256": sha256(Path(__file__)),
        },
        "model": {
            "id": MODEL_ID,
            "revision": MODEL_REVISION,
            "license": MODEL_LICENSE,
            "role": "relative-depth and uncertainty proposal",
        },
        "runtime": {
            "device": str(device),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "total_seconds": round(runtime, 6),
            "mean_seconds_per_view": round(runtime / expected_views, 6),
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated())
            if device.type == "cuda"
            else 0,
        },
        "coverage": {
            "object_count": len(records),
            "view_count": len(all_views),
            "views_per_object": len(VIEW_ORDER),
            "view_order": list(VIEW_ORDER),
            "splits": {
                split: sum(item["split"] == split for item in records)
                for split in ("train", "val", "test")
            },
        },
        "checks": {
            "all_24_objects_processed": len(records) == 24,
            "all_120_views_processed": len(all_views) == expected_views == 120,
            "existing_phase1_checks_pass": all(phase1_features["checks"].values()),
            "all_depth_outputs_written": all(
                (root / item["depth_u16"]).is_file() for item in all_views
            ),
            "all_uncertainty_outputs_written": all(
                (root / item["uncertainty_u16"]).is_file() for item in all_views
            ),
            "all_predictions_finite": all(
                np.isfinite(item["mean_flip_error_over_depth_span"]) for item in all_views
            ),
        },
        "phase1_gate": {
            "machine_image_evidence_complete": True,
            "human_reviewed_masks": False,
            "reviewed_component_identities": False,
            "calibrated_cameras": False,
            "physical_scale": False,
            "metric_depth": False,
            "cross_view_consistent_depth": False,
            "status": "blocked",
        },
        "metrics": {
            "name": "flip consistency diagnostic; lower is more self-consistent",
            "accuracy_metric": False,
            "overall": aggregate(all_views, "mean_flip_error_over_depth_span"),
            "by_view": grouped_aggregate(all_views, "view", "mean_flip_error_over_depth_span"),
            "by_split": grouped_aggregate(all_views, "split", "mean_flip_error_over_depth_span"),
            "highest_uncertainty": [
                {
                    "object_id": item["object_id"],
                    "view": item["view"],
                    "value": item["mean_flip_error_over_depth_span"],
                }
                for item in ranking[:10]
            ],
            "lowest_uncertainty": [
                {
                    "object_id": item["object_id"],
                    "view": item["view"],
                    "value": item["mean_flip_error_over_depth_span"],
                }
                for item in reversed(ranking[-10:])
            ],
        },
        "overview": str(overview_path.relative_to(root)),
        "objects": object_reports,
        "limitations": [
            "No human depth, scan or CAD ground truth exists for STL-1, so depth accuracy is not measured.",
            "The silhouette masks are pseudo-labels and are used only to scope diagnostics.",
            "Depth is relative, independently normalized per image and not expressed in millimetres.",
            "Monocular predictions are not cross-view consistent by default.",
            "Reflective metal, transparent stones, prongs and shadows remain likely failure regions.",
            "Flip consistency is not accuracy; it is only a model self-consistency diagnostic.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    report = run(args)
    print(
        json.dumps(
            {
                "status": report["status"],
                "coverage": report["coverage"],
                "checks": report["checks"],
                "runtime": report["runtime"],
                "metrics": report["metrics"]["overall"],
                "phase1_gate": report["phase1_gate"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
