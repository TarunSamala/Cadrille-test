const state = { summary: null, objects: [], selected: null, layer: "source" };

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

async function api(path) {
  const response = await fetch(path);
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
    return `<article class="view-card">
      <img src="${assetUrl(detail.object_id, state.layer, view)}" alt="${escapeHtml(data.label)} ${escapeHtml(state.layer)}" loading="lazy">
      <div class="view-card-footer"><strong>${escapeHtml(data.label)}</strong><span>Pseudo IoU ${score(data.metrics?.iou)}</span></div>
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
    await loadObjects("all", "ring_001");
  } catch (error) { showError(error); }
}

document.addEventListener("DOMContentLoaded", start);
