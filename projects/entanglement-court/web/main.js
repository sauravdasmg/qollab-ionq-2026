/** Entanglement Court — Interactive Courtroom (ES Module) */
import * as court from "court_bridge";

// Global state
let currentCase = 0;
let currentChallenge = "sealed";
let currentTrust = false;
let currentShots = 200;
let currentResults = null;
let currentVerdict = null;
let recordedData = null;
let runGeneration = 0;
let circuitGeneration = 0;
let stagedElements = null;
let announceTimer = null;
let lastSuccessfulParams = null;
let automaticRuns = true;

function plainData(value) {
  if (value && typeof value.toJs === "function") value = value.toJs({ dict_converter: Object.fromEntries });
  if (value instanceof Map) return Object.fromEntries([...value].map(([k, v]) => [k, plainData(v)]));
  if (Array.isArray(value)) return value.map(plainData);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, plainData(v)]));
  return value;
}
function renderElement(id) { return stagedElements?.get(id) || document.getElementById(id); }


// DOM references
const docket = document.getElementById("docket");
const evidenceDocket = document.getElementById("evidence-docket");
const loading = document.getElementById("loading");
const errorDisplay = document.getElementById("error-display");
const errorText = document.getElementById("error-text");
const statusRegion = document.getElementById("status-region");
const verdictOptions = document.getElementById("verdict-options");
const verdictNoteText = document.getElementById("verdict-note-text");
const evidenceTabs = document.getElementById("evidence-tabs");
const caseSelect = document.getElementById("case-select");
const challengeSelect = document.getElementById("challenge-select");
const trustToggle = document.getElementById("trust-toggle");
const remeasureBtn = document.getElementById("remeasure-btn");
const caseIdEl = document.getElementById("case-id");
const evidenceCaseIdEl = document.getElementById("evidence-case-id");
const meaningText = document.getElementById("meaning-text");
const circuitText = document.getElementById("circuit-text");
const liveValues = document.getElementById("live-values");
const recordedValues = document.getElementById("recorded-values");
const comparisonMeta = document.getElementById("comparison-meta");

// Utility functions
function announce(message, type = "polite") {
  statusRegion.textContent = message;
  statusRegion.className = "status-region visible";
  statusRegion.setAttribute("aria-live", type);
  clearTimeout(announceTimer);
  announceTimer = setTimeout(() => {
    statusRegion.classList.remove("visible");
  }, 5000);
}

function showLoading(text = "Convening the court…") {
  loading.querySelector("#loading-text").textContent = text;
  loading.setAttribute("aria-busy", "true");
  loading.hidden = false;
  errorDisplay.hidden = true;
  // Keep the previous docket visible during loading and failed runs.
}

function hideLoading() {
  loading.setAttribute("aria-busy", "false");
  loading.hidden = true;
}

function showError(message) {
  hideLoading();
  errorText.textContent = `${message}. Please retry; previous evidence is retained.`;
  if (docket.hidden && evidenceDocket.hidden) showDocket();
  errorDisplay.hidden = false;
  announce(message, "assertive");
}

function showDocket() {
  docket.hidden = false;
  evidenceDocket.hidden = true;
}

function showEvidenceDocket() {
  docket.hidden = true;
  evidenceDocket.hidden = false;
}

function setVerdictNote(text) {
  verdictNoteText.textContent = text;
}

// Explicit bridge rows avoid coercion of leading-zero dictionary keys.
function distributionRows(results, blockName) {
  const explicit = results.distributions?.[blockName];
  if (explicit) {
    const rows = explicit.map(row => ({ outcome: String(row.outcome), probability: Number(row.probability) }));
    const total = rows.reduce((sum, row) => sum + row.probability, 0);
    if (rows.length !== 16 || new Set(rows.map(row => row.outcome)).size !== 16 ||
        rows.some(row => !/^[01]{4}$/.test(row.outcome) || !Number.isFinite(row.probability) || row.probability < 0) ||
        Math.abs(total - 1) > 1e-8) throw new Error("Invalid measured distribution");
    return rows.sort((a, b) => a.outcome.localeCompare(b.outcome));
  }
  const hist = results.marginals?.[blockName];
  if (!hist) {
    if (results.manifest?.recipe_identity?.audited16) return null;
    throw new Error("Missing measured distribution");
  }
  const counts = {};
  for (const [rawKey, rawCount] of Object.entries(hist)) {
    const key = String(rawKey).replace(/\s/g, "").padStart(4, "0");
    const count = Number(rawCount);
    if (!/^[01]{4}$/.test(key) || !Number.isFinite(count) || count < 0) throw new Error("Invalid counts");
    counts[key] = (counts[key] || 0) + count;
  }
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  if (!(total > 0)) throw new Error("No measured samples");
  return Array.from({ length: 16 }, (_, i) => {
    const outcome = i.toString(2).padStart(4, "0");
    return { outcome, probability: (counts[outcome] || 0) / total };
  });
}

