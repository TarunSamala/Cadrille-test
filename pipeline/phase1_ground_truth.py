"""Create and maintain the Bible Phase 1 Ring01 review workspace.

Machine masks are copied into the manifest as proposals. They become human
ground truth only after an identified reviewer explicitly approves every
required label and the remaining scale/camera gates are resolved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np


VIEWS = ("front", "side", "top", "angled", "back")
LABELS = (
    "jewelry",
    "metal",
    "shank",
    "stone_visible",
    "setting",
    "prongs",
    "negative_space",
)
COMPONENT_CATALOG = (
    ("shank_001", "shank"),
    ("setting_001", "setting"),
    ("stone_001", "round_gemstone"),
    ("prong_001", "prong"),
    ("prong_002", "prong"),
    ("prong_003", "prong"),
    ("prong_004", "prong"),
)
DECISIONS = ("pending", "approved", "needs_correction", "rejected")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def source_commit(root: Path) -> str | None:
    try:
        return subprocess.run(
            ("git", "-C", str(root), "rev-parse", "HEAD"),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def read_mask(path: Path, shape: tuple[int, int]) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise ValueError(f"Cannot decode proposal mask: {path}")
    if mask.shape != shape:
        raise ValueError(f"Mask/image size mismatch for {path}")
    return np.where(mask > 127, 255, 0).astype(np.uint8)


def enclosed_negative_space(mask: np.ndarray) -> np.ndarray:
    background = np.where(mask == 0, 1, 0).astype(np.uint8)
    count, labels = cv2.connectedComponents(background, connectivity=8)
    border_ids = set(np.unique(labels[0]))
    border_ids.update(np.unique(labels[-1]))
    border_ids.update(np.unique(labels[:, 0]))
    border_ids.update(np.unique(labels[:, -1]))
    result = np.zeros_like(mask)
    for label_id in range(1, count):
        if label_id not in border_ids:
            result[labels == label_id] = 255
    return result


def overlay(source: np.ndarray, masks: dict[str, np.ndarray]) -> np.ndarray:
    colors = {
        "jewelry": (80, 210, 110),
        "stone_visible": (255, 210, 70),
        "prongs": (70, 120, 255),
        "negative_space": (215, 80, 210),
    }
    result = source.copy()
    for name, color in colors.items():
        mask = masks[name] > 0
        result[mask] = (
            result[mask].astype(np.float32) * 0.55
            + np.asarray(color, dtype=np.float32) * 0.45
        ).astype(np.uint8)
        contours, _ = cv2.findContours(
            masks[name], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(result, contours, -1, color, 1, cv2.LINE_AA)
    return result


def panel(image: np.ndarray, title: str, height: int = 250) -> np.ndarray:
    scale = height / image.shape[0]
    resized = cv2.resize(
        image,
        (max(1, int(round(image.shape[1] * scale))), height),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.full((height + 38, resized.shape[1], 3), 245, dtype=np.uint8)
    canvas[38:] = resized
    cv2.putText(
        canvas,
        title,
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (25, 32, 40),
        1,
        cv2.LINE_AA,
    )
    return canvas


def horizontal_stack(items: list[np.ndarray]) -> np.ndarray:
    height = max(item.shape[0] for item in items)
    normalized = []
    for item in items:
        if item.shape[0] < height:
            item = cv2.copyMakeBorder(
                item,
                0,
                height - item.shape[0],
                0,
                0,
                cv2.BORDER_CONSTANT,
                value=(245, 245, 245),
            )
        normalized.append(item)
    return cv2.hconcat(normalized)


def refresh_gate(manifest: dict[str, Any]) -> None:
    pending_labels = []
    for view, record in manifest["views"].items():
        for label, review in record["reviews"].items():
            if review["decision"] != "approved":
                pending_labels.append(f"{view}:{label}")
    pending_identities = [
        item["component_id"]
        for item in manifest["component_catalog"]
        if item["review"]["decision"] != "approved"
    ]
    camera_missing = [
        view
        for view, record in manifest["camera_records"].items()
        if record["review"]["decision"] != "approved"
    ]
    scale_missing = not manifest["physical_scale"]["measurements"]
    conflicts = list(manifest.get("review_conflicts", []))
    manifest["exit_gate"] = {
        "status": "pass"
        if not (pending_labels or pending_identities or camera_missing or scale_missing or conflicts)
        else "blocked",
        "pending_label_reviews": pending_labels,
        "pending_component_identities": pending_identities,
        "pending_camera_records": camera_missing,
        "physical_scale_missing": scale_missing,
        "unresolved_conflicts": conflicts,
        "human_ground_truth_complete": not (
            pending_labels or pending_identities or camera_missing or scale_missing or conflicts
        ),
    }
    manifest["updated_at_utc"] = utc_now()


def initialize(root: Path, output: Path, force: bool = False) -> dict[str, Any]:
    manifest_path = output / "manifest.json"
    if manifest_path.exists() and not force:
        raise FileExistsError(
            f"{manifest_path} already exists; use review commands or --force explicitly"
        )
    output.mkdir(parents=True, exist_ok=True)
    proposals = output / "proposals"
    negative_dir = proposals / "negative_space"
    review_dir = output / "review"
    negative_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)

    records: dict[str, Any] = {}
    review_rows = []
    for view in VIEWS:
        source_path = root / "data" / "ring01_reference_images" / f"ring01_{view}.png"
        source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        if source is None:
            raise ValueError(f"Cannot decode reference image: {source_path}")
        shape = source.shape[:2]
        masks: dict[str, np.ndarray] = {}
        proposal_paths: dict[str, str] = {}
        for label in LABELS:
            if label == "negative_space":
                continue
            path = (
                root
                / "data"
                / "ring01_phase2_refined"
                / "masks"
                / label
                / f"ring01_{view}_{label}.png"
            )
            masks[label] = read_mask(path, shape)
            proposal_paths[label] = relative(root, path)
        masks["negative_space"] = enclosed_negative_space(masks["jewelry"])
        negative_path = negative_dir / f"ring01_{view}_negative_space_proposal.png"
        if not cv2.imwrite(str(negative_path), masks["negative_space"]):
            raise OSError(f"Cannot write {negative_path}")
        proposal_paths["negative_space"] = relative(root, negative_path)

        visual = overlay(source, masks)
        view_sheet = horizontal_stack(
            [
                panel(source, f"{view.upper()} SOURCE"),
                panel(cv2.cvtColor(masks["jewelry"], cv2.COLOR_GRAY2BGR), "SILHOUETTE PROPOSAL"),
                panel(visual, "COMPONENT + NEGATIVE-SPACE PROPOSALS"),
            ]
        )
        sheet_path = review_dir / f"ring01_{view}_review.png"
        if not cv2.imwrite(str(sheet_path), view_sheet):
            raise OSError(f"Cannot write {sheet_path}")
        review_rows.append(view_sheet)

        records[view] = {
            "source": {
                "path": relative(root, source_path),
                "sha256": sha256(source_path),
                "size_wh": [int(source.shape[1]), int(source.shape[0])],
            },
            "proposals": {
                label: {
                    "path": path,
                    "sha256": sha256(root / path),
                    "authority": "machine_proposal",
                }
                for label, path in proposal_paths.items()
            },
            "reviews": {
                label: {
                    "decision": "pending",
                    "reviewer": None,
                    "reviewed_at_utc": None,
                    "note": None,
                }
                for label in LABELS
            },
            "review_sheet": relative(root, sheet_path),
            "depth_proposal": None,
        }

    width = max(row.shape[1] for row in review_rows)
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
        for row in review_rows
    ]
    all_views_path = review_dir / "ring01_phase1_all_views.png"
    if not cv2.imwrite(str(all_views_path), cv2.vconcat(padded)):
        raise OSError(f"Cannot write {all_views_path}")

    manifest: dict[str, Any] = {
        "schema_version": "lalitha_phase1_ground_truth_v1",
        "phase": "Phase 1 - Ground-Truth Ring01",
        "object_id": "ring01",
        "status": "human_review_required",
        "created_at_utc": utc_now(),
        "updated_at_utc": utc_now(),
        "source_commit": source_commit(root),
        "proposal_source": "data/ring01_phase2_refined/phase2_refined.json",
        "authority_policy": (
            "All masks, negative spaces and depth maps remain machine proposals until "
            "an identified human reviewer approves them."
        ),
        "views": records,
        "component_catalog": [
            {
                "component_id": component_id,
                "class": class_name,
                "cross_view_identity": "pending_human_review",
                "review": {
                    "decision": "pending",
                    "reviewer": None,
                    "reviewed_at_utc": None,
                    "note": None,
                },
            }
            for component_id, class_name in COMPONENT_CATALOG
        ],
        "physical_scale": {
            "status": "missing",
            "measurements": [],
            "required_examples": [
                "inner ring diameter in mm",
                "known gemstone diameter in mm",
                "calibration target visible in the capture",
            ],
        },
        "camera_records": {
            view: {
                "intrinsics": None,
                "extrinsics": None,
                "projection_model": "unknown",
                "uncertainty": "camera and crop metadata unavailable",
                "review": {
                    "decision": "pending",
                    "reviewer": None,
                    "reviewed_at_utc": None,
                    "note": None,
                },
            }
            for view in VIEWS
        },
        "review_conflicts": [],
        "review_summary": relative(root, all_views_path),
        "depth_policy": {
            "model": "Depth Anything V2 Small",
            "role": "relative-depth proposal only",
            "metric_ground_truth": False,
            "cross_view_consistent_by_default": False,
        },
    }
    refresh_gate(manifest)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_manifest(root: Path) -> tuple[Path, dict[str, Any]]:
    path = root / "data" / "ring01_ground_truth_v1" / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"Initialize Phase 1 first: {path}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    refresh_gate(manifest)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def review_label(args: argparse.Namespace) -> None:
    path, manifest = load_manifest(args.repo_root)
    record = manifest["views"][args.view]["reviews"][args.label]
    record.update(
        {
            "decision": args.decision,
            "reviewer": args.reviewer,
            "reviewed_at_utc": utc_now(),
            "note": args.note,
        }
    )
    save_manifest(path, manifest)


def review_identity(args: argparse.Namespace) -> None:
    path, manifest = load_manifest(args.repo_root)
    item = next(
        (
            item
            for item in manifest["component_catalog"]
            if item["component_id"] == args.component_id
        ),
        None,
    )
    if item is None:
        raise ValueError(f"Unknown component ID: {args.component_id}")
    item["review"].update(
        {
            "decision": args.decision,
            "reviewer": args.reviewer,
            "reviewed_at_utc": utc_now(),
            "note": args.note,
        }
    )
    if args.decision == "approved":
        item["cross_view_identity"] = "human_approved"
    save_manifest(path, manifest)


def set_dimension(args: argparse.Namespace) -> None:
    if args.value_mm <= 0:
        raise ValueError("Physical dimensions must be positive")
    path, manifest = load_manifest(args.repo_root)
    manifest["physical_scale"]["measurements"].append(
        {
            "name": args.name,
            "value_mm": args.value_mm,
            "source": args.source,
            "reviewer": args.reviewer,
            "recorded_at_utc": utc_now(),
            "uncertainty_mm": args.uncertainty_mm,
        }
    )
    manifest["physical_scale"]["status"] = "human_recorded"
    save_manifest(path, manifest)


def set_camera(args: argparse.Namespace) -> None:
    path, manifest = load_manifest(args.repo_root)
    record = manifest["camera_records"][args.view]
    record.update(
        {
            "intrinsics": json.loads(args.intrinsics_json)
            if args.intrinsics_json
            else None,
            "extrinsics": json.loads(args.extrinsics_json)
            if args.extrinsics_json
            else None,
            "projection_model": args.projection_model,
            "uncertainty": args.uncertainty,
        }
    )
    record["review"].update(
        {
            "decision": args.decision,
            "reviewer": args.reviewer,
            "reviewed_at_utc": utc_now(),
            "note": args.note,
        }
    )
    save_manifest(path, manifest)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--repo-root", type=Path, default=Path.cwd())
    commands = result.add_subparsers(dest="command", required=True)
    init = commands.add_parser("initialize")
    init.add_argument("--force", action="store_true")

    label = commands.add_parser("review-label")
    label.add_argument("--view", choices=VIEWS, required=True)
    label.add_argument("--label", choices=LABELS, required=True)
    label.add_argument("--decision", choices=DECISIONS[1:], required=True)
    label.add_argument("--reviewer", required=True)
    label.add_argument("--note")

    identity = commands.add_parser("review-identity")
    identity.add_argument(
        "--component-id", choices=[item[0] for item in COMPONENT_CATALOG], required=True
    )
    identity.add_argument("--decision", choices=DECISIONS[1:], required=True)
    identity.add_argument("--reviewer", required=True)
    identity.add_argument("--note")

    dimension = commands.add_parser("set-dimension")
    dimension.add_argument("--name", required=True)
    dimension.add_argument("--value-mm", type=float, required=True)
    dimension.add_argument("--uncertainty-mm", type=float)
    dimension.add_argument("--source", required=True)
    dimension.add_argument("--reviewer", required=True)

    camera = commands.add_parser("set-camera")
    camera.add_argument("--view", choices=VIEWS, required=True)
    camera.add_argument(
        "--projection-model",
        choices=("perspective", "orthographic", "weak_perspective", "unknown"),
        required=True,
    )
    camera.add_argument("--intrinsics-json")
    camera.add_argument("--extrinsics-json")
    camera.add_argument("--uncertainty", required=True)
    camera.add_argument(
        "--decision", choices=("approved", "needs_correction"), required=True
    )
    camera.add_argument("--reviewer", required=True)
    camera.add_argument("--note")
    return result


def main() -> None:
    args = parser().parse_args()
    args.repo_root = args.repo_root.resolve()
    if args.command == "initialize":
        output = args.repo_root / "data" / "ring01_ground_truth_v1"
        manifest = initialize(args.repo_root, output, force=args.force)
        print(json.dumps(manifest["exit_gate"], indent=2))
    elif args.command == "review-label":
        review_label(args)
    elif args.command == "review-identity":
        review_identity(args)
    elif args.command == "set-dimension":
        set_dimension(args)
    elif args.command == "set-camera":
        set_camera(args)


if __name__ == "__main__":
    main()
