# Phase 1: Image-only ground truth

Phase 1 converts the retained Ring01 machine proposals into reviewed image-space
evidence. It does not claim hidden geometry, calibrated cameras, physical scale,
or manufacturing accuracy.

## Exit gate

Phase 1 passes only when an identified human reviewer has:

- inspected and approved all seven labels in all five views;
- confirmed the seven cross-view component identities;
- reviewed every view label and recorded the camera/projection uncertainty;
- resolved any review conflict.

The seven labels are jewellery silhouette, metal, shank, visible stone, setting,
prongs, and enclosed negative space. An inaccurate proposal must be marked
needs_correction or rejected; approval is never automatic.

## Scale and depth policy

The supplied evidence contains no known physical dimension. Image-space
coordinates and relative Depth Anything V2 proposals are therefore usable, but
millimetres are not. Missing metric scale is recorded and visible in the Studio,
but it does not block the image-ground-truth gate. If a trusted known dimension
is supplied later, it can be recorded without changing the original image
evidence.

Camera intrinsics and extrinsics may remain unknown. A reviewer may approve the
view semantics only when the uncertainty states that calibration is unavailable.

## Studio workflow

Run the Studio, open Phase 1 / Ring01 Ground Truth, enter a reviewer name,
inspect the source and proposal side by side, and record a decision. The Studio
writes only review decisions to
data/ring01_ground_truth_v1/manifest.json; it does not execute model inference
or alter source images.

    python -m studio.app

The same operations remain available through
python -m pipeline.phase1_ground_truth for auditable command-line use.
