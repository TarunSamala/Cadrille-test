"""Generate Phase 0 environment and dependency/license manifests.

Run this inside the pinned validation image. Package license values are copied
from installed distribution metadata and are an engineering inventory, not a
legal opinion.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIREMENT_FILES = (
    "requirements-phase1.txt",
    "requirements-phase2.txt",
    "requirements-app.txt",
    "requirements-studio.txt",
    "requirements-validation.txt",
)
ENVIRONMENT_FILES = (
    "Dockerfile",
    "Dockerfile.auditor",
    "Dockerfile.cadrille",
    "Dockerfile.validation",
    "constraints-validation.txt",
    "docker/geometry-benchmark/Dockerfile.colmap",
    "docker/geometry-benchmark/Dockerfile.vggt",
    "docker/geometry-benchmark/constraints.vggt.txt",
    *REQUIREMENT_FILES,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command(*args: str) -> str | None:
    try:
        return subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def direct_requirement_names(root: Path) -> set[str]:
    names: set[str] = set()
    for filename in REQUIREMENT_FILES:
        path = root / filename
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", "-r ")):
                continue
            if " @ " in line:
                names.add(normalized_name(line.split(" @ ", 1)[0].strip()))
                continue
            match = re.match(r"([A-Za-z0-9_.-]+)", line)
            if match:
                names.add(normalized_name(match.group(1)))
    return names


def license_value(metadata: importlib.metadata.PackageMetadata) -> tuple[str, str]:
    expression = metadata.get("License-Expression")
    if expression:
        return expression.strip(), "License-Expression"
    value = metadata.get("License")
    if value and value.strip() and value.strip().upper() not in {"UNKNOWN", "N/A"}:
        compact = " ".join(value.split())
        return compact[:500], "License"
    classifiers = [
        item.removeprefix("License :: ")
        for item in metadata.get_all("Classifier", [])
        if item.startswith("License :: ")
    ]
    if classifiers:
        return " | ".join(classifiers), "Classifier"
    return "UNKNOWN_REVIEW_REQUIRED", "missing"


def package_inventory(root: Path) -> dict[str, Any]:
    direct = direct_requirement_names(root)
    packages = []
    for distribution in importlib.metadata.distributions():
        metadata = distribution.metadata
        name = metadata.get("Name") or "unknown"
        license_name, license_source = license_value(metadata)
        project_urls = metadata.get_all("Project-URL", [])
        packages.append(
            {
                "name": name,
                "version": distribution.version,
                "direct_project_requirement": normalized_name(name) in direct,
                "license": license_name,
                "license_metadata_source": license_source,
                "license_review_required": license_name == "UNKNOWN_REVIEW_REQUIRED",
                "home_page": metadata.get("Home-page"),
                "project_urls": project_urls,
            }
        )
    packages.sort(key=lambda item: normalized_name(item["name"]))
    return {
        "schema_version": "lalitha_dependency_license_manifest_v1",
        "scope": "installed Python distributions in the Phase 0 validation image",
        "legal_status": "engineering inventory only; legal review required before product distribution",
        "direct_requirement_files": list(REQUIREMENT_FILES),
        "package_count": len(packages),
        "unknown_license_count": sum(item["license_review_required"] for item in packages),
        "packages": packages,
    }


def memory_total_bytes() -> int | None:
    path = Path("/proc/meminfo")
    if not path.is_file():
        return None
    match = re.search(r"^MemTotal:\s+(\d+)\s+kB$", path.read_text(), re.MULTILINE)
    return int(match.group(1)) * 1024 if match else None


def torch_state() -> dict[str, Any]:
    try:
        import torch

        return {
            "version": torch.__version__,
            "compiled_cuda": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "gpu_names": [
                torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())
            ],
            "gpu_count": torch.cuda.device_count(),
        }
    except ImportError:
        return {"available": False}


def nvidia_state() -> dict[str, Any]:
    output = command(
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total",
        "--format=csv,noheader,nounits",
    )
    if not output:
        return {"available": False, "devices": []}
    devices = []
    for line in output.splitlines():
        values = [value.strip() for value in line.split(",")]
        if len(values) == 3:
            devices.append(
                {
                    "name": values[0],
                    "driver_version": values[1],
                    "memory_total_mib": int(values[2]),
                }
            )
    return {"available": bool(devices), "devices": devices}


def environment_manifest(root: Path, arguments: argparse.Namespace, package_count: int) -> dict[str, Any]:
    commit = arguments.source_commit or command("git", "-C", str(root), "rev-parse", "HEAD")
    status = command("git", "-C", str(root), "status", "--porcelain")
    if arguments.working_tree_clean == "true":
        working_tree_clean: bool | None = True
    elif arguments.working_tree_clean == "false":
        working_tree_clean = False
    else:
        working_tree_clean = status == "" if status is not None else None
    tracked_hashes = {
        name: sha256(root / name)
        for name in ENVIRONMENT_FILES
        if (root / name).is_file()
    }
    torch = torch_state()
    nvidia = nvidia_state()
    gpu_passed = bool(torch.get("cuda_available")) and nvidia["available"]
    return {
        "schema_version": "lalitha_phase0_environment_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "bible_phase": "Phase 0 - Reproducibility Freeze",
        "source": {
            "commit": commit,
            "working_tree_clean_at_generation": working_tree_clean,
            "canonical_branch": "main",
            "remote": "https://github.com/TarunSamala/Image2CAD.git",
            "baseline_tag": arguments.baseline_tag,
        },
        "container": {
            "image_name": arguments.image_name,
            "image_id": arguments.image_id,
            "base_image": "pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime",
            "base_digest": "sha256:c8268a92a69bd500f8be0e665b2630ee006dadaf7bfbc24249141b15ff622755",
        },
        "research_runtime_images": {
            "colmap": {
                "image_name": "image2cad-geometry-colmap:4.2.1",
                "image_id": arguments.colmap_image_id,
                "pycolmap_version": "4.2.1",
            },
            "vggt": {
                "image_name": "image2cad-geometry-vggt:a288dd0",
                "image_id": arguments.vggt_image_id,
                "code_commit": "a288dd0f14786c93483e45524328726ab7b1b4ce",
                "checkpoint_bundled": False,
            },
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "memory_total_bytes": memory_total_bytes(),
            "torch": torch,
            "nvidia": nvidia,
            "installed_python_distribution_count": package_count,
        },
        "gpu_validation": {
            "result": "passed" if gpu_passed else "failed",
            "command": "docker run --rm --gpus all image2cad-validation:phase0 python CUDA_SMOKE_TEST",
            "cuda_visible_in_validation_container": bool(torch.get("cuda_available")),
            "device_count": int(torch.get("gpu_count", 0)),
        },
        "regression": {
            "command": arguments.test_command,
            "result": arguments.test_result,
            "test_count": arguments.test_count,
        },
        "environment_file_sha256": tracked_hashes,
        "known_limits": [
            "CUDA availability is validated; model-specific peak VRAM and numerical accuracy remain separate benchmark concerns.",
            "The 4 GiB GPU does not satisfy the conservative 8 GiB VGGT execution gate.",
            "No VGGT checkpoint is bundled or downloaded automatically.",
            "Package license fields are metadata-derived and require legal review.",
            "STL-1 has no human masks, calibrated cameras, physical scale, component truth, or CAD targets.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--image-name", default="image2cad-validation:phase0")
    parser.add_argument("--image-id", default="unknown")
    parser.add_argument("--colmap-image-id", default="unknown")
    parser.add_argument("--vggt-image-id", default="unknown")
    parser.add_argument("--baseline-tag", default="baseline-v1.0")
    parser.add_argument(
        "--source-commit",
        help="Verified 40-character source commit; required when git is absent in the image.",
    )
    parser.add_argument(
        "--working-tree-clean",
        choices=("true", "false", "unknown"),
        default="unknown",
        help="Verified source-tree state; avoids inferring cleanliness when git is absent.",
    )
    parser.add_argument(
        "--test-command",
        default="PYTHONPATH=pipeline python -m unittest discover -s tests -v",
    )
    parser.add_argument("--test-result", choices=("passed", "failed", "not_run"), default="not_run")
    parser.add_argument("--test-count", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    root = arguments.repo_root.resolve()
    output = arguments.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    licenses = package_inventory(root)
    environment = environment_manifest(root, arguments, licenses["package_count"])
    (output / "dependency_license_manifest.json").write_text(
        json.dumps(licenses, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "environment_manifest.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {output / 'environment_manifest.json'}")
    print(f"wrote {output / 'dependency_license_manifest.json'}")


if __name__ == "__main__":
    main()