// Fixed SVG coordinates work even before a hidden parent is laid out.
function renderHistogram(containerId, tableId, results, blockName, colorClass) {
  const container = renderElement(containerId);
  const tableBody = renderElement(tableId).querySelector("tbody");
  const rows = distributionRows(results, blockName);
  const fragment = document.createDocumentFragment();
  if (!rows) {
    const note = document.createElement("p");
    note.textContent = "Z outcomes were not measured in audited16. Select sealed or anchor for measured Z distributions.";
    container.replaceChildren(note);
    tableBody.replaceChildren();
    return;
  }
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 720 310");
  svg.setAttribute("width", "720");
  svg.setAttribute("height", "310");
  svg.setAttribute("class", "histogram-svg");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${blockName}: measured Z probabilities. Full values in the table below.`);
  function shape(tag, attrs, text) {
    const node = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    if (text !== undefined) node.textContent = text;
    svg.appendChild(node);
    return node;
  }
  shape("rect", { x: 0, y: 0, width: 720, height: 310, fill: "#FFFFFF" });
  const maximum = Math.max(0.1, ...rows.map(row => row.probability));
  const upper = Math.min(1, Math.ceil(maximum * 20) / 20);
  for (let tick = 0; tick <= 4; tick++) {
    const y = 230 - tick * 50;
    shape("line", { x1: 60, x2: 708, y1: y, y2: y, stroke: "#D8CBB0" });
    shape("text", { x: 53, y: y + 5, "text-anchor": "end", fill: "#1F1A14", "font-size": 15 }, `${(upper * tick * 25).toFixed(1)}%`);
  }
  shape("text", { x: 60, y: 20, fill: "#1F1A14", "font-size": 16 }, "Probability");
  rows.forEach((row, i) => {
    const x = 65 + i * 40;
    const height = row.probability / upper * 200;
    const rect = shape("rect", { x, y: 230 - height, width: 30, height, fill: "#2B3A8C" });
    const title = document.createElementNS(ns, "title");
    title.textContent = `${row.outcome}: ${(row.probability * 100).toFixed(2)}%`;
    rect.appendChild(title);
    shape("text", { transform: `translate(${x + 15},244) rotate(50)`, fill: "#1F1A14", "font-size": 15 }, row.outcome);
    const tr = document.createElement("tr");
    tr.className = `${colorClass}-row`;
    tr.innerHTML = `<td><code>${row.outcome}</code></td><td>${row.probability.toFixed(6)}</td>`;
    fragment.appendChild(tr);
  });
  shape("text", { x: 385, y: 305, "text-anchor": "middle", fill: "#1F1A14", "font-size": 16 }, "Outcome (bit string)");
  container.replaceChildren(svg);
  tableBody.replaceChildren(fragment);
}

// Parity chart rendering
function renderParityChart(containerId, tableId, intervals, blockPrefix) {
  const container = renderElement(containerId);
  const tableBody = renderElement(tableId).querySelector("tbody");

  container.innerHTML = "";
  tableBody.innerHTML = "";

  // Filter intervals for this block prefix
  const relevant = Object.entries(intervals).flatMap(([block, rows]) =>
    block.endsWith(`_${blockPrefix}`) ? rows.map(r => ({ ...r, block })) : []
  );

  relevant.forEach(item => {
    const { block, generator, estimate, interval, shots } = item;
    const prepType = block.startsWith("target") ? "target" : "impostor";
    const prepLabel = prepType === "target" ? "Target (Graph)" : "Impostor (Product)";

    // Chart item
    const chartItem = document.createElement("div");
    chartItem.className = `parity-item ${prepType}`;
    const mid = (interval[0] + interval[1]) / 2;
    const range = interval[1] - interval[0];
    const offsetPx = ((estimate - mid) / (range || 1)) * 30; // scale to chart width
    chartItem.innerHTML = `
      <h4>Generator K${generator}</h4>
      <div class="parity-bar" role="img" aria-label="Parity estimate ${estimate.toFixed(3)} with 95% interval [${interval[0].toFixed(3)}, ${interval[1].toFixed(3)}]">
        <div class="interval" style="left: ${50 + offsetPx - range * 50}%; right: ${50 - offsetPx - range * 50}%;"></div>
        <div class="estimate ${prepType}" style="--offset: ${offsetPx}px;"></div>
      </div>
      <div class="parity-meta">
        <span>Estimate: ${estimate.toFixed(4)}</span>
        <span>95% CI: [${interval[0].toFixed(4)}, ${interval[1].toFixed(4)}]</span>
      </div>
    `;
    container.appendChild(chartItem);

    // Table row
    const row = document.createElement("tr");
    row.innerHTML = `<td>${prepLabel}</td><td>K${generator}</td><td>${estimate.toFixed(4)}</td><td>[${interval[0].toFixed(4)}, ${interval[1].toFixed(4)}]</td><td>${shots}</td>`;
    tableBody.appendChild(row);
  });
}

// Evidence stamp rendering
function renderEvidenceStamp(witness) {
  const stampContent = renderElement("stamp-content");
  const stampTableBody = renderElement("table-stamp").querySelector("tbody");

  stampContent.innerHTML = "";
  stampTableBody.innerHTML = "";

  const fLower = witness.F_lower ?? null;
  const threshold = witness.threshold ?? 0.5;
  const passed = witness.conditional_gme === true;
  const inconclusive = !passed && (witness.receipt?.includes("inconclusive") ?? true);

  let valueClass = "inconclusive";
  let valueText = "Inconclusive";
  if (passed) { valueClass = "pass"; valueText = "GME Certified"; }
  else if (fLower !== null && fLower <= threshold) { valueClass = "fail"; valueText = "Below Threshold"; }

  stampContent.innerHTML = `
    <div class="bound-row">
      <span class="bound-label">F_lower (simultaneous)</span>
      <span class="bound-value ${valueClass}">${fLower !== null ? fLower.toFixed(4) : "N/A"}</span>
    </div>
    <div class="bound-row">
      <span class="bound-label">GME Threshold</span>
      <span class="bound-value">${threshold.toFixed(2)}</span>
    </div>
    <div class="bound-row">
      <span class="bound-label">Per-generator α</span>
      <span class="bound-value">${(witness.per_generator_alpha ?? 0).toFixed(5)}</span>
    </div>
    <div class="bound-row">
      <span class="bound-label">Trust Flag</span>
      <span class="bound-value">${witness.trust_flag ? "Trusted" : "Untrusted (Conditional)"}</span>
    </div>
    <div class="threshold-line">
      ${witness.bias_bound_semantics ?? ""}
    </div>
    <div class="receipt-text">${witness.receipt ?? "No receipt available."}</div>
  `;

  // Full receipt table
  const rows = [
    ["Round α", witness.alpha_round ?? "N/A"],
    ["Per-generator α", witness.per_generator_alpha?.toFixed(5) ?? "N/A"],
    ["F_lower", fLower !== null ? fLower.toFixed(4) : "N/A"],
    ["Threshold", threshold.toFixed(2)],
    ["Conditional GME", witness.conditional_gme ? "Yes" : "No"],
    ["Trust Flag", witness.trust_flag ? "True" : "False"],
    ["Scope", witness.scope ?? "N/A"],
    ["Bias Bound Semantics", witness.bias_bound_semantics ?? "N/A"],
  ];

  if (witness.terms) {
    witness.terms.forEach((t, i) => {
      rows.push([`Generator K${t.index} Estimate`, t.estimate.toFixed(4)]);
      rows.push([`Generator K${t.index} L_lower`, t.L_lower.toFixed(4)]);
      rows.push([`Generator K${t.index} Bias Bound`, t.bias_bound.toFixed(4)]);
    });
  }

  rows.forEach(([term, value]) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${term}</td><td>${value}</td>`;
    stampTableBody.appendChild(row);
  });
}

