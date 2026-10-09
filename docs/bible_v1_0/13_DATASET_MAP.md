# Dataset Map

| Dataset / source | Contents | Ground truth available | Intended Lalitha use | Limitation / license note | Priority |
|---|---|---|---|---|---|
| Current Lalitha jewellery set | 24 objects × 5 views = 120 images | Pseudo masks; no CAD/cameras/scale/component truth | Preprocessing, silhouette learning, self-consistency, stress tests | Too small/incomplete for exact image→CAD | Existing |
| Ring01 | Five reference views + exact project checkpoints | Current exact CAD checkpoint; no final human masks/metric calibration in record | Core regression object | One object; risk of overfitting | Highest immediate |
| Project synthetic jewellery v1 | CAD-rendered rings with randomized cameras/material/light | Exact CAD, masks, depth, normals, component IDs, metric scale | Train perception and benchmark geometry | Synthetic-to-real gap | Highest |
| Project real paired-CAD v1 | 50–100 real rings, guided 8–12 views, production CAD, dimensions | Production CAD + metadata | Primary product benchmark | Must be collected | Highest |
| Project scan subset | 20–50 real pieces with calibrated high-resolution scan/inspection | Surface truth + dimensions | Fine relief / metric validation | Expensive; reflective scanning can itself need careful method | High |
| Controlled-detail set | Rings/pendants with engravings/deity relief, controlled RGB + polarization/light sweep | CAD/scan + landmark annotations | Intrinsic-detail research | Specialized capture | High research |
| ABC-mono | Rendered images paired with CAD from Img2CAD work | CAD-derived | CAD-program/image research | General CAD, not jewellery | Research |
| KOCAD | Real-world captured objects + CAD from Img2CAD work | CAD | General real image→CAD benchmark | Domain mismatch | Research |
| Fusion 360 Gallery | Parametric CAD sequences/parts/assemblies | CAD programs/B-reps | CAD reasoning pretraining/research | Non-commercial research license | Research only |
| T-ROBI / ROBI | Reflective/textureless industrial perception | Geometry/poses depending subset | Reflective-object stress test | Not jewellery | Research |
| PASMVS | Synthetic specular multi-view data | Cameras/depth/geometry | Specular MVS experiment | Domain adaptation needed | Research |
| NeRO Glossy Synthetic/Real | Reflective objects | Dataset-dependent geometry/material evaluation | Reflectance-aware reconstruction benchmark | Check original dataset terms | Research |
| NeRSP RMVP3D / related polarized sets | Sparse polarized reflective objects | Geometry evaluation data | Polarization experiment baseline | Not jewellery | Research |
| Thingi10K | Mesh corpus | Mesh geometry | Mesh robustness/manifold tests | Not semantic/parametric jewellery | Low |
| Amazon Berkeley Objects | Product images/3D assets | Varies | General product 3D/material experiments | Not manufacturing jewellery truth | Low |

## Project-owned ground truth schema

Every **real paired object** should ideally contain:

```text
object_id/
├── capture/
│   ├── rgb/
│   ├── polarized/              # optional research tier
│   ├── camera_metadata.json
│   └── calibration/
├── annotations/
│   ├── foreground/
│   ├── metal/
│   ├── stones/
│   ├── prongs/
│   ├── seats/
│   ├── negative_space/
│   ├── relief_landmarks/
│   └── component_graph.json
├── truth/
│   ├── production.step
│   ├── scan_mesh.*             # subset
│   ├── measured_dimensions.json
│   └── manufacturing_profile.json
└── provenance.json
```

## Split policy

- split by **physical object/design family**, never by image;
- no views of the same object across train and validation/test;
- keep a locked “never tuned on” physical test set;
- stratify by stone count, setting type, relief presence, metal appearance, capture device and difficulty;
- keep a separate challenging reflective/detail set so average scores cannot hide failure.
