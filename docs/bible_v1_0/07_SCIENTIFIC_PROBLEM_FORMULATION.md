# Scientific Problem Formulation

## 1. What is the inverse problem?

A photograph is not geometry. A simplified image-formation model for view \(i\) is:

\[
I_i = \mathcal{R}(S, M, L_i, C_i, E_i) + \epsilon_i
\]

where:

- \(I_i\): observed image;
- \(S\): unknown 3D surface/geometry;
- \(M\): material and reflectance properties;
- \(L_i\): illumination for view \(i\);
- \(C_i\): camera model and pose;
- \(E_i\): environment, occlusions and inter-reflections;
- \(\mathcal{R}\): image rendering/formation process;
- \(\epsilon_i\): sensor/compression/model error.

Lalitha must approximately solve the inverse problem: infer the most defensible \(S\), component structure and CAD representation from a small set of \(I_i\), while refusing to treat variables that are not observable as known facts.

For polished metal and gemstones the inverse problem is especially ill-posed because highlights, reflections and refraction can move between views even when the surface is unchanged.

## 2. Camera geometry

For a 3D point \(X_h\) in homogeneous coordinates, a pinhole camera projects it approximately as:

\[
p_i \sim K_i [R_i \mid t_i] X_h
\]

where:

- \(p_i = [u,v,1]^T\): image pixel in homogeneous coordinates;
- \(K_i\): camera intrinsic matrix;
- \(R_i\): camera rotation;
- \(t_i\): camera translation;
- \(X_h\): homogeneous 3D point.

If camera depth \(z\) is available, a pixel can be back-projected:

\[
X_c = z K^{-1}[u,v,1]^T
\]

This gives geometry in the camera coordinate frame. **Metric millimetres still require an external scale** unless the imaging system is metrically calibrated.

## 3. Why “depth + edges” is incomplete

The project's intuition that a sculpted face can be understood using protrusions, depressions, edges and curves is useful but incomplete.

For a local height field \(z(x,y)\):

\[
p=z_x,\qquad q=z_y
\]

A corresponding surface normal is:

\[
n = \frac{(-p,-q,1)}{\sqrt{1+p^2+q^2}}
\]

With second derivatives

\[
r=z_{xx},\qquad s=z_{xy},\qquad t=z_{yy}
\]

the Gaussian curvature of the height field is:

\[
K = \frac{rt-s^2}{(1+p^2+q^2)^2}
\]

and mean curvature is:

\[
H = \frac{(1+q^2)r-2pqs+(1+p^2)t}{2(1+p^2+q^2)^{3/2}}
\]

where:
- positive/negative curvature combinations describe convex, concave and saddle-like structures;
- ridges/valleys describe extrema of normal curvature along local directions;
- depth and normals describe surface position/orientation;
- high spatial frequencies describe small-scale changes.

However, an **RGB image gradient is not the same thing as a 3D surface gradient**. A dark/bright line can be:
- a silhouette;
- a geometric crease;
- an albedo/material boundary;
- a cast shadow;
- a specular highlight;
- gemstone reflection/refraction;
- a texture or engraving;
- image compression.

Therefore Lalitha must preserve image edges as **appearance evidence** until geometry, multi-view consistency or controlled-light evidence supports converting them to geometry.

## 4. Differential geometry of intrinsic detail

For a general parametric surface \(X(u,v)\), the first fundamental form describes local metric/stretching and the second fundamental form describes how the surface bends.

Let:

\[
I =
\begin{bmatrix}
E & F\\
F & G
\end{bmatrix},\qquad
II =
\begin{bmatrix}
e & f\\
f & g
\end{bmatrix}
\]

The shape operator is:

\[
S = I^{-1}II
\]

The eigenvalues of \(S\) are principal curvatures \(k_1,k_2\):

\[
H = \frac{k_1+k_2}{2},\qquad K=k_1k_2
\]

For deity faces and relief:
- nose/ornament protrusions: positive height with strong normal change;
- eye sockets: concave depth regions;
- cheeks/forehead: smooth low-to-medium curvature regions;
- eyelids/lips: thin ridge/valley structures;
- crown/filigree: high-frequency geometry and repeated semantic structure.

This mathematical description is useful **after** Lalitha has a surface hypothesis. Curvature cannot be safely recovered by taking the Hessian of raw RGB intensity.

## 5. Photometric information

Under the simplified Lambertian photometric-stereo model:

\[
I_k(x,y) = \rho(x,y)\, l_k^T n(x,y)
\]

where:
- \(I_k\): intensity under lighting condition \(k\);
- \(\rho\): diffuse albedo;
- \(l_k\): known light direction/intensity;
- \(n\): surface normal.

Several controlled lighting conditions can constrain \(n\). Jewellery violates the Lambertian assumption because gold, polished metal and gemstones are strongly specular/transparent. Classic photometric stereo is therefore a baseline, not the final physics model.

Controlled cross-polarization or polarimetric capture is valuable because it adds information for separating surface orientation and reflectance.

## 6. Observable vs ambiguous variables

| Variable | Ordinary sparse photos | Guided multi-view + known scale | Controlled light/polarization |
|---|---|---|---|
| Silhouette | Strong | Strong | Strong |
| Visible 2D components | Medium/Strong | Strong | Strong |
| Relative depth | Medium | Stronger | Stronger |
| Metric scale | No | Yes | Yes |
| Camera pose | Sometimes | Stronger | Strong |
| Surface normals | Prior-dependent | Stronger | Stronger |
| Reflectance/material separation | Weak | Medium | Stronger |
| Hidden geometry | Not observable directly | Partly constrained | Partly constrained |
| Manufacturing intent | Not observable | Not directly | Not directly |

## 7. Scientific representation of a reconstruction

Every reconstructed geometric element must carry:

\[
G = \{geometry,\; source,\; confidence,\; state,\; uncertainty\}
\]

with `state ∈ {observed, inferred, designed, unknown}`.

This is not metadata decoration. It is necessary to stop hallucinated hidden geometry from being mistaken for measured truth.

## 8. Geometry objective

A reconstruction optimizer may combine soft evidence:

\[
\mathcal{L} =
\lambda_s L_{silhouette}
+\lambda_e L_{edge}
+\lambda_d L_{depth}
+\lambda_n L_{normal}
+\lambda_p L_{photometric}
+\lambda_m L_{semantic}
+\lambda_f L_{fine-detail}
+\lambda_r L_{regularization}
\]

Hard constraints are not traded away for a lower soft loss:

- valid/closed B-rep where required;
- correct number and identity of required components;
- connectivity;
- minimum wall/prong rules once configured;
- no invalid Boolean result;
- valid STEP export;
- explicit metric-scale gate.

The project's previous failure where an optimizer improved a proxy objective but generated detached solids is the reason hard topology must outrank the proxy score.

## 9. Final scientific hypothesis

Fine jewellery detail is best modeled as a **multi-evidence constrained surface-estimation problem**, not as “edge detection” and not as a single monocular-depth prediction.

Required evidence can include:
1. multi-view silhouettes and parallax;
2. camera geometry;
3. relative/metric depth;
4. surface-normal predictions;
5. curvature derived from the current surface;
6. ridge/valley and multi-scale frequency evidence;
7. reflectance/highlight likelihood;
8. semantic landmarks;
9. controlled photometric/polarimetric evidence where needed;
10. learned priors;
11. uncertainty and provenance.

The exact subset depends on the object. No mathematical signal is included merely because it sounds sophisticated.
