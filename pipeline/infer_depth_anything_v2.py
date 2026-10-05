"""Generate non-metric Depth Anything V2 proposals for Phase 1 Ring01."""

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


MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"
MODEL_REVISION = "5426e4f0f36572d16453bbda7a8389317b1bef99"
MODEL_LICENSE = "Apache-2.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def robust_normalize(values: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, float, float]:
    selected = values[mask > 0]
    if selected.size == 0:
        selected = values.reshape(-1)
    low, high = np.percentile(selected, (2.0, 98.0))
    if high <= low:
        high = low + 1e-6
    normalized = np.clip((values - low) / (high - low), 0.0, 1.0)
    return normalized.astype(np.float32), float(low), float(high)


def align_prediction(reference: np.ndarray, candidate: np.ndarray, mask: np.ndarray) -> np.ndarray:
    valid = mask > 0
    x = candidate[valid].astype(np.float64)
    y = reference[valid].astype(np.float64)
    if x.size < 2 or np.var(x) < 1e-12:
        return candidate
    matrix = np.stack((x, np.ones_like(x)), axis=1)
    scale, offset = np.linalg.lstsq(matrix, y, rcond=None)[0]
    return (candidate * scale + offset).astype(np.float32)


def colorize(normalized: np.ndarray, mask: np.ndarray) -> np.ndarray:
    gray = np.round(normalized * 255).astype(np.uint8)
    color = cv2.applyColorMap(gray, cv2.COLORMAP_TURBO)
    color[mask == 0] = (238, 238, 238)
    return color


def infer(
    image: Image.Image,
    processor: Any,
    model: Any,
    device: torch.device,
) -> np.ndarray:
    inputs = processor(images=image, return_tensors="pt")
    inputs = {name: value.to(device) for name, value in inputs.items()}
    with torch.inference_mode():
        prediction = model(**inputs).predicted_depth
    resized = torch.nn.functional.interpolate(
        prediction.unsqueeze(1),
        size=(image.height, image.width),
        mode="bicubic",
        align_corners=False,
    ).squeeze()
    return resized.float().cpu().numpy().astype(np.float32)


