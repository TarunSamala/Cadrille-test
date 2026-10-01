# Architecture Decision Records

## ADR-001 — Rings first
**Decision:** Freeze rings as the product/research baseline before pendants/necklaces.  
**Why:** paired ground truth, component semantics and manufacturing validation are already hard enough.  
**Alternative rejected:** universal jewellery from day one.  
**Validation:** new ring designs must pass the same pipeline without design-specific hard coding.

## ADR-002 — Capture tiers
**Decision:** distinguish exploratory, product and intrinsic-detail capture contracts.  
**Why:** “3–4 photos” and “manufacturing accurate” are incompatible as one unconditional promise.  
**Validation:** every run records capture tier and permitted claim level.

## ADR-003 — Evidence-first architecture
**Decision:** models output evidence records, not direct final CAD authority.  
**Why:** reflections, hallucinations and disagreement must remain inspectable.  
**Validation:** every CAD parameter traces to evidence, review or a design rule.

## ADR-004 — STEP authoritative
**Decision:** exact STEP/B-rep is the engineering source; meshes are derived.  
**Why:** editability, component integrity and CAD-kernel validation.  
**Alternative:** mesh-only output.  
**Validation:** STEP opens independently and derived meshes match dimensions.

## ADR-005 — Dual geometry representation
**Decision:** exact parametric/B-rep for functional structure + local free-form/displacement for organic detail.  
**Why:** rings contain both engineering primitives and sculptural relief.  
**Validation:** attachment, wall thickness, topology and reprojection must pass together.

## ADR-006 — Generative 3D is not authoritative
**Decision:** TRELLIS/Hunyuan/Step1X/etc. are benchmarks or initialization.  
**Why:** hidden geometry can be generated plausibly but incorrectly.  
**Validation:** generated detail must be re-supported by real evidence and rebuilt/validated.

## ADR-007 — Per-view camera hypotheses for uncontrolled images
**Decision:** do not force one shared camera on unrelated product renders.  
**Why:** project experiment regressed.  
**Validation:** held-out reprojection and camera residuals.

## ADR-008 — Physical scale is a hard gate
**Decision:** no metric/manufacturing claim without known scale.  
**Why:** absolute dimensions are not observable from generic photos alone.  
**Validation:** calibration residual and dimensional check.

## ADR-009 — Human semantic review remains in the loop
**Decision:** uncertain components/hidden geometry require review.  
**Why:** current data/model evidence is insufficient for safe fully autonomous semantics.  
**Validation:** review conflicts must be zero before exact CAD promotion.

## ADR-010 — Do not train an end-to-end jewellery model yet
**Decision:** train only well-defined tasks with ground truth.  
**Why:** current 24-object dataset lacks CAD, scale and component truth.  
**Validation:** dataset capability matrix must support each claimed target.

## ADR-011 — Keep adapters, defer model router
**Decision:** standardize model interfaces but use explicit benchmark-based selection.  
**Why:** routing without evidence is architecture theater.  
**Validation:** router only returns if task-specific winners/conditions are reproducible.

## ADR-012 — Reflective-detail research gets a controlled capture lane
**Decision:** add controlled light/polarization experiments rather than trying to solve all reflectance in uncontrolled RGB.  
**Why:** polished metal creates shape-radiance ambiguity.  
**Validation:** scan/CAD ground truth and controlled ablations.

## ADR-013 — Manufacturing rules are versioned profiles
**Decision:** constraints are sourced from domain experts/processes, not invented by AI.  
**Why:** tolerances vary by process/material/stone.  
**Validation:** rule profile has owner, version, units and acceptance evidence.

## ADR-014 — Provenance is mandatory
**Decision:** geometry state is observed/inferred/designed/unknown.  
**Why:** prevents hallucination from becoming engineering fact.  
**Validation:** no exported critical feature without state/source.

## ADR-015 — Source control reconciliation precedes new architecture coding
**Decision:** establish one canonical commit/tag and clean-clone test result.  
**Why:** remote `main` currently lags the later locally tested Studio state.  
**Validation:** reproducible tests/build from tagged clone.

## ADR-016 — Hard geometry gates outrank optimization loss
**Decision:** invalid solids/connectivity cannot be accepted for a better image score.  
**Why:** project has already observed this failure.  
**Validation:** exact exported geometry passes hard gates before score comparison.
