import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eyes_bridge

ROOT = Path(__file__).resolve().parents[1]


def decode(value):
    assert isinstance(value, str)
    return json.loads(value)


def assert_fringe(record):
    for key in ("frequency", "contrast", "offset", "cos_coefficient", "sin_coefficient"):
        assert isinstance(record[key], (int, float)) and np.isfinite(record[key])
    for key in ("frequency_ci", "contrast_ci"):
        assert len(record[key]) == 2
        assert record[key][0] <= record[key[:-3]] <= record[key][1]
    for key in ("parity", "shots", "shots_per_phase", "phases_rad"):
        assert isinstance(record[key], list) and len(record[key]) == 12
    assert record["shots"] == record["shots_per_phase"]
    assert all(-1 <= value <= 1 for value in record["parity"])


def test_catalog_and_wav():
    records = decode(eyes_bridge.fringe_catalog())
    assert len(records) == 12
    assert {r["n"] for r in records} == {1, 2, 4}
    assert all(r["source"] == "LOCAL MODEL" for r in records)
    for r in records:
        assert_fringe(r)
        assert r["shots"] == [0] * 12
        np.testing.assert_allclose(r["parity"], r["contrast"] * np.cos(r["n"] * np.array(r["phases_rad"])))
    wav = decode(eyes_bridge.make_wav(2, 0.5))
    assert wav["mime_type"] == "audio/wav"
    data = bytes(wav["bytes"])
    assert data[:4] == b"RIFF"
    with wave.open(io.BytesIO(data)) as stream:
        assert stream.getnframes() == 96000 and stream.getframerate() == 48000
    assert "LOCAL MODEL" in decode(eyes_bridge.receipt_text(json.dumps(records[0])))


def test_actual_recorded_cloud_fits_are_js_catalog_records():
    records = decode(eyes_bridge.recorded_fringe())
    expected = json.loads((ROOT / "results/cloud_fit.json").read_text(encoding="utf-8"))["combined"]["suites"]
    assert len(records) == 6
    assert {r["source"] for r in records} == {"RECORDED"}
    assert {r["suite"] for r in records} == {"frozen", "fresh"}
    for r in records:
        assert_fringe(r)
        saved = expected[r["suite"]]["fits"][str(r["n"])]
        for key in ("frequency", "contrast", "frequency_ci", "contrast_ci", "offset", "cos_coefficient", "sin_coefficient", "parity", "phases_rad", "shots"):
            np.testing.assert_allclose(r[key], saved[key], rtol=0, atol=1e-6)
        assert r["informative"] and abs(r["frequency"] - r["n"]) < .03
        assert r["frequency_ci"][0] <= r["frequency"] <= r["frequency_ci"][1]
        assert len(r["source_files"]) == 4 and r["shots_per_phase"] == [1000] * 12
        assert r["source"] in decode(eyes_bridge.receipt_text(json.dumps(r)))


def test_live_counts_and_backend_gating(monkeypatch):
    calls = []
    def submit(circuits, shots):
        calls.append((circuits, shots))
        output = []
        for n in (1, 2, 4):
            for phase in eyes_bridge.eyes_core.PHASES:
                even = round(shots * (1 + np.cos(n * phase)) / 2)
                output.append({"0" * n: even, "0" * (n - 1) + "1": shots - even})
        return output
    monkeypatch.setattr(eyes_bridge.main, "_submit_job", submit)
    backend = SimpleNamespace(name="builtin")
    assert decode(eyes_bridge.is_ionq_backend(backend)) is False
    records = decode(eyes_bridge.live_fringe(backend, 256))
    assert len(calls) == 1 and len(calls[0][0]) == 36
    assert len(records) == 3
    for r in records:
        assert r["source"] == "LIVE"
        assert_fringe(r)
        assert r["shots"] == [256] * 12
        assert abs(r["frequency"] - r["n"]) < .03
    options = []
    backend = SimpleNamespace(name="ionq_simulator", set_options=lambda **kw: options.append(kw))
    assert decode(eyes_bridge.is_ionq_backend(backend)) is True
    monkeypatch.setattr(eyes_bridge.main, "_submit_job", lambda circuit, shots: {"0" * 21: shots})
    sample = decode(eyes_bridge.ionq_sample(backend))
    assert sample[0]["frequency"] is None and sample[0]["contrast"] is None
    assert sample[0]["parity"] == 1 and "partial" in sample[0]["status"]
    assert options == [{"noise_model": "aria-1"}]


