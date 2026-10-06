const state = { summary: null, objects: [], selected: null, layer: "source", phase1Review: null };

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function score(value, digits = 3) {
  return typeof value === "number" ? value.toFixed(digits) : "—";
}

function percent(value) {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "—";
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function showError(error) {
  const banner = $("#error-banner");
  banner.textContent = error.message || String(error);
  banner.classList.remove("hidden");
}

function clearError() { $("#error-banner").classList.add("hidden"); }

function renderSummary(summary) {
  const test = summary.phase2.test || {};
  const phase3Test = summary.phase3.mean_reprojection_iou_by_split?.test;
  $("#dataset-metrics").innerHTML = `
    <article class="metric"><span>Dataset objects</span><strong>${summary.dataset.object_count}</strong><small>${summary.dataset.image_count} source images · five views each</small></article>
    <article class="metric"><span>Phase 2 self-consistency IoU</span><strong>${score(test.iou)}</strong><small>Machine pseudo-label target · not human GT</small></article>
    <article class="metric"><span>Held-out Phase 3 IoU</span><strong>${score(phase3Test)}</strong><small>Non-metric reprojection score</small></article>
    <article class="metric"><span>Manufacturing validated</span><strong>${summary.phase3.manufacturing_accuracy_validated ? "Yes" : "No"}</strong><small>Scale and cameras are uncalibrated</small></article>`;
  const governance = summary.governance;
  $("#governance-summary").innerHTML = `
    <article class="metric"><span>Capture contract</span><strong>Tier ${escapeHtml(governance.capture_tier)}</strong><small>Five-view exploratory research</small></article>
    <article class="metric"><span>Evidence class</span><strong class="compact-value">${escapeHtml(governance.evidence_class)}</strong><small>Implemented and measured in-project</small></article>
    <article class="metric"><span>Decision</span><strong class="compact-value">Research only</strong><small>No metric or production claim</small></article>
    <article class="metric"><span>Authoritative output</span><strong class="compact-value">STEP / B-rep</strong><small>Not available for STL-1 objects</small></article>`;

  const phase0 = summary.phase0;
  const commit = phase0.source?.commit || "unknown";
  const torch = phase0.runtime?.torch || {};
  $("#phase0-summary").innerHTML = `
    <article class="metric"><span>Phase 0 status</span><strong class="compact-value">${escapeHtml(humanize(phase0.status))}</strong><small>CPU/software reproducibility freeze</small></article>
    <article class="metric"><span>Regression suite</span><strong>${phase0.regression?.test_count ?? "—"}</strong><small>${escapeHtml(phase0.regression?.result || "unknown")} in pinned container</small></article>
    <article class="metric"><span>Source commit</span><strong class="compact-value mono">${escapeHtml(commit.slice(0, 12))}</strong><small>Canonical branch: ${escapeHtml(phase0.source?.canonical_branch || "—")}</small></article>
    <article class="metric"><span>Validation runtime</span><strong class="compact-value">PyTorch ${escapeHtml(torch.version || "—")}</strong><small>CUDA available: ${torch.cuda_available ? "yes" : "no"} · ${phase0.dependency_package_count} packages inventoried</small></article>`;
  $("#phase0-limits").innerHTML = (phase0.known_limits || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`).join("");

  const groundTruth = summary.phase1_ground_truth;
  const gate = groundTruth.exit_gate;
  $("#phase1-summary").innerHTML = `
    <article class="metric"><span>Phase 1 gate</span><strong class="compact-value">${escapeHtml(humanize(gate.status))}</strong><small>Human GT complete: ${gate.human_ground_truth_complete ? "yes" : "no"}</small></article>
    <article class="metric"><span>Mask reviews pending</span><strong>${gate.pending_label_review_count}</strong><small>Five views · seven labels per view</small></article>
    <article class="metric"><span>Component IDs pending</span><strong>${gate.pending_component_identity_count}</strong><small>${groundTruth.component_count} stable identities proposed</small></article>
    <article class="metric"><span>Scale and cameras</span><strong class="compact-value">${gate.metric_scale_available ? "Metric scale recorded" : "Relative image scale"}</strong><small>${gate.pending_camera_record_count} view semantics pending · metric scale ${gate.physical_scale_required ? "required" : "optional"}</small></article>`;
  $("#phase1-authority").textContent = groundTruth.authority_policy;
  $("#phase1-depth-status").innerHTML = `
    <div class="key-value"><span>Model</span><strong>Depth Anything V2 Small</strong></div>
    <div class="key-value"><span>Status</span><strong class="bad">${escapeHtml(humanize(groundTruth.depth.status || "not run"))}</strong></div>
    <div class="key-value"><span>Metric depth</span><strong class="bad">${groundTruth.depth.metric ? "Yes" : "No"}</strong></div>
    <div class="key-value"><span>Role</span><strong>Proposal and uncertainty evidence</strong></div>`;

  const validation = groundTruth.depth_validation;
  const pixels = groundTruth.pixel_features;
  $("#phase1-deep-summary").innerHTML = `
    <article class="metric"><span>Repeated depth runs</span><strong>${validation.runtime?.repeat_count ?? "—"}</strong><small>All identical: ${validation.checks?.all_three_repeats_identical ? "yes" : "no"}</small></article>
    <article class="metric"><span>Front object bias</span><strong>${score(Math.abs(validation.front_raw_object_top_bottom_delta), 4)}</strong><small>Regularized: ${score(Math.abs(validation.front_regularized_object_top_bottom_delta), 4)}</small></article>
    <article class="metric"><span>Front stone bias</span><strong>${score(Math.abs(validation.front_raw_stone_top_bottom_delta), 4)}</strong><small>Regularized: ${score(Math.abs(validation.front_regularized_stone_top_bottom_delta), 4)}</small></article>
    <article class="metric"><span>Pixel reconstruction</span><strong class="compact-value">${pixels.reconstruction_contract?.pixel_exact_roundtrip ? "Exact" : "Failed"}</strong><small>${pixels.view_count} views · metric depth ${pixels.depth_contract?.metric_depth_available ? "available" : "blocked"}</small></article>`;

  const datasetDepth = summary.phase1.depth_anything_v2;
  const depthRuntime = datasetDepth.runtime || {};
  const depthCoverage = datasetDepth.coverage || {};
  const depthOverall = datasetDepth.metrics?.overall || {};
  $("#dataset-depth-summary").innerHTML = `
    <article class="metric"><span>Coverage</span><strong>${depthCoverage.view_count ?? "—"}</strong><small>${depthCoverage.object_count ?? "—"} objects · five views each</small></article>
    <article class="metric"><span>GPU runtime</span><strong>${score(depthRuntime.total_seconds, 2)}s</strong><small>${score(depthRuntime.mean_seconds_per_view, 3)} seconds per view</small></article>
    <article class="metric"><span>Mean flip error</span><strong>${score(depthOverall.mean, 4)}</strong><small>Diagnostic only · lower is more self-consistent</small></article>
    <article class="metric"><span>Phase 1 gate</span><strong class="compact-value">${escapeHtml(humanize(datasetDepth.phase1_gate?.status || "blocked"))}</strong><small>Metric depth: no · human GT: no</small></article>`;

  const complete = summary.phase1.complete_features || {};
  const completeCoverage = complete.coverage || {};
  const completeRuntime = complete.runtime || {};
  const completeChecks = complete.checks || {};
  const completeContract = complete.feature_contract || {};
  const reconstruction = complete.reconstruction_contract || {};
  const bias = complete.depth_validation?.top_bottom_absolute_bias_by_view?.front || {};
  $("#dataset-complete-summary").innerHTML = `
    <article class="metric"><span>Complete feature matrices</span><strong>${completeContract.stored_array_count_per_view ?? "—"}</strong><small>Per view · ${completeCoverage.view_count ?? "—"} views processed</small></article>
    <article class="metric"><span>Repeated depth runs</span><strong>${completeRuntime.repeat_count ?? "—"}</strong><small>All identical: ${completeChecks.all_three_repeats_identical ? "yes" : "no"}</small></article>
    <article class="metric"><span>Source reconstruction</span><strong class="compact-value">${reconstruction.source_pixel_roundtrip_exact ? "Pixel exact" : "Failed"}</strong><small>Normalized pixels retained: ${reconstruction.normalized_pixels_retained_exactly ? "yes" : "no"}</small></article>
    <article class="metric"><span>Front vertical depth delta</span><strong>${score(bias.raw?.mean, 4)}</strong><small>Flip ensemble: ${score(bias.regularized?.mean, 4)} · diagnostic, not correction</small></article>`;
}

const PHASE1_VIEWS = ["front", "side", "top", "angled", "back"];
const PHASE1_LABELS = ["jewelry", "metal", "shank", "stone_visible", "setting", "prongs", "negative_space"];

function phase1AssetUrl(view, kind, label = null) {
  const query = label ? `?label=${encodeURIComponent(label)}` : "";
  return `/api/phase1/assets/${encodeURIComponent(view)}/${encodeURIComponent(kind)}${query}`;
}

function selectedPhase1Review() {
  const manifest = state.phase1Review;
  if (!manifest) return;
  const view = $("#phase1-review-view").value;
  const label = $("#phase1-review-label").value;
  const componentId = $("#phase1-component").value;
  const cameraView = $("#phase1-camera-view").value;
  $("#phase1-source-preview").src = phase1AssetUrl(view, "source");
  $("#phase1-proposal-preview").src = phase1AssetUrl(view, "proposal", label);
  const labelReview = manifest.views[view].reviews[label];
  $("#phase1-label-current").textContent = `Current: ${humanize(labelReview.decision)}${labelReview.reviewer ? ` · ${labelReview.reviewer}` : ""}`;
  const component = manifest.component_catalog.find((item) => item.component_id === componentId);
  $("#phase1-component-current").textContent = `Current: ${humanize(component.review.decision)} · ${humanize(component.class)}`;
  const camera = manifest.camera_records[cameraView];
  $("#phase1-camera-current").textContent = `Current: ${humanize(camera.review.decision)} · ${humanize(camera.projection_model)}`;
}

function renderPhase1Review(manifest) {
  state.phase1Review = manifest;
  const populate = (selector, values, labeler = humanize) => {
    const select = $(selector);
    const previous = select.value;
    select.innerHTML = values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(labeler(value))}</option>`).join("");
    if (values.includes(previous)) select.value = previous;
  };
  populate("#phase1-review-view", PHASE1_VIEWS);
  populate("#phase1-camera-view", PHASE1_VIEWS);
  populate("#phase1-review-label", PHASE1_LABELS);
  populate("#phase1-component", manifest.component_catalog.map((item) => item.component_id), (value) => value);
  const gate = manifest.exit_gate;
  const pending = gate.pending_label_reviews.length + gate.pending_component_identities.length + gate.pending_camera_records.length;
  const status = $("#phase1-review-status");
  status.textContent = gate.status === "pass" ? "Image GT complete" : `${pending} reviews pending`;
  status.className = `pill ${gate.status === "pass" ? "pass" : "warning"}`;
  selectedPhase1Review();
}

