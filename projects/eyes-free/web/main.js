import * as eyes from "eyes_bridge";

const $ = (id) => document.getElementById(id);
const select = $("fringe"), status = $("status"), summary = $("summary");
const rows = $("results"), circuit = $("circuit");
let records = [], current = null, audioContext = null, oscillator = null, gain = null, lastUrl = null;

function cleanNumber(value, digits = 3) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "unavailable";
}

function addRecord(raw, fallback = "LOCAL MODEL") {
  const record = { ...raw, source: raw.source || fallback };
  record.n = Number(record.n);
  if (record.frequency == null || record.contrast == null) return;
  record.frequency = Number(record.frequency);
  record.contrast = Number(record.contrast);
  if (![1, 2, 4].includes(record.n) || !Number.isFinite(record.frequency) || !Number.isFinite(record.contrast)) return;
  const index = records.findIndex(item => item.id === record.id);
  if (index >= 0) records[index] = record; else records.push(record);
}

function render() {
  select.replaceChildren(); rows.replaceChildren();
  records.forEach((r, i) => {
    const option = document.createElement("option"); option.value = String(i);
    option.textContent = `${r.source} · n=${r.n} · scale ${r.scale ?? "—"}`; select.append(option);
    const tr = document.createElement("tr");
    [r.source, r.n, r.scale ?? "—", cleanNumber(r.frequency), cleanNumber(r.contrast), interval(r.frequency_ci), interval(r.contrast_ci), r.status || "measured"].forEach(value => {
      const td = document.createElement("td"); td.textContent = String(value); tr.append(td);
    }); rows.append(tr);
  });
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
  if (!Array.isArray(r.phases_rad) || !Array.isArray(r.parity)) {
    $("chart-note").textContent = "Illustrative reference: no measured parity chart available."; return;
  }
  const ns = "http://www.w3.org/2000/svg";
  const title = document.createElementNS(ns, "title"); title.textContent = sentence(r); svg.append(title);
  const poly = document.createElementNS(ns, "polyline");
  poly.setAttribute("points", r.phases_rad.map((p, i) => `${30 + Number(p) / (2 * Math.PI) * 520},${110 - Number(r.parity[i]) * 90}`).join(" "));
  poly.setAttribute("fill", "none"); poly.setAttribute("stroke", "#4B2E83"); poly.setAttribute("stroke-width", "3"); svg.append(poly);
  $("chart-note").textContent = "Measured parity (vertical, -1 to 1) versus phase (horizontal, 0 to 2*pi radians). This chart does not show fit intervals; the table and full text do.";
}

function stopSound() {
  if (oscillator) { const previous = oscillator; oscillator = null; previous.onended = null; try { previous.stop(); } catch (_) {} previous.disconnect(); }
  if (gain) { gain.disconnect(); gain = null; }
  if (status.textContent === "Playing fringe audio.") status.textContent = "Playback stopped.";
}

async function play() {
  updateSelection(); if (!current) return;
  if (current.informative === false) { status.textContent = "Inconclusive fit: use full text details; no sound offered."; return; }
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

function downloadWav() {
  updateSelection(); if (!current) return;
  if (current.informative === false) { status.textContent = "Inconclusive fit: no WAV offered."; return; }
  try {
    if (typeof sendFile === "function") {
      Promise.resolve(eyes.make_wav.callPromising ? eyes.make_wav.callPromising(current.frequency, current.contrast) : eyes.make_wav(current.frequency, current.contrast))
        .then(bytes => sendFile("eyes-free.wav", "audio/wav", bytes)).then(() => { status.textContent = "WAV download prepared."; })
        .catch(error => { status.textContent = `WAV export failed: ${error.message}`; });
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
    for (const raw of eyes.recorded_fringe()) addRecord(raw, "RECORDED");
    for (const raw of eyes.fringe_catalog()) addRecord(raw);
    if (backend && !eyes.is_ionq_backend(backend)) {
      status.textContent = "Running small ideal circuits on the built-in simulator…";
      try { for (const raw of await eyes.live_fringe.callPromising(backend, 256)) addRecord(raw, "LIVE"); }
      catch (error) { status.textContent = `Live simulator unavailable: ${error.message}. Local model records are shown.`; }
    }
    render(); if (status.textContent.includes("Loading")) status.textContent = "Ready. Choose a fringe and press Play.";
    else if (records.length) status.textContent += " Local and recorded examples are ready.";
  } catch (error) { status.textContent = `Initialization failed: ${error.message}`; }
}

initialize(typeof backend === "undefined" ? null : backend);

// Keep the run open for exactly one optional packed IonQ job. The local page remains usable if no click occurs.
if (typeof backend !== "undefined" && eyes.is_ionq_backend(backend) && $("ionq")) {
  try {
    await new Promise(resolve => $("ionq").addEventListener("click", async () => {
      const button = $("ionq"); button.disabled = true; status.textContent = "Submitting the single packed IonQ sample…";
      try {
        const result = await eyes.ionq_sample.callPromising(backend, 128);
        $("fit-details").textContent = JSON.stringify(result, null, 2);
        status.textContent = "LIVE partial IonQ parity sample received; no frequency or contrast fit. Recorded sweeps remain available.";
      } catch (error) { status.textContent = `IonQ sample failed: ${error.message}`; }
      finally { button.disabled = false; resolve(); }
    }, { once: true }));
  } catch (_) {}
}

if (typeof backend === "undefined" || !eyes.is_ionq_backend(backend)) $("ionq").disabled = true;
