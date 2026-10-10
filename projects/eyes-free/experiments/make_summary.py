"""Create compact, source-hashed evidence summary from saved local results."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTPUT = ROOT / "evidence_summary.json"
MAX_BYTES = int(1.5 * 1024 * 1024)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
                "seeds": data.get("seeds", []), "configuration": data.get("configuration", {}),
                "fit_spec": data.get("fit_spec", {}), "summary": data.get("summary", {}),
                "seed_summary": data.get("seed_summary", {}), "seed_results": data.get("seed_results", []),
                "record_count": len(data.get("records", [])),
                "gate": {"independent_science_pass": data.get("independent_science_pass"),
                         "cloud_confirmation": data.get("cloud_confirmation"),
                         "implementation_handoff_only": data.get("implementation_handoff_only")},
            }
            sources[rel] = sha256(path)
    config = suites.get("frozen", {}).get("configuration", {})
    payload = {
        "evidence_label": "LOCAL MODEL (calibrated IonQ-like approximation, not device)",
        "source_files_sha256": sources,
        "manifests_sha256": {n: sha256(p) for n, p in manifests.items() if p.exists()},
        "config": {"seeds_by_suite": {k: v.get("seeds", []) for k, v in suites.items()
                                      if isinstance(v, dict) and "seeds" in v},
                   "shots_per_phase": config.get("shots_per_phase"),
                   "noise_models": config.get("noise_models", config.get("noise", "see per-record source evidence")),
                   "noise_scales": config.get("noise_scales"), "grid": config.get("grid", config.get("fit_spec")),
                   "gate": suites.get("g1_gate")},
        "suites": suites,
        "recorded_ionq_file": "recorded_ionq.py",
        "scope": "Saved local simulation evidence only; Qollab IonQ simulator records are in recorded_ionq.py.",
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
