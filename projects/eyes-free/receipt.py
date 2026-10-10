"""Lossless accessible text and strict raw cloud-record validation."""
import json
import re
from datetime import datetime
from eyes_core import digest, normalized_counts

SCHEMA = "eyes-free-record-v1"


def transcript(estimate, label):
    # Audio and baseline use the exact same object; JSON retains full precision.
    return label + "\nUnits: frequency harmonic multiplier (cycles per 2*pi radians of phase); contrast unitless; phase radians.\n" + json.dumps(
        estimate, sort_keys=True, allow_nan=False) + "\nAudio: mono 48000 Hz, 2 s, carrier 220*frequency Hz, peak 0.5*contrast; 50 ms fades.\n"


def validate_record(record):
    if not isinstance(record, dict):
        raise ValueError("record must be a JSON object")
    if "slot" in record:
        record = normalize_slot_record(record)
    if record.get("schema") != SCHEMA or record.get("noise_model") != "aria-1":
        raise ValueError("unknown schema or effective noise model")
    if record.get("label") != "recorded Qollab IonQ":
        raise ValueError("record is not labeled Qollab evidence")
    if not isinstance(record.get("source_file"), str) or not record["source_file"].startswith("results/exports/"):
        raise ValueError("original local export source required")
    if ".." in record["source_file"].split("/"):
        raise ValueError("source path traversal")
    if not isinstance(record.get("utc"),str):
        raise ValueError("UTC timestamp required")
    if not isinstance(record.get("counts"),dict):
        raise ValueError("counts must be an object")
    datetime.fromisoformat(record["utc"].replace("Z", "+00:00"))
    if not record["utc"].endswith("Z"):
        raise ValueError("UTC Z timestamp required")
    if not isinstance(record.get("manifest"),list) or not all(isinstance(b,dict) for b in record["manifest"]):
        raise ValueError("manifest must be a list of blocks")
    if not isinstance(record.get("shots"),int) or isinstance(record["shots"],bool) or not 1 <= record["shots"] <= 1000:
        raise ValueError("invalid shot budget")
    width = record.get("qubits")
    if width not in (19, 21):
        raise ValueError("unexpected packed width")
    counts = normalized_counts(record["counts"], width)
    if counts != record["counts"] or sum(counts.values()) != record["shots"]:
        raise ValueError("counts/totals mismatch")
    if record.get("counts_sha256") != digest(counts) or record.get("manifest_sha256") != digest(record["manifest"]):
        raise ValueError("hash mismatch")
    manifest = record["manifest"]
    if width == 21:
        if record["shots"] != 1000:
            raise ValueError("science/export requires 1000 shots")
        expected = [(n, 7*j+o) for j in range(3) for n, o in ((1, 0), (2, 1), (4, 3))]
        if [(b.get("width"), b.get("offset")) for b in manifest] != expected:
            raise ValueError("invalid phase-major manifest")
        from eyes_core import PHASES
        import numpy as np
        shift = float(record["phase_frame"])
        if record["suite"] not in ("frozen", "fresh", "export"):
            raise ValueError("invalid science suite")
        required = np.pi/24 if record["suite"] == "fresh" else 0.0
        valid_frames = [k*np.pi/2+required for k in range(4)]
        if not any(abs(shift-v)<1e-9 for v in valid_frames):
            raise ValueError("suite/shift mismatch")
        for j in range(3):
            for b in manifest[j*3:j*3+3]:
                if abs(b["phase_rad"]-(PHASES[j]+shift)) > 1e-9:
                    raise ValueError("manifest/phase mismatch")
    elif record.get("suite") != "smoke":
        raise ValueError("19 wires reserved for smoke")
    else:
        from circuit_pack import smoke_pack
        if manifest != smoke_pack()[1] or record["shots"] != 100:
            raise ValueError("invalid smoke manifest/budget")
    return record


def parse_records(raw):
    records, errors = [], []
    for number, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith("RECORD_JSON"):
            line = line[len("RECORD_JSON"):].lstrip(" :")
        try:
            records.append(validate_record(json.loads(line)))
        except (ValueError, KeyError, TypeError, OverflowError) as e:
            errors.append("line %d: %s" % (number, e))
    if not records:
        errors.append("missing recorded Qollab IonQ evidence")
    return records, errors


def make_record(counts, manifest, shots, phase_frame, noise_model, suite="frozen", qubits=21):
    counts = normalized_counts(counts, qubits)
    return {"schema": SCHEMA, "label": "recorded Qollab IonQ", "noise_model": noise_model,
            "suite": suite, "phase_frame": phase_frame, "shots": shots, "qubits": qubits,
            "counts": counts, "manifest": manifest, "counts_sha256": digest(counts),
            "manifest_sha256": digest(manifest),
            "utc": datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_file": "results/exports/qollab-console.txt"}


def normalize_slot_record(record):
    """Validate slot output and derive metadata, preserving raw counts and source."""
    from cloud_slots import SLOTS, build_slot
    slot = record["slot"]
    if slot not in SLOTS:
        raise ValueError("unknown cloud slot")
    spec = SLOTS[slot]
    if (record.get("suite") != spec["suite"] or record.get("shots") != spec["shots"]
            or record.get("manifest_hash") != spec["manifest_hash"]
            or record.get("effective_noise_model") != "aria-1"):
        raise ValueError("slot provenance/budget mismatch")
    if record.get("manifest") != build_slot(slot)[1]:
        raise ValueError("slot manifest mismatch")
    source = record.get("source_file", "")
    match = re.search(r"(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2}\.\d+)Z", source)
    utc = record.get("utc")
    if not utc and match:
        utc = "%sT%s:%s:%sZ" % match.groups()
    derived = dict(record)
    derived.update(schema=SCHEMA, label="recorded Qollab IonQ", noise_model="aria-1",
                   phase_frame=spec["frame"], qubits=19 if slot == "E01" else 21,
                   utc=utc, counts_sha256=digest(record["counts"]),
                   manifest_sha256=digest(record["manifest"]),
                   utc_basis="record UTC" if record.get("utc") else "original export filename completion timestamp")
    # Derived hashes describe the preserved payload; provenance stays tied to its export.
    return derived
