# STL-1 Phase 1 and Depth Anything V2 benchmark

## Scope

This benchmark combines the existing STL-1 Phase 1 image evidence with Depth
Anything V2 Small for all 24 objects and all five prepared views. It does not
train Depth Anything V2 and does not convert its predictions into CAD.

Each review sheet contains:

1. the normalized 768 x 768 source;
2. the Phase 1 pseudo-silhouette and OpenCV edges;
3. the relative-depth proposal;
4. flip-consistency uncertainty.

## Completed run

- Objects: 24
- Views: 120
- Split: 18 train, 3 validation, 3 test objects
- Runtime: 33.821765 seconds on CUDA
- Mean runtime: 0.281848 seconds per view
- Peak allocated GPU memory: 219342336 bytes
- Mean normalized flip error: 0.046892
- Median normalized flip error: 0.043206
- P95 normalized flip error: 0.088043
- Maximum normalized flip error: 0.116265

All coverage, existing Phase 1, output-presence and finite-value checks passed.
The authoritative machine-readable result is
`dataset/phase_runs/v1/phase1_depth_anything_v2/report.json`.

## Interpretation

Flip error is normalized by each image's robust relative-depth span. Lower
values indicate that the model produced more similar results for an image and
its horizontally flipped copy after affine alignment. This is useful for
finding unstable views, but it is not an accuracy measurement.

The highest diagnostic uncertainty occurred in:

- ring_004 top;
- ring_007 front;
- ring_004 left side;
- ring_018 right side;
- ring_024 left side.

Isometric views were the most self-consistent on average. Front and top views
were less self-consistent, particularly around dense ornament, reflective
features and thin geometry. Visual review confirmed that the coarse near/far
ordering is useful, while fine relief, stones, prongs and reflective boundaries
remain unreliable.

## Phase 1 status

The machine-image evidence is complete, but the Phase 1 exit gate remains
blocked. STL-1 still lacks:

- human-reviewed masks;
- reviewed component identities;
- camera calibration;
- physical scale;
- metric depth or scans;
- cross-view-consistent depth.

Therefore these files can guide later reconstruction and review, but cannot
validate geometric or manufacturing accuracy.

## Reproduce

From the repository root, with the Phase 1 image already built and the model
present in the local Hugging Face cache:

```bash
docker run --rm --gpus all \
  -e HF_HOME=/workspace/hf_cache \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/workspace" -w /workspace \
  image2cad-phase1-depth:local \
  python -m pipeline.infer_dataset_depth_anything_v2 \
  --repo-root /workspace --device cuda --local-files-only --force
```

`--force` is intentionally required when a completed report already exists.
