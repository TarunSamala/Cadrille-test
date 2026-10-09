# Duplicate / Redundancy Matrix

| Concept A | Concept B | Relationship | Decision |
|---|---|---|---|
| “Jewellery Vision Engine” | Phase 2.3 Evidence Engine | Partial overlap | Keep evidence extraction; do not force final semantics in vision |
| Jewellery Part Graph | Component & Constraint Graph | Same objective, V1 is richer | Merge into Component & Constraint Graph |
| Monocular depth | VGGT depth/point maps | Same latent variable, different evidence | Keep as independent branches; fuse with disagreement |
| COLMAP MVS | Neural multi-view geometry | Same objective, different method | Benchmark side-by-side |
| Image edges | Geometry ridges/curvature | Partial overlap only | Keep separate domains; never treat RGB edge as curvature |
| Top-hat/black-hat/Laplacian | Wavelet/frequency bands | Same objective, different scale representation | Retain simple methods; add wavelet only if experiment shows benefit |
| Visual hull | Generative 3D mesh | Coarse shape, radically different assumptions | Visual hull baseline; generative only prior |
| Cadrille | CAD-Recode | Competing learned CAD-program methods | Benchmark on same jewellery GT |
| Cadrille | Img2CAD | Same high-level image→editable CAD goal | Research comparison, not parallel production modules |
| TRELLIS / Hunyuan / Step1X / Tripo-family | Each other | Competing generative 3D models | Keep registry, not all in product runtime |
| Trimesh repair | Manifold repair | Partial overlap | Trimesh for analysis, Manifold benchmark for difficult mesh Boolean |
| Human review | Confidence heatmap | Complementary | Confidence prioritizes review; never replaces it automatically |
| Model adapter layer | Model router | Adapter enables router | Keep adapters; defer autonomous router |
| 3–4 photo workflow | 5-view Studio | Conflicting capture contracts | Preserve as Tier A vs current research contract |
| 5-view Studio | 8–12 guided capture | Same objective, different evidence strength | Keep 5-view research; add stronger product capture profile |
| Hidden-geometry inference | Backside optimization/hollowing | Different goals often conflated | Separate “inferred reconstruction” from “designed optimization” |
| Mesh → CAD conversion | Direct parametric reconstruction | Competing routes | Prefer direct B-rep for known components; use conversion research only where useful |
| Relief displacement | NURBS/free-form patches | Alternative detail representations | Route by geometry: shallow vs deep/complex |
| Appearance texture | Microgeometry | Can look similar in RGB | Separate representations and validate independently |
| Semantic class confidence | Geometric confidence | Different uncertainty | Store separately; fuse only at decision layer |
