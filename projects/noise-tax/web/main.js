import * as tax from "tax_bridge";

const GAMES = ["W", "N"];
const MODEL_LABELS = {
  "aria-1": "Aria 1", "forte-1": "Forte 1", "forte-enterprise-1": "Forte Enterprise 1",
};
const CHART_W = 640;
const CHART_H = 240;
const PAD = { left: 46, right: 12, top: 12, bottom: 30 };

const state = {
  evidence: null,
  live: null,
  noise: 0,
  selectedModel: "aria-1",
  selectedGame: "W",
};

function $(id) {
  return document.getElementById(id);
}

function setStatus(message) {
  const region = $("status-region");
  region.textContent = message;
}

function showError(message) {
  $("loading").hidden = true;
  $("error-text").textContent = message;
  $("error-display").hidden = false;
  console.error(message);
}

function interp(grid, values, s) {
  if (!grid || !values || grid.length < 2 || grid.length !== values.length) return null;
  if (s < grid[0] - 1e-9 || s > grid[grid.length - 1] + 1e-9) return null;
  if (s <= grid[0]) return values[0];
  for (let i = 1; i < grid.length; i++) {
    if (s <= grid[i]) {
      const t = (s - grid[i - 1]) / (grid[i] - grid[i - 1]);
      return values[i - 1] + t * (values[i] - values[i - 1]);
    }
  }
  return values[values.length - 1];
}

function fmt(value) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toFixed(5);
}

function entryFor(model) {
  return state.evidence.games[state.selectedGame][model];
}

function badgeFor(entry, s) {
  const a = interp(entry.grid, entry.advantage, s);
  if (a === null) return { cls: "tie", text: "OUTSIDE RANGE" };
  const lo = entry.lower ? interp(entry.grid, entry.lower, s) : a;
  const hi = entry.upper ? interp(entry.grid, entry.upper, s) : a;
  const tol = 1e-9;
  if (lo > tol) return { cls: "quantum", text: "QUANTUM WINS" };
  if (hi < -tol) return { cls: "classical", text: "CLASSICAL WINS" };
  return { cls: "tie", text: "TIE REGION" };
}

function renderCardValues() {
  for (const game of GAMES) {
    const entry = state.evidence.games[game][state.selectedModel];
    const badge = badgeFor(entry, state.noise);
    const badgeEl = $(`badge-${game}`);
    badgeEl.className = `badge ${badge.cls}`;
    badgeEl.textContent = badge.text;
    const adv = interp(entry.grid, entry.advantage, state.noise);
    $(`adv-${game}`).textContent = fmt(adv);
    const lo = entry.lower ? interp(entry.grid, entry.lower, state.noise) : null;
    const hi = entry.upper ? interp(entry.grid, entry.upper, state.noise) : null;
    if (lo !== null) {
      $(`adv-${game}`).title = `CI [${fmt(lo)}, ${fmt(hi)}] at s=${fmt(state.noise)}`;
    }
    const xstar = entry.crossing;
    const cs = entry.ci;
    if (xstar === null) {
      $(`xstar-${game}`).textContent = "crossover s*: not measured within s = 0…2";
    } else if (cs && Array.isArray(cs)) {
      $(`xstar-${game}`).textContent =
        `crossover s* = ${xstar.toFixed(3)}  ·  CI [${cs[0].toFixed(3)}, ${cs[1].toFixed(3)}]`;
    } else {
      $(`xstar-${game}`).textContent = `crossover s* = ${xstar.toFixed(3)}`;
    }
    drawChart(game);
    rebuildTable(game);
  }
}

function setSliderLabel() {
  $("slider-value").textContent = state.noise.toFixed(2);
  const input = $("noise-slider");
  input.value = String(state.noise);
  input.setAttribute("aria-valuetext", `noise scale ${state.noise.toFixed(2)}`);
  for (const game of GAMES) {
    const marker = $(`slider-line-${game}`);
    if (marker) marker.setAttribute("x1", String(xScale(state.noise)));
    if (marker) marker.setAttribute("x2", String(xScale(state.noise)));
  }
}

function xScale(s) {
  return PAD.left + (s / 2) * (CHART_W - PAD.left - PAD.right);
}

function yScale(v, yMax, yMin) {
  return PAD.top + (1 - (v - yMin) / (yMax - yMin || 1)) * (CHART_H - PAD.top - PAD.bottom);
}

function curveY(entry) {
  const values = entry.lower ? entry.lower.concat(entry.upper, entry.advantage) : entry.advantage;
  return values.concat(0);
}

