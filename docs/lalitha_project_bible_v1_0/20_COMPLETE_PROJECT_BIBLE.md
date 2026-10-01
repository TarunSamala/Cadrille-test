# Lalitha / Image2CAD — Complete Project Bible
## BASELINE ARCHITECTURE V1.0

**Release date:** 2026-09-29  
**Owner context:** Live Metal / Lalitha  
**Baseline scope:** rings first  
**Authoritative engineering output:** STEP / exact B-rep  
**Status:** engineering/research baseline accepted with conditions  
**Manufacturing-accuracy claim:** not yet validated

---

# PART 1 — WHAT ARE WE BUILDING?

Lalitha is a jewellery reverse-engineering and CAD-assistance system.

The simplest useful example is a ring. A user supplies several photographs. The system should not merely create a 3D object that looks ring-like. It should determine, as defensibly as possible:

- where the shank is;
- where the head/setting is;
- how many stones exist;
- each stone's pose and dimensions when measurable;
- which prong belongs to which stone;
- where the seats and cavities are;
- which parts are repeated or symmetric;
- which decorative details are actual relief rather than color/reflection;
- which geometry was observed and which had to be inferred or designed;
- how the structure should be expressed as editable CAD.

The target result is closer to an engineering reconstruction than a visual asset.

## Appearance vs geometry vs CAD

### Appearance
What the camera sees: pixel color and intensity.

### Texture/material appearance
Color/albedo, metal/gemstone appearance, roughness, reflection and refraction cues.

### Geometry
The actual three-dimensional shape of a surface.

### Depth
Distance from a camera or reference frame to a surface point.

### Surface normal
The direction perpendicular to a local surface.

### Curvature
How rapidly the surface normal changes spatially.

### Semantic structure
What a piece of geometry means: stone, prong, shank, seat, cavity, relief, etc.

### CAD structure
How the object is represented as editable engineering entities, constraints, solids and feature relationships.

A visually convincing mesh can be wrong in all the ways a jeweller cares about. A beautiful render can hide:
- merged stones;
- missing seats;
- disconnected prongs;
- incorrect back construction;
- impossible wall thickness;
- invented hidden surfaces;
- invalid Boolean geometry.

Lalitha therefore makes a strict distinction between:
1. **visual reconstruction**;
2. **structural reconstruction**;
3. **manufacturing reconstruction**.

---

# PART 2 — WHY IS THIS PROBLEM DIFFICULT?

## 2.1 A photograph is a projection, not a measurement of shape

A camera collapses 3D geometry into 2D. Many different 3D shapes can produce similar images.

With a single uncalibrated image, absolute scale is not available. Even with several views, incorrect cameras can produce apparently good overlays.

## 2.2 Jewellery is highly reflective

Polished metals do not behave like matte clay. A bright stripe can move when the camera moves even though the geometry is unchanged. A dark region can be a reflected environment, not a cavity.

Gemstones add:
- refraction;
- internal reflection;
- transparency;
- dispersion;
- multiple interfaces.

This is why the current project failure in which reflection regions became geometry is scientifically important. It is not an implementation accident; it is a property of the inverse problem.

## 2.3 Small details matter disproportionately

For many generic objects, a small local error is visually tolerable. For deity faces, religious motifs, engravings or premium jewellery, millimetre/sub-millimetre form can determine whether the design is accepted.

The nose, eyelids, lips and crown cannot be treated as “texture noise” if they are physically sculpted.

## 2.4 Occlusion hides structure

A prong may disappear behind a stone in one view. A cavity may not be visible. The back of a decorative head may be missing entirely.

The system must not transform missing evidence into false certainty.

## 2.5 Manufacturing structure is not directly visible

A photograph cannot reliably tell us:
- the exact stone-seat construction;
- required clearance;
- casting allowance;
- polishing allowance;
- process-specific minimum wall;
- whether a hidden support exists;
- internal hollowing decisions.

Those can be inferred or designed, but they must be labelled accordingly.

---

# PART 3 — COMPLETE PROJECT HISTORY

## 3.1 Initial broad product concept

The project began as a broader AI jewellery design/manufacturing workspace: create or reconstruct designs, edit them, validate them and export for production.

This was strategically attractive but technically too broad. The project then focused on rings because rings provide:
- clear physical constraints;
- repeated known features;
- accessible CAD workflows;
- a reasonable first dataset;
- strong manufacturing relevance.

## 3.2 Shift from “generate 3D” to “reverse engineer jewellery”

Early exploration included modern image-to-3D models and learned CAD systems. This was useful for mapping the field, but the central product requirement became stricter:

> Preserve the original jewellery's component structure, culturally significant geometry and manufacturing relationships.

That immediately makes ordinary generative 3D insufficient as the final authority.

## 3.3 Benchmark-lab idea

The project correctly decided not to trust one 3D model. A benchmark framework was proposed so the same jewellery input could be given to multiple methods and audited.

That idea remains valid, but the benchmark is now governed by a stronger rule: model outputs are proposals/evidence, and performance is multi-dimensional.

## 3.4 Hybrid geometry + CAD architecture

The architecture then evolved toward:
- input normalization;
- jewellery-specific evidence/segmentation;
- multi-view geometry;
- structural inference;
- parametric/exact CAD;
- render-and-compare validation;
- manufacturing checks.

This is the direct ancestor of V1.

## 3.5 Implemented Phase 1 and 2

The project implemented deterministic evidence extraction with OpenCV and learned segmentation proposals using SAM2/GrabCut.

The important engineering choice was to preserve source images and independent measurements rather than replacing everything with one opaque neural representation.

## 3.6 Dataset experiment

The available dataset contains 24 objects with five views each: 120 views.

A small U-Net demonstrated that the existing pseudo-silhouette normalization target could be reproduced well on an object-level holdout.

This is useful software/ML evidence, but not proof of true jewellery understanding because the target itself is machine-generated.

## 3.7 Phase 2.3 — universal detail evidence

The fixed semantic schema was too narrow for:
- idols;
- faces;
- filigree;
- relief;
- chains;
- unknown ornamental structures.

Phase 2.3 therefore moved toward generic local observations, stable observation IDs, cross-view track hypotheses and explicit human review.

This was one of the most important architectural corrections in the project.

## 3.8 Phase 3 — visual hull

A dataset-wide visual hull was implemented using aligned orthographic silhouettes, voxel carving and marching cubes.

The resulting models are useful deterministic baselines. Their strong reprojection scores prove they reproduce silhouette evidence, but they do not prove:
- hidden concavity;
- semantic components;
- physical scale;
- manufacturing geometry.

They are correctly labelled non-metric.

## 3.9 Phase 3.3 — exact Ring01 CAD

The project then moved from mesh-only reconstruction to exact CAD fitting.

Ring01 Phase 3.3 and 3.3.1 demonstrated:
- exact CadQuery/OpenCascade solids;
- separate stone and metal;
- one valid connected metal B-rep;
- four individually addressable curved claws;
- open gallery;
- stable named structure;
- STEP export;
- derived watertight print mesh;
- multi-view render-and-compare scores.

This is the strongest current technical proof.

## 3.10 Failure-driven discoveries

### Reflection mistaken for geometry
The system interpreted highlights as physical openings.

**Correction:** preserve reflection/appearance evidence separately.

### Shared-camera assumption failed
A common camera model for independently framed product views worsened fit.

**Correction:** use per-view hypotheses unless capture calibration proves shared intrinsics.

### Proxy optimization made CAD worse
An optimizer improved its internal objective while degrading exact metrics and creating detached metal bodies.

**Correction:** hard topology and exported CAD validity outrank soft proxy score.

### Piecewise claws failed Boolean seams
A visually plausible construction was not robust as exact CAD.

**Correction:** use continuous smooth lofts or other kernel-stable construction.

### Camera preview hid an existing prong
The geometry was correct; the chosen inspection camera created a misleading projection.

**Correction:** geometry validation and presentation validation are separate.

## 3.11 Lalitha Studio

A browser Studio layer was built locally to expose:
- explicit view inputs;
- audits;
- jobs;
- model/system state;
- comparison modes;
- backend errors;
- benchmark flow.

Captured local test results show a later state than the public repository currently exposes. This created a new project-level engineering issue: source-control truth must be reconciled.

## 3.12 Product validation

A later product review correctly recommended a more disciplined wedge:
- B2B jewellery reverse-engineering/CAD copilot;
- rings first;
- guided captures;
- known scale;
- designer review;
- parametric reconstruction;
- confidence/validation.

It also recommended deferring the hardest deity reconstruction and autonomous optimization work from the MVP promise.

This does not remove intrinsic detail from the project. It moves it into a dedicated research lane.

## 3.13 Intrinsic-detail hypothesis

The project then asked whether sculptural detail can be represented mathematically through depth, edges, curves and surface structure.

The answer is yes in spirit, but with a major correction:

> **Geometry is not recoverable from raw edges alone.**

Depth, normals, curvature, ridges, valleys and spatial frequency describe surface geometry. Image edges and image frequency describe appearance. They become geometry evidence only when supported by multi-view/photometric/semantic evidence.

---