async function loadPhase1Review() {
  renderPhase1Review(await api("/api/phase1/review"));
}

function phase1ReviewerPayload() {
  const reviewer = $("#phase1-reviewer").value.trim();
  if (!reviewer) throw new Error("Enter the reviewer name before recording a decision.");
  return { reviewer, note: $("#phase1-review-note").value.trim() || null };
}

async function submitPhase1(path, payload) {
  clearError();
  await api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.summary = await api("/api/summary");
  renderSummary(state.summary);
  await loadPhase1Review();
}

function renderObjectList() {
  $("#object-count").textContent = state.objects.length;
  $("#object-list").innerHTML = state.objects.map((item) => `
    <button class="object-button ${state.selected?.object_id === item.object_id ? "active" : ""}" data-object-id="${escapeHtml(item.object_id)}">
      <strong>${escapeHtml(item.source_name)}</strong><span>${escapeHtml(item.split)} · ${item.view_count} views</span>
      <span class="object-score">${score(item.phase3_mean_iou)}</span>
    </button>`).join("");
  $$(".object-button").forEach((button) => button.addEventListener("click", () => selectObject(button.dataset.objectId)));
}

function assetUrl(objectId, kind, view = null) {
  const query = view ? `?view=${encodeURIComponent(view)}` : "";
  return `/api/objects/${encodeURIComponent(objectId)}/assets/${kind}${query}`;
}

