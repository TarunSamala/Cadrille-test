# Development Roadmap

## Phase 0 — Reproducibility Freeze

**Build**
- reconcile local/remote repository;
- choose canonical commit;
- push/tag Baseline source;
- clean-clone environment;
- run all core/backend/frontend tests;
- generate environment + dependency/license manifest.

**Exit**
- reproducible test/build results from clean clone;
- no ambiguity about latest source.

## Phase 1 — Ground-Truth Ring01

**Build**
- five human-reviewed masks;
- component identities;
- negative-space truth;
- at least one known physical dimension;
- camera metadata/uncertainty record.

**Exit**
- zero unresolved review conflicts;
- reproducible human-GT report.

## Phase 2 — Real Paired Benchmark

**Build**
- first 20 rings quickly, then 50–100;
- guided 8–12 view protocol;
- production CAD;
- physical dimensions;
- component graph annotations;
- scan subset.

**Exit**
- locked object-level test split;
- at least several design families;
- legal/data provenance documented.

## Phase 3 — Camera / Geometry Evidence Benchmark

**Run**
- COLMAP;
- VGGT;
- Depth Anything V2 Small;
- DSINE;
- research DUSt3R/MASt3R;
- existing visual hull.

**Exit**
- per-method camera/depth/normal/3D metrics;
- selected baseline for each evidence type;
- no vague “best model” statement.

## Phase 4 — Universal Component & Constraint Graph

**Build**
- stable IDs;
- cross-view tracks;
- part relationships;
- stone/seat/cavity/support dependencies;
- uncertainty/provenance states;
- generic scene graph API.

**Exit**
- synthetic ten-stone edit test passes 100%;
- no unrelated geometry changes during local edit.

## Phase 5 — Exact CAD V2

**Build**
- general shank/shoulder/head generators;
- stone family primitives;
- seats/cavities;
- prongs/bezels/channels;
- galleries;
- symmetry/repetition constraints;
- exact render-and-compare fitting.

**Exit**
- multiple unseen ring families meet structural/topology gates.

## Phase 6 — Intrinsic Detail Capture Lab

**Build**
- controlled turntable/camera protocol;
- repeatable light positions;
- cross-polarization/polarization branch;
- scan/CAD truth;
- relief/deity samples.

**Exit**
- repeatable calibrated dataset;
- baseline RGB vs controlled-light vs polarized comparison.

## Phase 7 — Hybrid Detail Geometry

**Benchmark**
- displacement;
- NURBS/subdivision/free-form;
- normal/depth/curvature/frequency fusion;
- NeRO/NeRSP-like reflective methods where appropriate.

**Exit**
- visible detail improves B5 metrics;
- no topology/wall-thickness regression;
- deity/semantic landmarks pass expert review.

## Phase 8 — Manufacturing Engine

**Build**
- versioned rule profiles;
- wall/prong minima;
- seat/pavilion/girdle clearances;
- collisions;
- trapped/floating bodies;
- casting/polishing/print allowance;
- volume/mass estimates.

**Exit**
- expert-reviewed test suite;
- physical/scan validation on critical dimensions.

## Phase 9 — B2B Pilot

**Workflow**
```text
guided capture
→ evidence
→ reviewed component graph
→ exact CAD
→ uncertainty review
→ manufacturing validation
→ designer approval
→ STEP
```

**Exit**
- measured reduction in CAD labor;
- acceptable designer correction time;
- no hidden manufacturing claim outside evidence.

## What NOT to build yet

- giant end-to-end jewellery foundation model;
- autonomous model router;
- necklaces/complex chains as first validation class;
- automatic hidden backside presented as truth;
- automatic deity-face reconstruction in the MVP promise;
- AI-invented manufacturing tolerances;
- new CAD kernel;
- product dependencies whose licenses prohibit commercial use;
- one universal benchmark score;
- heavy cloud 3D generators before the paired benchmark exists.

## Frozen immediate execution order

```text
SOURCE CONTROL
    ↓
HUMAN + METRIC GROUND TRUTH
    ↓
CAMERA / DEPTH / NORMAL BENCHMARK
    ↓
COMPONENT & CONSTRAINT GRAPH
    ↓
EXACT CAD GENERALIZATION
    ↓
INTRINSIC DETAIL RESEARCH
    ↓
MANUFACTURING VALIDATION
```
