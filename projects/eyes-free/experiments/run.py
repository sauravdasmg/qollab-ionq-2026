"""Bounded quick check and full evidence suites (full runs are orchestrator-only)."""
import argparse
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import scipy
import qiskit
from scipy.stats import beta
from eyes_core import WIDTHS, PHASES, ARIA, sample_counts, digest, probabilities, fringe
from fit import SPEC
from main import analyze
from sonify import wav_bytes
from receipt import transcript
from experiments.decode import decode


def evaluate(counts, phase_frame=0.0):
    # Exactly the demo path, including measurement rotations and little-endian counts.
    return analyze(counts, phase_frame)


def binomial_interval(successes, total):
    if total == 0:
        return [0.0, 1.0]
    return [0.0 if successes == 0 else float(beta.ppf(.025, successes, total-successes+1)),
            1.0 if successes == total else float(beta.ppf(.975, successes+1, total-successes))]


def summarize(records):
    cells = {}
    for r in records:
        key = "n%d/scale%g" % (r["truth"]["width"], r["config"]["noise_scale"])
        cells.setdefault(key, []).append(r)
    cells["overall"] = records
    out = {}
    for key, rows in cells.items():
        informative = [r for r in rows if r["fit"]["informative"]]
        audio_ok = sum(r["checks"]["digital_fidelity"] for r in informative)
        inferred = sum(r["checks"]["identified"] for r in informative)
        count, available = len(rows), len(informative)
        out[key] = {"seed_records": count, "informative": available, "abstentions": count-available,
                    "availability": available/count if count else 0,
                    "availability_ci": binomial_interval(available, count),
                    "audio_successes": audio_ok, "audio_failures": available-audio_ok,
                    "audio_fraction": audio_ok/available if available else 0,
                    "audio_ci": binomial_interval(audio_ok, available),
                    "identified": inferred, "inference_fraction": inferred/available if available else 0,
                    "inference_ci": binomial_interval(inferred, available),
                    "audio_success_full_denominator": audio_ok/count if count else 0,
                    "inference_full_denominator": inferred/count if count else 0,
                    "thresholds_met": bool(count and available/count >= .8 and available and
                                           audio_ok/available >= .95 and inferred/available >= .9)}
    if "overall" in out:
        # Repeated widths/scales within a seed are correlated, not Bernoulli trials.
        for field in ("availability_ci","audio_ci","inference_ci"):
            out["overall"].pop(field)
        out["overall"]["ci_basis"] = "see seed_summary: one threshold indicator per independent seed"
        out["overall"]["record_count"] = out["overall"].pop("seed_records")
    return out


def configuration(args):
    if args.quick:
        return [2026100400], [0.0, 1.0], 0.0, 128, None
    if args.suite == "frozen":
        return list(range(2026100500, 2026100524)), [0, .5, .75, 1, 1.5, 2], 0.0, 1000, None
    if args.suite == "fresh":
        if not args.independent_manifest:
            raise ValueError("fresh requires an independently supplied manifest")
        raw = Path(args.independent_manifest).read_text(encoding="utf-8")
        manifest = json.loads(raw)
        seeds = manifest["seeds"]
        if seeds != list(range(20261011500, 20261011520)):
            raise ValueError("fresh manifest requires the specified 20 independent seeds")
        if abs(manifest["phase_frame"]-np.pi/24)>1e-12:
            raise ValueError("fresh manifest requires pi/24 shift")
        return seeds, [0, .5, .75, 1, 1.5, 2], float(np.pi/24), 1000, digest(manifest)
    raise ValueError("select --quick or --suite frozen/fresh")