function renderViews(detail) {
  $("#view-grid").innerHTML = detail.view_order.map((view) => {
    const data = detail.views[view];
    const complete = data.complete_features || {};
    return `<article class="view-card">
      <img src="${assetUrl(detail.object_id, state.layer, view)}" alt="${escapeHtml(data.label)} ${escapeHtml(state.layer)}" loading="lazy">
      <div class="view-card-footer"><strong>${escapeHtml(data.label)}</strong><span>Flip H ${score(complete.horizontal_flip_error_over_depth_span, 4)} · V ${score(complete.vertical_flip_error_over_depth_span, 4)} · Pseudo IoU ${score(data.metrics?.iou)}</span></div>
    </article>`;
  }).join("");
}

function renderMetadata(detail) {
  $("#metadata-rows").innerHTML = detail.view_order.map((view) => {
    const data = detail.views[view];
    const dimensions = data.source_size_wh ? `${data.source_size_wh[0]} × ${data.source_size_wh[1]}` : "—";
    return `<tr><td>${escapeHtml(data.label)}</td><td>${dimensions}</td><td>${score(data.mask_occupancy)}</td><td>${score(data.metrics?.iou)}</td><td>${score(data.metrics?.boundary_f1_2px)}</td></tr>`;
  }).join("");

  const supervisionLabels = {
    jewelry_silhouette: "Jewellery silhouette",
    edge_map: "Edge map",
    individual_stones: "Individual stones",
    metal_components: "Metal components",
    prongs: "Prongs",
    stone_seats: "Stone seats",
    cavities: "Cavities",
    camera_intrinsics: "Camera intrinsics",
    camera_extrinsics: "Camera extrinsics",
    physical_scale: "Physical scale",
    mesh_target: "Mesh target",
    cad_target: "CAD target",
  };
  $("#supervision-list").innerHTML = Object.entries(supervisionLabels).map(([key, label]) => {
    const value = detail.supervision[key];
    const available = value !== null && value !== undefined;
    const display = available ? String(value).replaceAll("_", " ") : "Unavailable";
    return `<div class="key-value"><span>${label}</span><strong class="${available ? "good" : "bad"}">${escapeHtml(display)}</strong></div>`;
  }).join("");

  $("#feature-rows").innerHTML = detail.view_order.map((view) => {
    const data = detail.views[view];
    const features = data.features || {};
    return `<tr>
      <td>${escapeHtml(data.label)}</td>
      <td>${percent(features.foreground_fraction)}</td>
      <td>${percent(features.edge_fraction)}</td>
      <td>${features.contour_count ?? "—"}</td>
      <td>${features.hole_count ?? "—"}</td>
      <td>${score(features.horizontal_symmetry_iou)}</td>
    </tr>`;
  }).join("");

  $("#depth-rows").innerHTML = detail.view_order.map((view) => {
    const data = detail.views[view];
    const depth = data.depth || {};
    return `<tr>
      <td>${escapeHtml(data.label)}</td>
      <td>${score(depth.mean_flip_error_over_depth_span, 4)}</td>
      <td>${score(depth.p95_flip_error_over_depth_span, 4)}</td>
      <td>${depth.metric ? "Yes" : "No"}</td>
      <td>${depth.cross_view_aligned ? "Yes" : "No"}</td>
    </tr>`;
  }).join("");
}