function drawChart(game) {
  const box = $(`chart-box-${game}`);
  box.innerHTML = "";
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${CHART_W} ${CHART_H}`);
  svg.setAttribute("role", "presentation");
  const entry = state.evidence.games[game][state.selectedModel];
  const raw = curveY(entry);
  let yMin = Math.min(...raw);
  let yMax = Math.max(...raw);
  const pad = (yMax - yMin) * 0.1 || 0.02;
  yMin -= pad;
  yMax += pad;

  const NS = "http://www.w3.org/2000/svg";
  const line = (x1, y1, x2, y2, cls) => {
    const el = document.createElementNS(NS, "line");
    el.setAttribute("x1", String(x1)); el.setAttribute("y1", String(y1));
    el.setAttribute("x2", String(x2)); el.setAttribute("y2", String(y2));
    el.setAttribute("class", cls);
    svg.appendChild(el);
    return el;
  };
  const helper = (tag, attrs, text) => {
    const el = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
    if (text !== undefined) el.textContent = text;
    svg.appendChild(el);
    return el;
  };
  const pathOf = (points) => points.map((p) => `${p[0]},${p[1]}`).join(" ");

  line(PAD.left, yScale(0, yMax, yMin), CHART_W - PAD.right, yScale(0, yMax, yMin), "zero-line");

  if (entry.grid && entry.advantage) {
    const curvePoints = entry.grid.map((s) => [xScale(s), yScale(interp(entry.grid, entry.advantage, s), yMax, yMin)]);
    helper("polyline", { points: pathOf(curvePoints), class: "curve" });
    if (entry.lower && entry.upper) {
      const lowPts = entry.grid.map((s) => [xScale(s), yScale(interp(entry.grid, entry.lower, s), yMax, yMin)]);
      const upPts = entry.grid.map((s) => [xScale(s), yScale(interp(entry.grid, entry.upper, s), yMax, yMin)]);
      helper("polygon", { points: pathOf(lowPts.concat([...upPts].reverse())), class: "band" });
    }
  }

  const crossing = entry.crossing;
  if (crossing !== null) {
    const cx = xScale(crossing);
    if (cx >= PAD.left && cx <= CHART_W - PAD.right) {
      line(cx, PAD.top, cx, CHART_H - PAD.bottom, "cross-line");
      helper("polygon", {
        points: `${cx},${yScale(0, yMax, yMin) - 6} ${cx + 5},${yScale(0, yMax, yMin) + 5} ${cx - 5},${yScale(0, yMax, yMin) + 5}`,
        class: "cross-mark",
      });
      if (entry.ci && Array.isArray(entry.ci)) {
        const a = Math.max(xScale(entry.ci[0]), PAD.left);
        const b = Math.min(xScale(entry.ci[1]), CHART_W - PAD.right);
        helper("rect", {
          x: String(a), y: String(yScale(0, yMax, yMin) - 6 + 2),
          width: String(b - a), height: String(11 - 4),
          class: "ci-band",
        });
      }
    }
  }

  let anchorIndex = 0;
  for (const anchor of state.evidence.anchors) {
    if (anchor.game !== game) continue;
    const ay = yScale(anchor.advantage, yMax, yMin);
    const sign = anchor.advantage > 1e-9 ? "quantum" : anchor.advantage < -1e-9 ? "classical" : "quantum";
    helper("circle", { cx: String(xScale(1)), cy: String(ay), r: "5", class: `anchor anchor-${sign}` });
    const when = anchor.date ? String(anchor.date).slice(0, 10) : "";
    const tag = `R${anchorIndex + 1}`;
    helper("text", { x: String(xScale(1) - 18), y: String(ay + 4), class: "series-label" }, tag);
    helper("text", {
      x: String(CHART_W - PAD.right), y: String(PAD.top + 10 + 13 * anchorIndex),
      class: "series-label", "text-anchor": "end",
    }, `${tag}: ${MODEL_LABELS[anchor.model] || anchor.model} RECORDED · ${anchor.shots} shots · ${when}`);
    anchorIndex += 1;
  }

  if (state.live) {
    const liveS = state.live.source.indexOf("built-in") >= 0 ? 0 : 1;
    const ly = yScale(state.live[game].advantage, yMax, yMin);
    const lx = xScale(liveS);
    helper("polygon", {
      points: `${lx},${ly - 5} ${lx + 5},${ly + 4} ${lx - 5},${ly + 4}`,
      class: "live-mark",
    });
    helper("text", { x: String(lx + 7), y: String(ly - 6), class: "series-label" }, "LIVE");
  }

  const slider = line(0, 0, 0, 0, "slider-line");
  slider.setAttribute("x1", String(xScale(state.noise)));
  slider.setAttribute("x2", String(xScale(state.noise)));
  slider.setAttribute("y1", String(PAD.top));
  slider.setAttribute("y2", String(CHART_H - PAD.bottom));
  slider.setAttribute("id", `slider-line-${game}`);

  helper("text", { x: String(CHART_W / 2), y: String(CHART_H - 8), class: "axis-label" },
    "noise scale s  (0 = noiseless · 1 = today's IonQ noise · 2 = twice today's)");
  for (const t of [0, 0.5, 1, 1.5, 2]) {
    helper("text", {
      x: String(xScale(t) - 6), y: String(CHART_H - PAD.bottom + 14), class: "tick-label",
    }, String(t));
  }
  helper("text", { x: String(PAD.left - 8), y: String(PAD.top + 10), class: "axis-label" }, "advantage");

  box.appendChild(svg);
  renderLegend(game);
}

function renderLegend(game) {
  const legend = $(`legend-${game}`);
  legend.innerHTML = "";
  const items = [
    { shape: "—", style: "background:#0B5CAD;height:3px;width:16px;", label: `${MODEL_LABELS[state.selectedModel]} local model (± CI band)` },
    { shape: "●", style: "color:#1F6B3A;", label: "recorded IonQ advantage (>0)" },
    { shape: "●", style: "color:#9B1C1C;", label: "recorded IonQ advantage (<0)" },
    { shape: "▲", style: "color:#0B5CAD;", label: "live run" },
    { shape: "◆", style: "color:#C2410C;", label: "crossover s* (CI band)" },
    { shape: "- -", style: "color:#CBD5E1;", label: "advantage = 0" },
  ];
  for (const item of items) {
    const el = document.createElement("span");
    el.className = "legend-item";
    el.innerHTML = `<span class="legend-shape" style="${item.style}">${item.shape}</span>${item.label}`;
    legend.appendChild(el);
  }
}

function rebuildTable(game) {
  const entry = state.evidence.games[game][state.selectedModel];
  const body = $(`table-${game}`).querySelector("tbody");
  body.innerHTML = "";
  const rows = entry.grid.map((s, i) => {
    const adv = entry.advantage[i];
    const lo = entry.lower ? entry.lower[i] : null;
    const hi = entry.upper ? entry.upper[i] : null;
    const next = entry.grid[i + 1];
    const isCross = entry.crossing !== null && entry.crossing >= s &&
      (next === undefined || entry.crossing < next);
    return { s, adv, lo, hi, cross: isCross ? entry.crossing : null };
  });
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row.s.toFixed(2)}</td><td>${fmt(row.adv)}</td>` +
      `<td>${row.lo === null ? "—" : fmt(row.lo)}</td><td>${row.hi === null ? "—" : fmt(row.hi)}</td>` +
      `<td>${row.cross === null ? "—" : row.cross.toFixed(3)}</td><td>${MODEL_LABELS[state.selectedModel]}</td>`;
    body.appendChild(tr);
  }
  for (const anchor of state.evidence.anchors) {
    if (anchor.game !== game) continue;
    const tr = document.createElement("tr");
    const sign = anchor.advantage > 1e-9 ? "quantum" : anchor.advantage < -1e-9 ? "classical" : "tie";
    tr.innerHTML = `<td>1.00</td><td>${fmt(anchor.advantage)}</td><td>—</td><td>—</td>` +
      `<td>—</td><td>${MODEL_LABELS[anchor.model]} · RECORDED· ${sign}</td>`;
    body.appendChild(tr);
  }
  if (state.live) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${state.live.source.indexOf("built-in") >= 0 ? "0.00" : "1.00"}</td>` +
      `<td>${fmt(state.live[game].advantage)}</td><td>—</td><td>—</td><td>—</td><td>LIVE · ${state.live.model || "built-in simulator"}</td>`;
    body.appendChild(tr);
  }
}

function renderMeaning() {
  const meaning = state.evidence.meaning || tax.get_meaning();
  $("meaning-text").textContent = meaning;
}

function renderLabels() {
  const dl = $("label-legend");
  dl.innerHTML = "";
  for (const label of state.evidence.labels) {
    const dt = document.createElement("dt");
    dt.textContent = label.label;
    const dd = document.createElement("dd");
    dd.textContent = label.meaning;
    dl.appendChild(dt);
    dl.appendChild(dd);
  }
}

function renderAnchors() {
  const ul = $("anchor-receipts");
  ul.innerHTML = "";
  for (const anchor of state.evidence.anchors) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${MODEL_LABELS[anchor.model] || anchor.model}</strong> (${anchor.game}) — ` +
      `advantage ${fmt(anchor.advantage)}, ${anchor.shots} shots, ${anchor.date}<span class="secondary"> — ${anchor.detail}</span>`;
    ul.appendChild(li);
  }
}

