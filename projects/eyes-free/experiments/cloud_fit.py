import json
import re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from cloud_slots import SLOTS
from fit import fit_counts
from eyes_core import probabilities
EXPORTS = ROOT / "results" / "exports"


def extract_records(exports=EXPORTS):
    records = []
    for path in sorted(Path(exports).glob("*.html")):
        html = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"RECORD_JSON\s+(\{.*?\})(?=</div>)", html):
            record = json.loads(match.group(1))
            record["source_file"] = "results/exports/" + path.name
            slot = record.get("slot")
            if slot not in SLOTS:
                raise ValueError("unknown slot in %s: %r" % (path.name, slot))
            spec = SLOTS[slot]
            for key in ("suite", "shots", "manifest_hash"):
                expected = spec["manifest_hash"] if key == "manifest_hash" else spec[key]
                if record.get(key) != expected:
                    raise ValueError("%s %s mismatch: %r != %r" % (slot, key, record.get(key), expected))
            if record.get("effective_noise_model") != "aria-1":
                raise ValueError("%s is not aria-1" % slot)
            records.append(record)
    return records


def _slot_phase_counts(record, width):
    found = []
    for item in record["manifest"]:
        if item.get("width") != width:
            continue
        offset = int(item["offset"])
        parity = [0, 0]
        for bits, count in record["counts"].items():
            if len(bits) != 21:
                raise ValueError("unexpected packed result width")
            # Qiskit prints bit 0 at the right; exclude lower-offset blocks.
            segment = bits[21-offset-width:21-offset]
            parity[sum(c == "1" for c in segment) % 2] += int(count)
        found.append((float(item["phase_rad"]), {"0": parity[0], "1": parity[1]}))
    return found


def _local_prediction(phases, width):
    # Exact local Aria channel parity prediction, evaluated without shot noise.
    ys = []
    for phase in phases:
        probs = probabilities(width, phase, 1.0)
        even = sum(float(v) for i, v in enumerate(probs) if i.bit_count() % 2 == 0)
        ys.append(2 * even - 1)
    x = np.asarray(phases)
    design = np.column_stack((np.ones(len(x)), np.cos(width*x), np.sin(width*x)))
    b = np.linalg.lstsq(design, np.asarray(ys), rcond=None)[0]
    return {"frequency": float(width), "contrast": float(np.hypot(b[1], b[2])), "offset": float(b[0])}


def combine(records):
    by_suite = {"frozen": {}, "fresh": {}}
    for rec in records:
        if rec["slot"] not in ("E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09"):
            continue
        suite = rec["suite"]
        by_suite[suite][rec["slot"]] = rec
    output = {"label": "Qollab IonQ simulator aria-1 cloud RECORD_JSON counts", "suites": {}}
    for suite, slots in by_suite.items():
        expected_slots = ["E%02d" % n for n in (range(2, 6) if suite == "frozen" else range(6, 10))]
        if sorted(slots) != expected_slots:
            raise ValueError("incomplete %s batches: %s" % (suite, sorted(slots)))
        suite_result = {"slots": expected_slots, "fits": {}}
        for width in (1, 2, 4):
            series = []
            for slot in expected_slots:
                series.extend(_slot_phase_counts(slots[slot], width))
            series.sort(key=lambda row: row[0])
            phases, counts = zip(*series)
            fit = fit_counts(phases, counts)
            local = _local_prediction(phases, width)
            fit.update({"local_model_aria1": local,
                        "difference_from_local": {"frequency": fit["frequency"]-local["frequency"],
                                                   "contrast": fit["contrast"]-local["contrast"]},
                        "exact_ideal": {"frequency": width, "contrast": 1.0},
                        "difference_from_ideal": {"frequency": fit["frequency"]-width,
                                                  "contrast": fit["contrast"]-1.0},
                        "agreement": {"local_frequency_ci_contains_prediction": fit["frequency_ci"][0] <= local["frequency"] <= fit["frequency_ci"][1],
                                      "ideal_frequency_ci_contains_truth": fit["frequency_ci"][0] <= width <= fit["frequency_ci"][1],
                                      "ideal_contrast_ci_contains_truth": fit["contrast_ci"][0] <= 1 <= fit["contrast_ci"][1]}})
            suite_result["fits"][str(width)] = fit
        output["suites"][suite] = suite_result
    return output


def main():
    records = extract_records()
    payload = {"records": records, "combined": combine(records)}
    target = ROOT / "results" / "cloud_fit.json"
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    from experiments.make_summary import write_summary
    write_summary()
    # Keep the UI's embedded records synchronized with the exported source records.
    recorded = ROOT / "recorded_ionq.py"
    lines = [json.dumps(r, separators=(",", ":"), ensure_ascii=False) for r in records]
    recorded.write_text('"""Paste console RECORD_JSON objects here. No evidence is bundled."""\nRECORDED = r"""\n' + "\n".join(lines) + '\n"""\n', encoding="utf-8")
    for suite, data in payload["combined"]["suites"].items():
        for width, fit in data["fits"].items():
            print("%s n=%s f=%.4f [%.4f, %.4f] C=%.4f [%.4f, %.4f]" %
                  (suite, width, fit["frequency"], *fit["frequency_ci"], fit["contrast"], *fit["contrast_ci"]))
    return target


if __name__ == "__main__":
    print(main())
