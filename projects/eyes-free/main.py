"""Qollab invokes main itself. Backend and optional sendFile are injected."""
import json
import numpy as np
from eyes_core import WIDTHS, PHASES, circuits, fringe
from fit import fit_counts
from circuit_pack import pack, smoke_pack, unpack
from receipt import make_record, parse_records, transcript
from recorded_ionq import RECORDED
from sonify import wav_bytes
from figures import chart


def analyze(counts, phase_frame=0.0):
    if len(counts) != 36:
        raise ValueError("expected 36 small-circuit counts")
    return [fit_counts(PHASES+phase_frame, counts[j*12:(j+1)*12]) for j in range(3)]


def main(shots: int=256, phase_frame: float=0.0):
    if not 1 <= shots <= 1000 or not np.isfinite(phase_frame):
        raise ValueError("shots must be 1..1000 and phase_frame finite")
    print("Eyes-Free: starting one counts job", flush=True)
    if backend.name == "ionq_simulator":
        # Science runs are one phase-major triple; four explicit runs cover a sweep.
        smoke = phase_frame == -1.0
        export = abs(phase_frame-2*np.pi) < 1e-9
        base = phase_frame if not export else 0.0
        residue = base % (np.pi/2)
        fresh = abs(residue-np.pi/24) < 1e-9
        frozen = min(abs(residue), abs(residue-np.pi/2)) < 1e-9
        if not smoke and not (0 <= base < 2*np.pi and (fresh or frozen)):
            raise ValueError("use triple starts k*pi/2, fresh k*pi/2+pi/24, smoke -1, export 2*pi")
        if smoke and shots != 100:
            raise ValueError("smoke requires 100 shots")
        if not smoke and shots != 1000:
            raise ValueError("science/export requires the frozen 1000-shot budget")
        backend.set_options(noise_model="aria-1")
        effective = getattr(backend.options, "noise_model", None)
        if effective != "aria-1":
            raise ValueError("effective aria-1 option not confirmed")
        q, manifest = smoke_pack() if smoke else pack(base)
        job = backend.run(q, shots=shots)
        result = job.result()
        counts = result.get_counts()
        record = make_record(counts, manifest, shots, base, effective,
                             "smoke" if smoke else "export" if export else "fresh" if fresh else "frozen",
                             qubits=q.num_qubits)
        print("RECORD_JSON " + json.dumps(record, sort_keys=True), flush=True)
        print("Partial three-phase pack only; no frequency estimate. Preserve original console export.", flush=True)
        return record
    job = backend.run(circuits(phase_frame), shots=shots)
    result = job.result()
    counts = result.get_counts()
    estimates = analyze(counts, phase_frame)
    for n,e in zip(WIDTHS,estimates):
        print("Measured series width %d; estimate remains frequency-blind." % n,flush=True)
        print(transcript(e, "live built-in ideal"), flush=True)
    print("mathematical reference (not measured counts): " + json.dumps(
        {str(n): {control: [fringe(n,p+phase_frame,control) for p in PHASES]
                  for control in ("ghz","product","incoherent")} for n in WIDTHS}),flush=True)
    records, errors = parse_records(RECORDED)
    for error in errors:
        print(error, flush=True)
    print("Validated recorded packs: %d; these are not independent cloud instances." % len(records), flush=True)
    for suite in ("frozen", "fresh"):
        subset = [r for r in records if r["suite"] == suite]
        shift = np.pi/24 if suite == "fresh" else 0.0
        expected_frames = [k*np.pi/2+shift for k in range(4)]
        if len(subset) != 4 or any(sum(abs(r["phase_frame"]-f)<1e-9 for r in subset) != 1
                                   for f in expected_frames):
            print("Missing/duplicate recorded %s sweep; no complete fit." % suite, flush=True)
            continue
        subset.sort(key=lambda r: r["phase_frame"])
        by_width = {n: [] for n in WIDTHS}
        for r in subset:
            marginal = unpack(r["counts"], r["manifest"])
            for b, c in zip(r["manifest"], marginal):
                by_width[b["width"]].append(c)
        cloud_estimates = [fit_counts(PHASES+shift, by_width[n]) for n in WIDTHS]
        for e in cloud_estimates:
            print(transcript(e, "recorded Qollab IonQ aria-1 "+suite), flush=True)
    fig = chart(estimates, "live built-in ideal")
    import matplotlib.pyplot as plt
    plt.show()
    plt.close(fig)
    informative = [e for e in estimates if e["informative"]]
    if informative:
        audio = wav_bytes(informative[0])
        text = transcript(informative[0], "live built-in ideal")
        sender = globals().get("sendFile")
        if callable(sender):
            sender("eyes-free.wav", "audio/wav", audio)
            sender("eyes-free-receipt.txt", "text/plain", text.encode("utf-8"))
            print("Audio download requested. Start at low volume; use player Stop. Verify download works.", flush=True)
        else:
            print("Audio download unavailable: sendFile not injected; fallback needs operator verification.", flush=True)
    else:
        print("Inconclusive: no informative audio estimate available.", flush=True)
    return estimates
