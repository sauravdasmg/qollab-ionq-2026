"""Qollab invokes main itself. Backend and optional sendFile are injected."""
import json
from datetime import datetime, timezone
import numpy as np
from eyes_core import WIDTHS, PHASES, circuits, fringe
from fit import fit_counts
from circuit_pack import pack, smoke_pack, unpack
from receipt import make_record, parse_records, transcript
from recorded_ionq import RECORDED
from sonify import wav_bytes
from figures import chart
from cloud_slots import SLOTS, build_slot


def analyze(counts, phase_frame=0.0):
    if len(counts) != 36:
        raise ValueError("expected 36 small-circuit counts")
    return [fit_counts(PHASES+phase_frame, counts[j*12:(j+1)*12]) for j in range(3)]


def _submit_job(circuit_or_list, shots):
    """Single shared submission point for all paths."""
    job = backend.run(circuit_or_list, shots=shots)
    return job.result().get_counts()


def recorded_estimates(raw=RECORDED):
    records, errors = parse_records(raw)
    sweeps = {}
    for suite in ("frozen", "fresh"):
        subset = [r for r in records if r["suite"] == suite]
        shift = np.pi/24 if suite == "fresh" else 0.0
        expected_frames = [k*np.pi/2+shift for k in range(4)]
        if len(subset) != 4 or any(sum(abs(r["phase_frame"]-f)<1e-9 for r in subset) != 1
                                   for f in expected_frames):
            errors.append("Missing/duplicate recorded %s sweep; no complete fit." % suite)
            continue
        subset.sort(key=lambda r: r["phase_frame"])
        by_width = {n: [] for n in WIDTHS}
        for r in subset:
            marginal = unpack(r["counts"], r["manifest"])
            for b, c in zip(r["manifest"], marginal):
                by_width[b["width"]].append(c)
        cloud_estimates = [fit_counts(PHASES+shift, by_width[n]) for n in WIDTHS]
        sweeps[suite] = cloud_estimates
    return sweeps, records, errors


def main(shots: int=256, phase_frame: float=0.0, slot: str = ""):
    if slot:
        if slot not in SLOTS: raise ValueError("unknown cloud slot")
        spec = SLOTS[slot]
        if shots != spec["shots"]: raise ValueError("slot shot budget is fixed at %d" % spec["shots"])
        q, manifest = build_slot(slot)
        effective = "ideal"
        if backend.name == "ionq_simulator":
            backend.set_options(noise_model="aria-1")
            effective = getattr(backend.options, "noise_model", None)
            if effective != "aria-1": raise ValueError("effective aria-1 option not confirmed")
        circuit_or_list = q
        path_type = "slot"
        path_params = {"slot": slot, "spec": spec, "manifest": manifest, "effective": effective}
    elif backend.name == "ionq_simulator":
        if not 1 <= shots <= 1000 or not np.isfinite(phase_frame):
            raise ValueError("shots must be 1..1000 and phase_frame finite")
        print("Eyes-Free: starting one counts job", flush=True)
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
        circuit_or_list = q
        path_type = "ionq_default"
        path_params = {"smoke": smoke, "export": export, "base": base, "fresh": fresh, "frozen": frozen,
                       "manifest": manifest, "effective": effective}
    else:
        if not 1 <= shots <= 1000 or not np.isfinite(phase_frame):
            raise ValueError("shots must be 1..1000 and phase_frame finite")
        circuit_or_list = circuits(phase_frame)
        path_type = "builtin"
        path_params = {"phase_frame": phase_frame}

    counts = _submit_job(circuit_or_list, shots)

    if path_type == "slot":
        slot = path_params["slot"]
        spec = path_params["spec"]
        manifest = path_params["manifest"]
        effective = path_params["effective"]
        record = {"slot":slot,"suite":spec["suite"],"manifest_hash":spec["manifest_hash"],
                  "shots":shots,"effective_noise_model":effective,"counts":counts,"manifest":manifest,
                  "utc":datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                  "source_file":"results/exports/qollab-console.txt"}
        if slot != "E01":
            record["fits"] = {str(n): {"frequency":None,"frequency_ci":None,"contrast":None,
                "contrast_ci":None,"phase_points_received":3,"status":"awaiting complete twelve-phase suite"} for n in WIDTHS}
            print("Slot frequency and contrast fits require combining all four preregistered batches.", flush=True)
        print("RECORD_JSON " + json.dumps(record, sort_keys=True), flush=True)
        return record

    if path_type == "ionq_default":
        smoke = path_params["smoke"]
        export = path_params["export"]
        base = path_params["base"]
        fresh = path_params["fresh"]
        frozen = path_params["frozen"]
        manifest = path_params["manifest"]
        effective = path_params["effective"]
        record = make_record(counts, manifest, shots, base, effective,
                             "smoke" if smoke else "export" if export else "fresh" if fresh else "frozen",
                             qubits=21 if not smoke else 19)
        print("RECORD_JSON " + json.dumps(record, sort_keys=True), flush=True)
        print("Partial three-phase pack only; no frequency estimate. Preserve original console export.", flush=True)
        return record

    phase_frame = path_params["phase_frame"]
    estimates = analyze(counts, phase_frame)
    for n,e in zip(WIDTHS,estimates):
        print("Measured series width %d; estimate remains frequency-blind." % n,flush=True)
        print(transcript(e, "live built-in ideal"), flush=True)
    print("mathematical reference (not measured counts): " + json.dumps(
        {str(n): {control: [fringe(n,p+phase_frame,control) for p in PHASES]
                  for control in ("ghz","product","incoherent")} for n in WIDTHS}),flush=True)
    sweeps, records, errors = recorded_estimates()
    for error in errors:
        print(error, flush=True)
    print("Validated RECORDED packs: %d; these are not independent cloud instances." % len(records), flush=True)
    for suite, cloud_estimates in sweeps.items():
        for e in cloud_estimates:
            print(transcript(e, "RECORDED Qollab IonQ aria-1 " + suite), flush=True)
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
            print("Audio download unavailable: sendFile not injected; use the published JS page for browser playback.", flush=True)
    else:
        print("Inconclusive: no informative audio estimate available.", flush=True)
    return estimates