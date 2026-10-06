"""Pinned VGGT adapter for Phase 3/B2 camera and dense-geometry evidence.

The adapter never downloads a checkpoint implicitly.  The caller must provide
a local checkpoint and declare its licence class so legal and runtime blockers
are retained in the benchmark record instead of being hidden.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np


PINNED_VGGT_COMMIT = "a288dd0f14786c93483e45524328726ab7b1b4ce"
COMMERCIAL_CHECKPOINT_LICENSE = "VGGT-1B-Commercial"
NONCOMMERCIAL_CHECKPOINT_LICENSE = "VGGT-1B-NonCommercial"


def probe_vggt(
    checkpoint: str | Path | None,
    checkpoint_license_id: str | None,
    allow_noncommercial_research: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    checkpoint_path = Path(checkpoint).resolve() if checkpoint else None
    if checkpoint_path is None:
        blockers.append("local_checkpoint_not_supplied")
    elif not checkpoint_path.exists():
        blockers.append("local_checkpoint_not_found")

    permitted = checkpoint_license_id == COMMERCIAL_CHECKPOINT_LICENSE
    if (
        allow_noncommercial_research
        and checkpoint_license_id == NONCOMMERCIAL_CHECKPOINT_LICENSE
    ):
        permitted = True
    if not permitted:
        blockers.append("checkpoint_licence_not_approved_for_requested_use")

    try:
        import torch

        torch_version = torch.__version__
        cuda_available = bool(torch.cuda.is_available())
        gpu_name = torch.cuda.get_device_name(0) if cuda_available else None
        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info() if cuda_available else (0, 0)
        except RuntimeError:
            free_bytes, total_bytes = 0, 0
    except ImportError:
        torch_version = None
        cuda_available = False
        gpu_name = None
        free_bytes, total_bytes = 0, 0
        blockers.append("torch_not_installed")

    try:
        import vggt  # noqa: F401

        code_available = True
    except ImportError:
        code_available = False
        blockers.append("pinned_vggt_code_not_installed")

    if not cuda_available:
        blockers.append("cuda_not_available")
    elif total_bytes and total_bytes < 8 * 1024**3:
        blockers.append("gpu_memory_below_conservative_8_gib_probe_gate")

    return {
        "backend": "vggt",
        "status": "ready" if not blockers else "blocked",
        "authority": "machine_hypothesis",
        "metric": False,
        "cross_view_validated": False,
        "pinned_code_commit": PINNED_VGGT_COMMIT,
        "checkpoint": str(checkpoint_path) if checkpoint_path else None,
        "checkpoint_license_id": checkpoint_license_id,
        "noncommercial_research_override": bool(allow_noncommercial_research),
        "code_available": code_available,
        "runtime": {
            "torch_version": torch_version,
            "cuda_available": cuda_available,
            "gpu_name": gpu_name,
            "gpu_free_bytes": int(free_bytes),
            "gpu_total_bytes": int(total_bytes),
        },
        "blockers": sorted(set(blockers)),
    }


def _numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach().float().cpu().numpy()
    return np.asarray(value)


def run_vggt_object(
    image_paths: list[Path],
    output_dir: Path,
    checkpoint: str | Path,
    checkpoint_license_id: str,
    device: str = "cuda",
    save_dense: bool = False,
    allow_noncommercial_research: bool = False,
) -> dict[str, Any]:
    probe = probe_vggt(checkpoint, checkpoint_license_id, allow_noncommercial_research)
    if probe["status"] != "ready":
        return probe

    import torch
    from vggt.models.vggt import VGGT
    from vggt.utils.load_fn import load_and_preprocess_images
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri

    if device == "cuda" and not torch.cuda.is_available():
        return {**probe, "status": "blocked", "blockers": ["cuda_not_available"]}

    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    checkpoint_path = Path(checkpoint)
    if checkpoint_path.is_dir():
        model = VGGT.from_pretrained(str(checkpoint_path), local_files_only=True)
    else:
        model = VGGT()
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state)
    model = model.to(device).eval()
    images = load_and_preprocess_images([str(path) for path in image_paths]).to(device)
    autocast_enabled = device == "cuda"
    with torch.inference_mode(), torch.autocast(
        device_type=device, dtype=torch.bfloat16, enabled=autocast_enabled
    ):
        predictions = model(images)
    extrinsic, intrinsic = pose_encoding_to_extri_intri(
        predictions["pose_enc"], images.shape[-2:]
    )
    cameras_path = output_dir / "vggt_cameras.npz"
    np.savez_compressed(
        cameras_path,
        extrinsic=_numpy(extrinsic),
        intrinsic=_numpy(intrinsic),
    )
    dense_path = None
    dense_shapes = {}
    if save_dense:
        dense = {
            key: _numpy(value)
            for key, value in predictions.items()
            if key in {"depth", "depth_conf", "world_points", "world_points_conf"}
        }
        dense_shapes = {key: list(value.shape) for key, value in dense.items()}
        dense_path = output_dir / "vggt_dense_evidence.npz"
        np.savez_compressed(dense_path, **dense)

    report = {
        **probe,
        "status": "completed_machine_hypothesis",
        "image_count": len(image_paths),
        "image_names": [path.name for path in image_paths],
        "camera_shapes": {
            "extrinsic": list(_numpy(extrinsic).shape),
            "intrinsic": list(_numpy(intrinsic).shape),
        },
        "dense_shapes": dense_shapes,
        "artifacts": {
            "cameras": str(cameras_path),
            "dense": str(dense_path) if dense_path else None,
        },
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "peak_cuda_bytes": int(torch.cuda.max_memory_allocated()) if device == "cuda" else 0,
        "warning": "VGGT outputs are uncalibrated machine hypotheses until compared with reviewed camera and geometry truth.",
    }
    (output_dir / "vggt_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

