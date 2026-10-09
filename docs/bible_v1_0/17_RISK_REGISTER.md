# Risk Register

| ID | Risk | Consequence | Detection | Mitigation | Residual status |
|---|---|---|---|---|---|
| R01 | Specular highlight becomes geometry | False grooves/protrusions/cavities | Cross-view inconsistency; controlled light | Separate appearance evidence; polarization research | High |
| R02 | Gemstone refraction confuses surface | Wrong stone/depth | Component/material region checks | Model gemstones separately; do not use refracted texture as metal geometry | High |
| R03 | Hidden geometry hallucination | Unsafe manufacturing assumption | Provenance audit | observed/inferred/designed/unknown states | High |
| R04 | No metric scale | Wrong dimensions/weight | Scale-state gate | Require known dimension/calibration | Controlled |
| R05 | Dataset too small | Overfit/false confidence | Locked object-level test | Collect 50–100 paired rings + scan subset | High |
| R06 | Pseudo-label overfitting | Inflated segmentation metrics | Compare to human truth | Human masks + pseudo label disclosure | High until E01 |
| R07 | Topology breaks during optimization | Invalid CAD | B-rep/connectivity tests | Hard topology gates | Medium |
| R08 | Fine relief violates wall thickness | Pretty but unmanufacturable CAD | Wall analysis | Detail amplitude constraints + rule profile | High until manufacturing profile |
| R09 | Cross-view component ID switch | Wrong seat/prong relationships | Track consistency | Stable graph + review | Medium |
| R10 | Non-commercial model/data license enters product | Legal/product blocker | License manifest | Research isolation + commercial alternatives | High governance |
| R11 | Heavy model exceeds local GPU | Development stalls | VRAM/runtime benchmark | Small models local; remote research workers | Controlled |
| R12 | Model router complexity | Hard-to-debug product | Architecture review | Defer router | Controlled |
| R13 | CAD AI domain shift | Invalid programs on jewellery | Execution/shape benchmark | Candidate only; exact kernel validation | High |
| R14 | Deity face semantic deformation | Unacceptable design | Landmark/expert review | Separate detail benchmark + human approval | High |
| R15 | Manufacturing rules vary by alloy/process | False pass/fail | Rule provenance | Versioned profiles + expert owners | High |
| R16 | Remote/local source divergence | Irreproducible claims | Git audit | Canonical tag + CI | Immediate P0 |
| R17 | Single aggregate score hides failures | Bad model selected | Per-view/component scorecard | No single universal score | Controlled |
| R18 | Synthetic-to-real gap | Model fails on workshop photos | Real locked test | Material/camera randomization + real fine-tune | High |
| R19 | Controlled capture becomes too complex | Poor product UX | Pilot time/error tracking | Separate Tier B/C workflows | Medium |
| R20 | Human review cost too high | Poor scalability | Review minutes/object | Confidence-prioritized review; better capture | Medium |
| R21 | Free-form detail cannot attach robustly to STEP | Broken hybrid CAD | Boolean/attachment checks | Named frames + bounded patches + revalidation | High research |
| R22 | Poisson/neural surface oversmooths detail | Divine/engraving detail lost | B5 frequency/curvature metrics | Preserve direct detail evidence; compare reps | Medium |
| R23 | Ring01 overfit | False belief architecture generalizes | New-design test | Multiple families before release | High |
| R24 | Camera optimizer exploits crop/scale | Good overlay, wrong shape | calibration/held-out views | constrain camera; use known metadata | Medium |
| R25 | Marketing overclaims “manufacturing accurate” | Customer trust/safety issue | Claim-level audit | automatic report language tied to evidence tier | High governance |
