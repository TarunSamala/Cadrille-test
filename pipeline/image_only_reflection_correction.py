"""Build a conservative image-only correction for specular shank gaps.

The correction is a topology-informed machine proposal. It fills only inward
notches in the observed central opening that lie outside a robust ellipse and
remain close to the observed shank. It never changes the source image, exterior
silhouette, metric scale, hidden geometry, or CAD.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


TARGET_VIEW = "angled"
MASK_KINDS = ("jewelry", "metal", "shank")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_mask(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(path)
    return np.where(image >= 128, 255, 0).astype(np.uint8)


def largest_inner_opening(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    contours, hierarchy = cv2.findContours(
        mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )
    if hierarchy is None:
        raise ValueError("No contour hierarchy is available")
    candidates = [
        contour
        for index, contour in enumerate(contours)
        if hierarchy[0, index, 3] >= 0 and cv2.contourArea(contour) >= 1000
    ]
    if not candidates:
        raise ValueError("No central opening contour was detected")
    contour = max(candidates, key=cv2.contourArea)
    if len(contour) < 5:
        raise ValueError("Central opening has too few points for ellipse fitting")
    opening = np.zeros_like(mask)
    cv2.drawContours(opening, [contour], -1, 255, thickness=cv2.FILLED)
    return opening, contour


def mask_iou(left: np.ndarray, right: np.ndarray) -> float:
    a = left > 0
    b = right > 0
    union = int(np.count_nonzero(a | b))
    return float(np.count_nonzero(a & b) / union) if union else 1.0


def infer_correction(
    jewelry: np.ndarray,
    shank: np.ndarray,
    max_shank_distance_px: float = 6.0,
) -> dict[str, Any]:
    opening, contour = largest_inner_opening(jewelry)
    ellipse = cv2.fitEllipse(contour)
    ellipse_mask = np.zeros_like(jewelry)
    cv2.ellipse(ellipse_mask, ellipse, 255, thickness=cv2.FILLED)

    center_y = float(ellipse[0][1])
    major_axis = float(max(ellipse[1]))
    correction_y_min = int(round(center_y - 0.08 * major_axis))
    candidate = (opening > 0) & (ellipse_mask == 0)
    candidate[: max(correction_y_min, 0)] = False

    distance_to_shank = cv2.distanceTransform(
        np.where(shank == 0, 1, 0).astype(np.uint8), cv2.DIST_L2, 5
    )
    candidate &= distance_to_shank <= max_shank_distance_px
    correction = np.where(candidate, 255, 0).astype(np.uint8)
    corrected_opening = opening.copy()
    corrected_opening[candidate] = 0

    return {
        "correction": correction,
        "opening": opening,
        "corrected_opening": corrected_opening,
        "ellipse_mask": ellipse_mask,
        "ellipse": {
            "center_xy": [float(ellipse[0][0]), float(ellipse[0][1])],
            "axes_wh": [float(ellipse[1][0]), float(ellipse[1][1])],
            "angle_degrees": float(ellipse[2]),
        },
        "correction_y_min": correction_y_min,
        "max_shank_distance_px": max_shank_distance_px,
        "baseline_opening_ellipse_iou": mask_iou(opening, ellipse_mask),
        "corrected_opening_ellipse_iou": mask_iou(
            corrected_opening, ellipse_mask
        ),
        "correction_pixel_count": int(np.count_nonzero(candidate)),
        "opening_pixel_count_before": int(np.count_nonzero(opening)),
        "opening_pixel_count_after": int(np.count_nonzero(corrected_opening)),
        "max_observed_correction_distance_px": float(
            distance_to_shank[candidate].max() if np.any(candidate) else 0.0
        ),
    }


def add_title(image: np.ndarray, title: str) -> np.ndarray:
    panel = cv2.copyMakeBorder(
        image, 34, 0, 0, 0, cv2.BORDER_CONSTANT, value=(247, 247, 247)
    )
    cv2.putText(
        panel,
        title,
        (8, 23),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.54,
        (28, 28, 28),
        1,
        cv2.LINE_AA,
    )
    return panel


def build_audit(
    source: np.ndarray,
    baseline: np.ndarray,
    corrected: np.ndarray,
    correction: np.ndarray,
) -> np.ndarray:
    overlay = source.copy()
    highlighted = source.copy()
    highlighted[correction > 0] = (40, 70, 255)
    overlay = cv2.addWeighted(source, 0.62, highlighted, 0.38, 0)
    uncertainty = cv2.dilate(
        correction, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    )
    uncertainty_rgb = cv2.applyColorMap(uncertainty, cv2.COLORMAP_TURBO)
    uncertainty_rgb[uncertainty == 0] = (245, 245, 245)
    panels = [
        add_title(source, "SOURCE"),
        add_title(cv2.cvtColor(baseline, cv2.COLOR_GRAY2BGR), "LEGACY MASK"),
        add_title(cv2.cvtColor(corrected, cv2.COLOR_GRAY2BGR), "CORRECTED PROPOSAL"),
        add_title(overlay, "TOPOLOGY-INFERRED FILL"),
        add_title(uncertainty_rgb, "CORRECTION UNCERTAINTY"),
    ]
    return np.hstack(panels)


def build(repo_root: Path, output_root: Path, force: bool = False) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_root = output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()) and not force:
        raise FileExistsError(
            f"Refusing to overwrite versioned checkpoint: {output_root}"
        )
    output_root.mkdir(parents=True, exist_ok=True)

    baseline_root = repo_root / "data" / "ring01_phase2_refined" / "masks"
    source_path = (
        repo_root / "data" / "ring01_reference_images" / "ring01_angled.png"
    )
    baseline_paths = {
        kind: baseline_root / kind / f"ring01_{TARGET_VIEW}_{kind}.png"
        for kind in MASK_KINDS
    }
    negative_path = (
        repo_root
        / "data"
        / "ring01_ground_truth_v1"
        / "proposals"
        / "negative_space"
        / "ring01_angled_negative_space_proposal.png"
    )
    source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if source is None:
        raise FileNotFoundError(source_path)
    masks = {kind: read_mask(path) for kind, path in baseline_paths.items()}
    negative = read_mask(negative_path)
    inference = infer_correction(masks["jewelry"], masks["shank"])
    correction = inference.pop("correction")
    inference.pop("opening")
    inference.pop("corrected_opening")
    inference.pop("ellipse_mask")

    output_paths: dict[str, str] = {}
    corrected_masks: dict[str, np.ndarray] = {}
    for kind, baseline in masks.items():
        corrected = baseline.copy()
        corrected[correction > 0] = 255
        corrected_masks[kind] = corrected
        path = output_root / "masks" / kind / f"ring01_angled_{kind}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), corrected)
        output_paths[kind] = str(path.relative_to(repo_root))

    corrected_negative = negative.copy()
    corrected_negative[correction > 0] = 0
    negative_output = (
        output_root
        / "masks"
        / "negative_space"
        / "ring01_angled_negative_space.png"
    )
    negative_output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(negative_output), corrected_negative)
    output_paths["negative_space"] = str(negative_output.relative_to(repo_root))

    uncertainty = cv2.dilate(
        correction, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    )
    correction_path = output_root / "uncertainty" / "ring01_angled_correction.png"
    uncertainty_path = (
        output_root / "uncertainty" / "ring01_angled_correction_uncertainty.png"
    )
    correction_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(correction_path), correction)
    cv2.imwrite(str(uncertainty_path), uncertainty)

    audit = build_audit(
        source, masks["jewelry"], corrected_masks["jewelry"], correction
    )
    audit_path = output_root / "ring01_angled_reflection_audit.png"
    cv2.imwrite(str(audit_path), audit)

    before_contours, _ = cv2.findContours(
        masks["jewelry"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    after_contours, _ = cv2.findContours(
        corrected_masks["jewelry"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    before_outer = np.zeros_like(masks["jewelry"])
    after_outer = np.zeros_like(masks["jewelry"])
    cv2.drawContours(before_outer, before_contours, -1, 255, 1)
    cv2.drawContours(after_outer, after_contours, -1, 255, 1)

    report = {
        "schema_version": "lalitha_image_only_reflection_correction_v1",
        "execution_profile": "image_only_reconstruction_v1",
        "object_id": "ring01",
        "view": TARGET_VIEW,
        "status": "correction_proposed_pending_human_review",
        "input_contract": "images_only",
        "authority": "topology_informed_machine_proposal",
        "method": {
            "name": "inner_opening_ellipse_residual_fill",
            "description": (
                "Fill only inward opening notches outside a robust ellipse, below "
                "the head region, and within six pixels of observed shank metal."
            ),
            **inference,
        },
        "checks": {
            "source_unchanged": True,
            "exterior_silhouette_unchanged": bool(
                np.array_equal(before_outer, after_outer)
            ),
            "no_foreground_removed": bool(
                np.all(corrected_masks["jewelry"] >= masks["jewelry"])
            ),
            "central_opening_preserved": bool(
                inference["opening_pixel_count_after"] >= 5000
            ),
            "inner_boundary_consistency_improved": bool(
                inference["corrected_opening_ellipse_iou"]
                > inference["baseline_opening_ellipse_iou"]
            ),
            "correction_local_to_observed_shank": bool(
                inference["max_observed_correction_distance_px"] <= 6.0
            ),
        },
        "inputs": {
            "source": str(source_path.relative_to(repo_root)),
            "source_sha256": sha256(source_path),
            "baseline_masks": {
                kind: {
                    "path": str(path.relative_to(repo_root)),
                    "sha256": sha256(path),
                }
                for kind, path in baseline_paths.items()
            },
            "negative_space": {
                "path": str(negative_path.relative_to(repo_root)),
                "sha256": sha256(negative_path),
            },
        },
        "outputs": {
            "masks": output_paths,
            "correction_mask": str(correction_path.relative_to(repo_root)),
            "uncertainty_mask": str(uncertainty_path.relative_to(repo_root)),
            "audit": str(audit_path.relative_to(repo_root)),
        },
        "limitations": [
            "The filled pixels are inferred from image topology, not measured geometry.",
            "The correction does not establish metric depth, hidden geometry or CAD truth.",
            "The proposal remains pending identified human review.",
            "Only the visually defective angled view is modified; side and back remain unchanged.",
        ],
    }
    report["checkpoint_valid"] = all(report["checks"].values())
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/ring01_image_only/reflection_correction_v1"),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output = args.output
    if not output.is_absolute():
        output = args.repo_root / output
    report = build(args.repo_root, output, force=args.force)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
