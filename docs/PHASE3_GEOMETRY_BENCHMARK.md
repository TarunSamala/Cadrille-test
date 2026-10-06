# Phase 3/B2 camera and geometry evidence

This checkpoint follows the project Bible's Phase 3 order. It adds two independent
camera/geometry backends without promoting their output to CAD ground truth:

- **COLMAP / PyCOLMAP 4.2.1**: SIFT features, exhaustive matching, geometric
  verification, incremental camera recovery and sparse points. Exhaustive matching
  is appropriate here because each STL-1 object has only five views.
- **VGGT** pinned to commit `a288dd0f14786c93483e45524328726ab7b1b4ce`:
  camera, depth and point-map hypotheses through a local-checkpoint-only adapter.
  No model is downloaded automatically. Commercial use requires the separately
  gated commercial checkpoint and its terms to be reviewed.

## Reproducible runs

Build COLMAP:

```bash
docker build -f docker/geometry-benchmark/Dockerfile.colmap \
  -t image2cad-geometry-colmap:4.2.1 .
```

Build the combined pinned VGGT/PyCOLMAP runtime:

```bash
docker build -f docker/geometry-benchmark/Dockerfile.vggt \
  -t image2cad-geometry-vggt:a288dd0 .
```

Run all STL-1 COLMAP experiments and record a blocked VGGT probe:

```bash
docker run --rm --gpus all --user "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace \
  image2cad-geometry-vggt:a288dd0 \
  python -m pipeline.run_phase3_geometry_benchmark --backend all --force
```

A legal local VGGT checkpoint can be evaluated in the pinned VGGT container with
`--vggt-checkpoint` and `--vggt-license-id VGGT-1B-Commercial`. The original
non-commercial checkpoint is rejected unless the run is explicitly marked as
non-commercial research.

The VGGT image also contains the same pinned PyCOLMAP wheel so `--backend all`
records both backend states from one GPU-visible environment.
It is a backend runtime, not the Phase 0 full-regression image; run the complete
application suite in `image2cad-geometry-colmap:4.2.1` and the geometry contract
tests in the VGGT image.

## Gate

STL-1 is still Tier A image evidence. It has no reviewed camera truth, known
physical dimension, paired CAD/scan truth or human-approved component graph.
Therefore COLMAP/VGGT outputs are machine hypotheses and the decision remains
`research_only`. After reviewed B2 evidence exists, the Bible's next phase is
Phase 4: the universal component and constraint graph.

## STL-1 baseline result

The retained 24-object run extracted `136,472` SIFT keypoints from all `120`
views. It produced `31` tentative descriptor matches but `0` geometrically
verified correspondences, so no COLMAP sparse camera model could be formed.
This is a useful failure result: the supplied views do not currently provide
the cross-view photometric correspondence required by classical structure from
motion. It does not mean the jewellery has no recoverable geometry; it means the
next experiment must use learned cross-view matching/VGGT and reviewed capture
evidence rather than treating COLMAP as successful.