# PART 4 — SCIENTIFIC FOUNDATIONS

## 4.1 Pixels as matrices

An RGB image can be represented as a matrix/tensor:

\[
I \in \mathbb{R}^{H \times W \times 3}
\]

Each pixel stores three channel values. Operations such as gradients, filtering, convolutions and local statistics can expose image structure.

This mathematical view is useful, but the pixel matrix contains the result of **geometry + material + illumination + camera**, not geometry alone.

## 4.2 Image gradients

For grayscale intensity \(I(x,y)\):

\[
\nabla I =
\begin{bmatrix}
\partial I/\partial x\\
\partial I/\partial y
\end{bmatrix}
\]

A large gradient often indicates an image edge.

It may be useful for:
- silhouette;
- engraved line;
- stone boundary;
- prong boundary;
- highlight boundary;
- shadow boundary.

Therefore it is a constraint candidate, not an automatic 3D edge.

## 4.3 Hessian and Laplacian

The image Hessian:

\[
H_I =
\begin{bmatrix}
I_{xx} & I_{xy}\\
I_{xy} & I_{yy}
\end{bmatrix}
\]

captures second-order changes in image intensity.

The Laplacian:

\[
\nabla^2 I = I_{xx}+I_{yy}
\]

responds to local intensity structure.

These are useful for detecting image ridges/blobs/detail but must not be renamed “surface curvature” unless a valid mapping from image formation to shape exists.

## 4.4 Depth

A depth map:

\[
D(u,v)=z
\]

stores distance along the camera ray or another convention.

Relative depth is useful for shape ordering but does not automatically give metric millimetres.

## 4.5 Surface normals

For a local height map \(z(x,y)\), normal direction is related to its first derivatives:

\[
n \propto (-z_x,-z_y,1)
\]

Normals are particularly useful for fine relief because a tiny height change can cause a noticeable orientation change.

## 4.6 Curvature

Curvature measures how the surface bends.

Principal curvatures \(k_1,k_2\) give:
- mean curvature \(H=(k_1+k_2)/2\);
- Gaussian curvature \(K=k_1k_2\).

For a sculpted face, curvature can distinguish:
- rounded cheek;
- sharp eyelid;
- concave socket;
- ridge-like lip;
- flat/low-curvature forehead.

Curvature should normally be calculated from the current 3D surface hypothesis or ground truth.

## 4.7 Ridges and valleys

A ridge is a curve where a surface is locally maximally convex in an appropriate principal direction; a valley is the analogous concave structure.

These are valuable for:
- eyelids;
- lips;
- hair/crown;
- engraving borders;
- ornamental relief.

They are more geometrically meaningful than simply collecting Canny edges.

## 4.8 Spatial frequency

High-frequency geometry corresponds to rapidly varying small details. Multi-scale analysis can help separate:
- coarse body;
- medium setting/form;
- fine engraving/relief.

But image high-frequency energy can also be texture, gemstone sparkle or compression. Frequency is evidence, not proof.

## 4.9 Multi-view geometry

If the same physical feature is observed in several calibrated views, its 3D location becomes constrained by camera rays.

This is fundamentally stronger than a single-image prior.

## 4.10 Photometric/polarimetric geometry

Changing illumination without moving the object creates different evidence about surface orientation.

For reflective jewellery, polarization can provide additional constraints that ordinary RGB lacks.

This motivates a dedicated intrinsic-detail capture tier rather than forcing the consumer-photo workflow to solve an unnecessarily impossible inverse problem.

---

# PART 5 — FINAL SYSTEM ARCHITECTURE

The V1 architecture is:

```text
CAPTURE CONTRACT
      ↓
IMMUTABLE RAW EVIDENCE
      ↓
QA / NORMALIZATION / PROVENANCE
      ↓
 ┌───────────────┬────────────────────┐
 ↓               ↓                    ↓
CAMERA/SCALE   JEWELLERY EVIDENCE   APPEARANCE/REFLECTANCE
 ↓               ↓                    ↓
 └──────→ MULTI-VIEW GEOMETRY ←──────┘
                   ↓
        EVIDENCE FUSION + UNCERTAINTY
                   ↓
              HUMAN REVIEW
                   ↓
      COMPONENT + CONSTRAINT GRAPH
             ↙             ↘
   EXACT B-REP CAD       DETAIL SURFACE
             ↘             ↙
              UNIFIED GEOMETRY
                   ↓
          RENDER / COMPARE FIT
                   ↓
     GEOMETRY + TOPOLOGY VALIDATION
                   ↓
       MANUFACTURING VALIDATION
                   ↓
             HUMAN APPROVAL
                   ↓
        AUTHORITATIVE STEP
                   ↓
       DERIVED STL/3MF/OBJ/GLB
```