// Circuit text rendering
const CIRCUIT_VIEWS = { sealed: "sealed", Z: "Z", A: "A", B: "B", stamp: "stamp" };
async function renderCircuitText(caseNum, challenge, view) {
  const generation = ++circuitGeneration;
  try {
    const text = await court.get_circuit_text.callPromising(caseNum, challenge, CIRCUIT_VIEWS[view] || view);
    if (generation === circuitGeneration) circuitText.textContent = String(text);
  } catch (e) {
    if (generation !== circuitGeneration) return;
    if (!circuitText.textContent.trim()) circuitText.textContent = "Circuit preview is temporarily unavailable. Please retry.";
    announce("Circuit preview could not be updated. Please retry.", "assertive");
  }
}

// Live vs Recorded comparison
function renderComparison(results, recorded) {
  // Live values
  const witness = results.analysis.simultaneous_witness;
  const liveHtml = `
    <div>F_lower: ${witness.F_lower?.toFixed(4) ?? "N/A"}</div>
    <div>Threshold: ${witness.threshold?.toFixed(2) ?? "N/A"}</div>
    <div>Conditional GME: ${witness.conditional_gme ? "Yes" : "No"}</div>
    <div>Trust: ${witness.trust_flag ? "Trusted" : "Untrusted"}</div>
    <div>α per generator: ${witness.per_generator_alpha?.toFixed(5) ?? "N/A"}</div>
    <div>Shots/block: ${results.shots}</div>
  `;
  renderElement("live-values").innerHTML = liveHtml;

  // Recorded values
  if (recorded && recorded.records.length > 0) {
    const rec = recorded.records[0];
    const recWitness = rec.uncertainty?.simultaneous_witness;
    const recHtml = `
      <div>F_lower: ${recWitness?.F_lower?.toFixed(4) ?? "N/A"}</div>
      <div>Threshold: ${recWitness?.threshold?.toFixed(2) ?? "N/A"}</div>
      <div>Conditional GME: ${recWitness?.conditional_gme ? "Yes" : "No"}</div>
      <div>Trust: ${recWitness?.trust_flag ? "Trusted" : "Untrusted"}</div>
      <div>α per generator: ${recWitness?.per_generator_alpha?.toFixed(5) ?? "N/A"}</div>
      <div>Shots/block: ${rec.shots}</div>
      <div>Noise Model: ${rec.noise_model ?? "N/A"}</div>
      <div>UTC: ${rec.utc_end ?? "N/A"}</div>
    `;
    renderElement("recorded-values").innerHTML = recHtml;
    renderElement("comparison-meta").innerHTML = `
      <span>Live: ${results.source}</span>
      <span>Recorded: ${rec.backend} | ${rec.noise_model} | ${rec.shots} shots</span>
    `;
  } else {
    renderElement("recorded-values").innerHTML = "<div>No recorded IonQ data available.</div>";
    renderElement("comparison-meta").innerHTML = `<span>Live: ${results.source}</span><span>Recorded: No cloud evidence staged</span>`;
  }
}

