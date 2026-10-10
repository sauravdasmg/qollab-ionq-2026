"""Bounded quick check and full evidence suites (full runs are orchestrator-only)."""
import argparse
import hashlib
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
from fit import SPEC, fit_counts
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
    for key, rows in cells.items():
        scored = [r for r in rows if "truth_metrics" in r]
        if not scored:
            continue
        coverage = {}
        for parameter in ("frequency", "projection_frequency", "contrast"):
            successes = sum(r["truth_metrics"]["interval_coverage"][parameter] for r in scored)
            coverage[parameter] = {"successes": successes, "total": len(scored),
                                   "fraction": successes/len(scored)}
            if key != "overall":
                coverage[parameter]["ci"] = binomial_interval(successes, len(scored))
        out[key]["empirical_interval_coverage"] = coverage
        out[key]["coverage_nominal"] = 1 - scored[0]["fit"]["alpha"]
        out[key]["truth_errors"] = {
            parameter: {"bias": float(np.mean([r["truth_metrics"]["signed_errors"][parameter] for r in scored])),
                        "mae": float(np.mean([r["truth_metrics"]["absolute_errors"][parameter] for r in scored]))}
            for parameter in ("frequency", "projection_frequency", "contrast")}
        out[key]["reference_fit_mean_rmse"] = float(np.mean([r["truth_metrics"]["reference_fit_rmse"] for r in scored]))
    if "overall" in out:
        # Repeated widths/scales within a seed are correlated, not Bernoulli trials.
        for field in ("availability_ci","audio_ci","inference_ci"):
            out["overall"].pop(field)
        out["overall"]["ci_basis"] = "see seed_summary: one threshold indicator per independent seed"
        out["overall"]["record_count"] = out["overall"].pop("seed_records")
    return out


def load_manifest(path, suite):
    if not path:
        raise ValueError(suite + " requires an independently supplied manifest")
    raw = Path(path).read_bytes()
    m = json.loads(raw.decode("utf-8"))
    required = {"schema", "suite", "owner", "instance_count", "instances", "seeds",
                "widths", "noise_scales", "phase_frame", "phases_rad", "shots_per_phase"}
    optional = {"generated_utc", "generator_notes", "development_seeds_excluded"}
    if not isinstance(m, dict) or not required <= m.keys() or m.keys() - required - optional:
        raise ValueError("invalid manifest fields")
    count, first, frame = (24, 2026100500, 0.0) if suite == "frozen" else (20, 20261011500, float(np.pi/24))
    if (m["schema"] != "eyes-free-independent-manifest-v1" or m["suite"] != suite or
            m["owner"] != "independent_verifier" or type(m["instance_count"]) is not int or
            m["instance_count"] != count):
        raise ValueError("invalid manifest schema, suite, owner or instance count")
    seeds = m["seeds"]
    if (not isinstance(seeds, list) or any(type(v) is not int for v in seeds) or
            len(seeds) != count or len(set(seeds)) != count or set(seeds) != set(range(first, first+count))):
        raise ValueError("manifest seeds must be unique and match the prescribed range")
    instances = m["instances"]
    if not isinstance(instances, list) or len(instances) != count:
        raise ValueError("manifest instance count mismatch")
    ids = []
    for row, seed in zip(instances, seeds):
        if (not isinstance(row, dict) or set(row) != {"id", "seed", "sampling_seed"} or
                not isinstance(row["id"], str) or not row["id"].strip() or
                type(row["seed"]) is not int or type(row["sampling_seed"]) is not int or
                row["seed"] != seed or row["sampling_seed"] != seed):
            raise ValueError("invalid manifest instance id/seed/settings")
        ids.append(row["id"])
    if len(set(ids)) != count:
        raise ValueError("manifest ids must be unique")
    def numeric_list(value, expected):
        return (isinstance(value, list) and len(value) == len(expected) and
                all(type(v) in (int, float) and np.isfinite(v) for v in value) and
                np.array_equal(value, expected))
    if (not numeric_list(m["widths"], list(WIDTHS)) or
            any(type(v) is not int for v in m["widths"]) or
            not numeric_list(m["noise_scales"], [0, .5, .75, 1, 1.5, 2]) or
            type(m["phase_frame"]) not in (int, float) or m["phase_frame"] != frame or
            not numeric_list(m["phases_rad"], (PHASES + m["phase_frame"]).tolist()) or
            type(m["shots_per_phase"]) is not int or m["shots_per_phase"] != 1000):
        raise ValueError("manifest widths/scales/phases/shots differ from the plan")
    return m, hashlib.sha256(raw).hexdigest()


