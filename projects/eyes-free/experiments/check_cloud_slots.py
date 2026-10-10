"""Quick four-slot regression using the local Aria emulator (no cloud jobs)."""
import contextlib
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / "tools"))
sys.path.insert(0, str(ROOT))
import qollab_local
from cloud_slots import build_slot
from experiments.cloud_fit import combine, extract_records


def emulate_frozen():
    # MPS avoids a large 21-wire noisy statevector. Circuit, compilation,
    # calibrated noise, shots and main() contract remain those of qollab_local.
    original = qollab_local.get_backend
    def small_backend(*args, **kwargs):
        backend = original(*args, **kwargs)
        backend.set_options(method="matrix_product_state", max_parallel_threads=1)
        backend.name = "ionq_simulator"
        return backend
    records = []
    with patch.object(qollab_local, "get_backend", small_backend):
        for slot in ("E02", "E03", "E04", "E05"):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                qollab_local.run_project(ROOT, "ionq-aria", shots=1000,
                                         params={"slot": slot}, seed=1234)
            line = next(line for line in stdout.getvalue().splitlines()
                        if line.startswith("RECORD_JSON "))
            record = json.loads(line[len("RECORD_JSON "):])
            assert record["manifest"] == build_slot(slot)[1]
            records.append(record)
    return records


def check(records):
    cloud = extract_records()
    for record in records:
        source = next(r for r in cloud if r["slot"] == record["slot"])
        for key in ("manifest", "manifest_hash", "suite", "shots", "effective_noise_model"):
            assert record[key] == source[key], (record["slot"], key)
    # combine requires both complete suites; use existing fresh records solely
    # to satisfy that interface. Only emulated frozen fits are tested here.
    result = combine(records + [r for r in cloud if r["suite"] == "fresh"])
    fits = result["suites"]["frozen"]["fits"]
    for width, fit in fits.items():
        assert abs(fit["frequency"] - int(width)) < 0.05, fit["frequency"]
        assert fit["contrast"] > 0.85, fit["contrast"]
    return fits


def main():
    records = emulate_frozen()
    fits = check(records)
    target = ROOT / "results" / "local-cloud-slots.json"
    target.write_text(json.dumps({"label": "LOCAL IonQ-like Aria approximation; MPS",
                                  "seed": 1234, "records": records, "fits": fits},
                                 indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for record in records:
        print("RECORD_JSON " + json.dumps(record, sort_keys=True))
    for width, fit in fits.items():
        print("local n=%s f=%.6f C=%.6f" % (width, fit["frequency"], fit["contrast"]))


if __name__ == "__main__":
    main()
