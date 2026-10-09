"""main.py: Never Lose Twice - the two-question game running on Qollab's injected backend.

The game: two identical quantum tests (reference + prover pair); a legal prover-only strategy can trade
average passes for a much smaller double-failure tail. Under the frozen prize rule the ideal game prefers
the correlated joint strategy while recordable IonQ-simulator noise can reverse which strategy wins the
prize. Nothing is ever promised zero-risk: a zero double-failure count is always reported with its exact
finite-shot upper bound.

This project ships the shared circuit_pack.py / receipt.py helpers (see their module docstrings for the
shared disclosure). Project-specific physics, decoding, inference and the two-door presentation are
described on this project's page. This effort is supported by Qollab & IonQ.

Runs:
  - built-in backend:  four <=4-qubit circuits in ONE list job (local simulator lists are allowed);
  - ionq_simulator:    the four blocks packed onto disjoint wires (offsets 0/4/8/12, 16 qubits), ONE
                       circuit, ONE job, ONE job.result() fetch, cached get_counts().
Only one backend is used per run and noise_model is set exactly as
``if backend.name == "ionq_simulator": backend.set_options(noise_model=...)``.

Qollab itself calls main() - never call it from this module.
"""
from __future__ import annotations

import hashlib
import json
import platform
import time

import matplotlib.pyplot as plt

import core
import circuit_pack
import figures
import product_bounds
import receipt

NOISE_MODELS = ("aria-1", "forte-1", "forte-enterprise-1")
PRIZE_RULES = ("frozen", "tail", "mean")
MAX_SHOTS = 1_000_000
OUTCOME_ORDER = ("FF", "FP", "PF", "PP")


def _log(message) -> None:
    print(message, flush=True)


def _validate(case, shots, noise_model, prize) -> None:
    if isinstance(case, bool) or not isinstance(case, int) or not 0 <= case <= 8:
        raise ValueError("case must be the anchor 0 or a frozen development case 1..8")
    if isinstance(shots, bool) or not isinstance(shots, int) or not 1 <= shots <= MAX_SHOTS:
        raise ValueError(f"shots must be an integer in 1..{MAX_SHOTS}")
    if noise_model not in NOISE_MODELS:
        raise ValueError(f"noise_model must be one of {', '.join(NOISE_MODELS)}")
    if prize not in PRIZE_RULES:
        raise ValueError(f"prize must be one of {', '.join(PRIZE_RULES)}")


def _prize_lambda(prize, lambda_star) -> float:
    if prize == "frozen":
        return float(lambda_star)
    if prize == "tail":
        return 0.0
    return 2.0  # descriptive mean-pass rule; only frozen uses the preregistered lambda_star


def _qiskit_version() -> str:
    import qiskit

    return qiskit.__version__


def _environment() -> str:
    return f"{platform.system()} {platform.release()} / Python {platform.python_version()}"

def _run_single_job(backend, target, shots):
    """Exactly one backend.run, one job.result() and one result.get_counts(); no polling or retry."""
    job = backend.run(target, shots=shots)
    result = job.result()
    counts = result.get_counts()
    raw_job_id = getattr(job, "job_id", None) or getattr(job, "id", None) or getattr(result, "job_id", None)
    if callable(raw_job_id):
        try:
            raw_job_id = raw_job_id()
        except Exception:  # noqa: BLE001 - a non-callable fallback stays as-is
            pass
    return counts, "" if raw_job_id is None else str(raw_job_id)


def _effective_noise_model(backend, requested) -> str:
    try:
        options = getattr(backend, "options", None)
        if options is None:
            return requested
        if hasattr(options, "get"):
            value = options.get("noise_model")
        else:
            value = getattr(options, "noise_model", None)
    except Exception:  # noqa: BLE001 - any backend quirk falls back to the explicit request
        value = None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return requested


def _pad_histogram(histogram, width=4) -> dict:
    """Full-width binary keys so decoding never depends on dropped leading zeros."""
    padded = {}
    for key, value in histogram.items():
        text = str(key).replace(" ", "")
        if text[:2].lower() == "0x":
            number = int(text, 16)
        else:
            number = int(text, 2)
        padded[format(number, f"0{width}b")] = int(value)
    return padded


