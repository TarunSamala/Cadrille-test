"""Build a reversible pixel-level Phase 1 feature record for Ring01."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np


VIEWS = ("front", "side", "top", "angled", "back")
MASK_LABELS = (
    "jewelry",
    "metal",
    "shank",
    "stone_visible",
    "setting",
    "prongs",
    "negative_space",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    values = rgb.astype(np.float32) / 255.0
    return np.where(
        values <= 0.04045,
        values / 12.92,
        ((values + 0.055) / 1.055) ** 2.4,
    ).astype(np.float32)


def read_mask(root: Path, view: str, label: str, shape: tuple[int, int]) -> np.ndarray:
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
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None or mask.shape != shape:
        raise ValueError(f"Invalid mask: {path}")
    return np.where(mask > 127, 255, 0).astype(np.uint8)


def describe_array(values: np.ndarray) -> dict[str, Any]:
    return {
        "shape": list(values.shape),
        "dtype": str(values.dtype),
        "sha256": array_sha256(values),
        "finite": bool(np.isfinite(values).all())
        if np.issubdtype(values.dtype, np.number)
        else True,
    }


def normalize_feature(values: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    selected = values[mask > 0] if mask is not None and np.any(mask > 0) else values.reshape(-1)
    low, high = np.percentile(selected, (2.0, 98.0))
    if high <= low:
        high = low + 1e-6
    return np.clip((values - low) / (high - low), 0.0, 1.0).astype(np.float32)


def color_scalar(values: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    normalized = normalize_feature(values, mask)
    color = cv2.applyColorMap(np.round(normalized * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    if mask is not None:
        color[mask == 0] = (238, 238, 238)
    return color


def panel(image: np.ndarray, title: str, height: int = 190) -> np.ndarray:
    scale = height / image.shape[0]
    resized = cv2.resize(
        image,
        (max(1, int(round(image.shape[1] * scale))), height),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.full((height + 30, resized.shape[1], 3), 245, np.uint8)
    canvas[30:] = resized
    cv2.putText(canvas, title, (7, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (25, 32, 40), 1, cv2.LINE_AA)
    return canvas


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    workspace = root / "data" / "ring01_ground_truth_v1"
    output = workspace / "pixel_features_v1"
    report_path = output / "report.json"
    if report_path.exists() and not args.force:
        raise FileExistsError(f"{report_path} exists; use --force to rerun")
    bundle_dir = output / "bundles"
    roundtrip_dir = output / "roundtrip"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    roundtrip_dir.mkdir(parents=True, exist_ok=True)

    depth_metadata = json.loads(
        (workspace / "depth_anything_v2" / "depth_metadata.json").read_text(encoding="utf-8")
    )
    depth_validation = json.loads(
        (workspace / "depth_validation_v1" / "report.json").read_text(encoding="utf-8")
    )
    view_reports: dict[str, Any] = {}
    audit_rows = []
    for view in VIEWS:
        source_path = root / "data" / "ring01_reference_images" / f"ring01_{view}.png"
        source_bgr = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        if source_bgr is None:
            raise ValueError(f"Cannot decode {source_path}")
        rgb = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)
        lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB)
        hsv = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2HSV)
        gray_f32 = gray.astype(np.float32) / 255.0
        sobel_x = cv2.Sobel(gray_f32, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray_f32, cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude, gradient_angle = cv2.cartToPolar(sobel_x, sobel_y)
        laplacian = cv2.Laplacian(gray_f32, cv2.CV_32F, ksize=3)
        canny = cv2.Canny(gray, 60, 150, L2gradient=True)
        local_contrast = (
            cv2.GaussianBlur(gray_f32, (0, 0), 1.0)
            - cv2.GaussianBlur(gray_f32, (0, 0), 3.0)
        ).astype(np.float32)
        masks = {
            label: read_mask(root, view, label, gray.shape) for label in MASK_LABELS
        }

        depth_record = depth_metadata["views"][view]
        raw_depth = np.load(root / depth_record["raw_float32_npy"]).astype(np.float32)
        regularized_depth = np.load(
            root / depth_validation["views"][view]["symmetry_regularized_raw"]
        ).astype(np.float32)
        depth_u16 = cv2.imread(
            str(root / depth_record["normalized_u16"]), cv2.IMREAD_UNCHANGED
        )
        uncertainty_u16 = cv2.imread(
            str(root / depth_record["uncertainty_u16"]), cv2.IMREAD_UNCHANGED
        )
        if depth_u16 is None or uncertainty_u16 is None:
            raise ValueError(f"Missing depth evidence for {view}")

        arrays: dict[str, np.ndarray] = {
            "rgb_u8": rgb,
            "rgb_linear_f32": srgb_to_linear(rgb),
            "gray_u8": gray,
            "lab_u8": lab,
            "hsv_u8": hsv,
            "sobel_x_f32": sobel_x.astype(np.float32),
            "sobel_y_f32": sobel_y.astype(np.float32),
            "gradient_magnitude_f32": gradient_magnitude.astype(np.float32),
            "gradient_angle_radians_f32": gradient_angle.astype(np.float32),
            "laplacian_f32": laplacian.astype(np.float32),
            "local_contrast_f32": local_contrast,
            "canny_u8": canny,
            "relative_depth_raw_f32": raw_depth,
            "relative_depth_regularized_f32": regularized_depth,
            "relative_depth_normalized_u16": depth_u16,
            "relative_depth_uncertainty_u16": uncertainty_u16,
        }
        arrays.update({f"mask_{label}_u8": mask for label, mask in masks.items()})
        bundle_path = bundle_dir / f"ring01_{view}_pixel_features.npz"
        np.savez_compressed(bundle_path, **arrays)

        reconstructed_path = roundtrip_dir / f"ring01_{view}_reconstructed.png"
        if not cv2.imwrite(str(reconstructed_path), cv2.cvtColor(arrays["rgb_u8"], cv2.COLOR_RGB2BGR)):
            raise OSError(f"Cannot write {reconstructed_path}")
        reconstructed = cv2.cvtColor(
            cv2.imread(str(reconstructed_path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB
        )
        source_pixel_sha = array_sha256(rgb)
        reconstructed_pixel_sha = array_sha256(reconstructed)

        jewelry = masks["jewelry"]
        depth_overlay = cv2.imread(
            str(root / depth_validation["views"][view]["photo_depth_overlay"]),
            cv2.IMREAD_COLOR,
        )
        audit_rows.append(
            cv2.hconcat(
                [
                    panel(source_bgr, f"{view.upper()} SOURCE"),
                    panel(cv2.cvtColor(reconstructed, cv2.COLOR_RGB2BGR), "EXACT PIXEL ROUNDTRIP"),
                    panel(color_scalar(gradient_magnitude, jewelry), "GRADIENT MAGNITUDE"),
                    panel(cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR), "CANNY EDGES"),
                    panel(depth_overlay, "PHOTO + RELATIVE DEPTH"),
                ]
            )
        )
        view_reports[view] = {
            "view_contract": depth_validation["views"][view]["view_contract"],
            "source": str(source_path.relative_to(root)),
            "source_file_sha256": file_sha256(source_path),
            "source_pixel_sha256": source_pixel_sha,
            "size_wh": [int(rgb.shape[1]), int(rgb.shape[0])],
            "pixel_count": int(rgb.shape[0] * rgb.shape[1]),
            "bundle": str(bundle_path.relative_to(root)),
            "bundle_file_sha256": file_sha256(bundle_path),
            "reconstructed_image": str(reconstructed_path.relative_to(root)),
            "reconstructed_pixel_sha256": reconstructed_pixel_sha,
            "pixel_roundtrip_exact": bool(
                source_pixel_sha == reconstructed_pixel_sha
                and np.array_equal(rgb, reconstructed)
            ),
            "features": {name: describe_array(values) for name, values in arrays.items()},
            "pixel_statistics": {
                "rgb_mean": [round(float(value), 6) for value in rgb.mean(axis=(0, 1))],
                "rgb_std": [round(float(value), 6) for value in rgb.std(axis=(0, 1))],
                "foreground_pixels": int(np.count_nonzero(jewelry)),
                "canny_edge_pixels": int(np.count_nonzero(canny)),
                "gradient_mean": round(float(gradient_magnitude.mean()), 6),
                "gradient_p95": round(float(np.percentile(gradient_magnitude, 95)), 6),
            },
            "depth_unit": None,
            "metric_depth_available": False,
        }

    audit_path = output / "ring01_phase1_pixel_feature_audit.png"
    width = max(row.shape[1] for row in audit_rows)
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
        for row in audit_rows
    ]
    cv2.imwrite(str(audit_path), cv2.vconcat(padded))

    report = {
        "schema_version": "lalitha_phase1_pixel_features_v1",
        "created_at_utc": utc_now(),
        "phase": "Phase 1 full pixel-level feature extraction",
        "status": "machine_features_complete_human_semantics_pending",
        "object_id": "ring01",
        "view_count": len(view_reports),
        "views": view_reports,
        "feature_groups": {
            "lossless_pixels": ["rgb_u8", "rgb_linear_f32", "gray_u8", "lab_u8", "hsv_u8"],
            "differential_geometry": [
                "sobel_x_f32",
                "sobel_y_f32",
                "gradient_magnitude_f32",
                "gradient_angle_radians_f32",
                "laplacian_f32",
                "local_contrast_f32",
                "canny_u8",
            ],
            "semantic_masks": [f"mask_{label}_u8" for label in MASK_LABELS],
            "depth_evidence": [
                "relative_depth_raw_f32",
                "relative_depth_regularized_f32",
                "relative_depth_normalized_u16",
                "relative_depth_uncertainty_u16",
            ],
        },
        "reconstruction_contract": {
            "pixel_exact_roundtrip": all(
                item["pixel_roundtrip_exact"] for item in view_reports.values()
            ),
            "how": "The lossless RGB pixel matrix is retained in every feature bundle.",
            "semantic_features_alone_reconstruct_exact_rgb": False,
            "reason": "Edges, masks, colour statistics and depth are many-to-one transforms; exact inversion requires source pixels or a lossless residual.",
        },
        "depth_contract": {
            "relative_depth_available": True,
            "metric_depth_available": False,
            "unit": None,
            "conversion_to_mm_or_cm": None,
            "blocked_by": depth_validation["metric_depth"]["required"],
        },
        "audit_sheet": str(audit_path.relative_to(root)),
        "authority": "machine-derived evidence; human review required",
        "decision": "usable_for_review_and_future_fusion_not_metric_cad_truth",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    report = run(args)
    print(
        json.dumps(
            {
                "status": report["status"],
                "view_count": report["view_count"],
                "reconstruction_contract": report["reconstruction_contract"],
                "depth_contract": report["depth_contract"],
                "audit_sheet": report["audit_sheet"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
