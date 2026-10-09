# Contradiction Register

| ID | Statement A | Statement B | Why conflict | Can coexist? | Recommended interpretation | Confidence |
|---|---|---|---|---|---|---|
| C01 | “3–4 ordinary photos are enough” | Current Studio requires 5 explicit views; product validation recommends 8–12 guided views | Evidence coverage differs | Yes, as tiers | 1–5 uncontrolled = visual proposal; 5-view = research baseline; 8–12 + scale = product validation protocol | High |
| C02 | Generic image-to-3D model can be the core | Exact B-rep + evidence/constraints now has implemented proof | Different authority model | Only as prior | Generators may initialize/benchmark; final engineering truth is validated CAD | High |
| C03 | Cadrille as backbone | Cadrille has no project proof on jewellery/deity/manufacturing | General CAD benchmark ≠ jewellery | Yes as adapter | Benchmark, do not architect around it | High |
| C04 | Multiple models should be dynamically routed | No per-task benchmark yet proves a router is useful | Premature orchestration | Later | Keep adapters; manually select/benchmark first | High |
| C05 | Edges + depth define intrinsic detail | Reflections/shadows/material boundaries produce strong edges | Appearance is confounded with shape | Partly | Use depth, normals, curvature, multi-view, reflectance and semantic evidence together | High |
| C06 | Bright/dark regions imply stones/holes | Current failures show highlights became openings | Intensity is ambiguous | No as rule | Treat as proposals with review/physics evidence | High |
| C07 | One shared camera model for all product renders | Experiment showed shared camera worsened fit | Independent framing/cropping | Sometimes | Shared intrinsics only if capture protocol proves it; otherwise per-view hypothesis | High |
| C08 | Better proxy loss means better CAD | Proxy optimization created detached solids and worse exact metrics | Objective omitted hard topology | No | Hard topology/export gates outrank proxy score | High |
| C09 | Piecewise segmented prongs are adequate | Boolean seams made invalid exact CAD | Visual approximation ≠ kernel robustness | No for final | Use smooth loft/continuous exact construction | High |
| C10 | High silhouette IoU proves 3D accuracy | Visual hull has >0.94 reprojection yet lacks hidden concavity/scale | Metric mismatch | No | Report metric scope explicitly | High |
| C11 | AI can estimate scale from the image | Manufacturing needs defensible physical dimensions | Single photos lack absolute scale | Only with calibrated reference/prior | Require known dimension/calibration for metric claims | High |
| C12 | Hidden backside can be reconstructed | Unobserved geometry is underconstrained | Not observable | Only as inference/design | Label hidden geometry inferred/designed/unknown; never observed | High |
| C13 | Public `main` is the latest source of truth | Later local transcript has 89+11+6 tests/Studio changes; remote branch was not found | Repository state diverged | Temporarily | Reconcile, push/tag canonical commit, clean-clone reproduce | High |
| C14 | Project already covers arbitrary jewellery | Strongest exact-CAD proof is Ring01; current dataset lacks CAD truth | Scope claim exceeds evidence | Long-term only | Baseline is rings-first; expand only after benchmark exit criteria | High |
| C15 | Manufacturing thresholds can be automated from images | Manufacturing rules depend on process/alloy/setting practice | Image cannot reveal process rules | No | Versioned rule profiles from domain specialists | High |
| C16 | Deity reconstruction should be immediate MVP | Product validation says defer; science is not yet validated | Product sequencing | Yes as research branch | Continue research, but do not block first B2B CAD-copilot pilot | Medium/High |
| C17 | Texture maps can preserve fine design | Relief/deity details often require actual geometry | Appearance-only representation fails manufacturing/sculpture | Sometimes | Separate appearance from microgeometry; choose representation by physical relief | High |
