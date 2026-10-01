# Research / Paper Map

This map answers one question for every source: **what specific Lalitha architecture problem does it help solve?**

| Architecture problem | Work / resource | Year / venue | What it contributes | Lalitha fit | Integration status |
|---|---|---|---|---|---|
| Classical multi-view camera/geometry | COLMAP — Schönberger et al. | Mature SfM/MVS system | Camera pose, sparse/dense reconstruction | Baseline for guided captures | High-priority benchmark |
| Feed-forward multi-view geometry | VGGT: Visual Geometry Grounded Transformer | CVPR 2025 | Cameras, depth, point maps and tracks | Strong multi-view hypothesis generator | High-priority benchmark |
| Unconstrained image-pair geometry | DUSt3R | CVPR 2024 | Point maps without traditional SfM pipeline | Useful research comparator | Research only due current public license |
| Dense image matching | MASt3R | ECCV 2024 / 3DV follow-up | Matching/point maps/local features | Weak-texture comparator | Research only due current public license |
| Relative depth prior | Depth Anything V2 | NeurIPS 2024 | General monocular depth prior | Extra depth evidence, not metric truth | Benchmark Small checkpoint |
| Surface normals | DSINE — Rethinking Inductive Biases for Surface Normal Estimation | CVPR 2024 | Crisp piecewise-smooth normal prediction | Detail/curvature evidence | High-priority benchmark |
| Reflective geometry + BRDF | NeRO: Neural Geometry and BRDF Reconstruction of Reflective Objects | SIGGRAPH 2023 | Joint reflective-object shape/material modeling | Direct match to polished metal research | High-priority research |
| Sparse reflective capture | NeRSP | CVPR 2024 | Reflective 3D from sparse polarized images | Direct match to jewellery capture rig | High-priority controlled experiment |
| Glossy geometry/material/light | SpecGloss-GS | WACV 2026 Oral | Glossy surface and relightable decomposition | Recent reflective benchmark | Research |
| High-fidelity neural surface | Neuralangelo | CVPR 2023 | Dense neural surface reconstruction | Upper-bound research baseline | Remote GPU only |
| Differentiable fitting | PyTorch3D | library | Differentiable rendering/camera/mesh losses | Useful around exact-CAD optimizer | Integrate selectively |
| Oriented points → surface | Screened Poisson Surface Reconstruction | 2013 | Robust watertight surface reconstruction | Mesh research after point/normal fusion | Benchmark |
| Parametric jewellery history | ByzantineCAD | CAD journal, 2005 | Feature/parametric construction of complex jewellery | Strong conceptual precedent | Reference architecture |
| Image → editable CAD | Img2CAD | 2024 arXiv | Structured Visual Geometry intermediate representation; ABC-mono/KOCAD | Relevant direct image-conditioned CAD research | Benchmark/literature |
| Point cloud → CadQuery | CAD-Recode | ICCV 2025 | Reverse engineering CAD programs from point clouds | Tests learned exact-program reconstruction | Benchmark on synthetic jewellery |
| Multi-modal CAD program reconstruction | Cadrille | 2025 arXiv | Image/point/text → CadQuery; SFT/RL weights | Useful research adapter | Not core backbone |
| Generic segmentation | SAM 2 | 2024+ | Promptable mask proposals | Current production/research evidence source | In use |
| Open-set component localization | Grounding DINO | ECCV 2024 | Text-conditioned object detection | Candidate for stones/settings/repeated parts | Benchmark |
| Generative structured 3D | TRELLIS | CVPR 2025 | Image/text conditioned 3D latent generation | Coarse semantic prior only | Optional benchmark |
| Generative high-res 3D | TRELLIS.2 | 2026 repo | O-Voxel-based high-res 3D generation | Coarse/detail hypothesis, heavy GPU | Optional remote benchmark |
| Generative 3D | Hunyuan3D-2 | 2025 | Image/multiview generative mesh | Coarse prior | Optional; licensing review important |
| Generative 3D | Step1X-3D | 2025 | Watertight TSDF-oriented geometry + texture generation | Strong open generative comparator | Optional benchmark |
| Mesh/CAD exact construction | CadQuery + OpenCascade | active | Python parametric B-rep and STEP | Current proven exact-solid path | Core |
| Robust mesh Boolean | Manifold | active | Fast robust manifold mesh operations | Derived mesh repair/stress tests | Secondary |
| Synthetic data | Blender | active | PBR rendering, controlled cameras/material/light + exact GT buffers | Project-owned training/benchmark data | Core dataset tool |

