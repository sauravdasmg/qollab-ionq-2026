"""receipt.py: parse recorded IonQ evidence, validate it honestly, and assemble run receipts.

Shared helpers live in their own files: circuit_pack.py and receipt.py implement circuit packing,
count normalization, backend dispatch and evidence receipts. Written during Oct 9-11, 2026, with exact
UTC provenance and source/license attribution; used by Two Whispers Make a Word, Never Lose Twice and
Entanglement Court only where the shipped manifest lists the helper. Project-specific physics, decoding,
inference and presentation are described on each project page.

This module never submits a job and never reaches the network: it only parses serialized records,
validates them, serializes cached results and derives summaries. Live built-in ideal results,
the mathematical reference, recorded Qollab IonQ evidence and any local noise approximation are kept
as distinct labels and are never conflated.
"""

import json
import hashlib
import numbers
import re
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0.0"
SOURCE_STRING = "Qollab IonQ simulator run"
BACKEND_STRING = "ionq_simulator"
EFFECTIVE_MODELS = ("aria-1", "forte-1", "forte-enterprise-1")
WINDOW_START = datetime(2026, 10, 9, 23, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 10, 11, 23, 0, 0, tzinfo=timezone.utc)

REQUIRED_FIELDS = (
    "schema_version", "source", "environment", "backend", "noise_model", "shots", "settings",
    "qiskit_version", "utc_start", "utc_end", "case_id", "parameters", "hashes", "layout",
    "raw_counts", "marginals", "uncertainties", "job_id", "source_file", "receipt_path", "result_path",
)
_HASH_FIELDS = ("recipe", "circuit", "layout")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


# --------------------------------------------------------------------------- time helpers
def utc_now_string() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_utc(value):
    text = str(value).strip()
    if text.endswith("Z") or text.endswith("z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def _check_counts(mapping, expected_total, label):
    problems = []
    if not isinstance(mapping, dict) or not mapping:
        return [f"{label} must be a non-empty mapping"]
    total = 0
    for key, value in mapping.items():
        if isinstance(value, bool) or not isinstance(value, numbers.Integral) or value < 0:
            problems.append(f"{label} has a non-integer or negative count for {key!r}")
            continue
        total += int(value)
    if expected_total is not None and total != expected_total:
        problems.append(f"{label} sums to {total} shots, expected {expected_total}")
    return problems


def validate_record(record) -> list:
    """Return a list of human-readable problems; an empty list means the record is acceptable evidence."""
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    problems = [f"missing required field {field!r}" for field in REQUIRED_FIELDS if field not in record]
    if problems:
        return problems
    if record["source"] != SOURCE_STRING:
        problems.append(f"source {record['source']!r} is not {SOURCE_STRING!r}")
    if record["backend"] != BACKEND_STRING:
        problems.append(f"backend {record['backend']!r} is not {BACKEND_STRING!r}")
    if record["noise_model"] not in EFFECTIVE_MODELS:
        problems.append("noise_model must be an actual supported effective model")
    if record["schema_version"] != SCHEMA_VERSION:
        problems.append("unsupported schema_version")
    shots = record["shots"]
    if isinstance(shots, bool) or not isinstance(shots, numbers.Integral) or int(shots) <= 0:
        problems.append("shots must be a positive integer")
        shots = None
    for field in ("settings", "parameters", "uncertainties", "hashes"):
        if not isinstance(record[field], dict):
            problems.append(f"{field} must be a mapping")
    if not isinstance(record["layout"], (list, tuple)) or not record["layout"]:
        problems.append("layout must be a non-empty ordered list")
    for field in ("job_id", "source_file", "receipt_path", "result_path", "environment", "qiskit_version"):
        if not isinstance(record[field], str) or (field != "job_id" and not record[field].strip()):
            problems.append(f"{field} must be a non-empty string")
    # dates inside the build window
    try:
        start = _parse_utc(record["utc_start"])
        end = _parse_utc(record["utc_end"])
    except (TypeError, ValueError) as exc:
        problems.append(f"utc_start/utc_end are not valid ISO-8601 timestamps ({exc})")
    else:
        if start > end:
            problems.append("utc_start is after utc_end")
        if start < WINDOW_START or end > WINDOW_END:
            problems.append("timestamps fall outside the Oct 9-11, 2026 build window")
    # hashes
    if isinstance(record["hashes"], dict):
        for name in _HASH_FIELDS:
            value = record["hashes"].get(name)
            if not isinstance(value, str) or not _HEX64.match(value):
                problems.append(f"hashes[{name!r}] must be a 64-character sha256 hex digest")
    # counts
    if isinstance(record["raw_counts"], dict) and shots is not None:
        problems.extend(_check_counts(record["raw_counts"], int(shots), "raw_counts"))
    elif not isinstance(record["raw_counts"], dict) or not record["raw_counts"]:
        problems.append("raw_counts must be a non-empty mapping")
    if isinstance(record["marginals"], dict) and record["marginals"]:
        for block, histogram in record["marginals"].items():
            problems.extend(_check_counts(histogram, int(shots) if shots is not None else None,
                                          f"marginals[{block!r}]"))
    else:
        problems.append("marginals must be a non-empty mapping of block name to histogram")
    manifest = record.get("manifest")
    if not isinstance(manifest, dict) or "ordered_blocks" not in manifest:
        problems.append("complete construction manifest is required")
    if not str(record["source_file"]).startswith("results/exports/") or ".." in str(record["source_file"]):
        problems.append("source_file must point into local results/exports/")
    if isinstance(record["layout"], list) and record["layout"]:
        try:
            import circuit_pack
            derived = circuit_pack.unpack_counts(record["raw_counts"], record["layout"])
            if derived != record["marginals"]:
                problems.append("marginals do not match included raw counts and layout")
            layout_hash = hashlib.sha256(json.dumps(record["layout"], sort_keys=True).encode()).hexdigest()
            if isinstance(record["hashes"], dict) and record["hashes"].get("layout") != layout_hash:
                problems.append("layout hash mismatch")
            if isinstance(manifest, dict):
                import core
                circuits, expected = core.make_demo(record["case_id"], recipe=record["parameters"])
                _, expected_layout = circuit_pack.pack_circuits(circuits)
                digest = hashlib.sha256()
                for circuit in circuits:
                    digest.update(circuit_pack.circuit_digest(circuit).encode())
                    digest.update(b"\n")
                if manifest != expected or record["layout"] != expected_layout:
                    problems.append("manifest/layout do not match construction recipe")
                if record["hashes"].get("recipe") != expected["recipe_hash"] or record["hashes"].get("circuit") != digest.hexdigest():
                    problems.append("recipe/circuit hash mismatch")
                if not record["uncertainties"].get("assumptions"):
                    problems.append("explicit uncertainty assumptions required")
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError, IndexError) as exc:
            problems.append(f"invalid construction/count evidence: {exc}")
    return problems