The architecture is intentionally modular because no one model should be responsible for every latent variable.

---

# PART 6 — MODULE-BY-MODULE TECHNICAL SPECIFICATION

## 6.1 Capture Contract

### Purpose
Define what claims are scientifically allowed from the provided evidence.

### Input
User/capture source and intended claim level.

### Output
Capture tier, required views, calibration requirements and allowed downstream modes.

### Training
None.

### Failure
The system accepts weak evidence but produces a strong manufacturing claim.

### Validation
Run metadata must show capture tier and claim level.

---

## 6.2 Raw Evidence / QA

### Purpose
Keep source truth immutable.

### Input
Images and metadata.

### Output
Hashes, decoded images, crop transforms, quality warnings, coordinate transforms.

### Algorithms
OpenCV, deterministic checks.

### Failure
Normalization loses coordinate traceability.

### Validation
Hash preservation, transform round-trip tests.

---

## 6.3 Camera and Scale

### Purpose
Estimate how each image was formed geometrically.

### Input
Images, metadata, correspondence candidates, known physical reference.

### Output
Intrinsics, extrinsics, scale, uncertainty.

### Candidates
COLMAP, VGGT, calibrated capture, per-view fitting.

### Training
Not required for COLMAP; model-specific for learned systems.

### Failure
Reflective surface defeats feature matching; camera absorbs geometry error.

### Validation
Reprojection error + held-out geometry + calibration.

---

## 6.4 Jewellery Evidence Engine

### Purpose
Create inspectable perception evidence.

### Input
Normalized images.

### Output
Foreground, components/proposals, edges, negative spaces, detail responses, stable observations.

### Current stack
OpenCV + SAM2 + GrabCut + tiny U-Net + Phase2.3.

### Candidate additions
Grounding DINO, HQ-SAM-style boundary refinement.

### Failure
Highlight becomes a stone; shadow becomes cavity; occluded prong disappears.

### Validation
Human masks and cross-view IDs.

---

## 6.5 Geometry Evidence Ensemble

### Purpose
Estimate 3D using complementary assumptions.

### Inputs
Views, cameras, masks, correspondences.

### Outputs
Visual hull, points, relative depth, normals, confidence.

### Candidates
Visual hull, COLMAP, VGGT, Depth Anything V2 Small, DSINE, reflective research.

### Failure
Each method can fail differently; fusion hides disagreement.

### Validation
Keep separate evidence and compare against CAD/scan.

---

## 6.6 Appearance / Reflectance Evidence

### Purpose
Stop appearance from contaminating geometry.

### Input
RGB/capture metadata.

### Output
Highlight/shadow/material/refraction likelihoods.

### Candidate methods
Heuristics initially, later learned classification or inverse-rendering research.

### Failure
Over-filtering removes real relief.

### Validation
Controlled-light/polarization data.

---

## 6.7 Evidence Fusion and Uncertainty

### Purpose
Combine evidence without destroying provenance.

### Input
All evidence fields.

### Output
Resolved spatial constraints + uncertainty.

### Algorithmic principle
Robust weighted estimation / factor-graph-like reasoning is preferable to one opaque average. Conflicts can stay unresolved.

### Failure
Two wrong models agree; confidence is miscalibrated.

### Validation
Coverage-risk and calibration analysis.

---

## 6.8 Component & Constraint Graph

### Purpose
Convert evidence into editable jewellery structure.

### Input
Reviewed evidence.

### Output
Stable component graph with dependencies.

### Example dependency
```text
STONE_007
  → SEAT_007
  → CAVITY_007
  → PRONG_021..024
```

If stone 7 changes, only dependent geometry should update.

### Failure
ID switching, hidden dependencies, global regeneration.

### Validation
Ten-stone local-edit benchmark.

---

## 6.9 Exact B-rep Engine

### Purpose
Create manufacturing-oriented exact solids.

### Input
Component graph + fitted parameters.

### Output
STEP/B-rep, named component solids.

### Current stack
CadQuery + OpenCascade.

### Failure
Invalid Boolean, disconnected bodies, degenerate features.

### Validation
Kernel validity + independent STEP opening + render comparison.

---

## 6.10 Intrinsic Detail Surface Engine

### Purpose
Recover physical fine relief not captured by coarse primitives.

### Input
Base CAD surface, local image evidence, depth/normals, optional controlled photometric/polarimetric evidence, semantic landmarks.

### Output
Displacement or free-form patch + confidence/provenance.

