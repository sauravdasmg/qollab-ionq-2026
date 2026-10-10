import * as eyes from "eyes_bridge";

const $ = (id) => document.getElementById(id);
const select = $("fringe"), status = $("status"), summary = $("summary");
const rows = $("results"), circuit = $("circuit");
let records = [], current = null, audioContext = null, oscillator = null, gain = null;

function cleanNumber(value, digits = 3) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "unavailable";
}

function addRecord(raw, fallback = "LOCAL MODEL") {
  const record = raw;
  record.source = record.source || fallback;
  record.n = Number(record.n);
  if (record.frequency == null || record.contrast == null) return;
  record.frequency = Number(record.frequency);
  record.contrast = Number(record.contrast);
  if (![1, 2, 4].includes(record.n) || !Number.isFinite(record.frequency) || !Number.isFinite(record.contrast)) return;
  const index = records.findIndex(item => item.id === record.id);
  if (index >= 0) records[index] = record; else records.push(record);
}

function render() {
  const previousId = current?.id;
  select.replaceChildren(); rows.replaceChildren();
  records.forEach((r, i) => {
    const option = document.createElement("option"); option.value = String(i);
    option.textContent = `${r.source} · n=${r.n} · scale ${r.scale ?? "—"}`; select.append(option);
    const tr = document.createElement("tr");
    [r.source, r.n, r.scale ?? "—", cleanNumber(r.frequency), cleanNumber(r.contrast), interval(r.frequency_ci), interval(r.contrast_ci), r.status || "measured"].forEach(value => {
      const td = document.createElement("td"); td.textContent = String(value); tr.append(td);
    }); rows.append(tr);
  });
  const preferred = records.findIndex(r => r.id === previousId);
  const defaultIndex = records.findIndex(r => r.source === "RECORDED" && r.n === 4);
  select.value = String(preferred >= 0 ? preferred : Math.max(0, defaultIndex));
  if (records.length) select.dispatchEvent(new Event("change"));
}

function interval(value) { return Array.isArray(value) ? `[${value.map(v => cleanNumber(v, 6)).join(", ")}]` : "unavailable (reference)"; }

function selected() { return records[Number(select.value)] || records[0]; }
function sentence(r) { return `${r.source}: ${r.n} qubit${r.n === 1 ? "" : "s"}; ${r.status?.includes("reference") ? "reference frequency" : "fitted frequency"} ${cleanNumber(r.frequency)} cycles per 2*pi radians of phase; contrast ${cleanNumber(r.contrast)} (unitless). Frequency interval ${interval(r.frequency_ci)}; contrast interval ${interval(r.contrast_ci)}; status ${r.status}.`; }
function updateSelection() {
  current = selected(); if (!current) return;
  summary.textContent = sentence(current);
  $("fit-details").textContent = JSON.stringify(current, null, 2);
  $("transcript").textContent = sentence(current);
  drawChart(current);
  circuit.textContent = current.circuit || `GHZ preparation on ${current.n} qubit(s), phase rotation on each qubit, X-basis parity measurement.`;
}

function drawChart(r) {
  const svg = $("parity-chart"); svg.replaceChildren();
  const table = $("parity-results"); table.replaceChildren();
  if (!Array.isArray(r.phases_rad) || !Array.isArray(r.parity)) {
    $("chart-note").textContent = "Illustrative reference: no measured parity chart available."; return;
  }
  const ns = "http://www.w3.org/2000/svg";
  const title = document.createElementNS(ns, "title"); title.textContent = sentence(r); svg.append(title);
  const xmax = Math.max(2 * Math.PI, ...r.phases_rad);
  const x = p => 45 + p / xmax * 510;
  const y = p => 110 - p * 85;
  function element(tag, attributes, text) {
    const node = document.createElementNS(ns, tag);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
    if (text !== undefined) node.textContent = text;
    svg.append(node); return node;
  }
  [-1, 0, 1].forEach(value => {
    element("line", {x1: 45, x2: 555, y1: y(value), y2: y(value), stroke: "#D4D4CF"});
    element("text", {x: 5, y: y(value) + 5, fill: "#111111", "font-size": 14}, value);
  });
  element("text", {x: 45, y: 217, fill: "#111111", "font-size": 14}, "0");
  element("text", {x: 430, y: 217, fill: "#111111", "font-size": 14}, "Phase (radians): 2π");
  const curve = Array.from({length: 241}, (_, i) => {
    const phase = i / 240 * xmax;
    const prediction = r.offset + r.cos_coefficient * Math.cos(r.frequency * phase) + r.sin_coefficient * Math.sin(r.frequency * phase);
    return `${x(phase)},${y(prediction)}`;
  });
  element("polyline", {points: curve.join(" "), fill: "none", stroke: "#4B2E83", "stroke-width": 2});
  r.phases_rad.forEach((phase, i) => {
    const parity = r.parity[i], shots = r.shots[i];
    const bounds = parityInterval(parity, shots);
    if (bounds) {
      element("line", {x1: x(phase), x2: x(phase), y1: y(bounds[0]), y2: y(bounds[1]), stroke: "#111111"});
      bounds.forEach(bound => element("line", {x1: x(phase) - 4, x2: x(phase) + 4, y1: y(bound), y2: y(bound), stroke: "#111111"}));
    }
    element("circle", {cx: x(phase), cy: y(parity), r: 4, fill: "#111111"});
    const tr = document.createElement("tr");
    [cleanNumber(phase, 6), cleanNumber(parity, 6), shots, bounds ? interval(bounds) : "Exact model; no sampling"].forEach(value => {
      const td = document.createElement("td"); td.textContent = String(value); tr.append(td);
    }); table.append(tr);
  });
  $("chart-note").textContent = r.source === "LOCAL MODEL"
    ? "Analytic model points and curve; no sampled counts or statistical error bars."
    : "Measured parity (-1 to 1) versus phase (radians). Points show pointwise 95% Wilson intervals; purple curve is the fitted offset + cosine + sine model. Fit parameter intervals are in the results table.";
}

