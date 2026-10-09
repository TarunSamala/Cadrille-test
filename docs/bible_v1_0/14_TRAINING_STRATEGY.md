# Data & Training Strategy

## Principle

Do not train a giant end-to-end “jewellery brain” until the project possesses ground truth for the targets it expects the model to learn.

Training is justified only when:
1. the target variable is defined;
2. ground truth or a defensible self-supervised objective exists;
3. leakage is controlled;
4. the trained model beats a simpler baseline on a held-out physical set.

## T0 — Ground-truth creation

Immediate work:
- human foreground/component masks for Ring01;
- one or more physical dimensions;
- stable component identities;
- camera/capture metadata where available;
- explicit uncertainty for hidden regions.

No new architecture model should be allowed to compensate for missing truth.

## T1 — Targeted perception models

Train/fine-tune only narrow tasks:
- whole-jewellery segmentation;
- stone proposal/detection;
- prong/support proposal;
- negative-space proposal;
- view classification;
- reflection/highlight likelihood;
- detail-region detection.

Use synthetic exact labels + human-reviewed real labels.

## T2 — Synthetic geometry supervision

Render exact jewellery CAD with:
- randomized cameras;
- HDR/environment lighting;
- roughness/metal variations;
- gemstone optical variations;
- backgrounds;
- occluders;
- blur/noise/compression.

Export perfect:
- masks;
- component IDs;
- depth;
- normals;
- metric coordinates;
- material IDs;
- visible/amodal regions;
- surface points;
- curvature computed from truth;
- camera matrices.

## T3 — Geometry-prior adaptation

Only after B2/B3 benchmarks exist, consider adaptation of:
- depth model;
- normal model;
- matching model;
- reflective reconstruction model.

The model is promoted only if it improves held-out 3D or downstream exact-CAD metrics, not merely image appearance.

## T4 — Learned CAD-program reconstruction

Research Cadrille/CAD-Recode/Img2CAD-like approaches only after a meaningful jewellery CAD corpus exists.

Potential task:
```text
reviewed component graph + geometry evidence
→ parametric jewellery program / CadQuery code
```

This should initially generate **candidate programs**, followed by deterministic kernel execution and strict validation.

## T5 — Intrinsic-detail learning

Build only after controlled ground truth exists.

Possible inputs:
- multi-view RGB;
- controlled illumination/polarization;
- depth/normal priors;
- local semantic crop;
- base CAD surface.

Possible output:
- displacement field;
- local implicit surface;
- NURBS/subdivision patch control;
- uncertainty.

## Losses

Use losses only where physically meaningful.

### Segmentation
- BCE / focal loss;
- Dice loss;
- boundary loss.

### Geometry
- point/surface Chamfer;
- point-to-surface;
- normal angular loss;
- silhouette/reprojection;
- depth residual;
- camera reprojection residual.

### Detail
- local normal consistency;
- curvature consistency;
- multi-scale displacement/frequency loss;
- landmark distance;
- silhouette of high-relief regions.

### CAD
- execution validity;
- B-rep validity;
- primitive/feature parameter error;
- dependency correctness;
- dimensional error.

### Uncertainty
- calibration error / reliability diagram;
- selective risk: error when accepting only high-confidence regions.

## What must NOT be learned from the current pseudo labels

Do **not** claim to train:
- true jewellery semantics;
- metric depth;
- hidden backside ground truth;
- manufacturing validity;
- deity-face 3D fidelity;
- exact stone seat/prong engineering;
- material composition;
- physical weight.

The current pseudo-mask U-Net proves reproducibility of a pseudo target, not those properties.

## Curriculum

1. silhouettes and capture QA;
2. human-reviewed components;
3. synthetic exact component geometry;
4. real paired CAD;
5. cross-view identity;
6. exact CAD fitting;
7. reflective fine geometry;
8. manufacturing constraints.

## Evaluation split

- object-level split;
- design-family holdout;
- locked physical test set;
- report every principal view and component, not just means;
- synthetic test and real test are separate;
- record confidence intervals once enough physical objects exist.

## Fine-tuning policy

No model is fine-tuned “because we can.” A fine-tune requires:
- baseline result;
- hypothesis;
- target dataset;
- frozen test set;
- metric;
- minimum meaningful improvement;
- license compatibility;
- rollback checkpoint.