### Representations
- displacement for shallow relief;
- local NURBS/subdivision/free-form for deep complex surfaces;
- implicit/neural representations as intermediate evidence if useful.

### Failure
Texture copied into geometry; over-smoothing; noise amplification; wall-thickness violation.

### Validation
Local scan-to-surface + normal/curvature/landmark metrics.

---

## 6.11 Render-and-Compare Optimizer

### Purpose
Close the loop between CAD and source evidence.

### Input
Current geometry + cameras + reviewed masks/evidence.

### Output
Improved parameters and residual maps.

### Candidate
Existing exact renderer + optional PyTorch3D differentiable losses.

### Failure
Camera/geometry collusion; soft loss improves while topology breaks.

### Validation
Hard constraints always checked on exported geometry.

---

## 6.12 Manufacturing Validation

### Purpose
Determine whether a geometrically plausible CAD satisfies configured production constraints.

### Input
Authoritative STEP + manufacturing profile.

### Output
Pass/fail/warnings and exact violating regions.

### Rules
Wall/prong thickness, clearances, collisions, cavity breakthroughs, volume, etc.

### Failure
Invented universal thresholds.

### Validation
Expert-defined profile + real manufacturing/inspection.

---

# PART 7 — DATA & TRAINING STRATEGY

The project should train **small, well-defined tasks before a large integrated model**.

## Current dataset capability

The current 24-object set is useful for:
- preprocessing;
- pseudo-silhouette learning;
- self-consistency;
- visual hull;
- software stress testing.

It cannot establish:
- exact image-to-CAD learning;
- metric depth;
- manufacturing truth;
- hidden structure;
- deity detail.

## New dataset program

### Synthetic
Generate exact ground truth cheaply and at scale using CAD + Blender.

### Real paired CAD
Collect 50–100 rings as the first serious benchmark.

### Scan subset
Add high-quality surface scans to quantify geometric detail independently of the production CAD where appropriate.

### Controlled relief set
Build a small but precise scientific dataset for intrinsic detail.

## Training principle

No target without truth.

A loss function must correspond to the property being optimized. “Looks similar” is not a substitute for geometric ground truth.

---

# PART 8 — INTRINSIC DETAIL RECONSTRUCTION

This is a dedicated research area because it is one of Lalitha's differentiators.

## 8.1 Deity face example

Consider a Lakshmi face on a ring.

A conventional image-to-3D generator may produce:
- recognizable eyes and nose in texture;
- flattened geometry;
- blended crown/hair;
- asymmetric or semantically changed expression.

For Lalitha, the physical form matters.

## 8.2 Signal decomposition

### Nose
- positive depth relative to face;
- smoothly changing normals;
- convex curvature;
- silhouette contribution at some views.

### Eye socket
- concave depth;
- surrounding ridge/eyelid;
- local shadow that must be separated from geometry.

### Eyelid
- thin geometric ridge;
- high normal gradient;
- high-frequency local shape.

### Lips
- paired ridge/valley with semantic landmark alignment.

### Cheeks/forehead
- lower-frequency smooth convex surface.

### Crown/ornament
- repeated high-frequency structures and sometimes holes/undercuts.

## 8.3 Required evidence hierarchy

Strongest:
1. scan/CAD truth;
2. controlled multi-view geometry;
3. polarized/controlled-light geometry cues;
4. ordinary multi-view parallax;
5. normal/depth priors;
6. semantic prior;
7. raw image gradients.

Raw RGB edges are low in this hierarchy because they are highly confounded.

## 8.4 Detail fusion

A practical local solver can represent a base patch and optimize a detail field against:
- source silhouettes;
- source edges that have geometry probability;
- predicted/controlled normals;
- depth residual;
- cross-view consistency;
- semantic landmarks;
- smoothness prior;
- curvature target;
- manufacturing amplitude limits.

## 8.5 Representation selection

### Displacement
Best when the surface can be described as one offset along the base normal.

Advantages:
- compact;
- easy to regularize;
- naturally attached to base CAD.

Limitations:
- poor for undercuts and folds.

### NURBS/subdivision/free-form
Best when the sculptural region has deep or non-single-valued structure.

Advantages:
- flexible organic shape;
- can become editable surface control.

Limitations:
- attachment, topology and parameterization are harder.

## 8.6 What “divine form preservation” means technically

This should become measurable rather than subjective only.

Possible geometric/semantic checks:
- landmark position ratios;
- symmetry where appropriate;
- local depth ordering;
- nose projection;
- eye-socket depth;
- eyelid ridge continuity;
- lip ridge/valley structure;
- crown silhouette;
- local normal fields;
- curvature distribution;
- expert final approval.

