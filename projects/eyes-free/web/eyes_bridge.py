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
    """JSON list of analytic reference records; shots=0 means no sampling."""
    return json.dumps([
        {"id": f"local-{n}-s{scale}", "source": "LOCAL MODEL", "n": n,
         "scale": scale, "frequency": float(n), "contrast": float(np.exp(-0.025 * scale * n)),
         "status": "analytic reference; intervals are exact model values, not sampling uncertainty",
         "phases_rad": eyes_core.PHASES.tolist(),
         "parity": (np.exp(-0.025 * scale * n) * np.cos(n * eyes_core.PHASES)).tolist(),
         "shots": [0] * len(eyes_core.PHASES), "shots_per_phase": [0] * len(eyes_core.PHASES),
         "frequency_ci": [float(n), float(n)],
         "contrast_ci": [float(np.exp(-0.025 * scale * n))] * 2,
         "offset": 0.0, "cos_coefficient": float(np.exp(-0.025 * scale * n)),
         "sin_coefficient": 0.0,
         "circuit": str(eyes_core.circuit(n, 0.0))}
        for scale in (0.0, 0.5, 1.0, 2.0) for n in eyes_core.WIDTHS
    ], allow_nan=False)


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
                       "shots_per_phase": result["shots"],
                       "scale": 0, "frequency": float(result["frequency"]),
                       "contrast": float(result["contrast"]), "status": result["flag"],
                       "circuit": str(eyes_core.circuit(n, 0.0))})
    return json.dumps(output, allow_nan=False)


def recorded_fringe():
    """Decode embedded RECORD_JSON lines if available."""
    sweeps, records, errors = main.recorded_estimates(recorded_ionq.RECORDED)
    if errors:
        raise ValueError("; ".join(errors))
    output = []
    for suite, estimates in sweeps.items():
        sources = [r["source_file"] for r in records if r["suite"] == suite]
        for n, estimate in zip(eyes_core.WIDTHS, estimates):
            output.append({**estimate, "id": f"recorded-{suite}-{n}",
                           "source": "RECORDED", "n": n, "suite": suite,
                           "scale": "aria-1", "status": estimate["flag"],
                           "acquisition_date_utc": "2026-10-10", "shots_per_phase": estimate["shots"],
                           "source_files": sources})
    return json.dumps(output, allow_nan=False)


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
    return json.dumps([{"id": "ionq-sample", "source": "LIVE", "n": 1, "scale": "IonQ simulator",
             "frequency": None, "contrast": None, "parity": 2 * parity / max(total, 1) - 1, "status": "partial sample; no fitted frequency/contrast",
             "circuit": "Packed GHZ circuits at three phases; whole-register parity sample, not a single fringe."}], allow_nan=False)


def make_wav(frequency, contrast):
    """JSON object with MIME type and unsigned byte list for sendFile."""
    return json.dumps({"mime_type": "audio/wav", "bytes": list(sonify.wav_bytes(
        {"frequency": float(frequency), "contrast": float(contrast)}))})


def receipt_text(record):
    """Accept a JSON record string and return a JSON transcript string."""
    record = json.loads(str(record))
    return json.dumps(receipt.transcript(record, record.get("source", "unlabeled")))

def is_ionq_backend(backend):
    """JSON boolean for capability gating."""
    return json.dumps(backend.name == "ionq_simulator")