function renderCircuit() {
  const info = state.circuits ? state.circuits[state.selectedGame] : null;
  const pre = $("circuit-text");
  if (!info) {
    pre.textContent = "Circuit text is still loading…";
    return;
  }
  pre.textContent = `${info.title}\n\nSTAGES\n` + info.stages.map((s) => `- ${s}`).join("\n") +
    `\n\n${info.text}\n\n${info.diagram}`;
}

async function loadGateCosts() {
  const data = state.gateCosts ? state.gateCosts[state.selectedGame] : null;
  if (!data) return;
  $("gate-summary").textContent = data.summary;
  const ul = $("gate-facts");
  ul.innerHTML = "";
  for (const fact of data.ionq_facts) {
    const li = document.createElement("li");
    li.textContent = fact;
    ul.appendChild(li);
  }
  for (const [model, counts] of Object.entries(data.compiled_effective_gates)) {
    const li = document.createElement("li");
    li.textContent = `${MODEL_LABELS[model]} compiled effective gates (local model): ` +
      Object.entries(counts).map(([gate, count]) => `${gate}=${count}`).join(" ");
    ul.appendChild(li);
  }
}

function announceCard() {
  const w = $(`badge-W`).textContent;
  const n = $(`badge-N`).textContent;
  setStatus(`Noise scale ${state.noise.toFixed(2)}: Two Whispers ${w}, Never Lose Twice ${n}.`);
}

