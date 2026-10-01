# Historical / Deprecated Architecture Register

| ID | Deprecated idea | Why it was considered | Why replaced / restricted | Replacement |
|---|---|---|---|---|
| D01 | End-to-end generative image→final CAD | Attractive simplicity | Hallucinates hidden geometry and lacks exact component/manufacturing guarantees | Evidence-first + exact B-rep |
| D02 | Cadrille as universal CAD backbone | Direct image/point/text→CadQuery is compelling | General CAD evidence only; jewellery-specific detail and manufacturing unproven | Research adapter beside deterministic B-rep |
| D03 | Dynamic model router in early product | Avoid dependency on one model | Needs task-specific benchmark data first; adds architecture complexity | Simple adapter registry + explicit selection |
| D04 | Per-image blob counts for prong identity | Easy component estimate | Occlusion/reflection changed fragment count across views | Cross-view track IDs + review |
| D05 | Shared camera-distance model for arbitrary reference images | Fewer fitting variables | Failed experiment on independently framed views | Per-view cameras unless calibrated capture |
| D06 | Unconstrained optimizer driven by machine prong masks | Improve local score | Created detached solids and worsened exact metrics | Hard topology + reviewed evidence |
| D07 | Piecewise conical segments for curved claws | Easy geometric approximation | Invalid Boolean seams | Continuous multi-section lofts |
| D08 | Bright detail as gemstone / dark detail as hole | Simple appearance heuristic | Specularity/shadows caused false geometry | Appearance evidence + semantic review |
| D09 | Raw RGB edge/Hessian as “curvature” | Intuitive matrix-based detail extraction | Image derivatives mix lighting/material/shape | Geometry-derived curvature plus appearance evidence |
| D10 | Public `main` as sole current source | Normal repository assumption | Later local Studio work/tests are not reflected remotely | Canonical tagged state after reconciliation |
| D11 | 3–4 arbitrary images as manufacturing input | Low-friction UX | Too underconstrained for reliable scale/hidden detail | Guided multi-view + scale for production |
| D12 | Generative mesh as production output | Modern image-to-3D quality | Mesh may merge parts, invent surfaces and lack CAD semantics | STEP-authoritative exact CAD |