## Core URLs

- COLMAP: https://github.com/colmap/colmap
- VGGT: https://github.com/facebookresearch/vggt
- DUSt3R: https://github.com/naver/dust3r
- MASt3R: https://github.com/naver/mast3r
- Depth Anything V2: https://github.com/DepthAnything/Depth-Anything-V2
- DSINE: https://github.com/baegwangbin/DSINE
- NeRO: https://github.com/liuyuan-pal/NeRO
- NeRSP project: https://yu-fei-han.github.io/NeRSP-project/
- SpecGloss-GS: https://github.com/gkouros/SpecGloss-GS
- Neuralangelo: https://github.com/NVlabs/neuralangelo
- PyTorch3D: https://github.com/facebookresearch/pytorch3d
- CadQuery: https://github.com/CadQuery/cadquery
- CAD-Recode: https://github.com/puddleoasis/cad-recode
- Cadrille: https://github.com/col14m/cadrille
- Img2CAD: https://arxiv.org/abs/2410.03417
- TRELLIS: https://github.com/microsoft/TRELLIS
- TRELLIS.2: https://github.com/microsoft/TRELLIS.2
- Hunyuan3D-2: https://github.com/Tencent-Hunyuan/Hunyuan3D-2
- Step1X-3D: https://github.com/stepfun-ai/Step1X-3D
- SAM 2: https://github.com/facebookresearch/sam2
- Grounding DINO: https://github.com/IDEA-Research/GroundingDINO
- Manifold: https://github.com/elalish/manifold

## Research map: problem → literature → gap → Lalitha contribution

### A. Reflective fine geometry
**Problem:** specular highlights violate naive brightness-to-shape assumptions and can violate multi-view photometric consistency.  
**Literature:** NeRO, NeRSP, SpecGloss-GS, DSINE, classic photometric stereo.  
**Gap for us:** jewellery has very small relief, gemstones, metal, shadows, occlusions and sparse practical views.  
**Proposed Lalitha contribution:** provenance-aware fusion of multi-view geometry, normal/depth, reflectance and semantic evidence, validated against paired CAD/scan jewellery.

### B. Editable jewellery structure
**Problem:** a mesh does not know “stone 7,” “seat 7,” “prong 13,” or dependency rules.  
**Literature:** Cadrille/CAD-Recode/Img2CAD/general parametric CAD; ByzantineCAD as jewellery-specific conceptual precedent.  
**Gap:** image-conditioned CAD methods are not trained around jewellery component/manufacturing semantics.  
**Proposed contribution:** jewellery Component & Constraint Graph plus exact B-rep generators.

### C. Hybrid exact CAD + sculptural detail
**Problem:** parametric primitives work for functional structure; deity faces and relief do not fit simple primitives.  
**Literature:** exact CAD kernels plus neural/free-form surface literature.  
**Gap:** robustly attaching high-frequency free-form evidence to editable manufacturing CAD.  
**Proposed contribution:** named B-rep attachment frames plus displacement/NURBS patches with topology/manufacturing validation.

### D. Honest hidden geometry
**Problem:** unseen surfaces are underconstrained but generative models can make plausible shapes.  
**Literature:** generative image-to-3D systems.  
**Gap:** engineering systems often lack explicit epistemic provenance for hidden regions.  
**Proposed contribution:** observed/inferred/designed/unknown geometry states in the CAD/evidence graph.
