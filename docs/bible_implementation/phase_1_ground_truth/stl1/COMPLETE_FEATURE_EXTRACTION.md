# STL-1 Complete Phase 1 Feature Extraction

## Scope

The complete Phase 1 extractor processed all 24 STL-1 objects and all five
views per object: front, top, isometric, left-side and right-side. These are
source-provided semantic names, not calibrated camera poses.

The view contract is:

| Label | Observed meaning | Geometric limitation |
| --- | --- | --- |
| Front | Ornament or setting face toward the camera | Camera pose unknown |
| Top | Elevation view showing hoop and head or underside | Not a calibrated overhead camera |
| ISO | Oblique view showing face, thickness and hoop | Camera pose unknown |
| LSV | Source-labelled left profile | No pixel correspondence to RSV |
| RSV | Source-labelled right profile | No pixel correspondence to LSV |

## Extracted evidence

Every normalized view has a compressed bundle containing 22 aligned arrays:

- lossless source and normalized RGB;
- linear RGB, grayscale, LAB and HSV matrices;
- Sobel X/Y, gradient magnitude and direction, Laplacian, local contrast,
  Canny and the prepared edge proposal;
- raw Depth Anything V2 depth, three-way flip-ensemble depth, normalized depth
  and transformation uncertainty;
- jewellery, background and silhouette-hole proposals.

The source RGB array reconstructs every decoded source pixel exactly. This is
not evidence that edges, masks or depth can be inverted into the original
image: those transforms are many-to-one, so exact reconstruction requires the
retained RGB matrix or an equivalent lossless residual.

STL-1 has no reviewed individual-stone, metal-component, prong, seat or cavity
labels. Phase 1 records those fields as unavailable instead of inventing them.

## Depth validation

Depth Anything V2 Small was executed three times for each of the 120 normalized
views. All three raw outputs were identical for every view. A horizontal-flip
and vertical-flip inference were aligned back to the original prediction. Their
maximum normalized disagreement is retained as transformation uncertainty.

The three-way flip ensemble is an alternate diagnostic proposal. It is not
treated as corrected depth because it did not consistently reduce vertical
imbalance:

| View | Raw mean absolute top/bottom delta | Flip-ensemble delta |
| --- | ---: | ---: |
| Front | 0.181452 | 0.186010 |
| Top | 0.189878 | 0.207719 |
| ISO | 0.145535 | 0.142966 |
| LSV | 0.073836 | 0.076916 |
| RSV | 0.086449 | 0.082667 |

Repeatability proves deterministic execution, not geometric correctness.
Cross-view metric validation remains blocked because STL-1 has no intrinsics,
extrinsics, physical scale, scan or human depth truth.

## Reproduction

The full local run uses the pinned local model cache and does not require an
online service:

```bash
docker run --rm --gpus all --user 1000:1000 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e HF_HOME=/workspace/hf_cache \
  -v /home/satvara/Github/Image2CAD:/workspace:ro \
  -v /home/satvara/Github/Image2CAD/dataset/phase_runs/v1/phase1_complete_features_v1:/workspace/dataset/phase_runs/v1/phase1_complete_features_v1:rw \
  -w /workspace image2cad-phase1-depth:local \
  python -m pipeline.extract_dataset_complete_phase1 \
  --repo-root /workspace --device cuda --repeats 3 --local-files-only
```

The complete local evidence occupies approximately 963 MB. The reproducible
raw NPZ bundle and source-roundtrip cache are intentionally excluded from
ordinary Git history. The extractor, SHA-256 report, review images and compact
depth evidence remain versioned.

## Result

- 24 objects and 120 views processed.
- 22 matrices retained per view.
- 360 repeated primary depth predictions plus two transformed validations per
  view.
- Exact decoded source-pixel round-trip for every image.
- All feature matrices finite.
- Peak GPU allocation: 219,342,336 bytes.
- Runtime: 328.945 seconds.
- Metric millimetres or centimetres: blocked.
- Component-level semantic ground truth: blocked.

The authoritative machine-readable record is
`dataset/phase_runs/v1/phase1_complete_features_v1/report.json`.
