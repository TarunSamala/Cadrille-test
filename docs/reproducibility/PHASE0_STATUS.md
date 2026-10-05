# Phase 0 - Reproducibility Freeze

Status: **IN PROGRESS**

This freeze follows
`docs/lalitha_project_bible_v1_0/19_DEVELOPMENT_ROADMAP.md` and benchmark
gate B0. It establishes a repeatable CPU/software baseline. It does not change
the accuracy status of any reconstruction result.

## Canonical source

| Check | Result | Evidence |
|---|---|---|
| Canonical branch | PASS | `main` |
| Local versus remote | PASS | local `main` and `origin/main` resolve to `79b390acb6bade147f0e68757f647f9d881b2909` before this freeze |
| Prior development branch | PASS | `main..cad-test` contains no commits |
| Baseline tag | PENDING | create only after the complete suite passes from a clean checkout |

## Environment

| Check | Result | Evidence |
|---|---|---|
| Digest-pinned base image | PASS | `Dockerfile.validation` |
| Fixed project dependencies | PASS | `requirements-validation.txt` and `constraints-validation.txt` |
| SAM 2 source integrity | PASS | commit archive and SHA-256 are pinned |
| Environment manifest | PASS | `environment_manifest.json` |
| Dependency/license inventory | PASS WITH REVIEW | metadata inventory generated; legal review remains required |
| GPU reproducibility | PENDING | host NVIDIA driver was unavailable during this freeze |
| LFS integrity | PASS | `git lfs fsck` passed |
| LFS migration | DEFERRED | two tracked OBJ files exceed GitHub's recommended 50 MB size but are ordinary Git objects; history migration needs a separate approved operation |

## B0 software regression

| Check | Result | Evidence |
|---|---|---|
| Existing core/backend tests | PASS | 99 tests passed in `image2cad-validation:phase0` |
| Separate frontend production build | NOT APPLICABLE | Studio uses Flask templates plus static CSS/JavaScript; no Node build manifest exists |
| Corrupt-file rejection | PASS | explicit undecodable-image regression |
| Partial-view rejection | PASS | incomplete multi-view sets fail closed |
| Path traversal/security | PASS | repository and API tests reject traversal-like object/asset selectors |
| Restart/job persistence | NOT APPLICABLE YET | current Studio is read-only and audit execution is synchronous; this becomes a required gate before persistent background jobs are introduced |
| Artifact readability | PASS | previews, masks, STL, STEP and 3MF checks are covered by the regression suite |
| Full suite including freeze self-checks | PASS | 104 tests passed in the pinned validation image |
| Clean-checkout test | PENDING | run after the candidate baseline commit exists |

## Accuracy and release limits

- The current STL-1 dataset has no human-reviewed masks, calibrated cameras,
  physical scale, production CAD targets or scan truth.
- Machine-mask agreement is not ground-truth accuracy.
- Existing Phase 3 output remains experimental and non-metric.
- Manufacturing accuracy is not validated.
- The Phase 0 baseline cannot be promoted until the full suite and clean
  checkout checks pass.
