# Documentation index

## Start here

The **Project Bible v1.0 is the canonical phase system** for this repository.
It defines Phase 0 through Phase 9. The earlier Ring01 and STL-1 Phase 1 through
Phase 3.3.2 labels are historical and are now called the **legacy pipeline**.

The active execution profile accepts **images only**. Bible gates requiring
production CAD, scans, physical dimensions or calibrated cameras remain frozen
as unavailable validation gates; they are not requested project inputs.

- [Canonical Bible](bible_v1_0/README.md)
- [Canonical development roadmap](bible_v1_0/19_DEVELOPMENT_ROADMAP.md)
- [Current Bible implementation evidence](bible_implementation/README.md)
- [Legacy pipeline index](legacy_pipeline/README.md)
- [Research index](research/README.md)
- [Machine-readable phase registry](phase_registry.json)
- [Repository structure](REPOSITORY_STRUCTURE.md)

## Directory authority

| Directory | Role |
| --- | --- |
| `bible_v1_0/` | Frozen requirements, architecture, gates and Phase 0-9 roadmap |
| `bible_implementation/` | Current implementation reports and evidence mapped to Bible phases |
| `legacy_pipeline/` | Pre-Bible reports, diagrams and phase language retained for history |
| `research/` | Upstream projects, datasets and 2D-to-3D model research |

Existing artifact paths under `data/` and `dataset/phase_runs/` are not renamed
because their reports, manifests and tests record those exact paths. Their
legacy status is documented instead of rewriting provenance.
