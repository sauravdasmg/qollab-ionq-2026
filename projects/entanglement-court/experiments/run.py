"""Local paired evidence harness. Full suites are orchestrator-run only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from cases import make_demo, analyze_counts, SEEDS
from circuit_pack import digest
from experiments.noise import LABEL, config, ideal_probabilities
from graphs import edges
from measurements import graph_state, stabilizers, stabilizer_expectation, product_equatorial_state, biseparable_control_state
from experiments.noise import apply_local_depolarizing, readout_probabilities


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="bounded development-only smoke check")
    p.add_argument("--suite", choices=("development", "frozen", "fresh"))
    p.add_argument("--gate", choices=("g1",))
    p.add_argument("--independent-manifest", type=Path)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--output-dir", type=Path, default=ROOT / "results")
    p.add_argument("--draws", type=int)
    p.add_argument("--shots", type=int, default=100)
    p.add_argument("--seed", type=int, default=2026100100)
    p.add_argument("--help-config", action="store_true", help="print preregistered configuration")
    return p


def validate_args(a):
    if a.quick:
        if a.suite or a.gate or a.independent_manifest or a.resume or a.draws or a.shots != 100 or a.seed != 2026100100:
            raise ValueError("--quick conflicts with suite/gate/fresh/resume/custom sampling flags")
        if not a.output_dir.name.lower().startswith("quick-") and a.output_dir != ROOT / "results":
            raise ValueError("quick output directory must have a quick- prefix")
        return
    if a.suite in ("frozen", "fresh") and not a.independent_manifest:
        raise ValueError("--suite frozen/fresh requires --independent-manifest PATH")
    if a.suite == "development" and a.independent_manifest:
        raise ValueError("--independent-manifest is only valid with --suite frozen or fresh")
    if a.gate and a.suite != "development":
        raise ValueError("--gate g1 requires --suite development")
    if a.draws is not None and a.draws <= 0 or a.shots <= 0:
        raise ValueError("draws and shots must be positive")
    if a.suite and a.draws is None:
        a.draws = 1000


def binomial_interval(successes, trials, alpha=0.05):
    """Wilson score interval, stable at zero/all-success boundaries."""
    if type(successes) is not int or type(trials) is not int or trials <= 0 or not 0 <= successes <= trials or not 0 < alpha < 1:
        raise ValueError("invalid binomial counts or alpha")
    from scipy.stats import norm
    z = float(norm.ppf(1 - alpha / 2))
    if successes == 0:
        return [0.0, 1 - (alpha / 2) ** (1 / trials)]
    if successes == trials:
        return [(alpha / 2) ** (1 / trials), 1.0]
    phat = successes / trials
    den = 1 + z * z / trials
    mid = (phat + z * z / (2 * trials)) / den
    half = z * math.sqrt(phat * (1-phat)/trials + z*z/(4*trials*trials)) / den
    return [max(0., mid-half), min(1., mid+half)]


def _counts(prob, shots, seed):
    rng = np.random.default_rng(int(seed))
    c = rng.multinomial(int(shots), np.asarray(prob, dtype=float))
    width = int(round(math.log2(len(c))))
    return {format(i, f"0{width}b"): int(n) for i, n in enumerate(c) if n}


def _probabilities(case, block, kind=None, scale=0., model=None, bias=0., manifest=None):
    """Measured four-wire distributions, with Qiskit's little-endian count keys."""
    kind = kind or ("graph" if block.startswith("target") else "product")
    return _control_probabilities(kind, case, scale, model, bias, block, manifest)


