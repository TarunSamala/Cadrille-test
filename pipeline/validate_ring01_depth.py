"""Validate Ring01 relative-depth proposals without claiming metric truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
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


VIEWS = ("front", "side", "top", "angled", "back")
VIEW_CONTRACT = {
    "front": {
        "observed_role": "gemstone-face view with horizontal shank shoulders",
        "source_label": "front",
        "camera_pose_known": False,
        "symmetry_prior": "horizontal strong; vertical approximate within the central head only",
    },
    "side": {
        "observed_role": "ring-profile view showing hoop, basket and head elevation",
        "source_label": "side",
        "camera_pose_known": False,
        "symmetry_prior": "horizontal approximate; vertical invalid",
    },
    "top": {
        "observed_role": "second near gemstone-face view; not a calibrated geometric top camera",
        "source_label": "top",
        "camera_pose_known": False,
        "symmetry_prior": "horizontal strong; vertical approximate within the central head only",
    },
    "angled": {
        "observed_role": "oblique view showing gemstone face, head elevation and hoop",
        "source_label": "angled",
        "camera_pose_known": False,
        "symmetry_prior": "none",
    },
    "back": {
        "observed_role": "opposite-labelled ring-profile view showing hoop and basket",
        "source_label": "back",
        "camera_pose_known": False,
        "symmetry_prior": "horizontal approximate; vertical invalid",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def read_mask(path: Path, shape: tuple[int, int]) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None or mask.shape != shape:
        raise ValueError(f"Invalid mask: {path}")
    return np.where(mask > 127, 255, 0).astype(np.uint8)


def normalized_error(reference: np.ndarray, candidate: np.ndarray, mask: np.ndarray) -> float:
    valid = mask > 0
    low, high = np.percentile(reference[valid], (2.0, 98.0))
    return float(np.abs(reference[valid] - candidate[valid]).mean() / max(high - low, 1e-6))


def split_statistics(values: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    ys, xs = np.where(mask > 0)
    if not len(xs):
        return {}
    x_mid = (int(xs.min()) + int(xs.max()) + 1) / 2.0
    y_mid = (int(ys.min()) + int(ys.max()) + 1) / 2.0
    regions = {
        "top": (mask > 0) & (np.indices(mask.shape)[0] < y_mid),
        "bottom": (mask > 0) & (np.indices(mask.shape)[0] >= y_mid),
        "left": (mask > 0) & (np.indices(mask.shape)[1] < x_mid),
        "right": (mask > 0) & (np.indices(mask.shape)[1] >= x_mid),
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


def component_statistics(
    normalized: np.ndarray, root: Path, view: str, shape: tuple[int, int]
) -> dict[str, Any]:
    result = {}
    for label in ("shank", "stone_visible", "setting", "prongs", "negative_space"):
        if label == "negative_space":
            path = (
                root
                / "data"
                / "ring01_ground_truth_v1"
                / "proposals"
                / "negative_space"
                / f"ring01_{view}_negative_space_proposal.png"
            )
        else:
            path = (
                root
                / "data"
                / "ring01_phase2_refined"
                / "masks"
                / label
                / f"ring01_{view}_{label}.png"
            )
        mask = read_mask(path, shape)
        selected = normalized[mask > 0]
        result[label] = {
            "pixels": int(selected.size),
            "mean": round(float(selected.mean()), 6) if selected.size else None,
            "median": round(float(np.median(selected)), 6) if selected.size else None,
        }
    return result


def depth_overlay(source: np.ndarray, depth_color: np.ndarray, mask: np.ndarray) -> np.ndarray:
    result = source.copy()
    valid = mask > 0
    result[valid] = cv2.addWeighted(source[valid], 0.48, depth_color[valid], 0.52, 0)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(result, contours, -1, (28, 35, 43), 1, cv2.LINE_AA)
    return result


def panel(image: np.ndarray, title: str, subtitle: str = "", height: int = 260) -> np.ndarray:
    scale = height / image.shape[0]
    width = max(1, int(round(image.shape[1] * scale)))
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    canvas = np.full((height + 54, width, 3), 245, np.uint8)
    canvas[54:] = resized
    cv2.putText(canvas, title, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (25, 32, 40), 1, cv2.LINE_AA)
    if subtitle:
        cv2.putText(canvas, subtitle, (8, 41), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (75, 82, 90), 1, cv2.LINE_AA)
    return canvas


def front_audit(
    source: np.ndarray,
    raw_color: np.ndarray,
    regularized_color: np.ndarray,
    uncertainty_color: np.ndarray,
    overlay: np.ndarray,
    imbalance: float,
) -> np.ndarray:
    items = [
        panel(source, "SOURCE", "Observed RGB pixels"),
        panel(raw_color, "RAW RELATIVE DEPTH", f"Top-bottom mean delta {imbalance:+.4f}"),
        panel(regularized_color, "SYMMETRY-REGULARIZED", "Diagnostic proposal, not truth"),
        panel(uncertainty_color, "TRANSFORM UNCERTAINTY", "Brighter/warmer = less stable"),
        panel(overlay, "PHOTO + DEPTH", "Non-metric relative score overlay"),
    ]
    return cv2.hconcat(items)


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    workspace = root / "data" / "ring01_ground_truth_v1"
    output = workspace / "depth_validation_v1"
    report_path = output / "report.json"
    if report_path.exists() and not args.force:
        raise FileExistsError(f"{report_path} exists; use --force to rerun")
    output.mkdir(parents=True, exist_ok=True)

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
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()

    started = time.perf_counter()
    view_reports: dict[str, Any] = {}
    all_view_panels = []
    for view in VIEWS:
        source_path = root / "data" / "ring01_reference_images" / f"ring01_{view}.png"
        mask_path = (
            root
            / "data"
            / "ring01_phase2_refined"
            / "masks"
            / "jewelry"
            / f"ring01_{view}_jewelry.png"
        )
        stone_path = (
            root
            / "data"
            / "ring01_phase2_refined"
            / "masks"
            / "stone_visible"
            / f"ring01_{view}_stone_visible.png"
        )
        image = Image.open(source_path).convert("RGB")
        source = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        mask = read_mask(mask_path, source.shape[:2])
        stone_mask = read_mask(stone_path, source.shape[:2])

        repeated = [infer(image, processor, model, device) for _ in range(args.repeats)]
        reference = repeated[0]
        repeat_hashes = [array_sha256(item) for item in repeated]
        repeat_max_abs = [float(np.max(np.abs(reference - item))) for item in repeated[1:]]

        horizontal = infer(
            image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), processor, model, device
        )
        horizontal = align_prediction(reference, np.fliplr(horizontal).copy(), mask)
        vertical = infer(
            image.transpose(Image.Transpose.FLIP_TOP_BOTTOM), processor, model, device
        )
        vertical = align_prediction(reference, np.flipud(vertical).copy(), mask)
        normalized, low, high = robust_normalize(reference, mask)
        h_normalized, _, _ = robust_normalize(horizontal, mask)
        v_normalized, _, _ = robust_normalize(vertical, mask)

        if view in {"front", "top"}:
            regularized = (reference + horizontal + vertical) / 3.0
            regularization = "horizontal_and_vertical_symmetry_diagnostic"
        elif view in {"side", "back"}:
            regularized = (reference + horizontal) / 2.0
            regularization = "horizontal_symmetry_diagnostic"
        else:
            regularized = reference.copy()
            regularization = "none_for_oblique_view"
        regularized_normalized, regularized_low, regularized_high = robust_normalize(
            regularized, mask
        )
        transform_uncertainty = np.maximum(
            np.abs(normalized - h_normalized), np.abs(normalized - v_normalized)
        )
        uncertainty_normalized, uncertainty_low, uncertainty_high = robust_normalize(
            transform_uncertainty, mask
        )

        raw_color = colorize(normalized, mask)
        regularized_color = colorize(regularized_normalized, mask)
        uncertainty_color = colorize(uncertainty_normalized, mask)
        overlay = depth_overlay(source, raw_color, mask)
        regularized_path = output / f"ring01_{view}_symmetry_regularized_relative_depth.npy"
        overlay_path = output / f"ring01_{view}_depth_overlay.png"
        np.save(regularized_path, regularized.astype(np.float32))
        cv2.imwrite(str(overlay_path), overlay)

        full_stats = split_statistics(normalized, mask)
        stone_stats = split_statistics(normalized, stone_mask)
        report = {
            "view_contract": VIEW_CONTRACT[view],
            "source": str(source_path.relative_to(root)),
            "source_sha256": sha256(source_path),
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
            "raw_robust_range": {"p02": low, "p98": high},
            "regularization": regularization,
            "regularized_robust_range": {
                "p02": regularized_low,
                "p98": regularized_high,
            },
            "transform_uncertainty_range": {
                "p02": uncertainty_low,
                "p98": uncertainty_high,
            },
            "whole_object_distribution": full_stats,
            "stone_distribution": stone_stats,
            "regularized_whole_object_distribution": split_statistics(
                regularized_normalized, mask
            ),
            "regularized_stone_distribution": split_statistics(
                regularized_normalized, stone_mask
            ),
            "component_relative_depth": component_statistics(
                normalized, root, view, source.shape[:2]
            ),
            "symmetry_regularized_raw": str(regularized_path.relative_to(root)),
            "photo_depth_overlay": str(overlay_path.relative_to(root)),
            "metric": False,
            "cross_view_aligned": False,
        }
        view_reports[view] = report
        all_view_panels.append(
            cv2.hconcat(
                [
                    panel(source, f"{view.upper()} SOURCE", height=190),
                    panel(raw_color, "RAW RELATIVE DEPTH", height=190),
                    panel(regularized_color, "REGULARIZED PROPOSAL", height=190),
                    panel(uncertainty_color, "TRANSFORM UNCERTAINTY", height=190),
                ]
            )
        )
        if view == "front":
            front_overlay_path = output / "ring01_front_photo_with_depth.png"
            cv2.imwrite(str(front_overlay_path), overlay)
            front_audit_path = output / "ring01_front_depth_audit.png"
            cv2.imwrite(
                str(front_audit_path),
                front_audit(
                    source,
                    raw_color,
                    regularized_color,
                    uncertainty_color,
                    overlay,
                    full_stats["top_minus_bottom_mean"],
                ),
            )

    all_views_path = output / "ring01_all_views_depth_validation.png"
    width = max(row.shape[1] for row in all_view_panels)
    padded = [
        cv2.copyMakeBorder(
            row,
            0,
            0,
            0,
            width - row.shape[1],
            cv2.BORDER_CONSTANT,
            value=(245, 245, 245),
        )
        for row in all_view_panels
    ]
    cv2.imwrite(str(all_views_path), cv2.vconcat(padded))

    report = {
        "schema_version": "lalitha_ring01_depth_validation_v1",
        "created_at_utc": utc_now(),
        "status": "completed_research_only",
        "model": {
            "id": MODEL_ID,
            "revision": MODEL_REVISION,
            "license": MODEL_LICENSE,
        },
        "runtime": {
            "device": str(device),
            "repeat_count": args.repeats,
            "total_seconds": round(time.perf_counter() - started, 6),
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated())
            if device.type == "cuda"
            else 0,
        },
        "checks": {
            "all_five_views_processed": len(view_reports) == 5,
            "all_three_repeats_identical": all(
                item["repeat_deterministic"] for item in view_reports.values()
            ),
            "all_outputs_finite": all(
                np.isfinite(item["horizontal_flip_error_over_depth_span"])
                and np.isfinite(item["vertical_flip_error_over_depth_span"])
                for item in view_reports.values()
            ),
        },
        "validation_layers": {
            "repeatability": "three independent forward passes per source view",
            "transformation_consistency": "horizontal and vertical flip diagnostics",
            "component_consistency": "relative-depth summaries inside Phase 1 component masks",
            "cross_view_geometry": "blocked_without_camera_correspondence_and_calibration",
        },
        "metric_depth": {
            "status": "blocked",
            "unit": None,
            "millimetres_per_depth_unit": None,
            "centimetres_per_depth_unit": None,
            "required": [
                "at least one verified physical dimension",
                "camera intrinsics or a calibrated capture protocol",
                "cross-view camera poses and correspondences or scan supervision",
            ],
        },
        "views": view_reports,
        "front_photo_with_depth": str(front_overlay_path.relative_to(root)),
        "front_audit": str(front_audit_path.relative_to(root)),
        "all_views_audit": str(all_views_path.relative_to(root)),
        "decision": "relative_depth_is_repeatable_but_not_geometrically_validated",
        "limitations": [
            "Repeated inference validates determinism, not geometric correctness.",
            "Specular metal, faceted transparent stone, highlights and shadows bias monocular depth.",
            "The symmetry-regularized output is a diagnostic hypothesis and is retained separately from raw depth.",
            "The five labels are semantic view names, not calibrated camera extrinsics.",
            "Metric millimetre or centimetre depth is unavailable from the current evidence.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.repeats < 2:
        raise ValueError("At least two repeats are required for validation")
    report = run(args)
    print(
        json.dumps(
            {
                "status": report["status"],
                "checks": report["checks"],
                "runtime": report["runtime"],
                "front_whole_object": report["views"]["front"]["whole_object_distribution"],
                "front_stone": report["views"]["front"]["stone_distribution"],
                "metric_depth": report["metric_depth"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
