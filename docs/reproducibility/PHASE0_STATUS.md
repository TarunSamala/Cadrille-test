# Phase 0 - Reproducibility Freeze

Status: **COMPLETE — CPU/SOFTWARE/GPU REPRODUCIBILITY VALIDATED**

This freeze follows
`docs/lalitha_project_bible_v1_0/19_DEVELOPMENT_ROADMAP.md` and benchmark
gate B0. It establishes a repeatable CPU/software baseline. It does not change
the accuracy status of any reconstruction result.

## Canonical source

| Check | Result | Evidence |
|---|---|---|
| Canonical branch | PASS | `main` |
| Pre-freeze local versus remote | PASS | local `main` and `origin/main` both resolved to `79b390acb6bade147f0e68757f647f9d881b2909` before Phase 0 |
| Prior development branch | PASS | `main..cad-test` contains no commits |
| Validated source commit | PASS | `9cd88c81c92824792a4cf2996885eeb1b3b426dd` |
| Baseline tag | PASS | `baseline-v1.1` identifies the final Phase 0 evidence commit; `baseline-v1.0` remains preserved |

## Environment

| Check | Result | Evidence |
|---|---|---|
| Digest-pinned base image | PASS | `Dockerfile.validation` |
| Fixed project dependencies | PASS | `requirements-validation.txt` and `constraints-validation.txt` |
| SAM 2 source integrity | PASS | commit archive and SHA-256 are pinned |
| Environment manifest | PASS | `environment_manifest.json` |
| Dependency/license inventory | PASS WITH REVIEW | metadata inventory generated; legal review remains required |
| GPU reproducibility | PASS | RTX 3050 Laptop GPU, driver 615.71.09 and CUDA 12.4 were visible inside the pinned validation image |
| LFS integrity | PASS | `git lfs fsck` passed |
| LFS migration | DEFERRED | two tracked OBJ files exceed GitHub's recommended 50 MB size but are ordinary Git objects; history migration needs a separate approved operation |

## B0 software regression

| Check | Result | Evidence |
|---|---|---|
| Complete core/backend/Studio/B2 tests | PASS | 130 tests passed in the pinned CUDA/COLMAP validation environment |
| Separate frontend production build | NOT APPLICABLE | Studio uses Flask templates plus static CSS/JavaScript; no Node build manifest exists |
| Corrupt-file rejection | PASS | explicit undecodable-image regression |
| Partial-view rejection | PASS | incomplete multi-view sets fail closed |
| Path traversal/security | PASS | repository and API tests reject traversal-like object/asset selectors |
| Restart/job persistence | NOT APPLICABLE YET | current Studio is read-only and audit execution is synchronous; this becomes a required gate before persistent background jobs are introduced |
| Artifact readability | PASS | previews, masks, STL, STEP and 3MF checks are covered by the regression suite |
| Full suite including freeze self-checks | PASS | 130 tests passed, including the GPU-aware freeze and Phase 3/B2 contracts |
| Clean-checkout test | PASS | fresh local clone of `baseline-v1.1`; 130 tests passed in the pinned CUDA/COLMAP image |

## Accuracy and release limits

- The current STL-1 dataset has no human-reviewed masks, calibrated cameras,
  physical scale, production CAD targets or scan truth.
- Machine-mask agreement is not ground-truth accuracy.
- Existing Phase 3 output remains experimental and non-metric.
- Manufacturing accuracy is not validated.
- The CPU/software/GPU runtime baseline is reproducible. Model-specific VRAM,
  checkpoint licensing and scientific accuracy remain separate Phase 3 gates.
