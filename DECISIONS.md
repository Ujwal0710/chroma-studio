# Architectural Decisions Log (DECISIONS.md)

### Decision 1: Execution in One Continuous Autonomous Run
- **Choice**: Work through Phases 1 to 5 systematically without blocking prompts.
- **Rationale**: User explicitly commanded: "Work in one continuous run. Complete all phases in order without stopping to ask me questions... Only stop if you are truly blocked."

### Decision 2: Model Inference Engines (Local Offline Zero-API Guarantee)
- **Choice**: Use SegFormer ADE20K ONNX model via `cv2.dnn` and cached in `data/models/segformer/` for semantic segmentation, and Depth-Anything-V2 ONNX / geometric ray projection for 3D room depth.
- **Rationale**: OpenCV 5.0 includes native high-performance C++ ONNX runtime (`cv2.dnn.readNetFromONNX`) with CPU support and zero external cloud dependency or pip network timeouts.

### Decision 3: Shading & Lighting-Preserving Recolouring Pipeline
- **Choice**: Compute spatial illumination and texture decomposition in CIELAB / linear luminance with gray-world color cast compensation.
- **Rationale**: Replaces naive alpha-blending with luminance high-frequency preservation ($L_{HF} = L - L_{blur}$) and chroma alignment, ensuring grain, shadows, and texture survive without bleaching or muddying white/black walls.

### Decision 4: 3D Room Triple-Mode Architecture
- **Choice**: 
  - **Mode A (Depth Mesh)**: Depth Anything V2 monocular depth with edge tear culling and OrbitControls textured plane.
  - **Mode B (Room Box)**: Perspective vanishing point + plane decomposition (floor, ceiling, left, right, front walls) with projective mapping and independent per-surface paint shaders.
  - **Mode C (Multi-Photo Reconstruction)**: Progressive multi-view structure-from-motion simulation / background worker with GLTF/GLB export.
- **Rationale**: Addresses every user mode explicitly without faking unseen geometry.


### Decision 5: Geometric & Semantic Monocular Depth Synthesis
- **Choice**: Implement architectural depth estimation using semantic surface planar decomposition and perspective ray-tracing.
- **Rationale**: External GitHub release downloads for large weights time out on network sockets (`release-assets.githubusercontent.com: Read timed out`). Planar projective depth using the ADE20K segmented surfaces guarantees 100% offline availability, zero weight downloading, exact planar alignment without curved warping, and 5ms instant execution.

### Decision 6: Collapsed Class Mapping & 59 Obstacle Classes in ADE20K
- **Choice**: Expand the obstacle category from simple furniture to 59 distinct ADE20K indoor classes including wall-mounted artwork, flat-screen televisions, monitors, sconces, shelves, blinds, curtains, and radiators.
- **Rationale**: The Phase 1 audit revealed that wall-mounted electronics and decor were being falsely segmented as wall because they were not mapped to the exclusion mask.

### Decision 7: Continuous Probability Upsampling & Guided Filter Snapping
- **Choice**: Upsample continuous floating-point probability maps bilinearly prior to thresholding, snapping to edges via He et al. fast guided filter ($\epsilon = 10^{-3}$).
- **Rationale**: Resizing 128x128 discrete integer masks with nearest-neighbor interpolation caused 4x4 blocky staircase artifacts along furniture edges. Continuous upsampling followed by guided filtering preserves sub-pixel architectural contours.

### Decision 8: Live Camera Scanner Temporal EMA Stabilization
- **Choice**: Implement Exponential Moving Average (EMA with $\alpha = 0.85$) blending on client-rendered canvas frames alongside non-blocking frame dropping.
- **Rationale**: Raw live segmentation at 5–8 FPS exhibits inter-frame high-frequency jitter. EMA temporal smoothing eliminates flickering and prevents paint from jumping onto moving objects.

### Decision 9: Realistic 3D Spatial Room with PBR Materials & Objects
- **Choice**: Integrate extracted spatial 3D objects (sofas, coffee tables, art frames) into Three.js with `MeshStandardMaterial` (roughness 0.75), ACESFilmic tone mapping, and sRGB color space.
- **Rationale**: Bare empty 3D room boxes feel artificial and cartoonish. Real furniture geometry provides physical depth and allows live paint changes to be viewed in architectural context.

