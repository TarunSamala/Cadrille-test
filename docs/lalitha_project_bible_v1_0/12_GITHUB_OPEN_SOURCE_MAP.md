# GitHub / Open-Source Map

**Important:** code license, checkpoint/model-weight license, dataset license and dependency license are separate checks. This table is an engineering triage, not legal advice.

| Technology | Purpose | Repository | License / terms observed | Hardware / practical note | Production fit |
|---|---|---|---|---|---|
| OpenCV | Deterministic image processing | https://github.com/opencv/opencv | Apache-2.0 for modern OpenCV distribution; verify bundled modules | CPU friendly | Strong |
| SAM 2 | Promptable segmentation | https://github.com/facebookresearch/sam2 | Apache 2.0 code per project metadata | GPU useful; Tiny already used | Strong, subject to checkpoint audit |
| Grounding DINO | Open-set/text-conditioned detection | https://github.com/IDEA-Research/GroundingDINO | Apache-2.0 repo | GPU | Strong candidate |
| Depth Anything V2 Small | Relative depth | https://github.com/DepthAnything/Depth-Anything-V2 | Small checkpoint Apache-2.0; Base/Large/Giant are CC-BY-NC-4.0 per official project | Small is preferred for commercial/product benchmark | Strong candidate if Small |
| COLMAP | SfM/MVS | https://github.com/colmap/colmap | New BSD for COLMAP itself; third-party dependencies separately licensed | CUDA helps MVS | Strong baseline |
| VGGT | Camera/depth/point maps/tracks | https://github.com/facebookresearch/vggt | Repo reports commercial-use-friendly code; only `VGGT-1B-Commercial` checkpoint is commercial, original remains non-commercial | Larger GPU/remote recommended | Candidate; use correct checkpoint |
| DUSt3R | Pairwise geometry/point maps | https://github.com/naver/dust3r | CC BY-NC-SA 4.0 | GPU | Research-only for commercial product |
| MASt3R | Dense matching | https://github.com/naver/mast3r | CC BY-NC-SA 4.0 | GPU + compiled components | Research-only for commercial product |
| DSINE | Surface normals | https://github.com/baegwangbin/DSINE | Verify repo/checkpoint terms before packaging | GPU; practical single-image prior | Research/product benchmark |
| PyTorch3D | Differentiable 3D losses/rendering | https://github.com/facebookresearch/pytorch3d | BSD | CUDA recommended | Strong |
| CadQuery | Exact parametric B-rep | https://github.com/CadQuery/cadquery | Apache 2.0 | CPU; OCCT underneath | Core |
| OpenCascade/OCCT | CAD kernel | https://github.com/Open-Cascade-SAS/OCCT | Verify current OCCT terms with deployment | CPU | Core |
| Trimesh | Mesh analysis/validation | https://github.com/mikedh/trimesh | MIT | CPU | Strong |
| Manifold | Mesh Boolean/manifold operations | https://github.com/elalish/manifold | Apache 2.0 | CPU/GPU integrations possible | Strong secondary |
| Blender | Synthetic data + organic prototyping | https://projects.blender.org/blender/blender | GPL; generated artwork/output is not automatically GPL, but embedding/redistributing code has obligations | GPU rendering optional | Excellent as external tool/process boundary |
| Three.js | Browser 3D viewer | https://github.com/mrdoob/three.js | MIT | Browser | Strong |
| OpenMVS | Dense MVS | https://github.com/cdcseacave/openMVS | AGPL-3.0 | GPU useful | License architecture review before service/product use |
| NeRO | Reflective geometry + BRDF | https://github.com/liuyuan-pal/NeRO | MIT repo | Research training workload; nvdiffrast/raytracing deps | High-value research |
| NeRSP | Sparse polarized reflective geometry | https://yu-fei-han.github.io/NeRSP-project/ | Check released code/data terms individually | Requires polarization capture | High-value research |
| SpecGloss-GS | Glossy surfel/material reconstruction | https://github.com/gkouros/SpecGloss-GS | Repo currently exposes source; verify full dependency/data terms | Recent research stack | Research |
| Neuralangelo | High-fidelity neural surface | https://github.com/NVlabs/neuralangelo | NVIDIA research licensing path for business use | Official FAQ says ≥24 GB default; lower-memory settings sacrifice quality | Remote research only |
| Cadrille | Multi-modal CAD → CadQuery | https://github.com/col14m/cadrille | Verify repo + weights/datasets separately; public repo says RL fine-tuning code not provided | Transformer/GPU | Research adapter |
| CAD-Recode | Point cloud → CadQuery | https://github.com/puddleoasis/cad-recode | Verify repo/model/dataset licenses before packaging | Transformer/GPU | Benchmark |
| TRELLIS | Generative 3D | https://github.com/microsoft/TRELLIS | Models and majority of code MIT; submodules may differ | Heavy GPU | Remote benchmark only |
| TRELLIS.2 | High-res generative 3D | https://github.com/microsoft/TRELLIS.2 | Current repo has MIT LICENSE; still audit model/dependencies | Very heavy GPU | Remote benchmark only |
| Hunyuan3D-2 | Generative/multi-view 3D | https://github.com/Tencent-Hunyuan/Hunyuan3D-2 | Tencent Hunyuan 3D community license; geographic/commercial/use restrictions | >4 GB practical needs; remote | Research/benchmark with legal review |
| Step1X-3D | Generative geometry + texture | https://github.com/stepfun-ai/Step1X-3D | Apache-2.0 per official repo; audit model/data dependency terms too | Large models | Remote benchmark |
| Fusion 360 Gallery Dataset | Parametric CAD research data | https://github.com/AutodeskAILab/Fusion360GalleryDataset | Dataset license restricts use to non-commercial research | Offline dataset | Research only, not product-training default |

## Current local-vs-remote project source issue

The public `TarunSamala/Image2CAD` repository is accessible and contains the earlier/current core pipeline, but the later locally tested Studio branch/state captured in project logs is not fully represented on the remote branch queried during this audit.

**Action:** establish a canonical tagged commit before new architecture work. A project Bible cannot be a source of truth if the executable source has two competing “latest” states.