def run_quick(output_dir=None):
    """Exactly two development pairs, <=10 draws each, ideal and nominal aria."""
    outdir = Path(output_dir or ROOT / "results")
    outdir.mkdir(parents=True, exist_ok=True)
    if outdir != ROOT / "results" and not outdir.name.lower().startswith("quick-"):
        raise ValueError("quick output directory must have a quick- prefix")
    records = []
    for case, seed in zip((0, 1), (2026100100, 2026100101)):
        _, manifest = make_demo(case)
        # Keep each block's independent sample explicit; paired baselines consume these same counts.
        marginals = {}
        for block_index, name in enumerate(manifest["ordered_blocks"]):
            marginals[name] = _counts(_probabilities(case, name), 10, seed + block_index)
        analysis = analyze_counts(marginals, manifest)
        records.append({"case_id": case, "generation_seed": seed, "manifest": manifest,
                        "manifest_hash": digest(manifest), "draws": 10,
                        "noise_configurations": [config("aria", 1.0)],
                        "marginals": marginals, "analysis": analysis,
                        "baseline_same_counts": "two-color witness consumes the identical target_A/target_B histograms",
                        "label": "development-only local ideal multinomial smoke; not Qollab evidence"})
    result = {"schema_version": "1.0", "created_utc": datetime.now(timezone.utc).isoformat(),
              "suite": "quick-development-only", "machine": platform.platform(),
              "python": sys.version, "numpy": np.__version__, "noise_source": LABEL,
              "records": records, "science_verdict": None,
              "note": "Quick smoke only: the aria configuration is declared for label/configuration plumbing; draws are ideal mathematical probabilities and do not simulate its channels."}
    payload = json.dumps(result, sort_keys=True, indent=2, allow_nan=False)
    path = outdir / "quick-c-evidence.json"
    path.write_text(payload + "\n", encoding="utf-8")
    print("Saved bounded quick harness output: " + str(path), flush=True)
    return result


def load_independent_manifest(path):
    p = Path(path)
    if not p.is_file():
        raise ValueError("independent manifest path does not exist")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("independent manifest is missing or malformed JSON") from exc
    if not isinstance(data, dict) or data.get("owner") != "independent_verifier" or not isinstance(data.get("instances"), list) or not data["instances"]:
        raise ValueError("fresh manifest must identify independent_verifier and contain instances")
    ids, seeds = set(), set()
    for row in data["instances"]:
        if not isinstance(row, dict) or not isinstance(row.get("manifest"), dict) or not isinstance(row.get("sampling_seed"), int):
            raise ValueError("each fresh instance needs a manifest and independent integer sampling_seed")
        mid = row["manifest"].get("case_id")
        if mid in ids or row["sampling_seed"] in seeds:
            raise ValueError("fresh manifests and sampling seeds must be distinct")
        ids.add(mid); seeds.add(row["sampling_seed"])
    return data


NOISE_SCALES = (.5, .75, 1., 1.25, 1.5, 1.75, 2.)


def _control_probabilities(kind, case, scale, model, bias, block="target_Z", manifest=None):
    """Prepare the shared circuit, apply approximate noise, then measure its basis.

    Z uniformity does not imply uniform A/B witness outcomes. Apply the same
    frame inverse and color rotations as main.py before taking the diagonal.
    """
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import DensityMatrix, Operator
    from measurements import append_preparation, append_measurement
    from experiments.noise import RATES

    m = manifest if manifest is not None else make_demo(case)[1]
    params = m["generated_parameters"]
    g = params["edges"]
    frame = params["frame_radians"]
    prep = QuantumCircuit(4)
    if kind in ("graph", "product"):
        append_preparation(prep, 0, g, frame, params["product_angles_radians"], kind)
    elif kind == "biseparable":
        # Bell pair on little-endian wires 0,1 and |+> on 2,3.
        prep.h(0); prep.cx(0, 1); prep.h(2); prep.h(3)
        for q, angle in enumerate(frame):
            prep.rz(float(angle), q)
    else:
        raise ValueError("unknown control kind")
    rho = DensityMatrix.from_instruction(prep).data
    if model is not None:
        rates = RATES[model]
        # Preserve the declared aggregate local channel approximation.
        rho = apply_local_depolarizing(rho, list(range(4)), min(1., rates["1q"] * scale))
        rho = apply_local_depolarizing(rho, list(range(4)), min(1., rates["2q"] * scale * 3))
    if not block.endswith("_Z"):
        basis = QuantumCircuit(4)
        append_measurement(basis, 0, g, frame, 0 if block.endswith("_A") else 1)
        u = Operator(basis).data
        rho = u @ rho @ u.conj().T
    # Remove numerical roundoff negatives before multinomial sampling.
    prob = readout_probabilities(rho, bias=bias)
    prob = np.maximum(prob, 0.)
    return prob / prob.sum()


def _sample_marginals(probabilities, manifest, kind, shots, rng):
    """Sample the target control and the shared product-impostor blocks."""
    marginals = {}
    for name in manifest["ordered_blocks"]:
        source = kind if name.startswith("target") else "product"
        c = rng.multinomial(shots, probabilities[source][name])
        marginals[name] = {format(j, "04b"): int(n) for j, n in enumerate(c) if n}
    return marginals