// Verdict handling
function handleVerdictSelect(verdict) {
  currentVerdict = verdict;
  document.querySelectorAll(".verdict-btn").forEach(btn => {
    const selected = btn.dataset.verdict === verdict;
    btn.classList.toggle("selected", selected);
    btn.setAttribute("aria-checked", selected);
  });

  const messages = {
    A: "You find Preparation A (graph state) entangled. Open evidence tabs to test this.",
    B: "You find Preparation B (product state) entangled. This would be surprising — examine the evidence.",
    both: "You find both entangled. But the impostor is separable by construction — check the stabilizer evidence.",
    insufficient: "Correct — Z histograms alone cannot distinguish them. Open Exhibits A and B to see the difference."
  };
  setVerdictNote(messages[verdict] || "Select a verdict above to proceed.");
  announce(`Verdict selected: ${verdict}`);

  // Enable evidence tabs
  showEvidenceDocket();
  evidenceTabs.querySelectorAll(".evidence-tab").forEach(tab => tab.disabled = false);
}

// Tab switching
function switchTab(tabName) {
  document.querySelectorAll(".evidence-tab").forEach(tab => {
    const selected = tab.dataset.tab === tabName;
    tab.setAttribute("aria-selected", selected);
    tab.classList.toggle("selected", selected);
  });
  document.querySelectorAll(".evidence-panel").forEach(panel => {
    const selected = panel.id === `panel-${tabName}`;
    panel.setAttribute("aria-hidden", !selected);
    panel.hidden = !selected;
  });
  void renderCircuitText(currentCase, currentChallenge, tabName);
  announce(`Viewing ${tabName === "stamp" ? "Evidence Stamp" : `Exhibit ${tabName}`}`);
}

