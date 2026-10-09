# Test map

The test suite covers two phase systems:

- Bible tests: `test_phase0_reproducibility.py`,
  `test_phase1_ground_truth_bible.py`, `test_stl1_phase1_review.py`,
  `test_phase2_paired_benchmark.py`, and `test_phase3_geometry_benchmark.py`.
- Image-only execution tests: `test_image_only_reflection_correction.py`.
- Legacy regression tests: the remaining `test_phase1*`, `test_phase2*`,
  `test_phase3*`, dataset phase and Ring01 reconstruction tests.
- Shared tests: Studio, dataset integrity, upload auditing and 2D-to-3D model
  benchmark contracts.

Legacy tests remain necessary because those checkpoints are reproducible
evidence and useful baselines. A passing legacy Phase 3 test does not satisfy a
Bible Phase 3 exit gate.