def _true_parities(probabilities, manifest, kind):
    means = []
    for name in ("target_A", "target_B"):
        for mapping in manifest["blocks"][name]["parity_maps"]:
            signs = [mapping.get("sign", 1) * (-1) **
                     (sum((j >> q) & 1 for q in mapping["bits"]) % 2)
                     for j in range(16)]
            means.append(float(np.dot(probabilities[kind][name], signs)))
    return means


def _case_specs(suite, manifest_path=None):
    if suite == "development":
        return [{"case_id": i, "generation_seed": SEEDS[i], "manifest": make_demo(i)[1], "case_index": i}
                for i in range(4)]
    if manifest_path is None:
        raise ValueError("frozen/fresh suites require an independently staged campaign manifest; development cases are never relabeled")
    data = load_independent_manifest(manifest_path)
    rows = data["instances"]
    if suite == "frozen" and (data.get("owner") != "independent_verifier" or len(rows) != 24):
        raise ValueError("frozen manifest must be independently staged and contain 24 instances")
    if suite == "fresh" and len(rows) != 20:
        raise ValueError("fresh manifest must contain 20 instances")
    out = []
    for row in rows:
        m = row["manifest"]
        out.append({"case_id": m.get("case_id"), "generation_seed": m.get("seed"),
                    "sampling_seed": row["sampling_seed"], "manifest": m,
                    "case_index": int(m.get("case_id", 0)) % 4})
    return out


def _exact_checks(case_index):
    gs = graph_state(edges(case_index)); prod = product_equatorial_state(__import__("cases").ANGLES[case_index])
    graph_z = ideal_probabilities(gs); prod_z = ideal_probabilities(prod)
    tv = float(.5 * np.abs(graph_z - prod_z).sum())
    exp = [stabilizer_expectation(gs, x, z) for x, z in stabilizers(edges(case_index))]
    return {"z_tv": tv, "z_uniform_max_error": float(max(np.max(np.abs(graph_z - 1/16)), np.max(np.abs(prod_z - 1/16)))),
            "graph_stabilizer_expectations": exp, "stabilizer_max_error": float(max(abs(x - 1) for x in exp))}


def _draw_record(spec, draws, shots, base_seed):
    m = spec["manifest"]; idx = spec["case_index"]
    configs = [{"name": "ideal", "model": None, "scale": 0., "bias": 0.}]
    configs += [{"name": f"{model}@{scale:g}", "model": model, "scale": scale, "bias": 0.}
                for model in ("aria", "forte", "forte-enterprise") for scale in NOISE_SCALES]
    rows = []
    for cfg in configs:
        probabilities = {kind: {name: _probabilities(idx, name, kind, cfg["scale"],
                                cfg["model"], cfg["bias"], m) for name in m["ordered_blocks"]}
                         for kind in ("graph", "product", "biseparable")}
        true_means_by_kind = {kind: _true_parities(probabilities, m, kind) for kind in probabilities}
        outcomes = {k: {"certificates": 0, "false_certificates": 0, "inconclusive": 0,
                        "coverage": 0, "simultaneous_coverage": 0, "baseline_certificates": 0,
                        "paired_difference_sum": 0, "f_lower_sum": 0., "counts": []}
                    for k in probabilities}
        rng = np.random.default_rng(int(spec.get("sampling_seed", base_seed)) + int(cfg["scale"] * 1000) + (0 if cfg["model"] is None else sum(map(ord, cfg["model"]))))
        for d in range(draws):
            for kind, prob in probabilities.items():
                marginals = _sample_marginals(probabilities, m, kind, shots, rng)
                analysis = analyze_counts(marginals, m)
                w = analysis.get("simultaneous_witness", {})
                b = analysis.get("two_color_comparator", {})
                cert = bool(w.get("conditional_gme", False))
                rec = outcomes[kind]; rec["certificates"] += int(cert)
                rec["false_certificates"] += int(cert and kind != "graph")
                rec["inconclusive"] += int(not w.get("conditional_gme", False))
                rec["baseline_certificates"] += int(bool(b.get("conditional_gme", False)))
                rec["paired_difference_sum"] += int(bool(w.get("conditional_gme", False))) - int(bool(b.get("conditional_gme", False)))
                rec["f_lower_sum"] += float(w.get("F_lower", 0.))
                rec["counts"].append(marginals)
                if w.get("terms"):
                    true_means = true_means_by_kind[kind]
                    covered = [t["L_lower"] <= mu + 1e-12 for t, mu in zip(w["terms"], true_means)]
                    rec["coverage"] += sum(covered)
                    rec["simultaneous_coverage"] += int(all(covered))
        for kind, rec in outcomes.items():
            trials = draws
            rec["summary"] = {"certification_rate": rec["certificates"] / trials,
                               "certification_interval": binomial_interval(rec["certificates"], trials),
                               "false_certificates": rec["false_certificates"],
                               "inconclusive_rate": rec["inconclusive"] / trials,
                               "paired_difference_mean": rec["paired_difference_sum"] / trials,
                               "mean_F_lower": rec["f_lower_sum"] / trials,
                               "simultaneous_coverage_rate": rec["simultaneous_coverage"] / trials,
                               "coverage_interval": binomial_interval(rec["simultaneous_coverage"], trials)}
            rec.pop("counts")
        rows.append({"noise": cfg, "controls": outcomes, "exact_reference": _exact_checks(idx),
                     "shots_per_block": shots, "draws": draws})
    return rows