function humanize(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderBible(detail) {
  const bible = detail.bible;
  $("#bible-gates").innerHTML = Object.entries(bible.gates).map(([name, passed]) => `
    <div class="key-value"><span>${escapeHtml(humanize(name))}</span><strong class="${passed ? "good" : "bad"}">${passed ? "Pass" : "Blocked"}</strong></div>`).join("");
  $("#evidence-records").innerHTML = bible.evidence_records.map((record) => `
    <div class="key-value evidence-row">
      <span>${escapeHtml(record.stage)}</span>
      <strong>${escapeHtml(record.state)}</strong>
      <small>${escapeHtml(record.evidence_class)}</small>
    </div>`).join("");
  $("#artifact-authority").textContent = bible.artifact_authority;
}

function renderPhase3(detail) {
  const phase3 = detail.phase3;
  const preview = $("#phase3-preview");
  const metrics = $("#phase3-metrics");
  const geometry = detail.geometry_evidence || {};
  const database = geometry.database || {};
  const globalGeometry = state.summary?.phase3?.geometry_benchmark || {};
  const vggt = globalGeometry.backends?.vggt || {};
  $("#phase3-geometry").innerHTML = `
    <div class="key-value"><span>COLMAP object status</span><strong class="${geometry.status === "completed_with_sparse_model" ? "good" : "bad"}">${escapeHtml(humanize(geometry.status || "not run"))}</strong></div>
    <div class="key-value"><span>SIFT keypoints</span><strong>${database.keypoints_rows?.toLocaleString() ?? "—"}</strong></div>
    <div class="key-value"><span>Verified cross-view pairs</span><strong class="${database.two_view_geometries_nonempty_records ? "good" : "bad"}">${database.two_view_geometries_nonempty_records ?? "—"}</strong></div>
    <div class="key-value"><span>Sparse reconstruction</span><strong class="${geometry.sparse_model ? "good" : "bad"}">${geometry.sparse_model ? `${geometry.sparse_model.registered_images} / 5 views` : "Not formed"}</strong></div>
    <div class="key-value"><span>VGGT</span><strong class="${vggt.status === "ready" ? "good" : "bad"}">${escapeHtml(humanize(vggt.status || "not run"))}</strong></div>
    <div class="key-value"><span>Bible gate</span><strong class="bad">Research only</strong></div>`;
  if (!phase3) {
    preview.removeAttribute("src");
    metrics.innerHTML = "<p>No experimental Phase 3 artifact is available.</p>";
    return;
  }
  preview.src = assetUrl(detail.object_id, "phase3_preview");
  const mesh = phase3.mesh || {};
  const reprojection = phase3.reprojection || {};
  metrics.innerHTML = `
    <div class="phase3-score"><strong>${score(reprojection.mean_iou)}</strong><span>Mean reprojection IoU</span></div>
    <div class="key-value-list">
      <div class="key-value"><span>Watertight</span><strong class="${mesh.watertight ? "good" : "bad"}">${mesh.watertight ? "Pass" : "Fail"}</strong></div>
      <div class="key-value"><span>Connected bodies</span><strong>${mesh.body_count ?? "—"}</strong></div>
      <div class="key-value"><span>Vertices</span><strong>${mesh.vertices?.toLocaleString() ?? "—"}</strong></div>
      <div class="key-value"><span>Faces</span><strong>${mesh.faces?.toLocaleString() ?? "—"}</strong></div>
      <div class="key-value"><span>Camera calibrated</span><strong class="bad">${phase3.camera_calibrated ? "Yes" : "No"}</strong></div>
      <div class="key-value"><span>Physical scale</span><strong class="bad">${phase3.scale?.calibrated ? "Calibrated" : "Display scale only"}</strong></div>
      <div class="key-value"><span>Artifact authority</span><strong class="bad">Derived only</strong></div>
      <div class="key-value"><span>Decision</span><strong class="bad">Research only</strong></div>
    </div>`;
  $("#download-stl").href = assetUrl(detail.object_id, "phase3_stl");
  $("#download-3mf").href = assetUrl(detail.object_id, "phase3_3mf");
}

function renderObject(detail) {
  state.selected = detail;
  $("#object-workspace").classList.remove("hidden");
  $("#object-title").textContent = detail.source_name;
  $("#object-path").textContent = `STL-1 / ${detail.object_id}`;
  $("#object-badges").innerHTML = `<span class="pill ${detail.split === "test" ? "test" : "pass"}">${escapeHtml(detail.split)} split</span><span class="pill warning">Tier A</span><span class="pill warning">Research only</span>`;
  $("#report-download").href = `/api/objects/${encodeURIComponent(detail.object_id)}/report`;
  $("#report-download").classList.remove("disabled");
  $("#phase-sheet").src = assetUrl(detail.object_id, "phase_sheet");
  $("#phase1-depth-review").src = assetUrl(detail.object_id, "phase1_depth_review");
  $("#phase1-complete-audit").src = assetUrl(detail.object_id, "phase1_complete_audit");

  const heldOut = detail.artifacts.held_out_review;
  $("#held-out-card").classList.toggle("hidden", !heldOut);
  if (heldOut) $("#held-out-review").src = assetUrl(detail.object_id, "held_out_review");

  renderViews(detail);
  renderMetadata(detail);
  renderPhase3(detail);
  renderBible(detail);
  renderObjectList();
}

async function selectObject(objectId) {
  clearError();
  try {
    renderObject(await api(`/api/objects/${encodeURIComponent(objectId)}`));
  } catch (error) { showError(error); }
}

async function loadObjects(split = "all", preferredId = null) {
  const result = await api(`/api/objects?split=${encodeURIComponent(split)}`);
  state.objects = result.objects;
  renderObjectList();
  const target = state.objects.find((item) => item.object_id === preferredId) || state.objects[0];
  if (target) await selectObject(target.object_id);
}

function bindControls() {
  ["#phase1-review-view", "#phase1-review-label", "#phase1-component", "#phase1-camera-view"].forEach((selector) => {
    $(selector).addEventListener("change", selectedPhase1Review);
  });
  $$(".phase1-label-decision").forEach((button) => button.addEventListener("click", () => {
    const common = phase1ReviewerPayload();
    submitPhase1("/api/phase1/reviews/label", {
      ...common,
      view: $("#phase1-review-view").value,
      label: $("#phase1-review-label").value,
      decision: button.dataset.decision,
    }).catch(showError);
  }));
  $$(".phase1-identity-decision").forEach((button) => button.addEventListener("click", () => {
    const common = phase1ReviewerPayload();
    submitPhase1("/api/phase1/reviews/identity", {
      ...common,
      component_id: $("#phase1-component").value,
      decision: button.dataset.decision,
    }).catch(showError);
  }));
  $$(".phase1-camera-decision").forEach((button) => button.addEventListener("click", () => {
    const common = phase1ReviewerPayload();
    submitPhase1("/api/phase1/reviews/camera", {
      ...common,
      view: $("#phase1-camera-view").value,
      projection_model: $("#phase1-projection").value,
      uncertainty: $("#phase1-camera-uncertainty").value.trim(),
      decision: button.dataset.decision,
    }).catch(showError);
  }));
  $("#split-filter").addEventListener("change", (event) => loadObjects(event.target.value).catch(showError));
  $$("#layer-switcher button").forEach((button) => button.addEventListener("click", () => {
    state.layer = button.dataset.layer;
    $$("#layer-switcher button").forEach((item) => item.classList.toggle("active", item === button));
    if (state.selected) renderViews(state.selected);
  }));
  $$(".tab").forEach((button) => button.addEventListener("click", () => {
    $$(".tab").forEach((item) => item.classList.toggle("active", item === button));
    $$(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `panel-${button.dataset.panel}`));
  }));
}

async function start() {
  bindControls();
  try {
    state.summary = await api("/api/summary");
    renderSummary(state.summary);
    await loadPhase1Review();
    await loadObjects("all", "ring_001");
  } catch (error) { showError(error); }
}

document.addEventListener("DOMContentLoaded", start);
