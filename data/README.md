# Data and generated artifacts

The Ring01 workflow keeps every major checkpoint in a separate directory so results can be compared or backtracked without overwriting earlier geometry.

The `ring01_phase*` directory names belong to the **legacy pipeline**. They
predate the Project Bible and are retained unchanged because reports and
manifests refer to them. They are not evidence that the corresponding Bible
phase is complete.

## Active Ring01 files

| Path | Role |
| --- | --- |
| `ring01_reference_images/` | Normalized front, side, top, angled and back source images |
| `ring01_artifact.json` | Prepared inference artifact |
| `ring01_metadata.json` | Extracted jewellery metadata |
| `ring01_output.py` | Generated CadQuery program |
| `ring01_output_512.py` | Historical 512-token generated program |
| `ring01_ring.step` / `.stl` | Early generated reconstruction retained for comparison |
| `ring01_phase1/` | Legacy Phase 1 initial vision measurements |
| `ring01_phase2*` | Legacy Phase 2 segmentation and feature-extraction checkpoints |
| `ring01_phase3*` | Legacy Phase 3 Ring01 reconstruction, refinement and CAD-validation checkpoints |
| `ring01_ground_truth_v1/` | Bible Phase 1 image-evidence and ground-truth proposal artifacts |
| `ring01_image_only/` | Active image-only correction and uncertainty checkpoints |
| `ring01_validation*` | Cross-phase validation artifacts |
| `logs/` | Historical command output; new logs are ignored by Git |

## Legacy checkpoint convention

Each retained checkpoint directory contains its reports, masks/renders,
comparisons and exported geometry. New work follows the Bible roadmap; do not
create another ambiguous bare `phase1`, `phase2` or `phase3` family.

Do not silently replace an accepted earlier phase. Record experiments and validation results so a change can be evaluated and backtracked.

## Authoritative formats

- Source reference images are the visual input.
- JSON reports are the machine-readable validation record.
- STEP is the authoritative editable CAD representation.
- STL, OBJ and GLB are derived print, exchange or preview formats.
- Preview and comparison images support inspection but are not measurement ground truth.

Information about datasets used by the original general-purpose research code is retained in [Upstream datasets](../docs/research/UPSTREAM_DATASETS.md).