def _atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _output_paths(output_dir=None):
    """--output-dir is the results directory, never another project root."""
    result_dir = Path(output_dir) if output_dir is not None else ROOT / "results"
    if not result_dir.is_absolute():
        result_dir = ROOT / result_dir
    result_dir = result_dir.resolve()
    figure_dir = ROOT / "figures" if result_dir == (ROOT / "results").resolve() else result_dir / "figures"
    return result_dir, figure_dir


def run_suite(suite, draws=1000, shots=100, seed=2026100100, output_dir=None, resume=False, manifest_path=None,
              g1_cloud_projection=False):
    result_dir, figure_dir = _output_paths(output_dir)
    result_path = result_dir / f"{suite}.json"
    specs = _case_specs(suite, manifest_path)
    result = {"schema_version": "1.0", "suite": suite, "created_utc": datetime.now(timezone.utc).isoformat(),
              "config": {"draws": draws, "shots": shots, "seed": seed, "noise_scales": list(NOISE_SCALES),
                         "models": ["aria", "forte", "forte-enterprise"], "controls": ["graph", "separable-product", "known-biseparable"],
                         "alpha": .05, "alpha_allocation": ".05/(2*4) per generator", "noise_label": LABEL},
              "versions": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
                           "scipy": __import__("scipy").__version__, "qiskit": __import__("qiskit").__version__},
              "cases": [], "summary": {}}
    done = set()
    if resume and result_path.exists():
        try:
            previous = json.loads(result_path.read_text(encoding="utf-8"))
            if previous.get("suite") != suite or previous.get("config", {}).get("draws") != draws or previous.get("config", {}).get("shots") != shots:
                raise ValueError("checkpoint configuration does not match requested run")
            result["cases"] = previous.get("cases", [])
            done = {x["case_id"] for x in result["cases"]}
        except json.JSONDecodeError as exc:
            raise ValueError("resume checkpoint is malformed") from exc
    started = time.monotonic()
    for i, spec in enumerate(specs):
        if spec["case_id"] in done: continue
        checkpoint = result_dir / f".{suite}-case-{spec['case_id']}.json"
        if resume and checkpoint.exists():
            row = json.loads(checkpoint.read_text(encoding="utf-8"))
        else:
            row = {"case_id": spec["case_id"], "generation_seed": spec.get("generation_seed"),
                   "sampling_seed": spec.get("sampling_seed", seed + i), "manifest": spec["manifest"],
                   "manifest_hash": digest(spec["manifest"]), "noise_results": _draw_record(spec, draws, shots, seed)}
            if g1_cloud_projection:
                cloud = [x for x in _draw_record(spec, draws, 200, seed)
                         if x["noise"]["name"] == "aria@1"]
                for x in cloud:
                    x["purpose"] = "g1_cloud_projection"
                row["noise_results"].extend(cloud)
            _atomic_json(checkpoint, row)
        result["cases"].append(row)
        elapsed = time.monotonic() - started; remaining = max(0, len(specs)-i-1)
        eta = elapsed / max(1, i+1) * remaining
        print(f"[{suite}] case {i+1}/{len(specs)} complete; elapsed {elapsed:.1f}s; ETA {eta:.1f}s", flush=True)
        _atomic_json(result_path, result)
    rates = []
    for row in result["cases"]:
        rates.extend(x["controls"]["graph"]["summary"]["certification_rate"] for x in row["noise_results"] if x["noise"]["name"] == "ideal")
    result["summary"] = {"case_count": len(result["cases"]), "graph_certification_rate_mean": float(np.mean(rates)) if rates else 0.,
                         "draws_per_case_noise_control": draws, "complete": len(result["cases"]) == len(specs)}
    _atomic_json(result_path, result)
    figure_dir.mkdir(parents=True, exist_ok=True)
    _save_figure(result, figure_dir / f"{suite}.png")
    print(f"Saved {result_path}; figure {figure_dir / f'{suite}.png'}", flush=True)
    return result