def test_js_bridge_calls_are_parsed_json_and_syntax():
    source = (ROOT / "web/main.js").read_text(encoding="utf-8")
    assert not re.search(r"\.\.\.\s*raw\b", source)
    calls = re.findall(r"eyes\.\w+(?:\.callPromising)?\(", source)
    parsed_calls = re.findall(r"JSON\.parse\(String\((?:await\s+)?eyes\.\w+(?:\.callPromising)?\(", source)
    assert calls and len(calls) == len(parsed_calls)
    assert 'r.source === "RECORDED" && r.n === 4' in source
    assert '$("download").hidden = typeof sendFile !== "function"' in source
    assert '$("ionq").hidden = !ionqAvailable' in source
    assert "parityInterval" in source and 'element("circle"' in source
    node = shutil.which("node")
    assert node, "node is required for the JavaScript syntax check"
    with tempfile.TemporaryDirectory(dir=ROOT / "web", prefix=".syntax-check-") as folder:
        copy = Path(folder) / "main.mjs"
        copy.write_text(source, encoding="utf-8")
        result = subprocess.run([node, "--check", str(copy)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_web_sources_are_utf8_without_bom():
    for name in ("main.js", "index.html", "eyes_bridge.py", "test_bridge.py"):
        data = (ROOT / "web" / name).read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf")
        assert not re.search(r"^from __future__ import", data.decode("utf-8"), re.MULTILINE)


def test_page_charts_and_plays_all_sources():
    """Exercise parsed data, selection, chart DOM and Web Audio without a browser."""
    saved = json.loads((ROOT / "results/cloud_fit.json").read_text(encoding="utf-8"))["combined"]["suites"]
    recorded = []
    for suite, values in saved.items():
        for n, estimate in values["fits"].items():
            r = dict(estimate, id=f"recorded-{suite}-{n}", source="RECORDED", n=int(n), scale="aria-1", status="informative")
            recorded.append(r)
    local = decode(eyes_bridge.fringe_catalog())
    live = [dict(r, id=f"live-{r['n']}", source="LIVE") for r in recorded[:3]]
    payload = json.dumps({"recorded": recorded, "local": local, "live": live})
    harness = r'''
import assert from "node:assert/strict";
class Element {
  constructor() { this.children = []; this.listeners = {}; this.value = ""; this.textContent = ""; this.hidden = false; this.attributes = {}; }
  replaceChildren() { this.children = []; }
  append(child) { this.children.push(child); }
  addEventListener(event, callback) { this.listeners[event] = callback; }
  dispatchEvent(event) { return this.listeners[event.type]?.(event); }
  setAttribute(key, value) { this.attributes[key] = value; }
}
const elements = new Map();
globalThis.document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
  createElement() { return new Element(); }, createElementNS() { return new Element(); }
};
document.getElementById("volume").value = "0.5";
document.getElementById("status").textContent = "Loading";
const tones = [], spoken = [];
class AudioContext {
  constructor() { this.currentTime = 0; this.destination = {}; }
  async resume() {}
  createOscillator() { const o = {frequency: {}, connect() {}, disconnect() {}, start() { tones.push(this.frequency.value); }, stop() {}}; return o; }
  createGain() { return {gain: {setValueAtTime() {}, linearRampToValueAtTime() {}}, connect() {}, disconnect() {}}; }
}
globalThis.window = {AudioContext, speechSynthesis: {}};
globalThis.speechSynthesis = {cancel() {}, speak(value) { spoken.push(value.text); }};
globalThis.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
globalThis.backend = {name: "builtin"};
const bridge = value => ({toString() { return JSON.stringify(value); }});
const eyes = {
  recorded_fringe: {callPromising: async () => bridge(payload.recorded)},
  fringe_catalog: () => bridge(payload.local),
  live_fringe: {callPromising: async () => bridge(payload.live)},
  is_ionq_backend: () => bridge(false)
};
'''
    source = (ROOT / "web/main.js").read_text(encoding="utf-8").replace('import * as eyes from "eyes_bridge";', "")
    checks = r'''
assert.equal(records.length, 21);
assert.equal(current.source, "RECORDED"); assert.equal(current.n, 4);
assert.equal(document.getElementById("ionq").hidden, true);
assert.equal(document.getElementById("download").hidden, true);
for (let i = 0; i < records.length; i++) {
  select.value = String(i); updateSelection();
  const chart = document.getElementById("parity-chart");
  assert.equal(chart.children.filter(node => node.attributes.r === "4").length, 12);
  assert.equal(document.getElementById("parity-results").children.length, 12);
  const curve = chart.children.find(node => node.attributes.points);
  assert.equal(curve.attributes.points.split(" ").length, 241);
  assert.ok(!curve.attributes.points.includes("NaN"));
  if (current.source !== "LOCAL MODEL") assert.ok(chart.children.filter(node => node.attributes.stroke === "#111111").length >= 36);
  await document.getElementById("play").listeners.click();
  assert.equal(tones.at(-1), 220 * current.frequency);
  assert.ok(spoken.at(-1).includes(current.source));
}
const edge = parityInterval(1, 1000);
assert.ok(edge[0] < 1 && edge[1] <= 1);
assert.equal(parityInterval(1, 0), null);
'''
    with tempfile.TemporaryDirectory(dir=ROOT / "web", prefix=".page-check-") as folder:
        script = Path(folder) / "page.mjs"
        script.write_text("const payload = " + payload + ";\n" + harness + source + checks, encoding="utf-8")
        result = subprocess.run([shutil.which("node"), str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