def build_contact_sheet(rows: list[tuple[str, np.ndarray, np.ndarray, np.ndarray]]) -> np.ndarray:
    rendered = []
    for view, source, depth, uncertainty in rows:
        height = 220
        panels = []
        for title, image in (
            (f"{view.upper()} SOURCE", source),
            ("RELATIVE DEPTH PROPOSAL", depth),
            ("FLIP-CONSISTENCY UNCERTAINTY", uncertainty),
        ):
            scale = height / image.shape[0]
            resized = cv2.resize(
                image,
                (int(round(image.shape[1] * scale)), height),
                interpolation=cv2.INTER_AREA,
            )
            canvas = np.full((height + 34, resized.shape[1], 3), 245, np.uint8)
            canvas[34:] = resized
            cv2.putText(
                canvas,
                title,
                (8, 23),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (30, 35, 42),
                1,
                cv2.LINE_AA,
            )
            panels.append(canvas)
        row = cv2.hconcat(panels)
        rendered.append(row)
    width = max(row.shape[1] for row in rendered)
    rendered = [
        cv2.copyMakeBorder(
            row,
            0,
            0,
            0,
            width - row.shape[1],
            cv2.BORDER_CONSTANT,
            value=(245, 245, 245),
        )
        for row in rendered
    ]
    return cv2.vconcat(rendered)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    workspace = root / "data" / "ring01_ground_truth_v1"
    manifest_path = workspace / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Run phase1_ground_truth.py initialize first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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

    output = workspace / "depth_anything_v2"
    output.mkdir(parents=True, exist_ok=True)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    records: dict[str, Any] = {}
    contact_rows = []
    started = time.perf_counter()
    for view, view_record in manifest["views"].items():
        source_path = root / view_record["source"]["path"]
        mask_path = root / view_record["proposals"]["jewelry"]["path"]
        image = Image.open(source_path).convert("RGB")
        source_bgr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise ValueError(f"Cannot decode silhouette proposal: {mask_path}")
        mask = np.where(mask > 127, 255, 0).astype(np.uint8)

        start = time.perf_counter()
        depth = infer(image, processor, model, device)
        flipped = infer(image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), processor, model, device)
        flipped = np.fliplr(flipped).copy()
        aligned_flip = align_prediction(depth, flipped, mask)
        uncertainty = np.abs(depth - aligned_flip)
        normalized, low, high = robust_normalize(depth, mask)
        normalized_uncertainty, uncertainty_low, uncertainty_high = robust_normalize(
            uncertainty, mask
        )

        raw_path = output / f"ring01_{view}_relative_depth.npy"
        depth16_path = output / f"ring01_{view}_relative_depth_u16.png"
        preview_path = output / f"ring01_{view}_relative_depth_preview.png"
        uncertainty_path = output / f"ring01_{view}_uncertainty_u16.png"
        uncertainty_preview_path = output / f"ring01_{view}_uncertainty_preview.png"
        np.save(raw_path, depth)
        cv2.imwrite(str(depth16_path), np.round(normalized * 65535).astype(np.uint16))
        depth_preview = colorize(normalized, mask)
        uncertainty_preview = colorize(normalized_uncertainty, mask)
        cv2.imwrite(str(preview_path), depth_preview)
        cv2.imwrite(
            str(uncertainty_path),
            np.round(normalized_uncertainty * 65535).astype(np.uint16),
        )
        cv2.imwrite(str(uncertainty_preview_path), uncertainty_preview)
        elapsed = time.perf_counter() - start
        record = {
            "authority": "machine_proposal",
            "metric": False,
            "cross_view_aligned": False,
            "relative_depth_orientation": "model_native_uninterpreted",
            "runtime_seconds": round(elapsed, 6),
            "raw_float32_npy": str(raw_path.relative_to(root)),
            "normalized_u16": str(depth16_path.relative_to(root)),
            "preview": str(preview_path.relative_to(root)),
            "uncertainty_u16": str(uncertainty_path.relative_to(root)),
            "uncertainty_preview": str(uncertainty_preview_path.relative_to(root)),
            "raw_sha256": sha256(raw_path),
            "robust_range": {"p02": low, "p98": high},
            "uncertainty_robust_range": {
                "p02": uncertainty_low,
                "p98": uncertainty_high,
            },
            "mean_masked_flip_uncertainty": float(uncertainty[mask > 0].mean()),
        }
        records[view] = record
        view_record["depth_proposal"] = record
        contact_rows.append((view, source_bgr, depth_preview, uncertainty_preview))

    contact_path = output / "ring01_depth_anything_v2_review.png"
    cv2.imwrite(str(contact_path), build_contact_sheet(contact_rows))
    metadata = {
        "schema_version": "lalitha_depth_proposal_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": {
            "id": MODEL_ID,
            "revision": MODEL_REVISION,
            "license": MODEL_LICENSE,
            "role": "relative-depth proposal",
        },
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated())
        if device.type == "cuda"
        else 0,
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "review_summary": str(contact_path.relative_to(root)),
        "views": records,
        "limitations": [
            "No metric scale is inferred.",
            "Predictions from separate views are not cross-view consistent by default.",
            "Specular metal, transparent gemstone facets and reflections can produce false depth.",
            "Flip consistency is a diagnostic, not calibrated uncertainty.",
            "Human review and geometric benchmarking are required before promotion.",
        ],
        "decision": "research_only",
    }
    metadata_path = output / "depth_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    manifest["depth_anything_v2"] = {
        "status": "machine_proposals_pending_review",
        "metadata": str(metadata_path.relative_to(root)),
        "review_summary": str(contact_path.relative_to(root)),
        "model_revision": MODEL_REVISION,
        "metric": False,
    }
    manifest["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