The expert approval remains essential for cultural/semantic fidelity.

---

# PART 9 — MESH → CAD

## 9.1 Why a polygon mesh is not enough

A mesh is a set of vertices and faces. It often does not tell us:
- which faces form a stone seat;
- which cylinder/loft is a prong;
- which dimension is the ring size;
- what should update when a stone changes;
- how to edit wall thickness parametrically.

## 9.2 Preferred strategy

Do not make “mesh → CAD” the universal core.

For known jewellery components:
- recognize/fuse evidence;
- fit parameters directly;
- construct exact CAD.

Use dense mesh/implicit geometry mainly for:
- free-form detail;
- surface evidence;
- initialization;
- scan comparison.

## 9.3 General conversion tools as research

Cadrille, CAD-Recode and Img2CAD are scientifically relevant because they show that learned systems can produce editable CAD-like programs or intermediate representations.

They should be benchmarked on exact synthetic jewellery before they earn any production role.

## 9.4 Feature recognition

Candidate recoverable structure:
- circles/arcs;
- planes;
- cylinders;
- revolutions;
- sweeps/lofts;
- symmetry;
- repetition;
- standard stone shapes;
- prong families.

## 9.5 Negative geometry

Cavities and seats are first-class features, not mesh holes to clean up.

They should be parameterized and linked to the positive component that requires them.

---

# PART 10 — VALIDATION

Validation is not one score.

## 10.1 Silhouette IoU

For masks \(A,B\):

\[
IoU = \frac{|A\cap B|}{|A\cup B|}
\]

It tells us overlap in the image. It does not tell us hidden 3D accuracy.

## 10.2 Boundary F1

Measures how well predicted boundaries align with target boundaries within a tolerance.

Useful for:
- prong outline;
- shank contour;
- relief silhouette.

## 10.3 Chamfer distance

For point sets \(P,Q\), a common symmetric form is:

\[
CD(P,Q)=\frac{1}{|P|}\sum_{p\in P}\min_{q\in Q}\|p-q\|^2
+
\frac{1}{|Q|}\sum_{q\in Q}\min_{p\in P}\|q-p\|^2
\]

It summarizes average surface proximity but may hide localized worst errors.

## 10.4 Hausdorff distance

Measures worst-case nearest-neighbor deviation. Because a single outlier can dominate, percentile Hausdorff can also be reported.

## 10.5 Normal consistency

Measures angle between reconstructed and ground-truth surface normals.

This is especially relevant for sculptural detail.

## 10.6 Curvature error

Compare principal/mean/Gaussian curvature statistics or local curvature fields after reliable alignment.

This captures “shape character” not visible in point distance alone.

## 10.7 Dimensional error

For critical measured dimension \(d\):

\[
e_d = |\hat d - d|
\]

Report absolute mm and relative percentage.

## 10.8 CAD validity

Binary hard gates:
- solid validity;
- expected connectedness;
- no degeneracy;
- successful Boolean construction;
- STEP readability.

## 10.9 Manufacturing validity

Hard/soft rules from a versioned specialist profile.

Never label a model “manufacturing-ready” from silhouette IoU.

---

# PART 11 — EXPERIMENTS

The experiment backlog is prioritized so each step removes a major uncertainty.

## Immediate experiments

### Human Ring01 truth
Without this, current visual scores are comparisons to reviewed machine evidence rather than final human ground truth.

### Known scale
Without this, exact CAD fit is still non-metric.

### Camera/depth/normal benchmark
This determines whether COLMAP/VGGT/depth/normal priors actually help jewellery.

### Component graph
This converts the project from one successful ring construction into a reusable architecture.

## Intrinsic-detail experiments

Run later but design now:
- controlled RGB;
- cross-polarized capture;
- multiple known lights;
- scan/CAD truth;
- displacement vs free-form;
- normal/curvature/frequency ablations.

The purpose is to prove which signals actually improve physical relief reconstruction.

---

# PART 12 — OPEN-SOURCE TECHNOLOGY STACK

## Core likely product-compatible stack

- OpenCV — deterministic vision.
- SAM2 — segmentation proposals.
- Grounding DINO — candidate open-set detector.
- COLMAP — classical camera/geometry baseline.
- VGGT commercial checkpoint — candidate learned geometry branch.
- Depth Anything V2 Small — relative depth candidate.
- DSINE — normal candidate after license/checkpoint audit.
- PyTorch3D — differentiable fitting helper.
- CadQuery/OpenCascade — exact CAD.
- Trimesh — derived mesh analysis.
- Manifold — optional robust mesh operations.
- Blender — synthetic data and research workbench.
- Three.js — viewer/UI.