function parityInterval(parity, shots) {
  if (!(shots > 0)) return null;
  const z = 1.959963984540054, p = (1 + parity) / 2;
  const denominator = 1 + z * z / shots;
  const center = (p + z * z / (2 * shots)) / denominator;
  const radius = z * Math.sqrt(p * (1 - p) / shots + z * z / (4 * shots * shots)) / denominator;
  return [Math.max(-1, 2 * (center - radius) - 1), Math.min(1, 2 * (center + radius) - 1)];
}

function stopSound() {
  if (oscillator) { const previous = oscillator; oscillator = null; previous.onended = null; try { previous.stop(); } catch (_) {} previous.disconnect(); }
  if (gain) { gain.disconnect(); gain = null; }
  if (status.textContent === "Playing fringe audio.") status.textContent = "Playback stopped.";
}

async function play() {
  updateSelection(); if (!current) return;
  const text = sentence(current); $("transcript").textContent = text;
  if ("speechSynthesis" in window) {
    try { speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance(text)); } catch (_) {}
  }
  const Audio = window.AudioContext || window.webkitAudioContext;
  if (!Audio) { status.textContent = "Web Audio is unavailable. Transcript remains available; WAV download requires sendFile."; return; }
  try {
    if (!audioContext) audioContext = new Audio();
    await audioContext.resume(); stopSound();
    oscillator = audioContext.createOscillator(); gain = audioContext.createGain();
    oscillator.type = "sine"; oscillator.frequency.value = 220 * current.frequency;
    const now = audioContext.currentTime;
    const amplitude = 0.5 * Math.max(0, Math.min(1, current.contrast)) * Number($("volume").value);
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(amplitude, now + 0.05);
    gain.gain.setValueAtTime(amplitude, now + 1.95);
    gain.gain.linearRampToValueAtTime(0, now + 2);
    oscillator.connect(gain); gain.connect(audioContext.destination); oscillator.start();
    status.textContent = "Playing fringe audio.";
    oscillator.stop(audioContext.currentTime + 2);
    oscillator.onended = () => { stopSound(); status.textContent = "Playback complete."; };
  } catch (error) { stopSound(); status.textContent = `Audio could not start: ${error.message}. Use the transcript; WAV export requires sendFile.`; }
}

async function downloadWav() {
  updateSelection(); if (!current) return;
  try {
    if (typeof sendFile === "function") {
      const wav = JSON.parse(String(await eyes.make_wav.callPromising(current.frequency, current.contrast)));
      await sendFile("eyes-free.wav", wav.mime_type, new Uint8Array(wav.bytes));
      status.textContent = "WAV download prepared.";
    } else { status.textContent = "Download bridge unavailable; live playback and transcript remain available."; }
  } catch (error) { status.textContent = `WAV export failed: ${error.message}`; }
}

select.addEventListener("change", updateSelection);
$("play").addEventListener("click", play);
$("replay").addEventListener("click", play);
$("stop").addEventListener("click", () => { stopSound(); if ("speechSynthesis" in window) speechSynthesis.cancel(); });
$("download").addEventListener("click", downloadWav);
$("volume").addEventListener("input", event => { $("volume-value").value = `${Math.round(Number(event.target.value) * 100)}%`; if (gain) gain.gain.value = 0.5 * (current?.contrast || 0) * Number(event.target.value); });

async function initialize(backend) {
  try {
    for (const raw of JSON.parse(String(await eyes.recorded_fringe.callPromising()))) addRecord(raw, "RECORDED");
    for (const raw of JSON.parse(String(eyes.fringe_catalog()))) addRecord(raw);
    render();
    if (backend && !JSON.parse(String(eyes.is_ionq_backend(backend)))) {
      status.textContent = "Running small ideal circuits on the built-in simulator…";
      try { for (const raw of JSON.parse(String(await eyes.live_fringe.callPromising(backend, 256)))) addRecord(raw, "LIVE"); }
      catch (error) { status.textContent = `Live simulator unavailable: ${error.message}. Local model records are shown.`; }
    }
    render(); if (status.textContent.includes("Loading")) status.textContent = "Ready. Choose a fringe and press Play.";
    else if (records.length) status.textContent += " Local and recorded examples are ready.";
  } catch (error) { status.textContent = `Initialization failed: ${error.message}`; }
}

const injectedBackend = typeof backend === "undefined" ? null : backend;
const ionqAvailable = injectedBackend && JSON.parse(String(eyes.is_ionq_backend(injectedBackend)));
$("ionq").hidden = !ionqAvailable;
$("ionq-note").hidden = !ionqAvailable;
$("download").hidden = typeof sendFile !== "function";
await initialize(injectedBackend);

// Keep the run open for exactly one optional packed IonQ job. The local page remains usable if no click occurs.
if (ionqAvailable && $("ionq")) {
  try {
    await new Promise(resolve => $("ionq").addEventListener("click", async () => {
      const button = $("ionq"); button.disabled = true; status.textContent = "Submitting the single packed IonQ sample…";
      try {
        const result = JSON.parse(String(await eyes.ionq_sample.callPromising(backend, 128)));
        $("fit-details").textContent = JSON.stringify(result, null, 2);
        status.textContent = "LIVE partial IonQ parity sample received; no frequency or contrast fit. Recorded sweeps remain available.";
      } catch (error) { status.textContent = `IonQ sample failed: ${error.message}`; }
      finally { button.disabled = false; resolve(); }
    }, { once: true }));
  } catch (_) {}
}