def run(args):
    seeds, scales, shift, shots, manifest_hash = configuration(args)
    prefix = "quick" if args.quick else args.suite
    destination = Path("results") / (prefix+"-evidence.json")
    if destination.exists() and not args.quick:
        raise ValueError("full evidence already exists; preserve it before a separate orchestrator run")
    if not args.quick and any(Path("results").glob(prefix+"-seed*")):
        raise ValueError("existing full artifacts must be preserved before rerunning")
    start = time.perf_counter()
    records = []
    controls = []
    # Exact reference controls do not use width as a fit answer.
    for n in WIDTHS:
        for control in ("ghz", "product", "incoherent"):
            observed = []
            for phi in PHASES+shift:
                p = probabilities(n, phi, 0, control)
                observed.append(float(sum((-1)**k.bit_count()*v for k, v in enumerate(p))))
            controls.append({"width": n, "control": control, "label": "mathematical reference",
                             "parity": observed, "expected": [fringe(n, p, control) for p in PHASES+shift]})
    for scale in scales:
        # Reuse deterministic <=4-wire exact probabilities across seeds.
        cached = [[probabilities(n, p+shift, scale) for p in PHASES] for n in WIDTHS]
        for seed in seeds:
            rng = np.random.default_rng(seed)
            counts = []
            for n, probs in zip(WIDTHS, cached):
                for p in probs:
                    values = rng.multinomial(shots, p)
                    counts.append({format(k, "0%db" % n): int(v) for k, v in enumerate(values) if v})
            t0 = time.perf_counter()
            estimates = evaluate(counts, shift)
            for j, (n, e) in enumerate(zip(WIDTHS, estimates)):
                pcm = wav_bytes(e)
                decoded = decode(pcm)
                df = abs(decoded["frequency"]-e["frequency"])
                dc = abs(decoded["contrast"]-e["contrast"])
                identified = (abs(e["frequency"]-n)<=.25 and e["frequency_ci"][0]>=n-.5 and
                              e["frequency_ci"][1]<=n+.5 and
                              min(WIDTHS, key=lambda width: abs(width-e["frequency"])) == n)
                name = "%s-seed%d-scale%g-n%d" % (prefix, seed, scale, n)
                Path("results").mkdir(exist_ok=True)
                Path("results", name+".wav").write_bytes(pcm)
                text = transcript(e, "live built-in ideal" if scale == 0 else "local noise approximation aria-1")
                Path("results", name+".txt").write_text(text, encoding="utf-8")
                records.append({"seed": seed, "truth": {"width": n, "frequency": n},
                                "config": {"phase_frame": shift, "noise_scale": scale, "shots_per_phase": shots,
                                           "label": "live built-in ideal" if scale == 0 else "local noise approximation",
                                           "noise": ARIA, "baseline_shots": 12*shots, "audio_shots": 12*shots, "resamples": 0},
                                "counts": counts[j*12:(j+1)*12], "counts_sha256": digest(counts[j*12:(j+1)*12]),
                                "fit": e, "decoder": decoded, "pcm_sha256": __import__("hashlib").sha256(pcm).hexdigest(),
                                "text_sha256": digest(text), "text_error": 0.0, "frequency_error": df,
                                "contrast_error": dc, "checks": {"digital_fidelity": df<=.02 and dc<=.01,
                                                                   "identified": bool(identified)},
                                "abstention": not e["informative"], "pcm_file": "results/"+name+".wav",
                                "text_file": "results/"+name+".txt", "seconds_fit_group": time.perf_counter()-t0})
            print("%s seed=%d scale=%g complete" % (prefix, seed, scale), flush=True)
    # Overall intervals use one success/failure per seed, avoiding within-seed pseudoreplication.
    seed_rows = []
    for seed in seeds:
        subset = [r for r in records if r["seed"] == seed]
        info = [r for r in subset if not r["abstention"]]
        seed_rows.append({"seed": seed, "availability": len(info)/len(subset),
                          "audio_pass": bool(info and sum(r["checks"]["digital_fidelity"] for r in info)/len(info)>=.95),
                          "inference_pass": bool(info and sum(r["checks"]["identified"] for r in info)/len(info)>=.9)})
    seed_summary = {key: {"successes": sum(s[key] for s in seed_rows), "total": len(seeds),
                          "ci": binomial_interval(sum(s[key] for s in seed_rows), len(seeds))}
                    for key in ("audio_pass", "inference_pass")}
    payload = {"suite": prefix, "implementation_handoff_only": args.quick, "independent_science_pass": False,
               "cloud_confirmation": False, "noise_label": "local noise approximation; not cloud evidence",
               "fit_spec": SPEC, "seeds": seeds, "controls": controls, "records": records,
               "summary": summarize(records), "seed_summary": seed_summary, "seed_results": seed_rows,
               "independent_manifest_sha256": manifest_hash, "seconds": time.perf_counter()-start,
               "versions": {"numpy": np.__version__, "scipy": scipy.__version__, "qiskit": qiskit.__version__}}
    payload["config_sha256"] = digest({"fit": SPEC, "seeds": seeds, "scales": scales, "shift": shift, "shots": shots})
    destination.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    print(str(destination), flush=True)
    return payload


def cli():
    parser = argparse.ArgumentParser()
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--quick", action="store_true")
    selection.add_argument("--suite", choices=("frozen", "fresh"))
    parser.add_argument("--independent-manifest")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    cli()
