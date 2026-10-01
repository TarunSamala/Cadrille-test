# Experiment Backlog

| ID | Hypothesis | Method | Ground truth / baseline | Pass condition | Failure interpretation | Priority |
|---|---|---|---|---|---|---|
| E01 | Human review changes current Ring01 scores meaningfully | Annotate five views: foreground, metal, stone, setting, prongs, negative space | Current machine/review masks | Complete conflict-free human set | Existing metrics are not defensible accuracy | P0 |
| E02 | Exact Ring01 fit remains valid against human truth | Re-run Phase 3.3.x fitting | E01 masks + current checkpoint | Meets current minimum gates without topology regression | Current fit overfit machine masks | P0 |
| E03 | More guided views reduce 3D/detail error | Compare 5 vs 8 vs 12 guided views | Same physical ring CAD/scan | Significant B3/B5 improvement | Extra capture burden may not be justified | P0 |
| E04 | One known dimension is enough for usable metric scale | Calibrate via inner diameter vs stone size vs target | Physical calipers/CAD | Critical dims within chosen tolerance | Need multi-point calibration | P0 |
| E05 | VGGT improves camera/geometry on reflective rings over COLMAP | Same captures, common benchmark | CAD/scan + calibration | Better camera/3D downstream exact fit | Feed-forward geometry not robust to jewellery | P0 |
| E06 | Depth Anything V2 Small adds useful shape prior | Add relative depth loss/evidence | CAD/scan depth | Improves 3D/detail without bias | Monocular prior hurts reflective shapes | P1 |
| E07 | DSINE normals add useful relief evidence | Fuse normal prior | CAD/scan normals | Improves local normal/curvature error | Normal prior follows shading artifacts | P1 |
| E08 | Highlight-aware edge classification reduces false geometry | Classify/score edge as geometry vs appearance | Human + controlled truth | Lower false cavity/ridge rate | Need stronger physical capture |
| E09 | Cross-polarization materially improves metal detail | Capture cross/parallel polarized views | CAD/scan | Lower B5 geometry error | Hardware overhead not worth benefit |
| E10 | Multi-light photometric stereo improves normals on selected metals | Controlled known lights | Scan normals | Better normal/detail error | Non-Lambertian effects dominate |
| E11 | NeRSP-like polarized reconstruction works on jewellery scale | Six+ polarized views | Scan | Beats RGB sparse baselines | Inter-reflection/gemstone optics dominate |
| E12 | NeRO improves reflective geometry | Run on controlled multi-view ring | Scan | Better surface error than generic neural baseline | Too heavy/unstable |
| E13 | Displacement is sufficient for shallow engraving | Fit displacement on exact base | CAD/scan | Pass B5 + wall check | Use free-form patch |
| E14 | NURBS/subdivision patch is required for deep deity relief | Compare displacement vs free-form | Relief scan | Lower error with valid attachment | Representation complexity not justified |
| E15 | Multi-scale frequency loss preserves ornament detail | Add wavelet/Laplacian-pyramid loss | Scan/detail maps | Better high-frequency retention without noise | Loss overfits texture/reflection |
| E16 | Curvature-aware loss improves facial form | Add surface curvature term | Scan | Better curvature/landmark metrics | Numerically unstable/no value |
| E17 | Synthetic segmentation transfers to real jewellery | Train synthetic→test real | Human real masks | Beats real-only baseline or reduces annotation need | Domain gap too large |
| E18 | Synthetic geometry supervision helps depth/normal fine-tune | Synthetic exact buffers | Real scan test | Better real B2/B3 | Synthetic reflectance not realistic |
| E19 | Component graph supports independent ten-stone edits | Build synthetic ten-stone CAD | Exact graph truth | All edits local and IDs stable | Dependency model incomplete |
| E20 | Seat/cavity generator follows stone pose robustly | Parameter sweep stone shapes/poses | Exact rules | 100% valid Booleans over test sweep | Generator needs feature-specific logic |
| E21 | Manufacturing rule profiles can be encoded deterministically | Specialist-defined profile | Expert CAD review | Matches expert violations | Rules too contextual; add review |
| E22 | Cadrille can generate useful jewellery CAD candidates | Train/test with synthetic jewellery | Exact CadQuery truth | Better than simple retrieval/template baseline | Domain mismatch; keep out |
| E23 | CAD-Recode can recover jewellery primitives from point clouds | Jewellery point clouds | Exact CadQuery truth | Valid program + lower shape error | Poor on curved/organic settings |
| E24 | Generative 3D prior improves initialization only | Compare fit with/without TRELLIS/Hunyuan/Step1X init | Same final CAD truth | Fewer iterations/better convergence with no hallucination retained | Remove generative dependency |
| E25 | Confidence is calibrated enough for selective automation | Reliability/coverage analysis | Human review outcomes | Error decreases predictably as confidence threshold rises | Confidence cannot gate autonomy |
| E26 | Canonical repository reproduces all current tests | Push/tag + clean clone | Captured local test counts | Same or explicitly versioned results | Source history unresolved |