def _circuits_hash(circuits) -> str:
    digest = hashlib.sha256()
    for circuit in circuits:
        digest.update(circuit_pack.circuit_digest(circuit).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _layout_hash(layout) -> str:
    return hashlib.sha256(json.dumps(layout, sort_keys=True).encode("utf-8")).hexdigest()


def _make_record_paths(case, stamp) -> tuple:
    safe = str(stamp).replace(":", "-").replace("Z", "")
    return ("results/exports/qollab_ionq_case" + str(case) + "_" + safe + ".txt",
            "results/receipt_ionq_case" + str(case) + ".json",
            "results/summary_ionq_case" + str(case) + ".json")


def main(case: int = 0, shots: int = 1024, noise_model: str = "aria-1", prize: str = "frozen") -> None:
    started = time.time()
    _log("Never Lose Twice - two-question game: startup")
    _validate(case, shots, noise_model, prize)
    _log(f"Run settings: case={case}, shots={shots}, noise_model={noise_model!r}, prize={prize!r}")
    _log("Loading recorded IonQ evidence projection ...")
    records, record_issues = receipt.load_records()
    records_status = receipt.record_status(records, record_issues)
    _log(f"Recorded evidence now: {records_status}")

    circuits, manifest = core.make_demo(case)
    lambda_star = float(manifest["parameters"]["lambda_star"])
    lambda_value = _prize_lambda(prize, lambda_star)
    backend = globals().get("backend")
    if backend is None:
        raise RuntimeError("No `backend` was injected; run this on Qollab or via tools/qollab_local.py")

    if backend.name == "ionq_simulator":
        is_ionq = True
        try:
            backend.set_options(noise_model=noise_model)
        except Exception as exc:  # noqa: BLE001 - backend may refuse options; proceed on its defaults
            raise RuntimeError("Cannot establish the effective IonQ noise model before submission") from exc
    else:
        is_ionq = False
        if noise_model != "aria-1":
            _log(f"Note: noise_model={noise_model!r} applies to the IonQ simulator and is ignored on the "
                 "built-in backend.")
    effective_model = _effective_noise_model(backend, noise_model) if is_ionq else None
    _log(f"Backend: {getattr(backend, 'name', '?')} ({'IonQ simulator' if is_ionq else 'built-in'})")

    if is_ionq:
        packed, layout = circuit_pack.pack_circuits(circuits, max_qubits=25)
        _log(f"Packing {len(circuits)} blocks onto {packed.num_qubits} disjoint qubits in ONE IonQ circuit."
             if packed.num_qubits > 4 else f"Packing {len(circuits)} small blocks ({packed.num_qubits} qubits).")
        utc_start = receipt.utc_now_string()
        _log(f"Running one packed IonQ circuit with {shots} shots ...")
        try:
            raw_counts, job_id = _run_single_job(backend, packed, shots)
        except Exception as exc:  # noqa: BLE001 - a charged failed attempt is recorded, never retried here
            utc_end = receipt.utc_now_string()
            source_file, receipt_path, result_path = _make_record_paths(case, utc_start)
            failed = receipt.error_record(
                case_id=case, shots=shots, noise_model=noise_model, environment=_environment(),
                qiskit_version=_qiskit_version(), utc_start=utc_start, utc_end=utc_end, reason=str(exc),
                job_id=getattr(backend, "_last_job_id", None), source_file=source_file,
                receipt_path=receipt_path, result_path=result_path)
            _log("IonQ run FAILED; recording the charged attempt (no auto-resubmission).")
            _log("RECORD_JSON " + receipt.redact_for_log(failed))
            raise
        utc_end = receipt.utc_now_string()
        marginals = circuit_pack.unpack_counts(raw_counts, layout)
        analysis = core.analyze_counts(marginals, manifest, lambda_value=lambda_value)
        source_label = f"recorded Qollab IonQ simulator ({effective_model})"
        hashes = {"recipe": manifest["recipe_hash"], "circuit": _circuits_hash(circuits),
                  "layout": _layout_hash(layout), "packed": circuit_pack.circuit_digest(packed)}
        source_file, receipt_path, result_path = _make_record_paths(case, utc_start)
        record = receipt.assemble_record(
            manifest=manifest, layout=layout, raw_counts=raw_counts, marginals=marginals,
            analysis=analysis, lambda_star=lambda_star, prize=prize, shots=shots,
            backend_name=str(getattr(backend, "name", "")), noise_model=effective_model,
            settings={"runtime": "Qollab IonQ simulator (packed one-circuit job)",
                      "offsets": [int(entry["qubit_offset"]) for entry in layout],
                      "total_width": int(sum(entry["qubit_width"] for entry in layout)),
                      "error_mitigation": "none (IonQ cloud simulators offer no debiasing)",
                      "sampler_seed": "not set; remote sampler seeds are non-reproducible"},
            job_id=job_id, qiskit_version=_qiskit_version(),
            utc_start=utc_start, utc_end=utc_end, environment=_environment(), hashes=hashes,
            source_file=source_file, receipt_path=receipt_path, result_path=result_path)
        _log("RECORD_JSON " + receipt.redact_for_log(record))
        _log("IonQ run complete - copy the RECORD_JSON line above into recorded_ionq.RECORDED in Qollab's "
             "code editor.")
    else:
        _log("Built-in backend: running the four ideal circuits in one list job ...")
        utc_start = receipt.utc_now_string()
        counts_list, job_id = _run_single_job(backend, circuits, shots)
        utc_end = receipt.utc_now_string()
        if isinstance(counts_list, dict):
            counts_list = [counts_list]
        if len(counts_list) != len(circuits):
            raise ValueError(f"built-in backend returned {len(counts_list)} count sets for "
                             f"{len(circuits)} circuits")
        marginals = {name: _pad_histogram(counts_list[index]) for index, name in
                     enumerate(manifest["ordered_blocks"])}
        analysis = core.analyze_counts(marginals, manifest, lambda_value=lambda_value)
        source_label = f"live built-in ideal ({getattr(backend, 'name', 'basic_simulator')})"

    results = analysis["results"]
    winner = receipt.winner_strategy(analysis)
    alpha = float(manifest["parameters"]["alpha"])
    theta = float(manifest["parameters"]["theta"])
    p_bound = product_bounds.ideal_product_pass(alpha, theta)
    certificate = product_bounds.ideal_certificate(alpha, theta)
    if abs(certificate["primal_value"] - p_bound) > 1e-8:
        raise ValueError("Independent product certificate disagrees with mathematical reference")
    product_tail = (1.0 - p_bound) ** 2
    ideal_joint_loss = lambda_star  # ideal hedge: zero double-failures and exactly one pass per trial
    ideal_product_loss = product_tail + lambda_star * (2.0 - 2.0 * p_bound)
    _log("Analysis complete; building printable tables and figures ...")

    _log(figures.plain_report(
        results, source_label=source_label, shots=shots, lambda_star=lambda_star, prize_label=prize,
        winner_label=winner, lambda_value=lambda_value, p_bound=p_bound, product_tail=product_tail,
        record_status=records_status))

    recorded_view = None
    if records:
        record = receipt.preferred_record(records)
        recorded_frozen = receipt.analyze_record(record, lambda_value=lambda_star)
        recorded_winner = receipt.winner_strategy(recorded_frozen)
        recorded_label = (f"recorded Qollab IonQ simulator ({record['backend']}, {receipt.effective_model_label(record)}), "
                          f"case {record.get('case_id')}, {record.get('shots')} shots, UTC {record['utc_end']}")
        recorded_view = {"record": record, "analysis": recorded_frozen, "winner": recorded_winner,
                         "label": recorded_label}
        _log(f"Fixed-prize decision at frozen lambda*={lambda_star:.4f}:")
        _log(f"  mathematical anchor reference: joint loss {ideal_joint_loss:.4f}; "
             f"best legal product loss {ideal_product_loss:.4f} (anchor case 0 only).")
        if recorded_winner == "optimized_joint" or recorded_winner == "published_hedge":
            _log(f"  recorded noisy playback also prefers {recorded_winner}; no reversal in this record.")
        elif recorded_winner == "attained_product" and record['case_id'] == 0 and case == 0:
            _log(f"  recorded noisy playback prefers {recorded_winner}: the fixed-prize strategy choice "
                 f"reverses under IonQ-simulator noise.")
        else:
            _log("  No supported anchor product/joint reversal claim for this selected record.")
    else:
        _log("Readiness gap: no recorded Qollab IonQ runs yet; the live ideal game stands alone and is "
             "never mislabelled as a noisy measurement.")
        for issue in record_issues:
            _log(f"  record parser line {issue['line']}: {issue['reason']}")

    _log("Drawing the two-door trial board ...")
    _log("Readiness gap: development optimization/selection evidence and N01 asymmetric/projector/wire "
         "controls are not supplied by the current core interface.")
    for model, budget in (("aria-1", 4000), ("forte-1", 1000), ("forte-enterprise-1", 1000)):
        if not any(r['case_id'] == 0 and r['noise_model'] == model and r['shots'] == budget for r in records):
            _log(f"Readiness gap: anchor campaign {model}, {budget} shots missing; default shots do not substitute.")
    for issue in record_issues:
        _log(f"Record parser line {issue['line']}: {issue['reason']}")
    board = figures.build_trial_board(
        results, source_label=source_label, shots=shots, lambda_star=lambda_star, prize_label=prize,
        winner_label=winner, lambda_value=lambda_value, record_status=records_status,
        p_bound=p_bound, product_tail=product_tail)
    if recorded_view is not None:
        figures.build_trial_board(
            recorded_view["analysis"]["results"], source_label=recorded_view["label"],
            shots=recorded_view["record"]["shots"], lambda_star=lambda_star, prize_label="frozen",
            winner_label=recorded_view["winner"], lambda_value=lambda_star,
            record_status=records_status, p_bound=p_bound, product_tail=product_tail)
    plt.show()
    _log(f"Done in {time.time() - started:.1f}s ({OUTCOME_ORDER[0]}/{OUTCOME_ORDER[1]}/{OUTCOME_ORDER[2]}/"
         f"{OUTCOME_ORDER[3]} counts, per-test passes, tail, mean and finite-shot intervals above).")
