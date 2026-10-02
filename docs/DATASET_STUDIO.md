# Lalitha Studio — STL-1 Evidence Console

Lalitha Studio is a lightweight, read-only Flask backend and browser interface for `dataset/STL-1`. It exposes retained evidence instead of recomputing the GPU pipeline during a web request.

## What it shows

- All 24 rings and their five source views.
- The normalized 768 px images, pseudo-silhouettes and OpenCV edge maps.
- Per-view Phase 2 IoU, Dice and boundary-F1 measurements.
- The retained Phase 1 to Phase 2.2 audit sheet for every object.
- Held-out prediction sheets for the three test objects.
- Experimental Phase 3 visual-hull previews and validation metadata.
- Direct downloads of each non-metric STL and 3MF artifact.
- A portable per-object JSON evidence report.

The interface labels Phase 3 correctly: these are watertight research meshes at nominal display scale. The dataset has no calibrated cameras, physical dimensions, component ground truth or CAD targets, so the outputs are not manufacturing-validated CAD.

## Project Bible alignment

This interface follows `BASELINE ARCHITECTURE V1.0`:

- The current five-view dataset is classified as **Tier A — exploratory**.
- Source images remain immutable observed evidence.
- Normalization, pseudo-masks, edges and visual hulls are derived/inferred evidence.
- Phase 2 IoU is labelled pseudo-label self-consistency, not human-ground-truth accuracy.
- Phase 3 STL/3MF files are research-only derived meshes, not authoritative CAD.
- STEP/exact B-rep remains the required authoritative functional-geometry output.
- Metric, camera, reviewed-component, exact-B-rep and manufacturing gates are shown as blocked when their required evidence is absent.
- Every exported Studio report uses the final decision `research_only` and records which benchmark provenance fields are still missing.

The Studio belongs to the Bible's local/deterministic deployment boundary. It reads evidence, reports provenance and exposes review state. It does not let a browser request run a GPU model, mutate accepted evidence or silently write inferred geometry into STEP.

The frozen development order remains:

```text
source-control reproducibility → human and metric ground truth → camera/depth/normal benchmark → reviewed component and constraint graph → exact CAD generalization
```

## Run locally

Arch's system Python currently includes Flask. From the repository root:

```bash
/usr/bin/python3 -m studio.app
```

Open <http://127.0.0.1:8501>.

For another Python environment, install the small UI requirement first:

```bash
python -m pip install -r requirements-studio.txt
python -m studio.app
```

Optional settings:

```bash
IMAGE2CAD_STUDIO_HOST=0.0.0.0 IMAGE2CAD_STUDIO_PORT=8501 python -m studio.app
```

Only bind to `0.0.0.0` on a trusted network. The current service has no authentication because it is intended for local research use.

## Backend routes

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Dataset availability and read-only status |
| `GET /api/summary` | Dataset and phase-level metrics |
| `GET /api/objects?split=test` | Object index with optional split filter |
| `GET /api/objects/<object_id>` | Five-view metadata and phase evidence |
| `GET /api/objects/<object_id>/assets/<kind>` | Whitelisted image or 3D artifact |
| `GET /api/objects/<object_id>/report` | Downloadable evidence JSON |

Asset paths are resolved against the repository root and only named artifact kinds are accepted. The service does not expose arbitrary filesystem paths and does not write to the dataset.

## Validate

The service layer has no third-party dependency:

```bash
python -m unittest tests.test_dataset_studio -v
```

When Flask is installed, the same test module also checks the live API contract using Flask's in-process test client.
