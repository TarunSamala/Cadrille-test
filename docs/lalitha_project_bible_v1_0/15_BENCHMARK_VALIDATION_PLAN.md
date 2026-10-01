# Benchmark & Validation Plan

## Benchmark philosophy

A model is not “better” because one screenshot looks nicer or one aggregate score is larger.

Every benchmark run must record:
- exact input hashes;
- capture tier;
- code commit;
- model/checkpoint;
- code, checkpoint and dataset licenses separately;
- hardware and peak memory;
- configuration and random seed;
- runtime;
- output representation;
- failed hard gates;
- per-view metrics;
- per-component metrics;
- uncertainty;
- final decision: `accept`, `reject`, `backtrack`, `research_only`.

## B0 — Software regression

**Goal:** prove the pipeline itself is reproducible.

Checks:
- clean clone;
- all unit/integration/frontend tests;
- production frontend build;
- corrupt-file rejection;
- partial-view rejection;
- path traversal/security checks;
- restart/job persistence;
- artifact readability.

**Exit:** all required tests pass from canonical tagged source.

## B1 — 2D evidence benchmark

Human truth required.

Metrics:
- foreground IoU/Dice;
- boundary F1 at several tolerances;
- stone/prong/support instance precision/recall;
- component count;
- cross-view identity accuracy;
- negative-space IoU;
- highlight/reflection false-positive rate.

**Important:** agreement between two machine masks is not accuracy.

## B2 — Camera / depth / normal benchmark

Compare on the same reviewed captures:
- COLMAP;
- VGGT;
- Depth Anything V2 Small;
- DSINE;
- research-only DUSt3R/MASt3R.

Metrics:
- camera rotation error;
- translation direction/scale-aware error where applicable;
- reprojection pixel error;
- depth RMSE/AbsRel after allowed alignment;
- metric depth error when scale exists;
- normal angular error;
- point-cloud distance;
- completeness.

## B3 — 3D reconstruction benchmark

Ground truth: production CAD and/or high-quality scan.

Metrics:
- symmetric Chamfer distance;
- point-to-surface distance;
- Hausdorff or percentile Hausdorff;
- normal angular consistency;
- dimensional error at named landmarks;
- local curvature error;
- surface completeness;
- thin-feature survival.

## B4 — Structural/editability benchmark

Checks:
- stable component IDs;
- correct stone count;
- correct support/prong count;
- seat ↔ stone matching;
- dependency updates;
- valid separate solids;
- removal of one stone modifies only its dependent geometry;
- no floating metal;
- no duplicate/intersecting components.

**Synthetic ten-stone edit test:** remove, resize and replace any single stone; all IDs remain stable and unrelated geometry is unchanged.

## B5 — Intrinsic detail benchmark

Use objects with real sculptural/relief truth.

Regions:
- nose;
- eyes/eyelids;
- lips;
- cheeks/forehead;
- hair/crown;
- engraving;
- ornamentation.

Metrics:
- local point-to-surface error;
- normal angular error;
- curvature distribution error;
- ridge/valley localization;
- landmark distance;
- high-frequency energy retention;
- expert semantic acceptance.

A photometric/image-similarity score alone cannot pass this benchmark.

## B6 — Manufacturing benchmark

Hard gates:
- known physical scale;
- valid/closed solids;
- min wall profile;
- min prong/support profile;
- stone-seat clearance;
- girdle contact;
- pavilion clearance;
- no stone/metal collision except intended contact;
- no cavity breakthrough unless designed;
- no trapped/floating bodies;
- independent STEP load;
- derived STL/3MF watertight;
- critical dimensions checked against physical measurement/scan;
- specialist review.

## Current visual research gates inherited from the existing roadmap

| Measurement | Minimum current research gate | Strong target |
|---|---:|---:|
| Mean silhouette IoU | 0.80 | 0.90+ |
| Every principal view IoU | 0.70 | 0.85+ |
| Angled-view IoU | 0.70 | 0.82+ |
| Mean detail-region IoU | 0.75 | 0.85+ |
| External boundary F1 | 0.75 | 0.88+ |
| Stable component identity | 100% | 100% |
| Required topology/solid checks | 100% | 100% |

These gates become accuracy claims only when target masks are human-reviewed.

## Promotion rule

A candidate method is promoted only when:
1. it improves the intended held-out metric;
2. it does not regress a hard topology/manufacturing gate;
3. the improvement survives a second object/design family;
4. the license and compute requirements are acceptable;
5. failure modes are documented.

## Benchmark scorecard policy

Do not collapse all dimensions into a single “92/100” winner.

Use a vector:
```text
visual
geometry
semantic structure
editability
topology
manufacturing
runtime
VRAM
failure rate
license/deployment fit
```

This makes routing decisions evidence-based rather than aesthetic.
