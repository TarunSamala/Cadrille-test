# Repository structure

The repository keeps source code, inputs, generated artifacts, and validation tests separate.

```text
Image2CAD/
├── pipeline/                 Bible, shared and legacy implementation modules
├── tests/                    Regression and artifact-validation tests
├── docs/
│   ├── bible_v1_0/           Canonical specification and Phase 0-9 roadmap
│   ├── bible_implementation/ Current phase evidence and implementation docs
│   ├── legacy_pipeline/      Pre-Bible phase reports and diagrams
│   └── research/             Upstream project and model research
├── dataset/
│   ├── STL-1/                Original 24-ring, five-view source dataset
│   ├── prepared_v1/          Normalized images, masks, edges, and split manifests
│   ├── Sample_test/          Independent sample-ring validation input and results
│   └── phase_runs/v1/        Versioned legacy-numbered experiment outputs
│       ├── checkpoints/      Trained model weights
│       ├── comparisons/      Dataset comparison sheets
│       ├── phase_audits/     Per-ring phase audit sheets
│       ├── test_predictions/ Held-out predictions
│       └── phase3/
│           └── visual_hull/  Non-metric STL, 3MF, previews, and reports
└── data/                     Ring01 evidence and historical checkpoints
```

## Phase naming rule

The Project Bible v1.0 Phase 0-9 roadmap is the only canonical phase system.
The existing `ring01_phase*`, `phase_runs/v1/phase1`, `phase2`, `phase2_2` and
`phase3` paths use pre-Bible numbering. They remain in place to preserve
provenance and reproducibility, but are classified as legacy checkpoints.

New phase-specific modules and artifact roots must include `bible` in the name
or use an unambiguous named capability. The machine-readable authority is
`docs/phase_registry.json`.

## Conventions

- Original inputs stay unchanged.
- Generated dataset experiments are grouped by run version and phase.
- Phase outputs include their reports and previews beside the corresponding models.
- `hf_cache/`, Python bytecode, logs, and downloaded model files are local runtime data and remain ignored by Git.
- Legacy Phase 3 visual hulls are non-metric validation artifacts, not manufacturing-ready CAD.
