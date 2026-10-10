"""Small JS-facing adapter for measured fringe and receipt utilities."""
import json
import numpy as np
import eyes_core
import fit
import sonify
import receipt
import recorded_ionq
import circuit_pack
import main


def fringe_catalog():
    """Return demo records, preserving provenance labels on every value."""
    return [
        {"id": f"local-{n}-s{scale}", "source": "LOCAL MODEL", "n": n,
         "scale": scale, "frequency": float(n), "contrast": float(np.exp(-0.025 * scale * n)),
         "status": "illustrative reference, not a fit", "circuit": str(eyes_core.circuit(n, 0.0))}
        for scale in (0.0, 0.5, 1.0, 2.0) for n in eyes_core.WIDTHS
    ]


def live_fringe(backend, shots=256):
    """Run the small ideal reference circuits using the injected backend."""
    circuits = eyes_core.circuits()
    main.backend = backend
    counts = main._submit_job(circuits, shots)
    output = []
    phases = list(eyes_core.PHASES)
    for index, n in enumerate(eyes_core.WIDTHS):
        group = counts[index * 12:(index + 1) * 12]
        result = fit.fit_counts(phases, group)
        output.append({**result, "id": f"live-{n}", "source": "LIVE", "n": n,
                       "scale": 0, "frequency": float(result["frequency"]),
                       "contrast": float(result["contrast"]), "status": result["flag"],
                       "circuit": str(eyes_core.circuit(n, 0.0))})
    return output


def recorded_fringe():
    """Decode embedded RECORD_JSON lines if available."""
    sweeps, records, errors = main.recorded_estimates()
    if errors:
        raise ValueError("; ".join(errors))
    output = []
    for suite, estimates in sweeps.items():
        sources = [r["source_file"] for r in records if r["suite"] == suite]
        for n, estimate in zip(eyes_core.WIDTHS, estimates):
            output.append({**estimate, "id": f"recorded-{suite}-{n}",
                           "source": "RECORDED", "n": n, "suite": suite,
                           "scale": "aria-1", "status": estimate["flag"],
                           "acquisition_date_utc": "2026-10-10", "shots_per_phase": 1000,
                           "source_files": sources})
    return output


def ionq_sample(backend, shots=128):
    """Submit exactly one packed circuit, then return labeled fringe records."""
    main.backend = backend
    if backend.name == "ionq_simulator":
        backend.set_options(noise_model="aria-1")
    packed, _ = circuit_pack.pack(0.0)
    counts = main._submit_job(packed, shots)
    if isinstance(counts, list):
        counts = counts[0]
    total = sum(counts.values())
    parity = sum(v for key, v in counts.items() if str(key).replace(" ", "").count("1") % 2 == 0)
    contrast = max(0.0, min(1.0, 2 * parity / max(total, 1) - 1))
    return [{"id": "ionq-sample", "source": "LIVE", "n": 1, "scale": "IonQ simulator",
             "frequency": None, "contrast": None, "parity": 2 * parity / max(total, 1) - 1, "status": "partial sample; no fitted frequency/contrast",
             "circuit": "One-qubit GHZ fringe at phase 0; parity sample."}]


def make_wav(frequency, contrast):
    return sonify.wav_bytes({"frequency": float(frequency), "contrast": float(contrast)})


def receipt_text(record):
    return receipt.transcript(record, record.get("source", "unlabeled"))

def is_ionq_backend(backend):
    return backend.name == "ionq_simulator"
