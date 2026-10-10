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
    [r.source, r.n, r.scale ?? "—", cleanNumber(r.frequency), cleanNumber(r.contrast), r.status || "measured"].forEach(value => {
      const td = document.createElement("td"); td.textContent = String(value); tr.append(td);
    }); rows.append(tr);
  });
  if (records.length) select.dispatchEvent(new Event("change"));
}

function selected() { return records[Number(select.value)] || records[0]; }
function sentence(r) { return `${r.source}: ${r.n} qubit${r.n === 1 ? "" : "s"}; fitted frequency ${cleanNumber(r.frequency)} cycles per phase unit; contrast ${cleanNumber(r.contrast)}.`; }
function updateSelection() {
  current = selected(); if (!current) return;
  summary.textContent = sentence(current);
  circuit.textContent = current.circuit || `GHZ preparation on ${current.n} qubit(s), phase rotation on each qubit, X-basis parity measurement.`;
}

function stopSound() {
  if (oscillator) { try { oscillator.stop(); } catch (_) {} oscillator.disconnect(); oscillator = null; }
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
  if (!Audio) { status.textContent = "Web Audio is unavailable. Use Download WAV; transcript remains available."; return; }
  try {
    if (!audioContext) audioContext = new Audio();
    await audioContext.resume(); stopSound();
    oscillator = audioContext.createOscillator(); gain = audioContext.createGain();
    oscillator.type = "sine"; oscillator.frequency.value = Math.max(110, Math.min(990, 220 * current.frequency));
    gain.gain.value = 0.5 * Math.max(0, Math.min(1, current.contrast)) * Number($("volume").value);
    oscillator.connect(gain); gain.connect(audioContext.destination); oscillator.start();
    status.textContent = "Playing fringe audio.";
    oscillator.stop(audioContext.currentTime + 2);
    oscillator.onended = () => { stopSound(); status.textContent = "Playback complete."; };
  } catch (error) { stopSound(); status.textContent = `Audio could not start: ${error.message}. Download the WAV instead.`; }
}

function downloadWav() {
  updateSelection(); if (!current) return;
  try {
    const data = eyes.make_wav.callPromising ? null : null;
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
    for (const raw of eyes.fringe_catalog()) addRecord(raw);
    for (const raw of eyes.recorded_fringe()) addRecord(raw, "RECORDED");
    if (backend && typeof backend.run === "function") {
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
if (typeof backend !== "undefined" && $("ionq")) {
  try {
    await new Promise(resolve => $("ionq").addEventListener("click", async () => {
      const button = $("ionq"); button.disabled = true; status.textContent = "Submitting the single packed IonQ sample…";
      try {
        const result = await eyes.ionq_sample.callPromising(backend, 128);
        for (const raw of result) addRecord({ ...raw, source: "LIVE" }); render();
        status.textContent = "IonQ result received and labeled LIVE.";
      } catch (error) { status.textContent = `IonQ sample failed: ${error.message}`; }
      finally { button.disabled = false; resolve(); }
    }, { once: true }));
  } catch (_) {}
}
