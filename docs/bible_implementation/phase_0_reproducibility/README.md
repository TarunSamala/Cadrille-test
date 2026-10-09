# Phase 0 Reproducibility

This directory records the software baseline required by Phase 0 of the
Lalitha project Bible. It freezes the validation environment without changing
the scientific meaning of existing Phase 1-3 results.

## Build the validation image

```bash
docker build --pull=false -f Dockerfile.validation \
  -t image2cad-validation:phase0 .
```

The Dockerfile pins the PyTorch/CUDA base by digest. Project requirements,
transitive additions and the SAM 2 source archive are version or checksum
pinned.

## Run the complete regression suite

```bash
docker run --rm \
  --gpus all \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  image2cad-validation:phase0
```

The repository is mounted read-only so tests cannot silently modify the
canonical source or checked-in artifacts.

## Regenerate the manifests

```bash
docker run --rm \
  --gpus all \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/docs/bible_implementation/phase_0_reproducibility:/output" \
  -w /workspace \
  image2cad-validation:phase0 \
  python tools/generate_phase0_manifest.py \
    --repo-root /workspace \
    --output-dir /output \
    --image-id IMAGE_ID \
    --colmap-image-id COLMAP_IMAGE_ID \
    --vggt-image-id VGGT_IMAGE_ID \
    --source-commit SOURCE_COMMIT \
    --working-tree-clean true \
    --test-result passed \
    --test-count TEST_COUNT
```

The source commit and working-tree state are passed explicitly because the
minimal validation image does not install Git. The dependency/license file is
an engineering inventory generated from installed package metadata. It is not
legal approval.

The GPU gate proves that the host driver and CUDA are visible inside the pinned
validation image. It does not imply that every research model fits in VRAM or
that a model checkpoint has been approved for commercial use.

## Evidence files

- `PHASE0_STATUS.md`: gate-by-gate status and unresolved limits.
- `environment_manifest.json`: source, image, runtime and test evidence.
- `dependency_license_manifest.json`: installed Python package inventory.
