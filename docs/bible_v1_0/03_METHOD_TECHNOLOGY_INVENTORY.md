# Method & Technology Inventory

Legend: **KEEP** = baseline component, **BENCHMARK** = compare before adoption, **RESEARCH** = experimental lane, **DEFER** = not justified now, **REJECT-AS-AUTHORITY** = may be useful but must not determine final CAD alone.

| Area | Method / Technology | Role | State | Reason / Limitation |
|---|---|---|---|---|
| Capture | Explicit named views | Prevent view-order ambiguity | KEEP | Required by current Studio |
| Capture | Known dimension / calibration target | Metric scale | KEEP | Hard gate for mm claims |
| Capture | Guided 8–12 view protocol | Better coverage for product benchmark | PROPOSED/KEEP | More defensible than “3–4 arbitrary photos” |
| Capture | Controlled illumination | Detail/normal evidence | RESEARCH | Changes capture workflow |
| Capture | Cross-polarization / polarization | Reflectance/shape disambiguation | RESEARCH | Strong match to polished metal; requires hardware |
| QA | Blur/focus/exposure checks | Reject weak inputs early | KEEP | Cheap and deterministic |
| QA | Immutable source hashes/crop transforms | Provenance | KEEP | Prevents accidental coordinate mismatch |
| Segmentation | OpenCV foreground/morphology/contours | Deterministic baseline | KEEP | Working, inspectable |
| Segmentation | GrabCut refinement | Conservative edge refinement | KEEP | Working in current pipeline |
| Segmentation | SAM 2.1 Tiny | Promptable proposals | KEEP | Current working method; proposals ≠ truth |
| Segmentation | Tiny Jewellery U-Net | Task-specific silhouette baseline | KEEP BASELINE | Learns pseudo target; not component truth |
| Detection | Grounding DINO | Text/open-set component proposals | BENCHMARK | Useful for repeated parts; jewellery accuracy unknown |
| Boundary | HQ-SAM family | Fine boundary refinement | BENCHMARK | Must prove benefit on reflective prongs/filigree |
| Evidence | Canny | Image/silhouette edge evidence | KEEP | Edge ≠ geometry by itself |
| Evidence | Top-hat / black-hat | Small bright/dark structure | KEEP AS EVIDENCE | Can capture reflection as well as relief |
| Evidence | Laplacian | Local high-frequency response | KEEP AS EVIDENCE | Appearance-domain, not depth |
| Evidence | Wavelets / Laplacian pyramid | Multi-scale detail bands | RESEARCH | Useful for ablation; not standalone geometry |
| Evidence | Stable observations + track hypotheses | Cross-view identity | KEEP | Current Phase 2.3 direction |
| Review | Accept/reject/relabel gate | Semantic QA | KEEP | Prevents automatic hallucination |
| Camera | Per-view camera hypotheses | Independently framed references | KEEP | Project experiment rejected shared-camera assumption |
| Camera | COLMAP | Classical SfM/MVS baseline | BENCHMARK HIGH | Mature/inspectable; specularity can break matches |
| Camera | VGGT | Feed-forward cameras/point maps/tracks | BENCHMARK HIGH | Strong candidate; jewellery validation required |
| Matching | DUSt3R | Pairwise geometry | RESEARCH | Non-commercial public license |
| Matching | MASt3R | Dense matching/local features | RESEARCH | Non-commercial public license |
| Depth | Depth Anything V2 Small | Relative-depth prior | BENCHMARK HIGH | Small model license is practical; not metric truth |
| Normals | DSINE | Surface-normal prior | BENCHMARK HIGH | In-the-wild normals; reflective jewellery needs validation |
| Coarse 3D | Visual hull / voxel carving | Conservative multi-view volume | KEEP | Implemented; cannot recover concavity/scale |
| Surface extraction | Marching cubes | Occupancy → mesh | KEEP DERIVED | Standard deterministic extraction |
| Point/surface | Screened Poisson | Oriented point → watertight mesh | BENCHMARK | Can oversmooth fine relief |
| Reflective 3D | NeRO | Geometry + BRDF on reflective objects | RESEARCH HIGH | Excellent scientific match; compute/capture heavier |
| Reflective 3D | NeRSP | Sparse polarized reflective reconstruction | RESEARCH HIGH | Requires polarized capture; six-view paper setting |
| Reflective 3D | SpecGloss-GS | Glossy surface/material/light decomposition | RESEARCH | Recent; benchmark carefully |
| Neural surface | Neuralangelo | High-fidelity surface baseline | RESEARCH/REMOTE | Default ≥24GB GPU; not CAD |
| Differentiable fit | PyTorch3D | Camera/mesh losses | KEEP/BENCHMARK | Useful optimizer tool; exact CAD still validates |
| Exact CAD | CadQuery | Programmatic parametric B-rep | KEEP | Current exact-solid implementation |
| Exact CAD | OpenCascade/OCCT | Geometric kernel | KEEP | STEP/B-rep foundation |
| Mesh QA | Trimesh | Export/load/topology checks | KEEP | Current project dependency |
| Mesh Boolean | Manifold | Robust derived-mesh Boolean/repair | BENCHMARK | Does not replace B-rep |
| Semantics | Component & Constraint Graph | Stable parts + dependencies | BUILD NEXT | Needed for generalization |
| Detail | Normal displacement field | Shallow relief | RESEARCH/BUILD | Efficient when detail is single-valued over base surface |
| Detail | NURBS/subdivision/free-form patches | Organic/deep relief | RESEARCH/BUILD | Needed for deity faces and non-height-field geometry |
| Detail | Curvature/ridge/valley losses | Preserve shape character | RESEARCH | Must be computed on/referred to geometry, not raw RGB |
| CAD AI | Cadrille | Image/point/text → CadQuery research adapter | BENCHMARK | General CAD benchmarks; no jewellery proof |
| CAD AI | CAD-Recode | Point cloud → CadQuery | BENCHMARK | Mechanical/general CAD domain |
| CAD AI | Img2CAD | Image → structured visual geometry → CAD | LITERATURE BENCHMARK | Useful architectural reference; jewellery unknown |
| Generative 3D | TRELLIS / TRELLIS.2 | Coarse semantic shape prior | REJECT-AS-AUTHORITY | Hidden geometry can be generated |
| Generative 3D | Hunyuan3D | Coarse/multiview hypothesis | REJECT-AS-AUTHORITY | License restrictions + non-CAD output |
| Generative 3D | Step1X-3D | High-fidelity generated 3D candidate | REJECT-AS-AUTHORITY | Asset generator, not manufacturing reconstruction |
| Generative 3D | TripoSR / Stable Fast 3D / SPAR3D | Baselines | BENCHMARK OPTIONAL | Useful scorecard references, not final CAD |
| Synthetic | Blender | Render exact CAD with masks/depth/normals/material variation | KEEP HIGH | Best controllable GT generation route |
| UI | Lalitha Studio | Upload/debug/review/view/benchmark | KEEP | Locally tested state exists |
| Web viewer | Three.js-style viewer | Inspect geometry/components/confidence | KEEP | UI layer only |
| Validation | Reprojection/silhouette IoU | Visual consistency | KEEP | Must use human GT for accuracy claim |
| Validation | Boundary F1 | External boundary/detail edge fit | KEEP | 2D only |
| Validation | Chamfer/Hausdorff | 3D surface deviation | KEEP WHEN GT EXISTS | Needs CAD/scan truth |
| Validation | Normal consistency | Surface orientation | KEEP WHEN GT EXISTS | Needs aligned GT |
| Validation | Curvature error | Fine geometry character | RESEARCH/KEEP | Needs reliable surface GT |
| Validation | Dimensional error | Manufacturing-scale geometry | KEEP | Requires calibrated scale |
| Validation | B-rep validity/connectivity | CAD correctness | KEEP HARD GATE | Cannot be traded for visual score |
| Validation | Manufacturing rule checks | Production feasibility | BUILD LATER | Rules require specialist provenance |
