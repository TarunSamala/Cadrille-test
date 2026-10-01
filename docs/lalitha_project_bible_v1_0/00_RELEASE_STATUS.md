# Lalitha / Image2CAD — Project Bible Release Status

**Release:** BASELINE ARCHITECTURE V1.0  
**Date:** 2026-09-29  
**Project:** Live Metal / Lalitha — Jewellery Image-to-CAD Reconstruction  
**Primary near-term scope:** Rings  
**Status:** Engineering and research baseline accepted with conditions  
**Manufacturing-accuracy status:** **NOT YET VALIDATED**

## Release decision

This release is a **single source of engineering truth for what should be built next**, not a claim that the full product is already solved.

The strongest implemented checkpoint recovered from the project record is **Ring01 Phase 3.3.2**. The existing system already contains reproducible image evidence extraction, jewellery segmentation proposals, a review/evidence gate, dataset-wide non-metric visual-hull reconstruction, exact CadQuery/OpenCascade ring solids, and render-and-compare validation.

What is **not** yet proven:
- metric reconstruction from ordinary photographs;
- generalization from Ring01 to arbitrary jewellery;
- reliable hidden-surface reconstruction;
- fine sculptural/deity-face fidelity;
- jewellery-specific component truth across a real benchmark;
- manufacturing validity across jewellers, alloys, casting processes, setters and tolerances.

## Baseline principle

> **Evidence first. Exact CAD is authoritative. Learned or generative 3D is evidence, initialization, or benchmark output until validated.**

The final system therefore uses two geometric representations:
1. **Exact parametric/B-rep CAD** for functional jewellery structure.
2. **Validated high-frequency free-form detail** for sculptural relief, engravings and deity faces.

Both must retain source provenance, confidence and explicit labels for **observed / inferred / designed / unknown** geometry.

## Evidence classes

| Class | Meaning | Allowed use |
|---|---|---|
| PROVEN-IN-PROJECT | Implemented and measured in the current project record | May be part of baseline |
| PROVEN-EXTERNAL | Supported by established literature/tooling but not yet validated on Lalitha | Candidate/benchmark |
| ADAPTED | Established method with jewellery-specific engineering added | Allowed with project validation |
| PROPOSED | Engineering design not yet implemented | Roadmap only |
| EXPERIMENTAL | Research candidate requiring controlled experiment | Research branch |
| SPECULATIVE | Hypothesis without sufficient evidence | Never silently promoted |

## Claim levels

| Claim level | Minimum evidence |
|---|---|
| Visual reconstruction | Reprojection/silhouette/detail metrics against reviewed image truth |
| Structural reconstruction | Stable components, valid topology, editable constraints and cross-view identity |
| Metric reconstruction | Known physical scale plus calibrated/reviewed geometry |
| Manufacturing reconstruction | Metric truth, hidden-geometry verification or declared inference, rule validation, independent CAD inspection and physical/scan evidence |

## Final board status

- **Agent 1 — Project Archaeology:** COMPLETE for accessible project history, files, current repository state and prior design discussions.
- **Agent 2 — Forensic Audit:** PASS WITH SOURCE-CONTROL WARNING. The public GitHub `main` branch is behind a later locally tested Studio state.
- **Agent 3 — Principal Science/Architecture:** COMPLETE.
- **Agent 4 — Adversarial CTO/Scientific Review:** ACCEPTED WITH CONDITIONS.
- **Agent 5 — Research/Open-Source Intelligence:** COMPLETE for Baseline V1.0; licenses must be rechecked before production packaging.
- **Agent 6 — Project Bible:** COMPLETE.

## Conditions before calling Lalitha manufacturing-ready

1. Canonical source-control state is reproducible from a clean clone.
2. Human ground-truth annotations exist for the current Ring01 validation set.
3. At least one physical dimension is known for every metric test object.
4. A real paired photo ↔ production-CAD dataset is established.
5. Intrinsic-detail reconstruction passes controlled experiments on reflective jewellery.
6. Manufacturing rules are supplied and signed off by jewellery CAD/manufacturing specialists.
7. Critical dimensions are independently measured or scan-validated.
