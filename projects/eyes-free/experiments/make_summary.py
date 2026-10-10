"""Create compact, source-hashed evidence summary from saved local results."""
import hashlib
import json
import platform
from datetime import datetime, timezone
import numpy as np
import qiskit
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eyes_core import ARIA

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTPUT = ROOT / "evidence_summary.json"
MAX_BYTES = int(1.5 * 1024 * 1024)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_provenance(path, data):
    saved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    return {"software_versions": data.get("versions", {}),
            "simulator": "eyes_core.py exact NumPy small-state density/channel simulation; calibrated Aria-like approximation",
            "noise_settings": ARIA, "settings": data.get("configuration", {}),
            "acquisition": data.get("provenance", {
                "date_utc": saved[:10], "source_file_last_modified_utc": saved,
                "date_basis": "Saved source file filesystem timestamp, not an embedded acquisition clock; exact original run start was not captured.",
                "machine": "Original host identifier not captured by the saved harness",
                "platform": "Windows 11 repository environment (supplied project context)",
                "python": "Original Python version not captured; generation environment is reported separately."})}


def build_summary():
    suite_paths = [RESULTS / "frozen-evidence.json", RESULTS / "fresh-evidence.json"]
    dev_path = RESULTS / "development-evidence.json"
    if dev_path.exists():
        suite_paths.append(dev_path)
    manifests = {name: ROOT / "review" / "manifests" / (name + ".json")
                 for name in ("frozen", "fresh")}
    suites = {}
    sources = {}
    for path in suite_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        config = data.get("configuration", {})
        records = data.get("records", [])
        # Keep all published per-cell statistics and seed-level outcomes, but omit
        # bulky per-shot counts, fit profiles, text, and waveform data.
        suites[data["suite"]] = {
            "label": "LOCAL MODEL (calibrated IonQ-like approximation, not device)",
            "provenance": local_provenance(path, data),
            "suite_label": data.get("noise_label"),
            "seeds": data.get("seeds", []),
            "configuration": config,
            "fit_spec": data.get("fit_spec", {}),
            "independent_manifest_sha256": data.get("independent_manifest_sha256"),
            "summary": data.get("summary", {}),
            "seed_summary": data.get("seed_summary", {}),
            "seed_results": data.get("seed_results", []),
            "record_count": len(records),
            "gate": {"independent_science_pass": data.get("independent_science_pass"),
                     "cloud_confirmation": data.get("cloud_confirmation"),
                     "implementation_handoff_only": data.get("implementation_handoff_only")},
        }
        sources[path.relative_to(ROOT).as_posix()] = sha256(path)
    for name, path in manifests.items():
        if path.exists():
            sources[path.relative_to(ROOT).as_posix()] = sha256(path)
    gate_path = RESULTS / "g1.json"
    if gate_path.exists():
        suites["g1_gate"] = json.loads(gate_path.read_text(encoding="utf-8"))
        sources[gate_path.relative_to(ROOT).as_posix()] = sha256(gate_path)
    # Development files may use a distinct name; include existing complete result
    # files, excluding quick smoke samples and previously generated summaries.
    for path in sorted(RESULTS.glob("development*evidence.json")):
        rel = path.relative_to(ROOT).as_posix()
        if rel not in sources:
            data = json.loads(path.read_text(encoding="utf-8"))
            suites[data.get("suite", path.stem)] = {
                "label": "LOCAL MODEL (calibrated IonQ-like approximation, not device)",
                "provenance": local_provenance(path, data),
                "seeds": data.get("seeds", []), "configuration": data.get("configuration", {}),
                "fit_spec": data.get("fit_spec", {}), "summary": data.get("summary", {}),
                "seed_summary": data.get("seed_summary", {}), "seed_results": data.get("seed_results", []),
                "record_count": len(data.get("records", [])),
                "gate": {"independent_science_pass": data.get("independent_science_pass"),
                         "cloud_confirmation": data.get("cloud_confirmation"),
                         "implementation_handoff_only": data.get("implementation_handoff_only")},
            }
            sources[rel] = sha256(path)
    cloud_path = RESULTS / "cloud_fit.json"
    cloud_fit = None
    if cloud_path.exists():
        cloud = json.loads(cloud_path.read_text(encoding="utf-8"))
        cloud_fit = {"label": cloud.get("combined", {}).get("label"), "suites": cloud.get("combined", {}).get("suites", {})}
        sources[cloud_path.relative_to(ROOT).as_posix()] = sha256(cloud_path)
    config = suites.get("frozen", {}).get("configuration", {})
    for rel in ("recorded_ionq.py", "eyes_core.py", "fit.py", "sonify.py", "receipt.py",
                "main.py", "circuit_pack.py", "cloud_slots.py", "web/eyes_bridge.py",
                "web/main.js", "web/index.html", "web/main.css",
                "experiments/run.py", "experiments/make_summary.py"):
        sources[rel] = sha256(ROOT / rel)
    payload = {
        "evidence_label": "Mixed evidence: LOCAL MODEL suites and RECORDED Qollab IonQ simulator cloud fits",
        "provenance": {"generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                       "machine": platform.node(), "platform": platform.platform(),
                       "python": platform.python_version(), "qiskit": qiskit.__version__, "numpy": np.__version__,
                       "operation": "Summary generation from saved evidence; no new acquisition or verification",
                       "local_acquisition_metadata": "See suite provenance: original versions retained, date basis explicit; unknown original host/Python not invented."},
        "historical_status_note": "G1 FAIL and independent/cloud false flags preserve the earlier local acquisition stage. Later cloud fits are separate RECORDED evidence; this regeneration does not declare a new independent PASS.",
        "source_files_sha256": sources,
        "manifests_sha256": {n: sha256(p) for n, p in manifests.items() if p.exists()},
        "config": {"seeds_by_suite": {k: v.get("seeds", []) for k, v in suites.items()
                                      if isinstance(v, dict) and "seeds" in v},
                   "shots_per_phase": config.get("shots"),
                   "noise_models": config.get("noise_models", config.get("noise", "see per-record source evidence")),
                   "noise_scales": config.get("scales"), "grid": config.get("fit"),
                   "gate": suites.get("g1_gate")},
        "suites": suites,
        "cloud_fit": cloud_fit,
        "recorded_ionq_file": "recorded_ionq.py",
        "scope": "LOCAL MODEL suites summarize saved local simulations. cloud_fit contains RECORDED Qollab IonQ simulator fits; original raw records are in recorded_ionq.py.",
    }
    return payload


def write_summary():
    payload = build_summary()
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    if OUTPUT.stat().st_size >= MAX_BYTES:
        OUTPUT.unlink()
        raise ValueError("evidence summary exceeds 1.5 MB")
    return OUTPUT


if __name__ == "__main__":
    print(write_summary())