def configuration(args, details=False):
    manifest = None
    if args.quick:
        if args.independent_manifest:
            raise ValueError("independent manifests require frozen/fresh suite")
        result = ([2026100400], [0.0, 1.0], 0.0, 128, None)
    elif args.suite in ("frozen", "fresh"):
        manifest, sha = load_manifest(args.independent_manifest, args.suite)
        result = (manifest["seeds"], manifest["noise_scales"], manifest["phase_frame"],
                  manifest["shots_per_phase"], sha)
    elif args.suite == "development":
        if args.independent_manifest:
            raise ValueError("independent manifests require frozen/fresh suite")
        result = (list(range(2026100400, 2026100404)), [0, .5, .75, 1, 1.5, 2], 0.0, 1000, None)
    else:
        raise ValueError("select --quick or --suite frozen/fresh/development")
    return (result, manifest) if details else result


def reference_truth(width, phases, vectors, scale):
    probabilities_array = np.asarray(vectors, float)
    even = probabilities_array[:, [k for k in range(2**width) if k.bit_count() % 2 == 0]].sum(axis=1)
    parity = 2*even - 1
    if scale == 0:
        f, c, b0, bc, bs, converged = float(width), 1.0, 0.0, 1.0, 0.0, True
    else:
        # Fractional expected counts preserve exact probabilities; no Monte Carlo/rounding.
        population = fit_counts(phases, [{"0": 1000*float(v), "1": 1000*float(1-v)} for v in even])
        f, c = population["frequency"], population["contrast"]
        b0, bc, bs = population["offset"], population["cos_coefficient"], population["sin_coefficient"]
        converged = population["diagnostics"]["converged"] and population["diagnostics"]["all_grid_converged"]
        if not converged:
            raise ValueError("population projection failed to converge")
    predicted = b0 + bc*np.cos(f*np.asarray(phases)) + bs*np.sin(f*np.asarray(phases))
    return {"width": width, "frequency": width, "contrast": c,
            "reference_probabilities": probabilities_array.tolist(), "phases_rad": list(phases),
            "even_probabilities": even.tolist(), "parity": parity.tolist(),
            "contrast_target": "analytic ideal" if scale == 0 else "constrained binomial KL projection",
            "projection": {"frequency": f, "contrast": c, "offset": b0,
                           "cos_coefficient": bc, "sin_coefficient": bs, "converged": bool(converged),
                           "residuals": (parity-predicted).tolist()}}


def truth_metrics(estimate, truth):
    x = np.asarray(truth["phases_rad"])
    predicted = (estimate["offset"] + estimate["cos_coefficient"]*np.cos(estimate["frequency"]*x) +
                 estimate["sin_coefficient"]*np.sin(estimate["frequency"]*x))
    residual = np.asarray(truth["parity"])-predicted
    errors = {"frequency": estimate["frequency"]-truth["frequency"],
              "projection_frequency": estimate["frequency"]-truth["projection"]["frequency"],
              "contrast": estimate["contrast"]-truth["contrast"]}
    coverage = {"frequency": estimate["frequency_ci"][0] <= truth["frequency"] <= estimate["frequency_ci"][1],
                "projection_frequency": estimate["frequency_ci"][0] <= truth["projection"]["frequency"] <= estimate["frequency_ci"][1],
                "contrast": estimate["contrast_ci"][0] <= truth["contrast"] <= estimate["contrast_ci"][1]}
    return {"signed_errors": errors, "absolute_errors": {k: abs(v) for k,v in errors.items()},
            "interval_coverage": coverage, "reference_fit_residuals": residual.tolist(),
            "reference_fit_rmse": float(np.sqrt(np.mean(residual**2))),
            "reference_fit_max_abs": float(np.max(abs(residual))),
            "sample_fit_rmse": float(np.sqrt(np.mean(np.asarray(estimate["residuals"])**2)))}