def _save_figure(result, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    rows = [(r["case_id"], x["controls"]["graph"]["summary"]["certification_rate"])
            for r in result["cases"] for x in r["noise_results"] if x["noise"]["name"] in ("ideal", "aria@1")]
    if rows:
        ax.bar([str(k) for k, _ in rows], [v for _, v in rows], color="#28345a")
    ax.set_ylim(0, 1); ax.set_ylabel("Graph certification fraction")
    ax.set_title(f"{result['suite']} local evidence | {result['config']['shots']} shots")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def run_g1(result, output_dir):
    rows = [r for r in result["cases"]]
    witness_valid = all(r["noise_results"][0]["exact_reference"]["z_tv"] <= 1e-12 and
                        r["noise_results"][0]["exact_reference"]["stabilizer_max_error"] <= 1e-10 for r in rows)
    coverage_valid = all(all(x["draws"] >= 1000 and x["controls"]["graph"]["summary"]["simultaneous_coverage_rate"] >= .90
                             for x in r["noise_results"]) for r in rows)
    easy_rates = [x["controls"]["graph"]["summary"]["certification_rate"] for r in rows for x in r["noise_results"]
                  if x["noise"]["name"] == "ideal" and x["shots_per_block"] == 100]
    local_pass = bool(easy_rates and float(np.mean(easy_rates)) >= .60)
    cloud_rates = [x["controls"]["graph"]["summary"]["certification_rate"] for r in rows for x in r["noise_results"]
                   if x["noise"]["name"] == "aria@1" and x["shots_per_block"] == 200]
    cloud_pass = bool(cloud_rates and float(np.mean(cloud_rates)) >= .80)
    criteria = {"valid_witness_frame_math": witness_valid, "coverage_at_least_1000_draws_per_case": coverage_valid,
                "local_easy_case_power_at_least_60_percent": local_pass, "200_shot_cloud_projection_at_least_80_percent": cloud_pass}
    gate = {"suite": "development", "criteria": criteria, "overall": all(criteria.values()),
            "metrics": {"local_easy_certification_mean": float(np.mean(easy_rates)) if easy_rates else None,
                        "cloud_projection_mean": float(np.mean(cloud_rates)) if cloud_rates else None}}
    print("G1 decision", flush=True)
    for name, passed in criteria.items(): print(f"{'PASS' if passed else 'FAIL'} {name}", flush=True)
    print(f"{'PASS' if gate['overall'] else 'FAIL'} overall", flush=True)
    print(f"cloud_projection_mean: {gate['metrics']['cloud_projection_mean']}", flush=True)
    result_dir, _ = _output_paths(output_dir)
    _atomic_json(result_dir / "g1.json", gate)
    return gate


def main(argv=None):
    p = parser()
    a = p.parse_args(argv)
    try:
        validate_args(a)
        if a.help_config:
            print(json.dumps({"quick_max_draws": 10, "quick_pairs": 2,
                              "full_local_instances": 44, "shots": [100, 200],
                              "noise_scales": [.5,.75,1,1.25,1.5,1.75,2]}, indent=2))
            return 0
        if a.quick:
            run_quick(a.output_dir)
            return 0
        if not a.suite:
            raise ValueError("provide --suite development|frozen|fresh or --quick")
        result = run_suite(a.suite, a.draws, a.shots, a.seed, a.output_dir, a.resume, a.independent_manifest,
                           g1_cloud_projection=bool(a.gate))
        if a.gate:
            run_g1(result, a.output_dir)
        return 0
    except ValueError as exc:
        p.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
