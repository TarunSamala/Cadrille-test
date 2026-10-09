# Bible Phase 2 - Real Paired Benchmark

Status: **INACTIVE UNDER THE IMAGE-ONLY INPUT PROFILE**

The project can only receive images. Therefore this original Bible gate is
retained as an honest statement of unavailable validation—not as a request for
production STEP, scans, physical measurements or calibrated cameras.

Phase 2 is not another segmentation refinement. Its purpose is to build a real
paired benchmark in which every accepted jewellery object has guided images,
production CAD, physical measurements, component annotations and documented
legal provenance.

## Retained guardrail

- `dataset/paired_cad_v1/manifest.json` is the versioned dataset registry.
- `pipeline/bible_phase_2_paired_benchmark.py` validates each retained object.
- `dataset/paired_cad_v1/report.json` records the current gate state.
- Lalitha Studio exposes this unavailable gate separately from active
  image-only development and the older pseudo-mask experiment.

The validator fails closed when evidence is absent. It requires:

- 8-12 non-empty guided RGB views;
- camera/view metadata matching every retained image;
- an ISO 10303-21 production STEP file;
- at least one positive millimetre measurement with its source;
- a component graph with stable IDs and provenance states;
- rights holder, capture owner, CAD owner, agreement and permitted-use records;
- object-level, disjoint train/validation/test assignments.

The Bible exit gate additionally requires at least 20 valid pilot objects,
three or more design families, a scan-truth subset and a locked test split.

## Object layout

```text
dataset/paired_cad_v1/objects/<object_id>/
├── capture/
│   ├── rgb/                         # 8-12 guided images
│   └── camera_metadata.json
├── annotations/
│   └── component_graph.json
├── truth/
│   ├── production.step
│   ├── measured_dimensions.json
│   └── scan_mesh.*                  # required for the benchmark subset
└── provenance.json
```

## Validate

```bash
PYTHONPATH=pipeline python pipeline/bible_phase_2_paired_benchmark.py
```

The existing STL-1 set remains Tier A image evidence. It is not copied into
the paired registry because it has no production CAD, physical dimensions,
camera calibration or recorded redistribution/training rights.

## Ring01 carry-over

The user review identified inner-shank reflections as an unresolved visual
issue. A topology-informed image-only correction proposal is retained at
`data/ring01_ground_truth_v1/review/ring01_review_notes.json`. It may affect
metal boundaries, negative space and relative depth. The active work remains
image-only and the proposal still requires human review.
