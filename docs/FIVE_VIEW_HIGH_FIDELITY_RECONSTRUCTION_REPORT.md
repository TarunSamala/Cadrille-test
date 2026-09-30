# High-Fidelity Five-View Jewellery Reconstruction

## Feasibility, open-source model stack, implementation status and research roadmap

**Report date:** 28 September 2026  
**Project checkpoint reviewed:** Ring01 Phase 3.3.2  
**Input scenario:** one to five reference images, with special attention to front, back, side, top and angled views  
**Target output:** visually faithful, component-aware and editable 3D/CAD with explicit uncertainty

![Current project phase workflow](images/image2cad-phase-flowchart-v1.png)

## Executive decision

The project can build a strong five-view reconstruction system with open-source computer vision, depth, correspondence, inverse-rendering and CAD tools. The correct target is **near-exact visible-view agreement with editable structure**, followed by metric and manufacturing validation when physical evidence is available.

A mathematically perfect replica cannot be recovered or verified from five ordinary photographs alone. The images do not uniquely determine hidden surfaces, true thickness, physical scale, material reflectance or internal construction. Polished metal adds view-dependent reflections; gemstones add refraction and internal reflection; shadows and highlights can look like geometric edges. Several different 3D objects can therefore explain the same five images.

This does not make the project impractical. It changes the engineering strategy:

1. preserve the original image evidence;
2. classify rather than blindly trace edges;
3. estimate cameras, depth and normals with multiple independent methods;
4. fuse only evidence that agrees across views;
5. represent regular jewellery as exact parametric CAD and irregular detail as constrained free-form surfaces;
6. re-render every candidate into all source cameras;
7. expose uncertainty instead of inventing unsupported detail;
8. require physical scale or scan evidence before claiming manufacturing accuracy.

The existing repository already implements the evidence, segmentation, visual-hull, exact-solid and validation foundations needed for this direction. The next highest-value work is not another general image-to-3D generator. It is a calibrated camera/depth benchmark, human-reviewed component truth, edge taxonomy, uncertainty-aware fusion and hybrid CAD/free-form reconstruction.

## 1. What “perfect texture and edge replication” must mean

An image contains different kinds of boundaries. Treating all of them as geometry creates spikes, false grooves and melted surfaces.

| Image signal | Meaning | Correct treatment |
| --- | --- | --- |
| Outer silhouette | Object-to-background boundary | Strong geometric constraint in that camera view |
| Occlusion boundary | One component crosses another | Geometry and depth-order constraint |
| Crease or ridge | Real surface direction change | Candidate curve, normal or relief constraint |
| Engraved/embossed boundary | Fine surface geometry | Multi-view relief or displacement constraint |
| Material boundary | Gold, enamel, stone or paint change | Texture/material mask unless depth evidence agrees |
| Specular highlight | Reflection of a light source | Lighting/BRDF evidence; never geometry by itself |
| Cast or contact shadow | Lighting and spatial relation | Weak depth cue; exclude from the object silhouette |
| Gemstone facet line | Geometry mixed with reflection/refraction | Stone-cut model plus multi-view facet evidence |

The target should therefore be split into three deliverables:

- **Base geometry:** watertight shank, body, settings, galleries, links and cavities.
- **Microgeometry:** engraving, relief, faces, motifs, milgrain, ridges and controlled displacement.
- **Appearance:** base colour, metalness, roughness, normal/displacement maps and view-dependent material behaviour.

A colour texture alone cannot reproduce polished gold. A mesh alone cannot reproduce enamel and patina. The final system needs physically based materials and geometry, with the source images used to distinguish them.

## 2. Is five-view reconstruction achievable?

### 2.1 What five good views can constrain

Five views can be useful when they show the **same physical object**, retain full resolution, overlap substantially and use known or recoverable cameras. They can constrain:

- principal silhouettes;
- visible component count and placement;
- broad depth ordering;
- front/back/side proportions;
- repeated symmetry where it is genuinely present;
- stone and prong locations;
- visible negative spaces;
- medium-scale relief seen in more than one view;
- a plausible component-aware CAD model.

### 2.2 What five ordinary views cannot prove