// Stage every update off-screen and commit only after every renderer succeeds.
function renderResults(results, recorded) {
  const ids = ["bars-target", "table-target", "bars-impostor", "table-impostor",
    "parity-Z", "table-parity-Z", "parity-A", "table-parity-A", "parity-B", "table-parity-B",
    "stamp-content", "table-stamp", "live-values", "recorded-values", "comparison-meta"];
  const targets = ids.map(id => document.getElementById(id));
  if (targets.some(node => !node)) throw new Error("Evidence panel unavailable");
  const clones = targets.map(node => node.cloneNode(true));
  stagedElements = new Map(ids.map((id, i) => [id, clones[i]]));
  try {
    renderHistogram("bars-target", "table-target", results, "target_Z", "target");
    renderHistogram("bars-impostor", "table-impostor", results, "impostor_Z", "impostor");
    const intervals = results.analysis.parity_intervals_95 || {};
    for (const view of ["Z", "A", "B"]) renderParityChart(`parity-${view}`, `table-parity-${view}`, intervals, view);
    renderEvidenceStamp(results.analysis.simultaneous_witness);
    renderComparison(results, recorded);
  } finally { stagedElements = null; }
  const previous = targets.map(node => [...node.childNodes]);
  try { targets.forEach((node, i) => node.replaceChildren(...clones[i].childNodes)); }
  catch (e) {
    targets.forEach((node, i) => node.replaceChildren(...previous[i]));
    throw e;
  }
}

async function runDemo(preserveVerdict = false) {
  const generation = ++runGeneration;
  ++circuitGeneration;
  const params = { caseNum: currentCase, challenge: currentChallenge, trust: currentTrust, shots: currentShots };
  showLoading("Measuring preparations on the selected simulator?");
  try {
    const results = plainData(await court.run_demo.callPromising(
      backend, params.caseNum, params.shots, params.challenge, params.trust));
    if (generation !== runGeneration) return;
    let recorded = recordedData || { records: [], statuses: [] };
    try { recorded = plainData(await court.load_recorded.callPromising()); }
    catch (e) { /* Optional recorded evidence must not discard a live result. */ }
    if (generation !== runGeneration) return;
    renderResults(results, recorded);
    currentResults = results;
    lastSuccessfulParams = params;
    recordedData = recorded;
    caseIdEl.textContent = `Case ${params.caseNum}`;
    evidenceCaseIdEl.textContent = `Case ${params.caseNum}`;
    if (!preserveVerdict) {
      currentVerdict = null;
      document.querySelectorAll(".verdict-btn").forEach(btn => {
        btn.classList.remove("selected");
        btn.setAttribute("aria-checked", "false");
      });
      setVerdictNote("Select a verdict above to proceed.");
    }
    verdictOptions.querySelectorAll(".verdict-btn").forEach(btn => btn.disabled = false);
    evidenceTabs.querySelectorAll(".evidence-tab").forEach(tab => tab.disabled = !currentVerdict);
    remeasureBtn.disabled = params.challenge !== "sealed" || !String(results.source).includes("built-in");
    hideLoading();
    if (currentVerdict) showEvidenceDocket(); else showDocket();
    const activeTab = evidenceTabs.querySelector('[aria-selected="true"]')?.dataset.tab || "Z";
    void renderCircuitText(params.caseNum, params.challenge, currentVerdict ? activeTab : "sealed");
    announce("Measurement complete. Examine the measured evidence and render a tentative verdict.");
  } catch (e) {
    if (generation !== runGeneration) return;
    if (lastSuccessfulParams) {
      currentCase = lastSuccessfulParams.caseNum;
      currentChallenge = lastSuccessfulParams.challenge;
      currentTrust = lastSuccessfulParams.trust;
      caseSelect.value = String(currentCase);
      challengeSelect.value = currentChallenge;
      trustToggle.checked = currentTrust;
    }
    showError("Court evidence could not be updated");
    console.error(e);
  } finally { if (generation === runGeneration) hideLoading(); }
}

