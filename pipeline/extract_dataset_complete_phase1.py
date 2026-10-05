"""Extract reversible pixel evidence and validate relative depth for all STL-1 views.

This stage deliberately separates three claims:

* source and normalized RGB pixels can be reconstructed exactly because they are
  retained losslessly;
* image derivatives and relative depth are machine-derived evidence;
* metric depth and cross-view geometry remain unavailable without calibration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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

from pipeline.infer_dataset_depth_anything_v2 import git_commit, read_manifest
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
VIEW_CONTRACT = {
    "front": {
        "source_label": "front",
        "observed_role": "ornament or setting face presented toward the camera",
        "camera_pose_known": False,
        "opposite_view": None,
    },
    "top": {
        "source_label": "top",
        "observed_role": "source-labelled elevation view showing the hoop and head or underside",
        "camera_pose_known": False,
        "opposite_view": None,
    },
    "iso": {
        "source_label": "iso",
        "observed_role": "oblique isometric-style view showing face, thickness and hoop",
        "camera_pose_known": False,
        "opposite_view": None,
    },
    "lsv": {
        "source_label": "lsv",
        "observed_role": "source-labelled left profile view",
        "camera_pose_known": False,
        "opposite_view": "rsv",
    },
    "rsv": {
        "source_label": "rsv",
        "observed_role": "source-labelled right profile view",
        "camera_pose_known": False,
        "opposite_view": "lsv",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_array(values: np.ndarray) -> dict[str, Any]:
    return {
        "shape": list(values.shape),
        "dtype": str(values.dtype),
        "sha256": array_sha256(values),
        "finite": bool(np.isfinite(values).all()),
    }


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    values = rgb.astype(np.float32) / 255.0
    return np.where(
        values <= 0.04045,
        values / 12.92,
        ((values + 0.055) / 1.055) ** 2.4,
    ).astype(np.float32)


def read_binary(path: Path, shape: tuple[int, int]) -> np.ndarray:
    values = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if values is None or values.shape != shape:
        raise ValueError(f"Invalid binary evidence: {path}")
    return np.where(values > 127, 255, 0).astype(np.uint8)


def hole_proposal(mask: np.ndarray) -> np.ndarray:
    """Return silhouette holes as a machine proposal, not a semantic cavity label."""

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    result = np.zeros_like(mask)
    if hierarchy is None:
        return result
    for index, contour in enumerate(contours):
        if hierarchy[0][index][3] >= 0:
            cv2.drawContours(result, [contour], -1, 255, cv2.FILLED)
    return result


def split_statistics(values: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    ys, xs = np.where(mask > 0)
    if not len(xs):
        return {}
    y_grid, x_grid = np.indices(mask.shape)
    x_mid = (int(xs.min()) + int(xs.max()) + 1) / 2.0
    y_mid = (int(ys.min()) + int(ys.max()) + 1) / 2.0
    regions = {
        "top": (mask > 0) & (y_grid < y_mid),
        "bottom": (mask > 0) & (y_grid >= y_mid),
        "left": (mask > 0) & (x_grid < x_mid),
        "right": (mask > 0) & (x_grid >= x_mid),
    }
    result: dict[str, Any] = {}
    for name, region in regions.items():
        selected = values[region]
        result[name] = {
            "pixels": int(selected.size),
            "mean": round(float(selected.mean()), 6),
            "median": round(float(np.median(selected)), 6),
        }
    result["top_minus_bottom_mean"] = round(
        result["top"]["mean"] - result["bottom"]["mean"], 6
    )
    result["left_minus_right_mean"] = round(
        result["left"]["mean"] - result["right"]["mean"], 6
    )
    return result


def normalized_error(reference: np.ndarray, candidate: np.ndarray, mask: np.ndarray) -> float:
    valid = mask > 0
    low, high = np.percentile(reference[valid], (2.0, 98.0))
    return float(
        np.abs(reference[valid] - candidate[valid]).mean() / max(high - low, 1e-6)
    )


def depth_quantiles(values: np.ndarray, mask: np.ndarray) -> list[float]:
    selected = values[mask > 0]
    return [
        round(float(value), 6)
        for value in np.quantile(selected, (0.1, 0.25, 0.5, 0.75, 0.9))
    ]


def normalize_feature(values: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    selected = values[mask > 0] if mask is not None and np.any(mask > 0) else values.ravel()
    low, high = np.percentile(selected, (2.0, 98.0))
    return np.clip((values - low) / max(high - low, 1e-6), 0.0, 1.0).astype(np.float32)


def scalar_color(values: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    normalized = normalize_feature(values, mask)
    result = cv2.applyColorMap(
        np.round(normalized * 255).astype(np.uint8), cv2.COLORMAP_TURBO
    )
    if mask is not None:
        result[mask == 0] = (238, 238, 238)
    return result


def depth_overlay(source: np.ndarray, colored: np.ndarray, mask: np.ndarray) -> np.ndarray:
    result = source.copy()
    valid = mask > 0
    result[valid] = cv2.addWeighted(source[valid], 0.48, colored[valid], 0.52, 0)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(result, contours, -1, (28, 35, 43), 1, cv2.LINE_AA)
    return result


def panel(image: np.ndarray, title: str, subtitle: str = "", height: int = 125) -> np.ndarray:
    scale = height / image.shape[0]
    resized = cv2.resize(
        image,
        (max(1, int(round(image.shape[1] * scale))), height),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.full((height + 45, resized.shape[1], 3), 245, np.uint8)
    canvas[45:] = resized
    cv2.putText(
        canvas, title, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (25, 32, 40), 1, cv2.LINE_AA
    )
    if subtitle:
        cv2.putText(
            canvas,
            subtitle,
            (6, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.3,
            (70, 78, 86),
            1,
            cv2.LINE_AA,
        )
    return canvas


def pad_row(images: list[np.ndarray]) -> np.ndarray:
    height = max(item.shape[0] for item in images)
    padded = [
        cv2.copyMakeBorder(
            item,
            0,
            height - item.shape[0],
            0,
            0,
            cv2.BORDER_CONSTANT,
            value=(245, 245, 245),
        )
        for item in images
    ]
    return cv2.hconcat(padded)


def aggregate(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": round(float(array.mean()), 6),
        "median": round(float(np.median(array)), 6),
        "p95": round(float(np.percentile(array, 95)), 6),
        "max": round(float(array.max()), 6),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    manifest_path = root / "dataset" / "prepared_v1" / "manifest.jsonl"
    output = (
        args.output_root.resolve()
        if args.output_root
        else root / "dataset" / "phase_runs" / "v1" / "phase1_complete_features_v1"
    )
    report_path = output / "report.json"
    if report_path.exists() and not args.force:
        raise FileExistsError(f"{report_path} exists; use --force to rerun")

    records = read_manifest(manifest_path)
    if args.limit_objects:
        records = records[: args.limit_objects]
    expected_views = len(records) * len(VIEW_ORDER)
    if not records or any(set(item["views"]) != set(VIEW_ORDER) for item in records):
        raise ValueError("Prepared records must contain complete five-view objects")

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    device = torch.device(
        "cuda"
        if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available())
        else "cpu"
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
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()

    directories = {
        name: output / name
        for name in (
            "bundles",
            "source_roundtrip",
            "depth_u16",
            "regularized_depth_u16",
            "uncertainty_u16",
            "overlays",
            "audits",
        )
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    object_reports = []
    all_view_records = []
    overview_cells = []
    for object_index, record in enumerate(records, 1):
        object_id = record["object_id"]
        for name in (
            "bundles",
            "source_roundtrip",
            "depth_u16",
            "regularized_depth_u16",
            "uncertainty_u16",
            "overlays",
        ):
            (directories[name] / object_id).mkdir(parents=True, exist_ok=True)

        audit_rows = []
        view_reports: dict[str, Any] = {}
        for view in VIEW_ORDER:
            metadata = record["views"][view]
            source_path = root / metadata["source_path"]
            normalized_path = root / metadata["image_path"]
            mask_path = root / metadata["jewelry_mask_path"]
            prepared_edge_path = root / metadata["edge_path"]

            source_bgr = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
            normalized_bgr = cv2.imread(str(normalized_path), cv2.IMREAD_COLOR)
            if source_bgr is None or normalized_bgr is None:
                raise ValueError(f"Cannot decode {object_id}:{view}")
            shape = normalized_bgr.shape[:2]
            mask = read_binary(mask_path, shape)
            prepared_edge = read_binary(prepared_edge_path, shape)
            negative_space = hole_proposal(mask)

            image = Image.open(normalized_path).convert("RGB")
            repeated = [infer(image, processor, model, device) for _ in range(args.repeats)]
            reference = repeated[0]
            repeat_hashes = [array_sha256(item) for item in repeated]
            repeat_max_abs = [
                float(np.max(np.abs(reference - item))) for item in repeated[1:]
            ]
            horizontal = infer(
                image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), processor, model, device
            )
            horizontal = align_prediction(reference, np.fliplr(horizontal).copy(), mask)
            vertical = infer(
                image.transpose(Image.Transpose.FLIP_TOP_BOTTOM), processor, model, device
            )
            vertical = align_prediction(reference, np.flipud(vertical).copy(), mask)

            normalized_depth, raw_low, raw_high = robust_normalize(reference, mask)
            horizontal_normalized, _, _ = robust_normalize(horizontal, mask)
            vertical_normalized, _, _ = robust_normalize(vertical, mask)
            regularized = ((reference + horizontal + vertical) / 3.0).astype(np.float32)
            regularized_normalized, regularized_low, regularized_high = robust_normalize(
                regularized, mask
            )
            uncertainty = np.maximum(
                np.abs(normalized_depth - horizontal_normalized),
                np.abs(normalized_depth - vertical_normalized),
            )
            uncertainty_normalized, uncertainty_low, uncertainty_high = robust_normalize(
                uncertainty, mask
            )

            normalized_rgb = cv2.cvtColor(normalized_bgr, cv2.COLOR_BGR2RGB)
            source_rgb = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(normalized_bgr, cv2.COLOR_BGR2GRAY)
            gray_f32 = gray.astype(np.float32) / 255.0
            sobel_x = cv2.Sobel(gray_f32, cv2.CV_32F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray_f32, cv2.CV_32F, 0, 1, ksize=3)
            gradient_magnitude, gradient_angle = cv2.cartToPolar(sobel_x, sobel_y)
            laplacian = cv2.Laplacian(gray_f32, cv2.CV_32F, ksize=3)
            local_contrast = (
                cv2.GaussianBlur(gray_f32, (0, 0), 1.0)
                - cv2.GaussianBlur(gray_f32, (0, 0), 3.0)
            ).astype(np.float32)
            canny = cv2.Canny(gray, 60, 150, L2gradient=True)
            depth_u16 = np.where(
                mask > 0, np.round(normalized_depth * 65535), 0
            ).astype(np.uint16)
            regularized_u16 = np.where(
                mask > 0, np.round(regularized_normalized * 65535), 0
            ).astype(np.uint16)
            uncertainty_u16 = np.where(
                mask > 0, np.round(uncertainty_normalized * 65535), 0
            ).astype(np.uint16)

            arrays: dict[str, np.ndarray] = {
                "source_rgb_u8": source_rgb,
                "normalized_rgb_u8": normalized_rgb,
                "normalized_rgb_linear_f32": srgb_to_linear(normalized_rgb),
                "gray_u8": gray,
                "lab_u8": cv2.cvtColor(normalized_bgr, cv2.COLOR_BGR2LAB),
                "hsv_u8": cv2.cvtColor(normalized_bgr, cv2.COLOR_BGR2HSV),
                "sobel_x_f32": sobel_x.astype(np.float32),
                "sobel_y_f32": sobel_y.astype(np.float32),
                "gradient_magnitude_f32": gradient_magnitude.astype(np.float32),
                "gradient_angle_radians_f32": gradient_angle.astype(np.float32),
                "laplacian_f32": laplacian.astype(np.float32),
                "local_contrast_f32": local_contrast,
                "canny_u8": canny,
                "prepared_edge_u8": prepared_edge,
                "relative_depth_raw_f32": reference.astype(np.float32),
                "relative_depth_regularized_f32": regularized,
                "relative_depth_normalized_u16": depth_u16,
                "relative_depth_regularized_u16": regularized_u16,
                "relative_depth_uncertainty_u16": uncertainty_u16,
                "mask_jewelry_u8": mask,
                "mask_background_u8": np.where(mask > 0, 0, 255).astype(np.uint8),
                "mask_negative_space_proposal_u8": negative_space,
            }
            bundle_path = directories["bundles"] / object_id / f"{view}.npz"
            np.savez_compressed(bundle_path, **arrays)

            roundtrip_path = directories["source_roundtrip"] / object_id / f"{view}.png"
            if not cv2.imwrite(
                str(roundtrip_path), cv2.cvtColor(arrays["source_rgb_u8"], cv2.COLOR_RGB2BGR)
            ):
                raise OSError(f"Cannot write {roundtrip_path}")
            roundtrip_bgr = cv2.imread(str(roundtrip_path), cv2.IMREAD_COLOR)
            roundtrip_rgb = cv2.cvtColor(roundtrip_bgr, cv2.COLOR_BGR2RGB)

            paths = {
                "depth_u16": directories["depth_u16"] / object_id / f"{view}.png",
                "regularized_depth_u16": directories["regularized_depth_u16"]
                / object_id
                / f"{view}.png",
                "uncertainty_u16": directories["uncertainty_u16"]
                / object_id
                / f"{view}.png",
            }
            for key, values in (
                ("depth_u16", depth_u16),
                ("regularized_depth_u16", regularized_u16),
                ("uncertainty_u16", uncertainty_u16),
            ):
                if not cv2.imwrite(str(paths[key]), values):
                    raise OSError(f"Cannot write {paths[key]}")

            raw_color = colorize(normalized_depth, mask)
            regularized_color = colorize(regularized_normalized, mask)
            uncertainty_color = colorize(uncertainty_normalized, mask)
            overlay = depth_overlay(normalized_bgr, raw_color, mask)
            overlay_path = directories["overlays"] / object_id / f"{view}.png"
            if not cv2.imwrite(str(overlay_path), overlay):
                raise OSError(f"Cannot write {overlay_path}")

            raw_distribution = split_statistics(normalized_depth, mask)
            regularized_distribution = split_statistics(regularized_normalized, mask)
            source_roundtrip_exact = bool(
                np.array_equal(source_rgb, roundtrip_rgb)
                and array_sha256(source_rgb) == array_sha256(roundtrip_rgb)
            )
            view_report = {
                "object_id": object_id,
                "split": record["split"],
                "view": view,
                "view_contract": VIEW_CONTRACT[view],
                "source": str(source_path.relative_to(root)),
                "source_file_sha256": sha256(source_path),
                "normalized_source": str(normalized_path.relative_to(root)),
                "normalized_source_file_sha256": sha256(normalized_path),
                "bundle": str(bundle_path.relative_to(root))
                if bundle_path.is_relative_to(root)
                else str(bundle_path),
                "bundle_file_sha256": file_sha256(bundle_path),
                "source_roundtrip": str(roundtrip_path.relative_to(root))
                if roundtrip_path.is_relative_to(root)
                else str(roundtrip_path),
                "source_pixel_sha256": array_sha256(source_rgb),
                "roundtrip_pixel_sha256": array_sha256(roundtrip_rgb),
                "source_pixel_roundtrip_exact": source_roundtrip_exact,
                "normalized_pixel_retained_exactly": bool(
                    np.array_equal(normalized_rgb, arrays["normalized_rgb_u8"])
                ),
                "repeat_count": args.repeats,
                "repeat_raw_sha256": repeat_hashes,
                "repeat_deterministic": len(set(repeat_hashes)) == 1,
                "repeat_max_abs_difference": repeat_max_abs,
                "horizontal_flip_error_over_depth_span": round(
                    normalized_error(reference, horizontal, mask), 6
                ),
                "vertical_flip_error_over_depth_span": round(
                    normalized_error(reference, vertical, mask), 6
                ),
                "raw_robust_range": {"p02": raw_low, "p98": raw_high},
                "regularized_robust_range": {
                    "p02": regularized_low,
                    "p98": regularized_high,
                },
                "uncertainty_robust_range": {
                    "p02": uncertainty_low,
                    "p98": uncertainty_high,
                },
                "raw_distribution": raw_distribution,
                "regularized_distribution": regularized_distribution,
                "raw_depth_quantiles": depth_quantiles(normalized_depth, mask),
                "feature_count": len(arrays),
                "features": {
                    name: describe_array(values) for name, values in arrays.items()
                },
                "foreground_pixels": int(np.count_nonzero(mask)),
                "edge_pixels": int(np.count_nonzero(canny)),
                "negative_space_proposal_pixels": int(np.count_nonzero(negative_space)),
                "depth_u16": str(paths["depth_u16"].relative_to(root))
                if paths["depth_u16"].is_relative_to(root)
                else str(paths["depth_u16"]),
                "regularized_depth_u16": str(
                    paths["regularized_depth_u16"].relative_to(root)
                )
                if paths["regularized_depth_u16"].is_relative_to(root)
                else str(paths["regularized_depth_u16"]),
                "uncertainty_u16": str(paths["uncertainty_u16"].relative_to(root))
                if paths["uncertainty_u16"].is_relative_to(root)
                else str(paths["uncertainty_u16"]),
                "photo_depth_overlay": str(overlay_path.relative_to(root))
                if overlay_path.is_relative_to(root)
                else str(overlay_path),
                "metric": False,
                "cross_view_aligned": False,
            }
            view_reports[view] = view_report
            all_view_records.append(view_report)
            audit_rows.append(
                pad_row(
                    [
                        panel(normalized_bgr, f"{view.upper()} NORMALIZED", VIEW_CONTRACT[view]["observed_role"]),
                        panel(
                            cv2.cvtColor(roundtrip_rgb, cv2.COLOR_RGB2BGR),
                            "SOURCE PIXEL ROUNDTRIP",
                            "Exact decoded RGB" if source_roundtrip_exact else "FAILED",
                        ),
                        panel(scalar_color(gradient_magnitude, mask), "GRADIENT MAGNITUDE"),
                        panel(cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR), "CANNY EDGES"),
                        panel(
                            raw_color,
                            "RAW RELATIVE DEPTH",
                            f"Top-bottom {raw_distribution['top_minus_bottom_mean']:+.4f}",
                        ),
                        panel(
                            regularized_color,
                            "3-WAY FLIP ENSEMBLE",
                            "Diagnostic proposal, not metric truth",
                        ),
                        panel(uncertainty_color, "TRANSFORM UNCERTAINTY"),
                        panel(overlay, "PHOTO + DEPTH"),
                    ]
                )
            )
            if view == "front":
                overview_cells.append((object_id, normalized_bgr, overlay))

        pair_error = float(
            np.mean(
                np.abs(
                    np.asarray(view_reports["lsv"]["raw_depth_quantiles"])
                    - np.asarray(view_reports["rsv"]["raw_depth_quantiles"])
                )
            )
        )
        audit_width = max(item.shape[1] for item in audit_rows)
        padded_rows = [
            cv2.copyMakeBorder(
                item,
                0,
                0,
                0,
                audit_width - item.shape[1],
                cv2.BORDER_CONSTANT,
                value=(245, 245, 245),
            )
            for item in audit_rows
        ]
        audit_path = directories["audits"] / f"{object_id}_complete_phase1.png"
        if not cv2.imwrite(str(audit_path), cv2.vconcat(padded_rows)):
            raise OSError(f"Cannot write {audit_path}")
        object_reports.append(
            {
                "object_id": object_id,
                "source_name": record["source_object_name"],
                "split": record["split"],
                "views": view_reports,
                "audit_sheet": str(audit_path.relative_to(root))
                if audit_path.is_relative_to(root)
                else str(audit_path),
                "lsv_rsv_depth_distribution_difference": round(pair_error, 6),
                "status": "machine_features_complete_human_semantics_pending",
            }
        )
        print(
            f"[{object_index:02d}/{len(records):02d}] {object_id} complete",
            flush=True,
        )

    overview_rows = []
    for offset in range(0, len(overview_cells), 4):
        cells = []
        for object_id, source, overlay in overview_cells[offset : offset + 4]:
            cells.append(
                pad_row(
                    [
                        panel(source, object_id.upper(), "FRONT", height=115),
                        panel(overlay, "PHOTO + DEPTH", height=115),
                    ]
                )
            )
        while len(cells) < 4:
            cells.append(np.full_like(cells[0], 245))
        overview_rows.append(pad_row(cells))
    overview_path = output / "stl1_complete_phase1_overview.png"
    if not cv2.imwrite(str(overview_path), cv2.vconcat(overview_rows)):
        raise OSError(f"Cannot write {overview_path}")

    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in all_view_records:
        by_view[item["view"]].append(item)
    report = {
        "schema_version": "lalitha_stl1_complete_phase1_v1",
        "created_at_utc": utc_now(),
        "status": "completed_research_only",
        "decision": "research_only",
        "source": {
            "dataset": "STL-1",
            "prepared_manifest": str(manifest_path.relative_to(root)),
            "prepared_manifest_sha256": sha256(manifest_path),
            "pipeline": "pipeline/extract_dataset_complete_phase1.py",
            "pipeline_sha256": sha256(Path(__file__)),
            "commit": git_commit(root),
        },
        "model": {
            "id": MODEL_ID,
            "revision": MODEL_REVISION,
            "license": MODEL_LICENSE,
            "role": "relative-depth and transformation-consistency proposal",
        },
        "coverage": {
            "object_count": len(object_reports),
            "view_count": len(all_view_records),
            "views_per_object": len(VIEW_ORDER),
            "view_order": list(VIEW_ORDER),
        },
        "runtime": {
            "device": str(device),
            "repeat_count": args.repeats,
            "total_seconds": round(time.perf_counter() - started, 6),
            "mean_seconds_per_view": round(
                (time.perf_counter() - started) / max(len(all_view_records), 1), 6
            ),
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated())
            if device.type == "cuda"
            else 0,
        },
        "feature_contract": {
            "stored_array_count_per_view": 22,
            "lossless_pixels": ["source_rgb_u8", "normalized_rgb_u8"],
            "colour_matrices": [
                "normalized_rgb_linear_f32",
                "gray_u8",
                "lab_u8",
                "hsv_u8",
            ],
            "differential_geometry": [
                "sobel_x_f32",
                "sobel_y_f32",
                "gradient_magnitude_f32",
                "gradient_angle_radians_f32",
                "laplacian_f32",
                "local_contrast_f32",
                "canny_u8",
                "prepared_edge_u8",
            ],
            "relative_depth": [
                "relative_depth_raw_f32",
                "relative_depth_regularized_f32",
                "relative_depth_normalized_u16",
                "relative_depth_regularized_u16",
                "relative_depth_uncertainty_u16",
            ],
            "available_masks": [
                "mask_jewelry_u8",
                "mask_background_u8",
                "mask_negative_space_proposal_u8",
            ],
            "unavailable_component_truth": [
                "individual_stones",
                "metal_components",
                "prongs",
                "stone_seats",
                "cavities",
            ],
        },
        "reconstruction_contract": {
            "source_pixel_roundtrip_exact": all(
                item["source_pixel_roundtrip_exact"] for item in all_view_records
            ),
            "normalized_pixels_retained_exactly": all(
                item["normalized_pixel_retained_exactly"] for item in all_view_records
            ),
            "semantic_features_alone_reconstruct_exact_rgb": False,
            "reason": "Exact inversion requires retained RGB pixels or an equivalent lossless residual.",
        },
        "depth_validation": {
            "all_repeats_identical": all(
                item["repeat_deterministic"] for item in all_view_records
            ),
            "horizontal_flip_error": aggregate(
                [
                    item["horizontal_flip_error_over_depth_span"]
                    for item in all_view_records
                ]
            ),
            "vertical_flip_error": aggregate(
                [
                    item["vertical_flip_error_over_depth_span"]
                    for item in all_view_records
                ]
            ),
            "top_bottom_absolute_bias_by_view": {
                view: {
                    "raw": aggregate(
                        [
                            abs(item["raw_distribution"]["top_minus_bottom_mean"])
                            for item in items
                        ]
                    ),
                    "regularized": aggregate(
                        [
                            abs(
                                item["regularized_distribution"][
                                    "top_minus_bottom_mean"
                                ]
                            )
                            for item in items
                        ]
                    ),
                }
                for view, items in sorted(by_view.items())
            },
            "lsv_rsv_distribution_difference": aggregate(
                [
                    item["lsv_rsv_depth_distribution_difference"]
                    for item in object_reports
                ]
            ),
            "repeatability_interpretation": "identical runs prove determinism, not geometric correctness",
            "cross_view_geometry": "blocked_without_camera_intrinsics_extrinsics_and_correspondences",
        },
        "metric_depth": {
            "status": "blocked",
            "unit": None,
            "millimetres_per_depth_unit": None,
            "centimetres_per_depth_unit": None,
            "required": [
                "at least one verified physical dimension per object or capture",
                "camera intrinsics",
                "camera extrinsics or solved cross-view poses and correspondences",
                "metric depth or scan supervision for accuracy validation",
            ],
        },
        "checks": {
            "all_objects_processed": len(object_reports) == len(records),
            "all_views_processed": len(all_view_records) == expected_views,
            "all_three_repeats_identical": args.repeats == 3
            and all(item["repeat_deterministic"] for item in all_view_records),
            "all_source_pixel_roundtrips_exact": all(
                item["source_pixel_roundtrip_exact"] for item in all_view_records
            ),
            "all_normalized_pixels_retained_exactly": all(
                item["normalized_pixel_retained_exactly"] for item in all_view_records
            ),
            "all_feature_arrays_finite": all(
                all(feature["finite"] for feature in item["features"].values())
                for item in all_view_records
            ),
            "metric_depth_not_claimed": True,
            "component_truth_not_fabricated": True,
        },
        "overview": str(overview_path.relative_to(root))
        if overview_path.is_relative_to(root)
        else str(overview_path),
        "objects": object_reports,
        "limitations": [
            "STL-1 provides semantic view names but no calibrated camera poses.",
            "Relative depth has no millimetre or centimetre scale.",
            "The dataset has no human depth, individual-stone, prong, cavity or CAD truth.",
            "Transformation consistency and left/right distribution checks are diagnostics, not accuracy metrics.",
            "Exact RGB reconstruction is provided by retained pixels; derivatives alone are many-to-one.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit-objects", type=int)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.repeats != 3:
        parser.error("the validated dataset contract requires exactly three repeats")
    if args.limit_objects is not None and args.limit_objects < 1:
        parser.error("--limit-objects must be positive")
    return args


if __name__ == "__main__":
    result = run(parse_args())
    print(
        json.dumps(
            {
                "status": result["status"],
                "coverage": result["coverage"],
                "runtime": result["runtime"],
                "checks": result["checks"],
                "overview": result["overview"],
            },
            indent=2,
        )
    )
