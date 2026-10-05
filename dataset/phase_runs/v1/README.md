# Dataset phase run v1

This directory is the reproducible run for `dataset/prepared_v1`.

- Root JSON files summarize phase coverage, Phase 1 extraction, Phase 2 training, and Phase 2.2 held-out evaluation.
- `checkpoints/` contains the trained segmentation checkpoint.
- `comparisons/` contains dataset-wide comparison sheets.
- `phase1_depth_anything_v2/` contains the pinned Depth Anything V2 Small
  relative-depth benchmark, 16-bit proposals, uncertainty diagnostics and
  one review sheet per object.
- `phase_audits/` contains per-object phase comparisons.
- `test_predictions/` contains held-out prediction images.
- `phase3/visual_hull/` contains one non-metric STL, 3MF, preview, and validation report per object.

The Phase 3 exports preserve image-derived shape evidence but do not contain calibrated physical scale or manufacturing geometry.

The Phase 1 depth outputs are independently normalized, non-metric machine
proposals. Their flip-consistency values are diagnostics rather than accuracy
measurements because STL-1 contains no scan or human depth ground truth.