function redrawHistograms() {
  if (!currentResults) return;
  try { renderResults(currentResults, recordedData); }
  catch (e) { announce("Chart could not be redrawn. Previous evidence retained.", "assertive"); }
}

// Event handlers
function setupEventListeners() {
  // Verdict buttons
  verdictOptions.querySelectorAll(".verdict-btn").forEach(btn => {
    btn.addEventListener("click", () => handleVerdictSelect(btn.dataset.verdict));
    btn.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleVerdictSelect(btn.dataset.verdict);
      }
    });
  });

  // Evidence tabs
  evidenceTabs.querySelectorAll(".evidence-tab").forEach(tab => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
    tab.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        switchTab(tab.dataset.tab);
      }
      // Arrow key navigation
      if (e.key === "ArrowRight") {
        e.preventDefault();
        const tabs = Array.from(evidenceTabs.querySelectorAll(".evidence-tab"));
        const idx = tabs.indexOf(tab);
        const next = tabs[(idx + 1) % tabs.length];
        next.focus();
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        const tabs = Array.from(evidenceTabs.querySelectorAll(".evidence-tab"));
        const idx = tabs.indexOf(tab);
        const prev = tabs[(idx - 1 + tabs.length) % tabs.length];
        prev.focus();
      }
    });
  });

  // Case selector
  caseSelect.addEventListener("change", async () => {
    currentCase = parseInt(caseSelect.value, 10);
    if (automaticRuns) await runDemo();
  });

  // Challenge selector
  challengeSelect.addEventListener("change", async () => {
    currentChallenge = challengeSelect.value;
    if (automaticRuns) await runDemo();
  });

  // Trust toggle
  trustToggle.addEventListener("change", async () => {
    currentTrust = trustToggle.checked;
    if (automaticRuns) await runDemo();
  });

  remeasureBtn.addEventListener("click", async () => {
    if (currentChallenge === "sealed") await runDemo(true);
  });
  let resizeFrame = null;
  window.addEventListener("resize", () => {
    if (resizeFrame !== null) cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => { resizeFrame = null; redrawHistograms(); });
  });
}

// Initialize; failures never remove the page shell or previous evidence.
async function init() {
  const backendName = typeof backend.name === "function" ? backend.name() : backend.name;
  automaticRuns = backendName !== "ionq_simulator";
  setupEventListeners();
  try { recordedData = plainData(await court.load_recorded.callPromising()); }
  catch (e) { recordedData = { records: [], statuses: [] }; }
  try { meaningText.textContent = await court.get_measurement_meaning.callPromising(); }
  catch (e) { meaningText.textContent = "Matching Z statistics can hide different correlations in other bases."; }
  void renderCircuitText(currentCase, currentChallenge, "sealed");
  if (backendName === "ionq_simulator") {
    hideLoading();
    const button = document.createElement("button");
    button.textContent = "Run one IonQ job";
    button.className = "verdict-btn";
    document.querySelector(".courtroom").insertBefore(button, loading);
    await new Promise(resolve => {
      button.addEventListener("click", async () => {
        button.disabled = true;
        caseSelect.disabled = true;
        challengeSelect.disabled = true;
        trustToggle.disabled = true;
        try { await runDemo(); } finally { resolve(); }
      }, { once: true });
    });
  } else { await runDemo(); }
}

window.addEventListener("error", () => showError("The page could not complete that action"));
window.addEventListener("unhandledrejection", () => showError("The page could not complete that action"));
function start() { void init().catch(() => showError("Court could not be initialized")); }
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
else start();