async function runLiveDiff() {
  const loader = $("loading");
  loader.hidden = false;
  $("loading-text").textContent = "Running the live demo job on this backend…";
  try {
    const result = await tax.run_demo.callPromising(backend, 512, state.selectedModel);
    state.live = result;
    loader.hidden = true;
    $("loading-text").textContent = `Live job ${result.backend_name} done (${result.shots} shots).`;
    renderCardValues();
    for (const game of GAMES) {
      $(`live-${game}`).textContent =
        `LIVE (${result.model || "built-in simulator, noiseless"}, ${result.shots} shots): ${fmt(result[game].advantage)}`;
    }
    announceCard();
  } catch (error) {
    loader.hidden = true;
    showError("Live run failed: " + (error && error.message ? error.message : String(error)));
  }
}

async function init() {
  setStatus("The Noise Tax is loading…");
  state.evidence = await tax.get_evidence.callPromising();
  try {
    state.circuits = {
      W: await tax.get_circuit_text.callPromising("W"),
      N: await tax.get_circuit_text.callPromising("N"),
    };
  } catch (error) {
    state.circuits = null;
  }
  try {
    state.gateCosts = {
      W: await tax.get_gate_costs.callPromising("W"),
      N: await tax.get_gate_costs.callPromising("N"),
    };
  } catch (error) {
    state.gateCosts = null;
  }

  const name = typeof backend.name === "function" ? backend.name() : backend.name;
  state.backendName = name;

  renderMeaning();
  renderLabels();
  renderAnchors();
  renderCircuit();
  loadGateCosts();
  setSliderLabel();
  renderCardValues();
  $("loading").hidden = true;
  $("loading-text").textContent = "Loaded.";

  announceCard();

  if (name === "basic_simulator") {
    await runLiveDiff();
  } else {
    const panel = $("run-panel");
    const keepOpen = document.createElement("button");
    keepOpen.type = "button";
    keepOpen.id = "keep-open-btn";
    keepOpen.textContent = "Run one packed IonQ job (both games)";
    keepOpen.classList.add("keep-open");
    panel.appendChild(keepOpen);
    panel.hidden = false;
    setStatus("IonQ backend selected. Press the run button to send exactly one packed job.");
    await new Promise((resolve) => {
      keepOpen.addEventListener("click", async () => {
        keepOpen.disabled = true;
        await runLiveDiff();
        keepOpen.textContent = "IonQ job finished (one job sent)";
        resolve();
      }, { once: true });
    });
  }
}

$("noise-slider").addEventListener("input", (event) => {
  state.noise = Number(event.target.value);
  setSliderLabel();
  renderCardValues();
  announceCard();
});

$("model-select").addEventListener("change", (event) => {
  state.selectedModel = event.target.value;
  renderCardValues();
  announceCard();
});

for (const game of GAMES) {
  $(`gamebtn-${game}`).addEventListener("click", () => {
    state.selectedGame = game;
    for (const other of GAMES) {
      $(`gamebtn-${other}`).classList.toggle("selected", other === game);
      $(`gamebtn-${other}`).setAttribute("aria-pressed", String(other === game));
    }
    renderCircuit();
    loadGateCosts();
  });
}

window.addEventListener("error", (event) => {
  showError(event.message || "Uncaught page error.");
});

init().catch((error) => {
  showError("Initialization failed: " + (error && error.message ? error.message : String(error)));
});