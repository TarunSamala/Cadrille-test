# Module Dependency Graph

```mermaid
graph TD
  CAP[Capture Contract] --> RAW[Raw Evidence Store]
  RAW --> QA[QA + Normalization]
  QA --> CAM[Camera / Scale]
  QA --> VIS[Jewellery Evidence]
  CAM --> MV[Multi-view Geometry Evidence]
  VIS --> MV
  QA --> APP[Appearance / Reflectance Evidence]
  VIS --> FUSE[Evidence Fusion + Uncertainty]
  MV --> FUSE
  APP --> FUSE
  FUSE --> REV[Human Review / Resolved Evidence]
  REV --> GRAPH[Component + Constraint Graph]
  GRAPH --> CAD[Exact B-rep CAD]
  GRAPH --> DET[Intrinsic Detail Surface]
  MV --> DET
  APP --> DET
  DET --> UNI[Unified Geometry]
  CAD --> UNI
  UNI --> FIT[Render + Compare Fit]
  CAM --> FIT
  RAW --> FIT
  FIT --> V2D[2D Validation]
  UNI --> V3D[3D / Topology Validation]
  V3D --> MFG[Manufacturing Validation]
  V2D --> APPROVE[Approval Gate]
  MFG --> APPROVE
  APPROVE --> STEP[Authoritative STEP]
  STEP --> DER[STL / 3MF / OBJ / GLB]
```

## Dependency sanity rules

1. **Scale-dependent modules** cannot run in “metric” mode until `Camera/Scale` supplies a calibrated scale.
2. **Component CAD** cannot be authoritative until semantic evidence is reviewed or exceeds a validated confidence policy.
3. **Intrinsic detail** may consume depth/normals/appearance evidence, but must not write directly to STEP without wall/topology validation.
4. **Manufacturing validation** consumes exact CAD and a versioned rule profile; it does not consume raw RGB as a substitute for a rule.
5. **Generative models** may write to the evidence store only.
6. **Every arrow crossing coordinate systems** carries the transform and uncertainty.
7. **Every derived artifact** records the exact upstream hashes/model versions/configuration.
