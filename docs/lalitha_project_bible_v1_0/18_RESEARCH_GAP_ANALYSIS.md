# Research Gap Analysis

## Solved well enough by existing technology

These are not places to invent novelty:
- deterministic image QA and basic edge/contour extraction;
- promptable foreground segmentation proposals;
- standard B-rep construction/STEP export;
- visual hulls from calibrated/aligned silhouettes;
- standard SfM/MVS when texture/capture is favorable;
- browser 3D visualization;
- mesh manifold/readability checks;
- experiment/job orchestration.

## Partially solved

### Reflective multi-view geometry
Methods such as NeRO, NeRSP and newer glossy-scene methods address important parts of the reflectance problem, but practical sparse jewellery includes metal, gemstones, self-occlusion and sub-millimetre relief.

### Component-level jewellery semantics
General detectors/segmenters can propose parts, but stable identities, seats, prongs, cavities and relationships are not solved as a manufacturing graph.

### Depth and normals on polished fine relief
Foundation models provide useful priors, but their error on small reflective relief must be measured against scan/CAD truth.

### Image-conditioned editable CAD
Img2CAD, Cadrille and CAD-Recode show meaningful routes to editable/programmatic CAD, but their demonstrated domains do not establish jewellery-specific manufacturing reconstruction.

### Dense/neural geometry → exact CAD
Converting rich free-form evidence into robust exact CAD while retaining editability remains difficult.

### Confidence / uncertainty
Model confidence is not automatically calibrated engineering uncertainty.

## Project-specific engineering gaps

### G1 — Reflectance-aware sub-millimetre detail fusion
Fuse multi-view parallax, normals, relative depth, reflectance likelihood, controlled lighting and semantic landmarks without copying texture/highlights into geometry.

### G2 — Jewellery Component & Constraint Graph
Represent stone ↔ seat ↔ prong ↔ gallery ↔ shank relationships with stable IDs, editable parameters and localized dependency updates.

### G3 — Hybrid exact CAD + free-form detail
Attach validated relief/free-form patches to exact B-rep parts without destroying topology, wall thickness or downstream editability.

### G4 — Provenance-aware hidden geometry
Engineering data model and UI for observed/inferred/designed/unknown regions.

### G5 — Jewellery image-to-CAD benchmark
A real paired dataset with guided images, production CAD, physical dimensions, component annotations and scan subset.

## Potential original research contributions

These are **candidates**, not novelty claims until literature search and experiments confirm them:

1. **Reflectance-aware intrinsic-detail reconstruction for jewellery** with provenance-aware fusion and controlled capture ablations.
2. **Jewellery Component & Constraint Graph** for image-conditioned editable exact CAD.
3. **Hybrid B-rep + free-form relief representation** with manufacturing-aware attachment/validation.
4. **A paired jewellery image/CAD/scan benchmark** with component and detail metrics.
5. **Uncertainty-aware reconstruction** that distinguishes measured, inferred and designed geometry.

## What should not be presented as novel

- using SAM;
- using COLMAP;
- using depth maps;
- using surface normals;
- using curvature;
- using CadQuery;
- using NeRF/Gaussians;
- using a model ensemble;
- using a web viewer;
- using Chamfer distance.

Novelty, if any, must come from the jewellery-specific formulation, data, fusion, representation, constraints or demonstrated result.
