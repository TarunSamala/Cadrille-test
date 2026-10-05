# Ring01 complete Phase 1 feature extraction

## Objective

Phase 1 now retains exact pixels, colour spaces, differential image features,
semantic-mask proposals, relative-depth evidence and uncertainty for every
Ring01 view. It separates three different claims:

1. exact source-pixel preservation;
2. machine-derived feature and relative-depth proposals;
3. unavailable metric geometry and human semantic truth.

## View semantics

The five names are treated as semantic labels, not camera calibration:

| Label | Observed image role | Current geometric status |
| --- | --- | --- |
| Front | Gemstone-face view with horizontal shank shoulders | Pose unknown |
| Side | Ring-profile view showing hoop, basket and head elevation | Pose unknown |
| Top | A second near gemstone-face view, not a calibrated top camera | Pose unknown |
| Angled | Oblique view showing face, head elevation and hoop | Pose unknown |
| Back | Opposite-labelled profile view of hoop and basket | Pose unknown |

Front/top and side/back are visually similar pairs. Therefore the input has
less than five independent geometric baselines, even though it contains five
files.

## Pixel-level feature bundle

Each compressed NPZ bundle retains 23 aligned arrays:

- exact RGB uint8 pixels;
- linear-light RGB float32;
- grayscale, Lab and HSV matrices;
- Sobel X/Y, gradient magnitude and gradient angle;
- Laplacian and local contrast;
- Canny edges;
- jewellery, metal, shank, stone, setting, prong and negative-space masks;
- raw and symmetry-regularized relative depth;
- normalized 16-bit depth and uncertainty.

The stored RGB matrix reconstructs every source view pixel-for-pixel. This is
an honest reversible record, but it is not evidence that semantic features
alone can reconstruct the source. Masks, edges, statistics and depth are
many-to-one transforms; exact inversion requires the source pixels or a
lossless residual.

## Depth Anything V2 repeated validation

Every view was evaluated three times. All raw matrices were byte-identical and
the maximum difference between repeated runs was zero. This establishes
determinism for the pinned hardware/software path, not depth correctness.

The front-view raw map contains the suspected vertical imbalance:

| Region | Raw top-minus-bottom mean | Symmetry-regularized |
| --- | ---: | ---: |
| Whole visible ring | -0.090743 | -0.060645 |
| Visible stone | -0.181748 | -0.124339 |

Left-minus-right stone imbalance is only `0.005462`. The vertical-flip
consistency error is `0.107243`, while horizontal-flip error is `0.039367`.
Together these measurements confirm a repeatable vertical model bias around
the gemstone rather than random execution noise.

Symmetry regularization reduces the absolute bias by roughly one third, but a
large residual remains. It is retained as a separate diagnostic hypothesis and
does not replace raw depth.

## Why millimetres and centimetres are blocked

Depth Anything V2 Small provides relative monocular depth. A colour or numeric
change in the map is not currently convertible to a physical distance. Metric
depth requires:

- at least one verified physical dimension;
- camera intrinsics or a calibrated capture protocol;
- cross-view camera poses and correspondences, or scan supervision.

One known ring diameter can set an overall reconstruction scale after camera
geometry exists. It cannot by itself correct local depth errors caused by
reflections, gemstone refraction, highlights or shadows.

## Evidence

- `data/ring01_ground_truth_v1/depth_validation_v1/report.json`
- `data/ring01_ground_truth_v1/depth_validation_v1/ring01_front_photo_with_depth.png`
- `data/ring01_ground_truth_v1/depth_validation_v1/ring01_front_depth_audit.png`
- `data/ring01_ground_truth_v1/depth_validation_v1/ring01_all_views_depth_validation.png`
- `data/ring01_ground_truth_v1/pixel_features_v1/report.json`
- `data/ring01_ground_truth_v1/pixel_features_v1/ring01_phase1_pixel_feature_audit.png`

The next geometric step is calibrated cross-view correspondence and depth
fusion. Until then, all depth remains non-metric machine evidence.
