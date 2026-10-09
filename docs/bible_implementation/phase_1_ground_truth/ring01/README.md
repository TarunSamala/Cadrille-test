# Phase 1 - Ring01 Ground Truth

Phase 1 converts the existing Ring01 machine proposals into reviewed evidence.
It does not automatically promote refined Phase 2 masks or monocular depth to
ground truth.

## Current state

- Five source views are hash-recorded.
- Seven mask classes per view are staged for review.
- Enclosed negative-space proposals are generated from each silhouette.
- Stable IDs are proposed for one shank, one setting, one stone and four prongs.
- Depth Anything V2 Small generated relative-depth and flip-consistency
  uncertainty proposals.
- Human mask/component review, camera review and physical scale are unresolved.

The authoritative state is
`data/ring01_ground_truth_v1/manifest.json`.

The pixel-level feature contract and repeated depth validation are documented
in `docs/bible_implementation/phase_1_ground_truth/ring01/FULL_FEATURE_EXTRACTION.md`.

## Why Depth Anything V2 is included

Depth Anything V2 Small provides inexpensive relative-depth evidence and fits
the 4 GB RTX 3050. It does not recover millimetres, hidden geometry or
cross-view-consistent depth by itself. Specular metal and transparent gemstone
facets are known failure regions, so the raw float map, normalized 16-bit map,
preview and flip-consistency diagnostic are retained together.

## Review a label

```bash
docker run --rm \
  -v "$PWD:/workspace" -w /workspace \
  image2cad-validation:phase0 \
  python pipeline/phase1_ground_truth.py --repo-root /workspace \
  review-label --view front --label jewelry \
  --decision approved --reviewer "REVIEWER NAME"
```

Use `needs_correction` or `rejected` when a proposal is wrong. Approval
must not be used merely because the overlay looks plausible at a distance.

## Record a known dimension

```bash
python pipeline/phase1_ground_truth.py set-dimension \
  --name inner_ring_diameter \
  --value-mm 17.30 \
  --uncertainty-mm 0.05 \
  --source "digital caliper measurement" \
  --reviewer "REVIEWER NAME"
```

The value above is only an example; never copy it without measuring Ring01 or
obtaining reliable manufacturer data.

## Record camera information

```bash
python pipeline/phase1_ground_truth.py set-camera \
  --view front \
  --projection-model unknown \
  --uncertainty "Original camera and crop metadata unavailable" \
  --decision approved \
  --reviewer "REVIEWER NAME"
```

Unknown information can be reviewed and accepted as explicitly unknown. It
must not be replaced with invented focal lengths or poses.