def parse_record_line(line: str) -> dict:
    """Parse one console line: bare JSON or a ``RECORD_JSON: {...}`` prefix. Raises ValueError if malformed."""
    text = line.strip()
    if text[:11].upper() == "RECORD_JSON":
        text = text[11:].lstrip()
        if text.startswith(":"):
            text = text[1:].lstrip()
    if not text:
        raise ValueError("empty RECORD_JSON line")
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg}") from exc
    problems = validate_record(record)
    if problems:
        raise ValueError("; ".join(problems))
    return record


def parse_records(text: str):
    """Parse multi-line RECORDED text. Returns ``(valid_records, issues)``; malformed lines are reported."""
    records = []
    issues = []
    for lineno, raw in enumerate(str(text).splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            records.append(parse_record_line(line))
        except ValueError as exc:
            issues.append({"line": lineno, "reason": str(exc), "text": line[:160]})
    return records, issues


def load_records():
    """Load and validate the top-level ``recorded_ionq.RECORDED`` string shipped with the project."""
    from recorded_ionq import RECORDED

    return parse_records(RECORDED)


def record_status(records, issues=None) -> str:
    if not records:
        status = "No recorded IonQ runs yet"
    else:
        status = f"Recorded IonQ runs: {len(records)}"
    if issues:
        status += f"; {len(issues)} malformed line(s) skipped"
    return status


def preferred_record(records):
    """Pick the most representative recorded run: the anchor, aria-1, most recent, highest-shot one."""
    if not records:
        return None
    return max(records, key=lambda r: (r.get("case_id") == 0, r.get("noise_model") == "aria-1",
                                       int(r.get("shots", 0)), str(r.get("utc_start", ""))))


def effective_model_label(record) -> str:
    model = str(record.get("noise_model", "")).strip()
    return model or "unspecified IonQ noise model"


def analyze_record(record, lambda_value=None):
    """Analyze included raw marginals against the record's manifest (or the frozen case recipe)."""
    import core

    manifest = record.get("manifest")
    if not isinstance(manifest, dict):
        manifest = core.make_demo(int(record["case_id"]))[1]
    options = {}
    if lambda_value is not None:
        options["lambda_value"] = lambda_value
    import circuit_pack
    return core.analyze_counts(circuit_pack.unpack_counts(record["raw_counts"], record["layout"]), manifest, **options)


def winner_strategy(analysis) -> str:
    return min(analysis["results"], key=lambda entry: entry["loss"])["block"]


def compact_uncertainties(analysis, lambda_star):
    results = analysis["results"]
    return {
        "confidence": results[0]["uncertainties"]["confidence"],
        "method": results[0]["uncertainties"]["method"],
        "assumptions": list(results[0]["assumptions"]) + list(analysis.get("assumptions", [])),
        "lambda_star": float(lambda_star),
        "per_block": {
            entry["block"]: {
                "double_failure_interval": entry["uncertainties"]["ff_interval"],
                "marginal_pass_intervals": entry["uncertainties"]["marginal_pass_intervals"],
                "mean_pass_interval": mean_pass_interval(entry),
                "double_failure_upper_if_zero": entry["double_failure_upper_if_zero"],
            }
            for entry in results
        },
    }


def mean_pass_interval(entry):
    """Sum exact marginal intervals; union bound covers both without test independence.

    Two individual 95% intervals give at least 90% coverage for their sum.
    This is an interval for population mean passes (0..2), not a trial prediction.
    """
    intervals = entry["uncertainties"]["marginal_pass_intervals"]
    confidence = entry["uncertainties"]["confidence"]
    return {"interval": [sum(i[0] for i in intervals), sum(i[1] for i in intervals)],
            "coverage_at_least": max(0., 1-2*(1-confidence)),
            "method": "sum of exact marginal binomial intervals; union bound; IID shots"}


def assemble_record(*, manifest, layout, raw_counts, marginals, analysis, lambda_star, prize, shots,
                    backend_name, noise_model, settings, job_id, qiskit_version, utc_start, utc_end,
                    environment, hashes, source_file, receipt_path, result_path):
    """Build the complete RECORD_JSON payload from one cached result. Never invents evidence."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE_STRING,
        "environment": environment,
        "backend": backend_name,
        "noise_model": noise_model,
        "shots": int(shots),
        "settings": dict(settings),
        "qiskit_version": qiskit_version,
        "utc_start": utc_start,
        "utc_end": utc_end,
        "case_id": manifest["case_id"],
        "parameters": dict(manifest.get("parameters", {})),
        "hashes": dict(hashes),
        "manifest": manifest,
        "layout": [dict(entry) for entry in layout],
        "raw_counts": {str(key): int(value) for key, value in raw_counts.items()},
        "marginals": {name: {str(key): int(value) for key, value in hist.items()}
                      for name, hist in marginals.items()},
        "uncertainties": compact_uncertainties(analysis, lambda_star),
        "job_id": str(job_id if job_id is not None else ""),
        "prize": prize,
        "source_file": source_file,
        "receipt_path": receipt_path,
        "result_path": result_path,
    }
    return payload


def error_record(*, case_id, shots, noise_model, environment, qiskit_version, utc_start, utc_end,
                 reason, job_id="", source_file="", receipt_path="", result_path=""):
    """A charged failed attempt: an explicit error reason, never auto-resubmitted, never counts invented."""
    payload = {field: None for field in REQUIRED_FIELDS}
    payload.update({
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE_STRING,
        "environment": environment,
        "backend": BACKEND_STRING,
        "noise_model": noise_model,
        "shots": int(shots),
        "qiskit_version": qiskit_version,
        "utc_start": utc_start,
        "utc_end": utc_end,
        "case_id": case_id,
        "job_id": str(job_id),
        "error": str(reason),
        "settings": {"failed_attempt": True},
        "parameters": {"case_id": case_id},
        "hashes": {},
        "layout": [],
        "raw_counts": {},
        "marginals": {},
        "uncertainties": {"status": "failed attempt; no counts returned"},
        "source_file": source_file,
        "receipt_path": receipt_path,
        "result_path": result_path,
    })
    return payload


def redact_for_log(record) -> str:
    """One-line JSON for the RECORD_JSON console line; sorted keys keep it stable and diffable."""
    return json.dumps(record, sort_keys=True, default=str)
