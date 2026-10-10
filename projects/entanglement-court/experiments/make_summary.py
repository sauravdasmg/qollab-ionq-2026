"""Build a compact evidence index from the saved local campaign JSON files."""

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 1_500_000
SUITES = ("frozen", "fresh", "development")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize_campaign(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    result = {
        "source": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "suite": data.get("suite"),
        "created_utc": data.get("created_utc"),
        "versions": data.get("versions", {}),
        "simulator": "local small-block density-channel approximation plus multinomial sampling",
        "retention": "Aggregate counters, probabilities and seeds retained; sampled draw-level counts were discarded. No hashed replay transcript is retained.",
        "config": {key: data.get("config", {}).get(key) for key in (
            "seed", "sampled_case_ids", "staged_manifest_count", "draws", "shots",
            "models", "noise_scales", "noise_label", "alpha", "controls",
        )},
        "summary": data.get("summary", {}),
        "cases": [],
    }
    for case in data.get("cases", []):
        row = {
            "case_id": case.get("case_id"),
            "generation_seed": case.get("generation_seed"),
            "sampling_seed": case.get("sampling_seed"),
            "manifest_sha256": case.get("manifest_hash"),
            "configurations": [],
        }
        for run in case.get("noise_results", []):
            controls = {}
            for control, metrics in run.get("controls", {}).items():
                controls[control] = {
                    key: metrics.get(key)
                    for key in ("certificates", "baseline_certificates", "false_certificates", "inconclusive", "coverage", "simultaneous_coverage")
                }
                controls[control]["statistics"] = {
                    key: metrics.get("summary", {}).get(key)
                    for key in ("certification_rate", "certification_interval", "inconclusive_rate", "mean_F_lower", "coverage_interval", "simultaneous_coverage_rate", "paired_difference_mean")
                }
            row["configurations"].append({
                "noise": run.get("noise"),
                "shots_per_block": run.get("shots_per_block"),
                "draws": run.get("draws"),
                "controls": controls,
            })
        result["cases"].append(row)
    return result


def summarize_gate(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"source": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "result": data}


def build_summary(generated_utc=None):
    import numpy
    import qiskit
    import scipy
    campaigns = [summarize_campaign(ROOT / "results" / (name + ".json")) for name in SUITES]
    gate_path = ROOT / "results" / "g1.json"
    payload = {
        "schema_version": "1.1",
        "provenance": {
            "generated_utc": generated_utc or datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python": sys.version,
            "qiskit": qiskit.__version__,
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "generator": "experiments/make_summary.py",
            "generator_sha256": sha256(Path(__file__)),
        },
        "evidence_label": "LOCAL MODEL (IonQ-like noise approximation with preliminary rates; not official calibration, not device)",
        "description": "Compact LOCAL MODEL statistics derived from repository-only frozen, fresh and development result files. Full sources are repository evidence, not top-level Qollab uploads; source SHA-256s are included. Aggregates can be summed, but original sampled draws cannot be audited from retained counts.",
        "campaigns": campaigns,
        "gate_decisions": summarize_gate(gate_path),
        "sources": [
            {"path": c["source"], "sha256": c["sha256"], "bytes": (ROOT / c["source"]).stat().st_size}
            for c in campaigns
        ] + [{"path": "results/g1.json", "sha256": sha256(gate_path), "bytes": gate_path.stat().st_size}],
    }
    return payload


def write_summary(path=None):
    path = Path(path or ROOT / "evidence_summary.json")
    path.write_text(json.dumps(build_summary(), separators=(",", ":"), sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    if path.stat().st_size >= LIMIT:
        raise ValueError("evidence summary exceeds 1.5 MB")
    return path


if __name__ == "__main__":
    target = write_summary()
    print("Wrote {} ({} bytes)".format(target, target.stat().st_size))