## Research-only or legal-review stack

- DUSt3R / MASt3R: current public code licenses are non-commercial.
- Fusion 360 Gallery Dataset: non-commercial research license.
- OpenMVS: AGPL implications require architecture/legal review.
- Neuralangelo: NVIDIA research licensing/business inquiry path and heavy VRAM.
- Hunyuan3D-2: custom community license with material restrictions.
- Cadrille/CAD-Recode: code, model weights and datasets must be checked separately.
- NeRSP/reflective datasets: code/data terms must be individually verified.

## Generative models

TRELLIS, TRELLIS.2, Hunyuan3D and Step1X-3D are useful as:
- baselines;
- visual priors;
- coarse initialization candidates.

They are not evidence that Lalitha has reconstructed the original hidden engineering structure.

---

# PART 13 — RESEARCH GAPS

The project's most defensible research gaps are not “AI for jewellery” in the abstract.

They are more specific:

1. reflective sparse-view fine geometry at jewellery scale;
2. stable image-conditioned jewellery component/dependency graphs;
3. hybrid exact CAD + free-form relief;
4. uncertainty/provenance for hidden engineering geometry;
5. paired jewellery image/CAD/scan benchmarks.

These are testable and publishable if experiments demonstrate real improvement.

---

# PART 14 — DEVELOPMENT ROADMAP

## P0 — source truth
Reconcile Git and reproduce tests.

## P1 — measurement truth
Human Ring01 masks + physical scale.

## P2 — dataset truth
Real paired CAD + scan subset.

## P3 — geometry benchmark
COLMAP vs VGGT + depth/normal priors.

## P4 — semantic/editability core
Component & Constraint Graph.

## P5 — general exact CAD
Multiple ring families.

## P6 — reflective detail laboratory
Polarization/controlled light.

## P7 — hybrid intrinsic geometry
Displacement/free-form.

## P8 — manufacturing profiles
Expert-defined checks.

## P9 — B2B pilot
Measure CAD time saved, correction effort and failure rate.

---

# PART 15 — WHAT NOT TO BUILD YET

The following are attractive distractions:

- an end-to-end giant model;
- an autonomous model router;
- a universal all-jewellery architecture before rings generalize;
- an “AI jewellery material detector” used for engineering truth;
- manufacturing thresholds invented from internet examples;
- a new CAD kernel;
- autonomous deity reconstruction marketed before a scan benchmark;
- automatic hidden back generation called reconstruction;
- every new image-to-3D model that appears on GitHub.

The project now has enough architecture. The next value comes from **truth and measurement**, not more boxes.

---

# PART 16 — CURRENT UNKNOWNS

Maintain these as living questions.

## Scientific
- How much does polarization improve sub-millimetre jewellery detail?
- Can DSINE/Depth Anything priors improve reflective relief after multi-view fusion?
- Is a height/displacement model sufficient for most ring engraving, or do free-form patches dominate?
- Which curvature/frequency losses correlate with expert perception of deity fidelity?
- Can reflective-object neural methods handle gemstones mixed with metal?

## Geometry
- How many guided views are the best tradeoff: 5, 8, 10, 12?
- What camera calibration protocol is simple enough for jewellers?
- How should evidence disagreement be fused/calibrated?

## CAD
- What generic parameterization covers the first 80% of ring settings?
- How robust are exact Boolean operations across dense multi-stone settings?
- Can learned CAD program systems produce useful candidate feature trees from jewellery data?

## Data
- How quickly can 50–100 paired real rings be collected?
- Can original production CAD legally/contractually be used for training?
- What scanner/metrology method handles polished metal best?

## Manufacturing
- Which rule profiles should be encoded for casting, resin printing, stone setting and finishing?
- Which parameters vary by alloy, stone and shop?
- What accuracy is actually required at each feature?

## Product
- How much correction time do designers tolerate?
- Which reconstruction errors are unacceptable vs quickly fixable?
- Is the best first user a CAD designer, manufacturer, retailer or catalog digitization team?

---

# PART 17 — GLOSSARY