- hidden surfaces that appear in no image;
- absolute millimetres without at least one known measurement;
- wall thickness and internal cavities that are not visible;
- the true shape under a strong reflection or shadow;
- exact gemstone pavilion, seat and clearance when obscured by metal;
- the physically correct BRDF, illumination and colour calibration;
- one-to-one correspondence when independently generated/reference views contain inconsistent details;
- manufacturing tolerances.

COLMAP’s own capture guidance expects overlapping images, similar illumination, sufficient texture and recommends that each object point be seen in at least three images; it also warns against specularities. That is directly relevant to jewellery and explains why five orthogonal catalogue renders are harder than a dense turntable capture: [COLMAP capture guidance](https://colmap.github.io/tutorial).

### 2.3 Practical evidence rating

| Target | Five ordinary images | Five calibrated studio images | Dense calibrated capture or scan |
| --- | --- | --- | --- |
| Visible silhouette | Strong | Very strong | Very strong |
| Component layout | Moderate to strong | Strong | Very strong |
| Camera pose | Weak to moderate | Strong | Very strong |
| Broad visible depth | Moderate | Strong | Very strong |
| Fine relief | Weak | Moderate | Strong with macro views |
| Hidden/backside geometry | Weak or absent | Weak if still hidden | Strong if covered |
| Absolute dimensions | Not recoverable | Recoverable with known scale | Recoverable |
| Metal/enamel appearance | View-specific approximation | Good with controlled lighting | Strong with material capture |
| Gemstone interior | Unreliable | Still difficult | Requires specialised capture/model |
| Manufacturing accuracy | Not defensible | Partial after CAD checks | Defensible after scan/CAD inspection |

**Decision:** five views are sufficient for the next research stage, but they are not a universal evidence ceiling. The pipeline should accept five views and report coverage gaps; the capture protocol should request additional macro, underside and oblique views when confidence is low.

## 3. Recommended open-source depth and geometry stack

No single model should be treated as ground truth. The strongest design is an ensemble in which classical geometry, learned multi-view geometry, monocular depth and surface normals cross-check one another.

### 3.1 Priority models for the first benchmark

| Model or algorithm | Role in this project | Why it is useful | Limitation or caution | Priority |
| --- | --- | --- | --- | --- |
| [COLMAP](https://github.com/colmap/colmap) | Camera intrinsics/extrinsics, sparse SfM, classical MVS baseline | Established, inspectable and reproducible; supports SIFT, learned features and LightGlue paths | Shiny, texture-poor jewellery and only five low-overlap views can fail | P0 |
| [VGGT](https://github.com/facebookresearch/vggt) | Joint camera, depth, point-map and track proposal | Designed for one, few or many images and supplies several geometric outputs together | Research licence; benchmark on jewellery before depending on it | P0 remote |
| [Depth Anything 3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Spatially consistent multi-view depth and pose proposal | Accepts arbitrary views with or without known poses and exports depth/camera/3D forms | Newer stack; author benchmarks are not project validation; verify every checkpoint licence | P0 remote |
| [MASt3R](https://github.com/naver/mast3r) / [DUSt3R](https://github.com/naver/dust3r) | Dense cross-view matches and point maps when feature matching is weak | Useful fallback for wide viewpoint changes and weak local texture | DUSt3R code is non-commercial CC BY-NC-SA; MASt3R checkpoint terms also require review | P0 research |
| [Depth Pro](https://github.com/apple-aiml-research/ml-depth-pro) | Sharp monocular metric-depth and focal-length hypothesis | Explicitly targets sharp high-frequency depth boundaries and predicts focal length | Single-view depth remains a prior, not multi-view truth | P1 |
| [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) | Lightweight relative-depth prior | Small model is practical locally and useful for ranking near/far structure | Relative depth must be aligned across views and to known scale | P1 local |
| [DSINE](https://github.com/baegwangbin/DSINE) | Per-pixel surface-normal proposal | Crisp, piecewise-smooth normal estimates can protect relief and curved metal | Normals inferred from one image may follow lighting errors | P1 |
| [OpenMVS](https://github.com/cdcseacave/openMVS) | Dense depth fusion, meshing, refinement and texture mapping | Provides a classical end-to-end dense reconstruction baseline after camera recovery | Needs reliable calibrated views and careful licence review for distribution | P1 |

Depth Anything 3 states that it predicts spatially consistent geometry from arbitrary visual inputs with or without known camera poses. Its published claims make it worth benchmarking, but those claims must be verified on the project’s jewellery and sculptural assets rather than accepted as a guarantee: [DA3 official repository](https://github.com/ByteDance-Seed/Depth-Anything-3). VGGT similarly predicts cameras, depth, point maps and tracks from few or many views and is a strong independent branch for the ensemble: [VGGT CVPR 2025 paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_VGGT_Visual_Geometry_Grounded_Transformer_CVPR_2025_paper.pdf).

### 3.2 Reflective-object and inverse-rendering research

Jewellery is not a normal photogrammetry subject. The system needs a branch that separates geometry from reflections and materials.

| Project | Proposed use | Status |
| --- | --- | --- |
| [NeRO](https://github.com/liuyuan-pal/NeRO) | Joint neural geometry and BRDF reconstruction for reflective objects | High-value research benchmark; expects a richer multi-view capture than five sparse catalogue views |
| [nvdiffrec](https://github.com/NVlabs/nvdiffrec) | Joint topology, material and lighting optimisation | Useful for learning whether a mismatch is geometry or appearance; remote GPU recommended |
| [nvdiffrast](https://nvlabs.github.io/nvdiffrast/) | Low-level differentiable rasterisation | Strong optimisation backend for camera, mesh and texture losses |
| [PyTorch3D](https://github.com/facebookresearch/pytorch3d) | Differentiable render-and-compare, mesh losses and batched cameras | Good integration target for the existing validation loop |
| [Nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | Modular NeRF/3DGS experiments and view synthesis | Research evidence, not automatically editable CAD |
| [Neuralangelo](https://github.com/NVlabs/neuralangelo) | Detailed neural surface baseline from dense image/video capture | Better suited to many frames and remote compute than five sparse views |

NeRO is especially relevant because it explicitly targets reflective-object geometry and BRDF reconstruction from multi-view images: [NeRO official implementation](https://github.com/liuyuan-pal/NeRO). nvdiffrec jointly optimises topology, materials and lighting from multi-view observations: [nvdiffrec official implementation](https://github.com/NVlabs/nvdiffrec).

These methods should not replace the CAD branch. They should supply surface and material evidence that is converted into editable parts or bounded relief patches.

### 3.3 Segmentation, instances and edge evidence

| Model or algorithm | Use |
| --- | --- |
| OpenCV Canny, contours, morphology and line/curve fitting | Deterministic silhouette, holes, symmetry, ridge candidates and pixel measurements |
| [SAM 2](https://github.com/facebookresearch/sam2) | Promptable jewellery/component masks and cross-frame propagation when a turntable video is available |
| [HQ-SAM / HQ-SAM 2](https://github.com/SysCV/sam-hq) | Boundary-refinement benchmark for prongs, stones, chains and engraved regions |
| [Grounded SAM](https://github.com/IDEA-Research/Grounded-Segment-Anything) | Text-guided proposals for stones, prongs, settings, links and motifs |
| [TEED](https://github.com/xavysp/TEED) | Lightweight learned edge proposal alongside deterministic Canny |
| Jewellery-specific instance model | Final per-stone/per-prong IDs after human-reviewed labels exist |

SAM-family masks are proposals, not measurements. The output must preserve uncertainty bands and allow reviewer correction. For a ten-stone item, the evidence graph must contain ten stable stone instances, not one merged “stone” mask.

### 3.4 CAD and geometry processing

- [CadQuery](https://github.com/CadQuery/cadquery) with OpenCascade remains the exact-solid and STEP path for shanks, bezels, prongs, galleries, seats, cavities and assemblies.
- Blender can handle remeshing, sculptural patches and Boolean experiments; its Boolean modifier supports union, intersection and difference operations: [Blender Boolean manual](https://docs.blender.org/manual/en/5.1/modeling/modifiers/generate/booleans.html).
- Trimesh remains useful for mesh inspection, connected components, watertightness and export checks.
- A robust mesh Boolean backend such as Manifold can be evaluated for cavity and seat generation before conversion/validation.
- UV unwrapping and view-weighted texture baking should create base-colour, roughness, metalness, normal and displacement maps separately.

CadQuery is appropriate because it is a scriptable parametric CAD system based on OCCT and supports STEP, STL, 3MF and other outputs: [CadQuery official repository](https://github.com/CadQuery/cadquery).

## 4. Proposed depth-estimation architecture

“Almost perfect depth” should be approached as an evidence-fusion problem, not a model-selection problem.

### Stage A — camera hypotheses

Run three independent branches:

1. COLMAP with SIFT, then ALIKED/LightGlue if available;
2. VGGT camera and track prediction;
3. DA3 or MASt3R camera/point-map prediction.

Align all successful camera sets into one coordinate frame. Reject solutions with incorrect view ordering, mirrored geometry, implausible focal length or poor source-view reprojection.

### Stage B — depth and normal hypotheses

For every view, produce:

- multi-view depth from DA3/VGGT or classical MVS;
- monocular depth from Depth Pro and Depth Anything V2;
- normals from DSINE;
- silhouette and component masks;
- per-pixel confidence and an invalid/reflection mask.

Monocular estimates may fill weak areas, but they must not override cross-view geometry where multiple cameras agree.

### Stage C — uncertainty-aware fusion

Convert each valid pixel into a camera ray and fuse only mutually consistent measurements. Each sample receives a weight based on:

- number of supporting views;
- reprojection error;
- edge type;
- depth-model agreement;
- normal agreement;
- segmentation confidence;
- reflection/shadow probability;
- distance from an occlusion boundary.

The result should be a signed-distance/occupancy field plus an uncertainty volume, not only a point cloud. Hidden regions remain explicitly uncertain.

### Stage D — hybrid reconstruction

- Fit analytic or parametric components where jewellery structure is known.
- Fit free-form subdivision/NURBS or dense mesh patches for faces, deities, organic motifs and ornament relief.
- Store detail as real displacement when it affects silhouette or manufacture; otherwise retain it as normal/appearance detail.
- Generate gemstone seats and cavities directly from each named stone’s geometry and pose.

### Stage E — differentiable render-and-compare

Render geometry, depth, normals, component IDs and physically based appearance from the source cameras. Optimise in a coarse-to-fine order:

1. camera and scale;
2. silhouette and component placement;
3. depth and normals;
4. visible creases and relief;
5. materials and texture.

Geometry must be frozen or strongly regularised while optimising appearance so that a highlight cannot carve a groove into the CAD model.

## 5. Texture and fine-detail replication plan

### 5.1 Texture is a multi-map result

The texture deliverable should contain:

- base colour/albedo;
- metalness or material class;
- roughness;
- normal map;
- displacement/height where supported;
- optional ambient-occlusion preview map;
- source-view visibility and confidence atlas.

Images should be exposure- and white-balance-normalised before baking. For each texel, choose source pixels using camera angle, focus, occlusion, highlight probability and cross-view consistency. Blend only compatible observations.

### 5.2 Metal and gemstone rules

- Polished-metal highlights are view-dependent and should be fitted as illumination/BRDF, not copied permanently into albedo.
- Enamel, patina and painted regions belong in material masks and base colour.
- Repeated stamped or engraved motifs should use geometry when they affect silhouette/shadows or when manufacturing requires them.
- Gemstones should use a parametric cut with material shaders; photographed sparkle should not be baked as fixed white spots.
- If a facet is visible in only one view, record it as low confidence until the known cut topology or another view supports it.

### 5.3 Controlled capture upgrade

Five reference images remain supported, but the preferred research capture should add:

- fixed focal length and locked focus/exposure/white balance;
- a scale marker or one measured object dimension;
- same object and unchanged articulation in every view;
- neutral matte background;
- 12–36 overlapping turntable views for geometry;
- macro detail views for engraving/faces;
- cross-polarised diffuse-light pass to reduce specular glare;
- separate reflective-light pass for material estimation;
- underside and cavity coverage;
- optional turntable angle metadata.

This capture change is likely to improve accuracy more reliably than replacing one large foundation model with another.

## 6. What has already been implemented

The following results are repository evidence, not projections.

### 6.1 Input and evidence handling

- Upload audit accepts single-view and five-view inputs.
- Source files, hashes, view labels, quality warnings and transforms are preserved.
- Phase 1 extracts foreground, contours, holes, edges, symmetry and pixel-space measurements.
- Phase 2 combines SAM 2.1 Tiny, OpenCV and GrabCut for silhouette/component proposals.
- Phase 2.2 applies topology and cross-view consistency rules.
- Phase 2.3 stores an evidence graph, instance hypotheses and review decisions.

### 6.2 Dataset processing

The current dataset contains 24 objects and five views per object, for 120 processed images. The small U-Net experiment reports:

| Dataset result | Recorded value |
| --- | ---: |
| Validation pseudo-mask IoU | 0.978183 |
| Held-out pseudo-mask IoU | 0.977586 |
| Held-out Dice | 0.988646 |
| Held-out boundary F1 at 2 px | 0.999753 |

These numbers measure reproduction of machine-generated pseudo-masks. They do **not** prove human-quality component segmentation, depth accuracy or 3D accuracy.

The dataset visual-hull experiment created 24 watertight coarse meshes at 128-voxel resolution:

| Split | Reprojection IoU |
| --- | ---: |
| Train | 0.948832 |
| Validation | 0.946122 |
| Test | 0.961753 |

These are non-metric visual-hull reprojection scores. They validate the batch workflow, not hidden shape or manufacturing geometry.

![Dataset phase comparison](../dataset/phase_runs/v1/comparisons/dataset_processing_comparison.png)

### 6.3 Ring01 exact reconstruction checkpoint

Ring01 Phase 3.3.1 produced one valid metal B-rep, one separate gemstone, a two-rail gallery, shank/shoulders and four named curved cubic claws. Phase 3.3.2 corrected the inspection preview so all four prongs are visible without changing geometry.

| Metric | Recorded value |
| --- | ---: |
| Mean silhouette IoU | 0.819726 |
| Mean detail-region IoU | 0.787388 |
| Mean external-boundary F1 at 2 px | 0.795969 |
| Front IoU | 0.854535 |
| Side IoU | 0.813976 |
| Top IoU | 0.871267 |
| Angled IoU | 0.770454 |
| Back IoU | 0.788398 |

The exact checkpoint is structurally useful, but it has not reached the 0.90 research target, the complete Phase 3 exit gate, or manufacturing validation. Human-reviewed masks and metric scale remain missing.

![Ring01 Phase 3.3.2 inspection preview](../data/ring01_phase3_3_2/ring01_phase3_3_2_visibility_preview.png)

### 6.4 External image-to-3D benchmark findings

The benchmark validates exported geometry using independent renders before metrics.

- **TripoSR:** produced a recognisable elephant, but geometry and texture were too coarse for the ornamental target.
- **Stable Fast 3D:** hosted runs failed before a usable mesh was produced.
- **InstantMesh:** produced a coherent recognisable elephant and passed the human preview gate as research evidence; the mesh was non-watertight and split into 18 connected bodies, so it was not a CAD or manufacturing result.
- **Hunyuan3D 2.1:** exported geometry was catastrophically torn/fused and was rejected at the preview gate.
- **TRELLIS:** the official hosted environment failed at configuration level.
- **TRELLIS.2:** reached a running service, but the free hosted quota blocked inference; no result and no paid transaction were accepted.

![Independent InstantMesh export preview](../runs/benchmarks/2d_to_3d/elephant/instantmesh/run-002/previews/instantmesh_elephant_actual_glb_preview.png)

The lesson is that generative models are useful candidate generators, not geometric authorities. A visually attractive website preview is not sufficient; the actual OBJ/GLB must be independently rendered, inspected and validated.

## 7. Gap analysis

| Required capability | Current position | Main gap |
| --- | --- | --- |
| Whole-object silhouette | Working | Human-reviewed truth at scale |
| Individual stone/prong segmentation | Proposed and partly represented | Jewellery instance dataset and stable cross-view IDs |
| Camera recovery | Basic assumptions/experimental paths | Calibrated benchmark across COLMAP, VGGT, DA3 and MASt3R |
| Depth estimation | Visual hull/coarse semantics | Multi-model depth/normal ensemble with uncertainty |
| Exact parametric body | Ring01 prototype | Universal component grammar across jewellery classes |
| Stone cavity/seat update | Design requirement | Dependency graph and robust Boolean/clearance engine |
| Faces/idols/relief | Evidence extraction planned | Free-form surface branch and macro-detail capture |
| Texture/material | Basic external-model textures | View-weighted PBR baking and reflective-object inverse rendering |
| Metric validation | Not available from current dataset | Known dimensions, camera calibration and scan/CAD ground truth |
| Manufacturing claim | Not validated | Rules, tolerances and independent CAD/scan inspection |

## 8. Implementation roadmap

### Milestone A — freeze ground truth and capture protocol

**Deliverables**

- Human-reviewed silhouettes and component masks for Ring01, one multi-stone item and one sculptural/face item.
- Stable IDs for every stone, prong, cavity and visible motif.
- Camera calibration board procedure and one known metric dimension.
- Dense turntable capture for at least one benchmark object, while retaining the five-view subset for comparison.

**Exit gate**

- Two reviewers agree on instance count and masks, or disagreements are recorded.
- All reference views are the same physical object.
- Ground-truth source is labelled `human_reviewed`, `scan`, `CAD` or `measured`; pseudo-truth is never mixed with it.

### Milestone B — edge taxonomy and evidence confidence

**Deliverables**

- Canny + TEED proposal comparison.
- Boundary classes: silhouette, occlusion, crease/relief, material, highlight and shadow.
- Reflection/shadow confidence map.
- Cross-view edge tracks and uncertainty bands.

**Exit gate**

- Human-reviewed external-boundary F1 and per-class precision/recall reported.
- Highlight-only boundaries do not modify geometry in regression tests.

### Milestone C — camera, depth and normal benchmark

**Deliverables**

- Isolated adapters for COLMAP, VGGT, DA3, MASt3R/DUSt3R, Depth Pro, Depth Anything V2 and DSINE.
- Common NPZ/JSON contract for camera, depth, normals, confidence, runtime and memory.
- Five-view and dense-view runs on the same benchmark objects.
- Licence manifest for code and weights.

**Exit gate**

- Camera reprojection error, depth error against scan/CAD, normal angular error and failure rate are reported separately.
- No model is selected using its own preview or confidence alone.
- The chosen ensemble beats every single branch on the held-out objects or is rejected.

### Milestone D — uncertainty-aware fusion and hybrid geometry

**Deliverables**

- Calibrated TSDF/SDF or occupancy fusion.
- Uncertainty volume and visible/hidden surface labelling.
- Parametric fitting for regular parts and free-form patches for sculptural detail.
- Source-view correspondence retained for every fitted region.

**Exit gate**

- Mean and worst-view silhouette, boundary, depth and normal metrics improve without topology regression.
- Unsupported hidden geometry remains flagged rather than scored as correct.
- A face/idol relief is recognisable from geometry without relying on colour texture alone.

### Milestone E — component-aware CAD and dependent cavities

**Deliverables**

- Universal component graph for stones, settings, supports, cavities, metal bodies, links and decorations.
- Individual stone resize/removal/replacement.
- Automatic seat/cavity regeneration from the edited stone geometry and manufacturing clearance.
- CadQuery/OpenCascade exact solids with Blender/Manifold research fallback for difficult Booleans.

**Exit gate**

- Ten-stone test preserves ten stable IDs.
- Editing one stone changes only its dependent seat/support region.
- Exact-solid validity, collision, wall-thickness and export checks pass.

### Milestone F — texture, BRDF and microdetail

**Deliverables**

- Exposure-normalised, confidence-weighted texture atlas.
- Albedo, material, roughness, normal and displacement outputs.
- NeRO/nvdiffrec experiment on controlled reflective captures.
- Source-camera photometric comparison under fitted lighting and a neutral relighting test.

**Exit gate**

- Texture seams, baked highlights and view inconsistency are measured.
- Geometry-only and appearance-only ablations are included.
- A different light can be rendered without the original highlight being fixed in the albedo.

### Milestone G — manufacturing validation

**Deliverables**

- Known metric scale and units.
- Minimum wall, clearance, seat, prong and casting rules supplied by the manufacturing partner.
- STEP inspection, mesh manifold checks and scan-to-CAD deviation map.
- Final decision report with accepted, inferred and unknown dimensions.

**Exit gate**

- No `manufacturing_ready` result without physical scale and independent evidence.
- Scan/CAD deviations are reported in millimetres by component and surface region.

## 9. Validation matrix

| Layer | Metric | Why it matters |
| --- | --- | --- |
| Input | Blur, clipping, coverage, overlap, calibration validity | Bad evidence cannot be repaired reliably downstream |
| Segmentation | Per-instance IoU, Dice, boundary F1, count accuracy | Whole-object IoU can hide missing stones or prongs |
| Camera | Reprojection error, focal error, pose consistency | Incorrect cameras make all later comparisons misleading |
| Depth | AbsRel/RMSE against scan where available, cross-view consistency | Measures actual surface distance rather than appearance alone |
| Normals | Mean/median angular error and edge-aware error | Protects curves, facets and shallow relief |
| Geometry | Chamfer/Hausdorff and signed scan-to-CAD deviation | Finds local shape error hidden by silhouette scores |
| Visible views | Per-view silhouette IoU and boundary F1 | Prevents a strong front view hiding a failed side/back view |
| Components | Count, stable IDs, pose/dimension errors | Required for editability |
| Topology | Watertightness, manifoldness, connected bodies, intersections | Required for reliable geometry processing |
| CAD | Valid B-rep, editable dependency graph, successful STEP round-trip | Distinguishes engineering CAD from a display mesh |
| Appearance | PSNR/SSIM/LPIPS plus seam and highlight tests | Measures texture without confusing it with geometry |
| Manufacturing | Scale, wall thickness, clearance, collision, scan deviation | Required before production claims |

Every average must be accompanied by the lowest-performing view and lowest-performing component. A missing prong cannot be hidden by a large, accurate shank.

## 10. Compute plan for the current laptop

The workstation contains an RTX 3050 Mobile-class NVIDIA GPU with 4 GB VRAM and 15 GiB system memory. At this report’s system probe, Linux still detected the GPU and loaded NVIDIA kernel modules, but `nvidia-smi` could not communicate with the driver. The root filesystem had 5.6 GiB free and `/home` had 127 GiB free. GPU experiments should not start until driver communication is restored and a fresh VRAM probe succeeds.

### Practical local workload

- OpenCV, GrabCut, audit generation and deterministic metrics;
- SAM 2.1 Tiny at controlled resolution;
- the small U-Net and current visual hull;
- Depth Anything V2 Small;
- limited Depth Pro/DSINE inference one image at a time, after memory profiling;
- COLMAP sparse reconstruction and small dense experiments;
- CadQuery/OpenCascade modelling and most topology checks;
- independent preview rendering.

### Remote 24 GB or larger GPU workload

- VGGT and larger DA3 variants;
- MASt3R/DUSt3R high-resolution multi-view runs;
- NeRO, nvdiffrec and Neuralangelo training/optimisation;
- high-resolution differentiable rendering;
- large generative image-to-3D benchmarks.

All remote work should use pinned containers, immutable input hashes and downloaded outputs. Free hosted demos are useful for smoke tests but are not a reproducible training or validation platform.

## 11. Experiment design and backtracking rules

Each model or algorithm receives an isolated adapter and writes a versioned run:

```text
runs/reconstruction/<asset>/<method>/<run_id>/
├── input_manifest.json
├── environment.json
├── cameras.json
├── depth/
├── normals/
├── masks/
├── geometry/
├── textures/
├── renders/
├── metrics.json
├── preview_review.json
└── decision.md
```

The decision is one of `accept`, `reject`, `backtrack` or `research_only`.

A change is accepted only when:

- the intended metric improves on held-out, human-reviewed evidence;
- the lowest view and component do not regress beyond a declared tolerance;
- topology and exact-solid checks remain valid;
- runtime and memory remain practical for the selected deployment tier;
- the licence is compatible with the intended use;
- the actual exported geometry passes independent preview inspection.

Rejected runs remain in the experiment registry with their failure reason. Backtracking is therefore a controlled research action, not loss of progress.

## 12. Recommended execution order

1. Restore and verify NVIDIA driver communication; keep model caches under `/home`.
2. Create human-reviewed Ring01 and multi-stone masks with stable component IDs.
3. Capture one calibrated, measured jewellery object with both five-view and dense-view subsets.
4. Add the common camera/depth/normal adapter contract.
5. Benchmark COLMAP first as the inspectable geometric baseline.
6. Benchmark Depth Anything V2 Small and DSINE locally.
7. Run DA3, VGGT and MASt3R remotely on identical inputs.
8. Build the uncertainty-weighted fusion and compare five views against dense views.
9. Fit hybrid exact/free-form geometry and run the existing render-and-compare loop.
10. Implement per-stone dependency and cavity updates.
11. Add reflective inverse-rendering and PBR texture baking.
12. Validate against scan/CAD ground truth before setting manufacturing thresholds.

## 13. Final assessment

Open-source models can provide nearly every technical building block: segmentation, camera estimation, depth, normals, correspondence, reflective inverse rendering, differentiable optimisation, meshing and exact CAD. They do not remove the information limits of the input photographs.

For five ordinary reference images, the defensible output is:

- a high-fidelity visible replica where evidence is strong;
- editable jewellery structure for recognised components;
- plausible but explicitly uncertain hidden geometry;
- non-metric output unless a dimension is supplied;
- no manufacturing claim without independent physical validation.

For five calibrated high-resolution images plus one known dimension, the system can produce a substantially stronger metric and structural result for simple and medium-complexity jewellery. For dense relief, deity faces, complex ornaments, chains, transparent stones and hidden construction, the pipeline should automatically request additional macro/oblique views or scan evidence.

The path to near-perfection is therefore not “find one perfect image-to-3D model.” It is controlled evidence, specialised models, confidence-aware fusion, jewellery constraints, hybrid CAD/free-form geometry, render-and-compare refinement and honest validation.

## 14. Source register

Primary project and research sources used for this report:

- [COLMAP](https://github.com/colmap/colmap) and [capture guidance](https://colmap.github.io/tutorial)
- [OpenMVS](https://github.com/cdcseacave/openMVS)
- [VGGT](https://github.com/facebookresearch/vggt) and [CVPR 2025 paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_VGGT_Visual_Geometry_Grounded_Transformer_CVPR_2025_paper.pdf)
- [Depth Anything 3](https://github.com/ByteDance-Seed/Depth-Anything-3)
- [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2)
- [Depth Pro](https://github.com/apple-aiml-research/ml-depth-pro)
- [DUSt3R](https://github.com/naver/dust3r) and [MASt3R](https://github.com/naver/mast3r)
- [DSINE](https://github.com/baegwangbin/DSINE)
- [SAM 2](https://github.com/facebookresearch/sam2), [HQ-SAM](https://github.com/SysCV/sam-hq) and [Grounded SAM](https://github.com/IDEA-Research/Grounded-Segment-Anything)
- [TEED](https://github.com/xavysp/TEED)
- [NeRO](https://github.com/liuyuan-pal/NeRO)
- [nvdiffrec](https://github.com/NVlabs/nvdiffrec), [nvdiffrast](https://nvlabs.github.io/nvdiffrast/) and [PyTorch3D](https://github.com/facebookresearch/pytorch3d)
- [Nerfstudio](https://github.com/nerfstudio-project/nerfstudio) and [Neuralangelo](https://github.com/NVlabs/neuralangelo)
- [CadQuery](https://github.com/CadQuery/cadquery) and [Blender Boolean documentation](https://docs.blender.org/manual/en/5.1/modeling/modifiers/generate/booleans.html)

Before a model enters a commercial workflow, review the code licence, checkpoint licence, training-data restrictions and redistribution terms separately. “Open source” or public code does not automatically mean unrestricted commercial use.