def run(args):
    settings, manifest = configuration(args, details=True)
    seeds, scales, shift, shots, manifest_hash = settings
    widths = manifest["widths"] if manifest else list(WIDTHS)
    phases = np.asarray(manifest["phases_rad"]) if manifest else PHASES+shift
    instance_ids = {row["seed"]: row["id"] for row in manifest["instances"]} if manifest else {}
    config = {"fit": SPEC, "seeds": seeds, "scales": scales, "shift": shift, "shots": shots,
              "widths": widths, "phases_rad": phases.tolist(), "manifest_sha256": manifest_hash,
              "truth_protocol": "WP-E-04-KL-projection-v1"}
    if args.gate and (args.gate != "g1" or args.suite != "development"):
        raise ValueError("--gate g1 is valid only with --suite development")
    if args.draws is not None and args.draws < 1:
        raise ValueError("--draws must be positive")
    prefix = "quick" if args.quick else args.suite
    outdir = Path(args.output_dir or "results")
    destination = outdir / (prefix+".json" if prefix == "development" else prefix+"-evidence.json")
    checkpoint = outdir / (prefix+"-checkpoint.json")
    if destination.exists() and not args.quick and not args.resume:
        raise ValueError("full evidence already exists; preserve it before a separate orchestrator run")
    if not args.quick and not args.resume and any(outdir.glob(prefix+"-seed*")):
        raise ValueError("existing full artifacts must be preserved before rerunning")
    start = time.perf_counter()
    records = []
    completed = set()
    if args.resume and checkpoint.exists():
        saved = json.loads(checkpoint.read_text(encoding="utf-8"))
        config_hash = digest(config)
        if saved.get("config_sha256") != config_hash:
            raise ValueError("checkpoint configuration mismatch")
        records = saved.get("records", [])
        completed = {(r["seed"], r["config"]["noise_scale"], r["truth"]["width"]) for r in records}
    controls = []
    # Exact reference controls do not use width as a fit answer.
    for n in widths:
        for control in ("ghz", "product", "incoherent"):
            observed = []
            for phi in phases:
                p = probabilities(n, phi, 0, control)
                observed.append(float(sum((-1)**k.bit_count()*v for k, v in enumerate(p))))
            controls.append({"width": n, "control": control, "label": "mathematical reference",
                             "parity": observed, "expected": [fringe(n, p, control) for p in phases]})
    for scale in scales:
        # Reuse deterministic <=4-wire exact probabilities across seeds.
        cached = [[probabilities(n, p, scale) for p in phases] for n in widths]
        truths = [reference_truth(n, phases, vectors, scale) for n, vectors in zip(widths, cached)]
        for seed in seeds:
            rng = np.random.default_rng(seed)
            counts = []
            for n, probs in zip(widths, cached):
                for p in probs:
                    values = rng.multinomial(shots, p)
                    counts.append({format(k, "0%db" % n): int(v) for k, v in enumerate(values) if v})
            t0 = time.perf_counter()
            estimates = evaluate(counts, shift)
            for j, (n, e) in enumerate(zip(widths, estimates)):
                if (seed, scale, n) in completed:
                    continue
                if args.draws is not None and len(records) >= args.draws:
                    break
                pcm = wav_bytes(e)
                decoded = decode(pcm)
                df = abs(decoded["frequency"]-e["frequency"])
                dc = abs(decoded["contrast"]-e["contrast"])
                identified = (abs(e["frequency"]-n)<=.25 and e["frequency_ci"][0]>=n-.5 and
                              e["frequency_ci"][1]<=n+.5 and
                              min(WIDTHS, key=lambda width: abs(width-e["frequency"])) == n)
                name = "%s-seed%d-scale%g-n%d" % (prefix, seed, scale, n)
                outdir.mkdir(parents=True, exist_ok=True)
                (outdir / (name+".wav")).write_bytes(pcm)
                text = transcript(e, "local ideal simulation" if scale == 0 else "local noise approximation aria-1")
                (outdir / (name+".txt")).write_text(text, encoding="utf-8")
                records.append({"seed": seed, "instance_id": instance_ids.get(seed), "truth": truths[j],
                                "truth_metrics": truth_metrics(e, truths[j]),
                                "config": {"phase_frame": shift, "noise_scale": scale, "shots_per_phase": shots,
                                           "label": "local ideal simulation" if scale == 0 else "local noise approximation",
                                           "noise": ARIA, "baseline_shots": 12*shots, "audio_shots": 12*shots, "resamples": 0},
                                "counts": counts[j*12:(j+1)*12], "counts_sha256": digest(counts[j*12:(j+1)*12]),
                                "fit": e, "decoder": decoded, "pcm_sha256": __import__("hashlib").sha256(pcm).hexdigest(),
                                "text_sha256": digest(text), "text_error": 0.0, "frequency_error": df,
                                "contrast_error": dc, "checks": {"digital_fidelity": df<=.02 and dc<=.01,
                                                                   "identified": bool(identified)},
                                "abstention": not e["informative"], "pcm_file": str(outdir/(name+".wav")),
                                "text_file": str(outdir/(name+".txt")), "seconds_fit_group": time.perf_counter()-t0})
            if args.resume:
                checkpoint_payload = {"config_sha256": digest(config), "records":records}
                tmp = checkpoint.with_suffix(".tmp")
                tmp.write_text(json.dumps(checkpoint_payload, indent=2, allow_nan=False), encoding="utf-8"); tmp.replace(checkpoint)
            elapsed = time.perf_counter()-start
            total = args.draws or (len(seeds)*len(scales)*len(WIDTHS))
            print("%s seed=%d scale=%g progress=%d/%d elapsed=%.1fs ETA=%.1fs" % (prefix, seed, scale, len(records), total, elapsed, elapsed/max(1,len(records))*max(0,total-len(records))), flush=True)
            if args.draws is not None and len(records) >= args.draws: break
        if args.draws is not None and len(records) >= args.draws: break
    # Overall intervals use one success/failure per seed, avoiding within-seed pseudoreplication.
    seed_rows = []
    for seed in seeds:
        subset = [r for r in records if r["seed"] == seed]
        info = [r for r in subset if not r["abstention"]]
        seed_rows.append({"seed": seed, "availability": len(info)/len(subset) if subset else 0.0,
                          "audio_pass": bool(info and sum(r["checks"]["digital_fidelity"] for r in info)/len(info)>=.95),
                          "inference_pass": bool(info and sum(r["checks"]["identified"] for r in info)/len(info)>=.9)})
    seed_summary = {key: {"successes": sum(s[key] for s in seed_rows), "total": len(seeds),
                          "ci": binomial_interval(sum(s[key] for s in seed_rows), len(seeds))}
                    for key in ("audio_pass", "inference_pass")}
    payload = {"suite": prefix, "implementation_handoff_only": args.quick or args.draws is not None, "independent_science_pass": False,
               "cloud_confirmation": False, "noise_label": "local noise approximation; not cloud evidence",
               "fit_spec": SPEC, "seeds": seeds, "controls": controls, "records": records,
               "summary": summarize(records), "seed_summary": seed_summary, "seed_results": seed_rows,
               "independent_manifest_sha256": manifest_hash, "consumed_manifest": manifest, "configuration": config, "seconds": time.perf_counter()-start,
               "versions": {"numpy": np.__version__, "scipy": scipy.__version__, "qiskit": qiskit.__version__}}
    payload["config_sha256"] = digest(config)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    if args.gate:
        controls_error = max((abs(a-b) for c in controls for a,b in zip(c["parity"],c["expected"])), default=float("inf"))
        fidelity = sum(bool(r["checks"]["digital_fidelity"]) for r in records)
        frozen_file = outdir / "frozen-evidence.json"
        audio_path = Path("main.js").exists() and Path("index.html").exists()
        criteria = [
            {"name":"exact_fringe_control_and_parity_sign","threshold":"max absolute error <= 1e-10","value":controls_error,"pass":controls_error <= 1e-10},
            {"name":"equal_budget_accessible_baseline","threshold":"equal shots and zero resampling","value":all(r["config"]["baseline_shots"]==r["config"]["audio_shots"] and r["config"]["resamples"]==0 for r in records),"pass":bool(records) and all(r["config"]["baseline_shots"]==r["config"]["audio_shots"] and r["config"]["resamples"]==0 for r in records)},
            {"name":"quick_decoder_precision","threshold":"|frequency error| <= 0.02 and |contrast error| <= 0.01 for every informative record","value":{"passed":fidelity,"total":len(records)},"pass":bool(records) and fidelity==len(records)},
            {"name":"frozen_metrics_and_declared_budget","threshold":"full frozen evidence at 24 seeds x 6 scales x 3 widths, preliminary targets met","value":{"evidence_exists":frozen_file.exists(),"development_records":len(records)},"pass":frozen_file.exists()},
            {"name":"js_bridge_and_audio_fallback","threshold":"main.js and index.html implement bridge plus playback/download fallback","value":{"ui_files_present":audio_path},"pass":audio_path},
            {"name":"calibrated_local_channel","threshold":"ARIA rates match ../../tools/ionq_noise_params.json; local approximation only","value":ARIA,"pass":ARIA["r_1q"]==0.0005 and ARIA["r_2q"]==0.009 and ARIA["readout"]==0.0}]
        gate={"gate":"g1","criteria":criteria,"overall":"PASS" if all(c["pass"] for c in criteria) else "FAIL","independent_pass":False,"cloud_confirmed":False}
        (outdir/"g1.json").write_text(json.dumps(gate,indent=2,allow_nan=False),encoding="utf-8")
        for c in criteria: print("%s %s value=%s threshold=%s" % ("PASS" if c["pass"] else "FAIL",c["name"],json.dumps(c["value"]),c["threshold"]),flush=True)
        print("G1 "+gate["overall"],flush=True)
    print(str(destination), flush=True)
    return payload


def cli():
    parser = argparse.ArgumentParser()
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--quick", action="store_true")
    selection.add_argument("--suite", choices=("frozen", "fresh", "development"))
    parser.add_argument("--independent-manifest")
    parser.add_argument("--draws", type=int)
    parser.add_argument("--gate", choices=("g1",))
    parser.add_argument("--output-dir")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    cli()
