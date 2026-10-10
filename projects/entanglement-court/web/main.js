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
  setTimeout(() => {
    statusRegion.classList.remove("visible");
  }, 5000);
}

function showLoading(text = "Convening the court…") {
  loading.querySelector("#loading-text").textContent = text;
  loading.hidden = false;
  errorDisplay.hidden = true;
  docket.hidden = true;
  evidenceDocket.hidden = true;
}

function hideLoading() {
  loading.hidden = true;
}

function showError(message, error = null) {
  hideLoading();
  errorText.textContent = error ? `${message}\n\n${error}` : message;
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

// Histogram rendering
function renderHistogram(containerId, tableId, marginals, blockName, colorClass) {
  const container = document.getElementById(containerId);
  const tableBody = document.getElementById(tableId).querySelector("tbody");
  const hist = marginals[blockName] || {};
  const total = Object.values(hist).reduce((a, b) => a + b, 0) || 1;

  // Clear
  container.innerHTML = "";
  tableBody.innerHTML = "";

  // Create bars
  const barContainer = document.createElement("div");
  barContainer.className = "histogram-bar";

  for (let i = 0; i < 16; i++) {
    const key = i.toString(2).padStart(4, "0");
    const count = hist[key] || 0;
    const prob = count / total;
    const height = Math.max(2, prob * 180); // min 2px for visibility

    const bar = document.createElement("div");
    bar.className = `bar ${colorClass}`;
    bar.style.height = `${height}px`;
    bar.setAttribute("data-outcome", key);
    bar.setAttribute("title", `${key}: ${(prob * 100).toFixed(2)}%`);
    barContainer.appendChild(bar);

    // Table row
    const row = document.createElement("tr");
    row.className = `${colorClass}-row`;
    row.innerHTML = `<td><code>${key}</code></td><td>${prob.toFixed(6)}</td>`;
    tableBody.appendChild(row);
  }

  container.appendChild(barContainer);
}

// Parity chart rendering
function renderParityChart(containerId, tableId, intervals, blockPrefix) {
  const container = document.getElementById(containerId);
  const tableBody = document.getElementById(tableId).querySelector("tbody");

  container.innerHTML = "";
  tableBody.innerHTML = "";

  // Filter intervals for this block prefix
  const relevant = Object.entries(intervals).flatMap(([block, rows]) =>
    block.startsWith(blockPrefix) ? rows.map(r => ({ ...r, block })) : []
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
  const stampContent = document.getElementById("stamp-content");
  const stampTableBody = document.getElementById("table-stamp").querySelector("tbody");

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
async function renderCircuitText(caseNum, challenge, blockName) {
  try {
    const text = await court.get_circuit_text.callPromising(caseNum, challenge, blockName);
    circuitText.textContent = text;
  } catch (e) {
    circuitText.textContent = `Error loading circuit: ${e.message}`;
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
  liveValues.innerHTML = liveHtml;

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
    recordedValues.innerHTML = recHtml;
    comparisonMeta.innerHTML = `
      <span>Live: ${results.source}</span>
      <span>Recorded: ${rec.backend} | ${rec.noise_model} | ${rec.shots} shots</span>
    `;
  } else {
    recordedValues.innerHTML = "<div>No recorded IonQ data available.</div>";
    comparisonMeta.innerHTML = `<span>Live: ${results.source}</span><span>Recorded: No cloud evidence staged</span>`;
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
  announce(`Viewing ${tabName === "stamp" ? "Evidence Stamp" : `Exhibit ${tabName}`}`);
}

// Main run function
async function runDemo() {
  showLoading("Measuring sealed preparations on built-in simulator…");

  try {
    // Get backend (built-in simulator) - global injected by Qollab
    const results = await court.run_demo.callPromising(
      backend,
      currentCase,
      currentShots,
      currentChallenge,
      currentTrust
    );

    currentResults = results;

    // Load recorded data
    recordedData = await court.load_recorded.callPromising();

    // Update case IDs
    caseIdEl.textContent = `Case ${currentCase}`;
    evidenceCaseIdEl.textContent = `Case ${currentCase}`;

    // Render Z histograms (target_Z and impostor_Z)
    renderHistogram("bars-target", "table-target", results.marginals, "target_Z", "target");
    renderHistogram("bars-impostor", "table-impostor", results.marginals, "impostor_Z", "impostor");

    // Render parity charts for all tabs
    const intervals = results.analysis.parity_intervals_95 || {};
    renderParityChart("parity-Z", "table-parity-Z", intervals, "target_Z");
    renderParityChart("parity-Z", "table-parity-Z", intervals, "impostor_Z");
    renderParityChart("parity-A", "table-parity-A", intervals, "target_A");
    renderParityChart("parity-A", "table-parity-A", intervals, "impostor_A");
    renderParityChart("parity-B", "table-parity-B", intervals, "target_B");
    renderParityChart("parity-B", "table-parity-B", intervals, "impostor_B");

    // Render evidence stamp
    renderEvidenceStamp(results.analysis.simultaneous_witness);

    // Render sidebar
    meaningText.textContent = await court.get_measurement_meaning.callPromising();
    await renderCircuitText(currentCase, currentChallenge, "target_Z");

    // Render comparison
    renderComparison(results, recordedData);

    // Reset verdict
    currentVerdict = null;
    document.querySelectorAll(".verdict-btn").forEach(btn => {
      btn.classList.remove("selected");
      btn.setAttribute("aria-checked", "false");
    });
    setVerdictNote("Select a verdict above to proceed.");

    // Enable controls
    verdictOptions.querySelectorAll(".verdict-btn").forEach(btn => btn.disabled = false);
    evidenceTabs.querySelectorAll(".evidence-tab").forEach(tab => tab.disabled = true);
    remeasureBtn.disabled = currentChallenge !== "sealed" || !results.source.includes("built-in");

    hideLoading();
    showDocket();
    announce("Court convened. Two sealed preparations presented. Examine the Z histograms and render a tentative verdict.");
  } catch (e) {
    showError("Failed to convene court", e.message);
    console.error(e);
  }
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
    await runDemo();
  });

  // Challenge selector
  challengeSelect.addEventListener("change", async () => {
    currentChallenge = challengeSelect.value;
    await runDemo();
  });

  // Trust toggle
  trustToggle.addEventListener("change", async () => {
    currentTrust = trustToggle.checked;
    await runDemo();
  });

  // Remeasure button
  remeasureBtn.addEventListener("click", async () => {
    if (currentChallenge !== "sealed") return;
    showLoading("Remeasuring on built-in simulator…");
    try {
      const results = await court.run_demo.callPromising(
        backend,
        currentCase,
        currentShots,
        currentChallenge,
        currentTrust
      );
      currentResults = results;

      // Re-render everything
      renderHistogram("bars-target", "table-target", results.marginals, "target_Z", "target");
      renderHistogram("bars-impostor", "table-impostor", results.marginals, "impostor_Z", "impostor");
      const intervals = results.analysis.parity_intervals_95 || {};
      renderParityChart("parity-Z", "table-parity-Z", intervals, "target_Z");
      renderParityChart("parity-Z", "table-parity-Z", intervals, "impostor_Z");
      renderParityChart("parity-A", "table-parity-A", intervals, "target_A");
      renderParityChart("parity-A", "table-parity-A", intervals, "impostor_A");
      renderParityChart("parity-B", "table-parity-B", intervals, "target_B");
      renderParityChart("parity-B", "table-parity-B", intervals, "impostor_B");
      renderEvidenceStamp(results.analysis.simultaneous_witness);
      renderComparison(results, recordedData);
      announce("Remeasure complete. New ideal samples drawn.");
    } catch (e) {
      showError("Remeasure failed", e.message);
    } finally {
      hideLoading();
    }
  });

  // Evidence panel circuit text updates
  evidenceTabs.addEventListener("click", async (e) => {
    const tab = e.target.closest(".evidence-tab");
    if (!tab) return;
    const tabName = tab.dataset.tab;
    let blockName = "target_Z";
    if (tabName === "A") blockName = "target_A";
    else if (tabName === "B") blockName = "target_B";
    else if (tabName === "stamp") blockName = "target_Z"; // default
    await renderCircuitText(currentCase, currentChallenge, blockName);
  });
}

// Initialize
async function init() {
  // Load recorded data first
  try {
    recordedData = await court.load_recorded.callPromising();
  } catch (e) {
    console.warn("Could not load recorded data:", e);
    recordedData = { records: [], statuses: [] };
  }

  // Set initial meaning
  try {
    meaningText.textContent = await court.get_measurement_meaning.callPromising();
  } catch (e) {
    meaningText.textContent = "Matching Z statistics can hide different correlations in other bases.";
  }

  // Set initial circuit text
  await renderCircuitText(currentCase, currentChallenge, "target_Z");

  // Run initial demo based on backend type
  if (backend.name === "ionq_simulator") {
    // Show button for one IonQ job, don't run on load
    const button = document.createElement("button");
    button.textContent = "Run one IonQ job";
    button.className = "verdict-btn";
    button.setAttribute("aria-label", "Run one IonQ job");
    const loading = document.getElementById("loading");
    document.querySelector(".courtroom").insertBefore(button, loading);

    await new Promise((resolve) => {
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          announce("Running IonQ job…");
          const results = await court.run_demo.callPromising(
            backend,
            currentCase,
            currentShots,
            currentChallenge,
            currentTrust
          );
          currentResults = results;

          // Load recorded data
          recordedData = await court.load_recorded.callPromising();

          // Update case IDs
          caseIdEl.textContent = `Case ${currentCase}`;
          evidenceCaseIdEl.textContent = `Case ${currentCase}`;

          // Render Z histograms
          renderHistogram("bars-target", "table-target", results.marginals, "target_Z", "target");
          renderHistogram("bars-impostor", "table-impostor", results.marginals, "impostor_Z", "impostor");

          // Render parity charts for all tabs
          const intervals = results.analysis.parity_intervals_95 || {};
          renderParityChart("parity-Z", "table-parity-Z", intervals, "target_Z");
          renderParityChart("parity-Z", "table-parity-Z", intervals, "impostor_Z");
          renderParityChart("parity-A", "table-parity-A", intervals, "target_A");
          renderParityChart("parity-A", "table-parity-A", intervals, "impostor_A");
          renderParityChart("parity-B", "table-parity-B", intervals, "target_B");
          renderParityChart("parity-B", "table-parity-B", intervals, "impostor_B");

          // Render evidence stamp
          renderEvidenceStamp(results.analysis.simultaneous_witness);

          // Render sidebar meaning and circuit
          meaningText.textContent = await court.get_measurement_meaning.callPromising();
          await renderCircuitText(currentCase, currentChallenge, "target_Z");

          // Render comparison
          renderComparison(results, recordedData);

          // Reset verdict
          currentVerdict = null;
          document.querySelectorAll(".verdict-btn").forEach(btn => {
            btn.classList.remove("selected");
            btn.setAttribute("aria-checked", "false");
          });
          setVerdictNote("Select a verdict above to proceed.");

          // Enable controls
          verdictOptions.querySelectorAll(".verdict-btn").forEach(btn => btn.disabled = false);
          evidenceTabs.querySelectorAll(".evidence-tab").forEach(tab => tab.disabled = true);
          remeasureBtn.disabled = currentChallenge !== "sealed" || !results.source.includes("built-in");

          hideLoading();
          showDocket();
          announce("IonQ job complete. Court convened with IonQ results.");
        } catch (e) {
          showError("IonQ job failed", e.message);
          announce("IonQ job error", "assertive");
        } finally {
          resolve();
        }
      }, { once: true });
    });
  } else {
    await runDemo();
  }

  setupEventListeners();
}

// Start when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}