**Albedo:** diffuse/base reflectance independent of lighting in an idealized model.  
**B-rep:** boundary representation; exact CAD representation made of faces, edges, vertices and topology.  
**CAD:** computer-aided design.  
**Camera extrinsics:** pose of camera relative to the object/world.  
**Camera intrinsics:** focal length/principal point and related internal projection parameters.  
**Chamfer distance:** average nearest-neighbor distance between two point/surface samples.  
**Curvature:** measure of how a surface bends.  
**Depth:** distance from camera/reference to visible surface.  
**Displacement map:** scalar offset applied to a base surface, usually along the normal.  
**Evidence:** a measurement or algorithmic observation that constrains but does not automatically define final geometry.  
**Gaussian curvature:** product of principal curvatures.  
**Intrinsic detail:** physically present small-scale surface geometry, as used in this project.  
**IoU:** intersection-over-union between two masks.  
**MASt3R / DUSt3R:** learned multi-view geometry/matching research methods.  
**Mean curvature:** average of principal curvatures.  
**Mesh:** vertices and polygon faces representing a surface.  
**MVS:** multi-view stereo.  
**Normal:** unit vector perpendicular to surface.  
**NURBS:** smooth parametric surface representation common in CAD.  
**OCCT/OpenCascade:** open-source CAD geometry kernel used under CadQuery.  
**Parametric CAD:** CAD defined by editable parameters/features rather than only polygons.  
**Photometric stereo:** estimating surface orientation using multiple lighting conditions.  
**Polarization:** light property that can supply extra cues about reflective surface geometry/material.  
**Principal curvature:** maximum/minimum normal curvature at a point.  
**Provenance:** record of where evidence/geometry came from and whether it is observed, inferred or designed.  
**Reprojection:** rendering/projecting estimated 3D back into an input camera for comparison.  
**Ridge/valley:** curves describing local extrema of surface bending.  
**SfM:** structure from motion; estimates cameras and 3D structure from multiple images.  
**STEP:** engineering exchange format for exact CAD/B-rep.  
**Visual hull:** maximal volume consistent with object silhouettes; cannot recover concavities not visible in silhouettes.  
**VGGT:** feed-forward multi-view geometry model producing cameras/depth/point maps/tracks.

---

# PART 18 — SOURCE INDEX

The separate `SOURCE_INDEX.md` is the maintained no-duplicate source list.

The key project sources for this release are:
- current Image2CAD repository;
- current technical roadmap/report;
- captured local Studio test/build transcript;
- prior consolidated Lalitha architecture description;
- historical project discussions.

The key external source families are:
- multi-view geometry: COLMAP, VGGT, DUSt3R, MASt3R;
- depth/normals: Depth Anything V2, DSINE;
- reflective reconstruction: NeRO, NeRSP, SpecGloss-GS;
- differentiable/exact geometry: PyTorch3D, CadQuery/OpenCascade, Manifold;
- learned CAD: Img2CAD, CAD-Recode, Cadrille;
- generative 3D benchmarks: TRELLIS, TRELLIS.2, Hunyuan3D-2, Step1X-3D;
- data: Fusion 360 Gallery and project-owned paired/synthetic datasets.

---

# FINAL ARCHITECTURE REVIEW BOARD

## Evidence preservation
**ACCEPTED.** This is already one of the strongest aspects of the current project.

## Segmentation/evidence engine
**ACCEPTED WITH CONDITIONS.** Keep machine proposals separate from human truth.

## Camera and multi-view reconstruction
**REQUIRES EXPERIMENTAL VALIDATION.** Reflective jewellery is exactly where generic geometry systems can fail.

## Component & Constraint Graph
**ACCEPTED WITH CONDITIONS / BUILD NEXT.** It is the missing generalization layer.

## Exact B-rep engine
**ACCEPTED for the current Ring01 proof.** Generalization beyond Ring01 remains unproven.

## Intrinsic-detail engine
**REQUIRES EXPERIMENTAL VALIDATION.** The scientific model is defensible; the performance is not yet proven.

## Manufacturing engine
**REQUIRES DOMAIN + EXPERIMENTAL VALIDATION.** Rules cannot be invented from images.

## Generative 3D route
**REJECTED AS AUTHORITATIVE CAD.** Accepted only as benchmark, prior or initialization.

## Model router
**DEFERRED.** There is not enough benchmark evidence to justify complexity.

---

# BASELINE V1.0 RELEASE DECISION

The project may now stop jumping between random models and use this baseline:

> **Capture defensible evidence → preserve provenance → estimate geometry using multiple independent cues → review uncertain semantics → build a component/constraint graph → construct exact functional CAD → reconstruct free-form detail only where evidence supports it → render and compare → enforce topology/manufacturing gates → obtain human approval → export STEP.**

The next implementation is **not another 3D model**.

The next implementation sequence is:

```text
1. Reconcile canonical repository
2. Human + metric Ring01 ground truth
3. Camera/depth/normal benchmark
4. Universal Component & Constraint Graph
5. Multi-ring exact CAD generalization
6. Controlled intrinsic-detail research
7. Manufacturing validation
```

That sequence converts Lalitha from a promising collection of methods into a measurable engineering program.
