"""Local evidence harness. Full suites/search/power are orchestrator-only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from scipy.stats import beta
import core
from product_bounds import ideal_certificate, solve_product_tester, product_tail_lower_bound
from strategies import frozen_recipe, LAMBDA_MENU
from experiments.noise import configuration, probabilities, histogram, product_tester, digest

SCHEMA = "HN-2"
GENERATION = {"development": list(range(2026102900, 2026102908)),
              "frozen": list(range(2026103000, 2026103024)),
              "fresh": list(range(2026103100, 2026103124))}
ALPHA = .025


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc


def write_json(path, value):
    # Atomic replace; a partial write can never become a resumable checkpoint.
    path = Path(path)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def sample_seed(*parts):
    return int(digest(list(parts))[:16], 16)


def interval(k, n, confidence=.975, one_sided=False):
    if isinstance(n, bool) or isinstance(k, bool) or int(n) != n or int(k) != k or \
            n <= 0 or k < 0 or k > n or not 0 < confidence < 1:
        raise ValueError("invalid binomial observations/confidence")
    a = (1-confidence) / (1 if one_sided else 2)
    return [0. if k == 0 else float(beta.ppf(a, k, n-k+1)),
            1. if k == n else float(beta.ppf(1-a, k+1, n-k))]


def generated(seed):
    rng = np.random.default_rng(seed)
    return {"alpha": math.pi/4+float(rng.uniform(-.04, .04)),
            "theta": math.pi/8+float(rng.uniform(-.04, .04))}


def _selection(path):
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError("recipe must be a development selection object")
    body = {k: v for k, v in value.items() if k != "hash"}
    if value.get("hash") != digest(body) or value.get("schema") != SCHEMA or \
            value.get("development_seeds") != GENERATION["development"] or \
            value.get("evaluations_per_class_per_lambda") != 256:
        raise ValueError("invalid development selection hash/schema/budget")
    params = value.get("parameters", {})
    if params.get("lambda_star") not in LAMBDA_MENU:
        raise ValueError("invalid frozen lambda")
    for key in ("joint_phase", "local_phase", "local_rotation"):
        if not isinstance(params.get(key), (int, float)) or not math.isfinite(params[key]):
            raise ValueError("invalid frozen strategy parameters")
    return value


def _manifest_from_json(path, selection_hash=None, worker_seed=314159):
    obj = read_json(path)
    if not isinstance(obj, dict) or obj.get("independent") is not True or not obj.get("author"):
        raise ValueError("independent manifest requires author and independent=true")
    if selection_hash is not None and obj.get("selection_hash") != selection_hash:
        raise ValueError("fresh selection_hash mismatch")
    entries = obj.get("manifests")
    if not isinstance(entries, list) or len(entries) != 24:
        raise ValueError("fresh manifest requires exactly 24 entries")
    required = {"instance_id", "generation_seed", "sampling_seed", "alpha", "theta"}
    all_generation = set(sum(GENERATION.values(), []))
    author_samples = {sample_seed(worker_seed, suite, s) for suite in ("development", "frozen")
                      for s in GENERATION[suite]}
    ids, seeds, samples = set(), set(), set()
    for row in entries:
        if not isinstance(row, dict) or not required <= row.keys():
            raise ValueError("fresh entry requires instance_id/generation_seed/sampling_seed/alpha/theta")
        seed, sampling, identity = row["generation_seed"], row["sampling_seed"], row["instance_id"]
        if not isinstance(identity, str) or not identity or identity in ids:
            raise ValueError("fresh instance IDs must be unique strings")
        if type(seed) is not int or seed not in GENERATION["fresh"] or seed in seeds:
            raise ValueError("fresh generation seeds must be the specified unique fresh range")
        if type(sampling) is not int or sampling < 0 or sampling == worker_seed or sampling in samples or sampling in all_generation or sampling in author_samples:
            raise ValueError("fresh sampling seeds must be distinct independent nonnegative integers")
        expected = generated(seed)
        if any(not isinstance(row[k], (int, float)) or not math.isfinite(row[k]) or
               abs(row[k]-expected[k]) > 1e-14 for k in expected):
            raise ValueError("fresh parameters disagree with declared seed/distribution")
        ids.add(identity); seeds.add(seed); samples.add(sampling)
    return obj


def cases(suite, seed, independent=None):
    if suite == "quick":
        return [{"instance_id": f"quick-{i}", "generation_seed": frozen_recipe(i)["seed"],
                 "sampling_seed": sample_seed(seed, "quick", i),
                 "alpha": frozen_recipe(i)["alpha"], "theta": frozen_recipe(i)["theta"]} for i in (0, 1, 2)]
    if suite == "fresh":
        return sorted(independent["manifests"], key=lambda r: r["generation_seed"])
    return [dict(instance_id=f"{suite}-{i:02}", generation_seed=s,
                 sampling_seed=sample_seed(seed, suite, s), **generated(s))
            for i, s in enumerate(GENERATION[suite])]


def regimes(quick=False):
    result = [{"id": "ideal", "config": None}]
    if quick:
        return result + [{"id": "aria-s1", "config": configuration()}]
    for model in ("aria", "forte", "forte-enterprise"):
        for scale in (.5, .75, 1, 1.25, 1.5, 1.75, 2):
            result.append({"id": f"{model}-s{scale:g}", "config": configuration(model, scale)})
        for key in ("one_factor", "two_factor"):
            for factor in (.75, 1.25):
                result.append({"id": f"{model}-{key}-{factor}", "config": configuration(model, **{key: factor})})
        for rate in (.001, .005):
            result.append({"id": f"{model}-readout-{rate}", "config": configuration(model, readout=rate)})
        for shift in (-.01, .01):
            result.append({"id": f"{model}-source-{shift}", "config": configuration(model, source_imbalance=shift)})
    return result


def build_case(case, recipe, regime):
    params = dict(frozen_recipe(0), **recipe)
    params.update(alpha=case["alpha"], theta=case["theta"], seed=case["generation_seed"],
                  identity=case["instance_id"])
    cfg = regime["config"]
    if cfg is not None:
        params["alpha"] += cfg.get("source_imbalance", 0.)
    circuits, manifest = core.make_demo(0, recipe=params)
    return circuits, manifest


def simulation_config(regime):
    return dict(regime["config"], source_imbalance=0.) if regime["config"] is not None else configuration(scale=0.)


def metrics(p, manifest):
    result = {}
    for name, decode in zip(manifest["ordered_blocks"], manifest["decoding_maps"]):
        joint = dict.fromkeys(("FF", "FP", "PF", "PP"), 0.)
        for i, value in enumerate(p[name]):
            key = "".join("P" if all(not ((i >> bit) & 1) for bit in bits) else "F"
                          for bits in decode["test_pass_cbits"])
            joint[key] += float(value)
        mean = joint["FP"]+joint["PF"]+2*joint["PP"]
        result[name] = {"f": joint["FF"], "m": mean,
                        "loss": joint["FF"]+manifest["parameters"]["lambda_star"]*(2-mean)}
    return result


def vector(hist):
    p = np.zeros(16)
    for key, value in hist.items():
        p[int(key, 2)] += value
    if p.sum() <= 0:
        raise ValueError("empty histogram")
    return p/p.sum()


def certify(circuits, manifest, regime, quick=False):
    params = manifest["parameters"]
    if regime["id"] == "ideal":
        certificate = ideal_certificate(params["alpha"], params["theta"])
    elif quick:
        return {"status": "NOT_RUN", "reason": "quick mode forbids noisy SDP certification"}
    else:
        source, effect = product_tester(circuits[0], simulation_config(regime))
        certificate = solve_product_tester(source, effect, max_gap=1e-4)
    bound = product_tail_lower_bound(certificate["dual_upper_bound"], certificate["dual_upper_bound"],
                                     lambda_value=params["lambda_star"])
    return {"status": "CERTIFIED", "same_certificate_applies_to_tests": [0, 1],
            "certificate": certificate, "bound": bound}


def evaluate(case, recipe, regime, shots, replicates, quick=False):
    circuits, manifest = build_case(case, recipe, regime)
    cfg = simulation_config(regime)
    probs = {n: probabilities(c, cfg, ideal=regime["id"] == "ideal").tolist()
             for n, c in zip(manifest["ordered_blocks"], circuits)}
    failure = None
    try:
        certificate = certify(circuits, manifest, regime, quick)
    except (ValueError, RuntimeError) as exc:
        failure = str(exc)
        certificate = {"status": "FAILED", "reason": failure}
    counts, paired = [], []
    for rep in range(replicates):
        h = {name: histogram(p, shots, sample_seed(case["sampling_seed"], regime["id"], rep, name))
             for name, p in probs.items()}
        analysis = core.analyze_counts(h, manifest, confidence=.975)
        counts.append(h)
        paired.append({r["block"]: {k: r[k] for k in ("f", "m", "loss", "double_failure_upper_if_zero")}
                       for r in analysis["results"]})
    gates = {name: {"one_qubit": sum(len(i.qubits) == 1 and i.operation.name != "measure" for i in c.data),
                    "two_qubit": sum(len(i.qubits) == 2 for i in c.data),
                    "measurement": sum(i.operation.name == "measure" for i in c.data)}
             for name, c in zip(manifest["ordered_blocks"], circuits)}
    return {"instance_id": case["instance_id"], "case": case, "regime": regime["id"],
            "configuration": regime["config"], "manifest": manifest, "manifest_hash": digest(manifest),
            "source": "mathematical reference" if regime["id"] == "ideal" else "local IonQ-like approximation",
            "probabilities": probs, "exact_metrics": metrics(probs, manifest), "counts": counts,
            "paired_replicates": paired, "certificate": certificate, "failure": failure,
            "sampling": {"root_seed": case["sampling_seed"], "algorithm": "sha256(root,regime,rep,block)[:16]; numpy multinomial",
                         "shots_per_arm_per_replicate": shots, "replicates": replicates,
                         "arm_covariance": "zero by local independent-block model; not observed cloud covariance"},
            "resources": {"max_simulated_qubits": 4, "physical_packed_width": 16,
                          "submitted_gates_per_arm": gates, "games_per_arm": shots*replicates,
                          "submitted_operation_shots": shots*replicates*sum(g["one_qubit"]+g["two_qubit"] for g in gates.values()),
                          "native_gate_cost": None}}


def contrasts(ideal, noisy, ideal_metrics, noisy_metrics):
    ib = ideal["certificate"]["bound"]
    nb = noisy["certificate"]["bound"]
    return np.array([.75*nb["double_failure_lower_bound"]-noisy_metrics["optimized_joint"]["f"],
                     ib["loss_lower_bound"]-ideal_metrics["optimized_joint"]["loss"]-.005,
                     noisy_metrics["optimized_joint"]["loss"]-noisy_metrics["attained_product"]["loss"]-.005])


def paired_entries(entries):
    groups = {}
    for e in entries:
        if e["regime"] in ("ideal", "aria-s1"):
            groups.setdefault(e["instance_id"], {})[e["regime"]] = e
    if not groups or any(set(g) != {"ideal", "aria-s1"} for g in groups.values()):
        raise ValueError("primary inference needs paired ideal and nominal aria entries")
    pairs = [(g["ideal"], g["aria-s1"]) for key, g in sorted(groups.items())]
    if any(e["certificate"]["status"] != "CERTIFIED" for pair in pairs for e in pair):
        raise ValueError("primary inference requires all product certificates")
    return pairs


def _resampled_metrics(entry, rng):
    h = entry["counts"][0]
    draws = {name: rng.multinomial(sum(counts.values()), vector(counts)) for name, counts in h.items()}
    return metrics({k: v/v.sum() for k, v in draws.items()}, entry["manifest"])


def inference(entries, draws=2000, seed=271828):
    pairs = paired_entries(entries)
    rng = np.random.default_rng(seed)
    observed = np.array([contrasts(i, n, i["paired_replicates"][0], n["paired_replicates"][0]) for i, n in pairs])
    estimate = observed.mean(axis=0)
    bootstrap = []
    for _ in range(draws):
        values = []
        for index in rng.integers(0, len(pairs), len(pairs)):
            i, n = pairs[index]
            values.append(contrasts(i, n, _resampled_metrics(i, rng), _resampled_metrics(n, rng)))
        bootstrap.append(np.mean(values, axis=0))
    lower = 2*estimate-np.quantile(bootstrap, 1-ALPHA, axis=0)
    # Empirical bootstrap has no unseen FF mass. Protect zero-cell boundaries
    # with simultaneous exact FF upper bounds, not a zero-width bootstrap claim.
    # Correct only the missing-count component, keeping instance variability.
    correction = np.zeros(3)
    for ideal, noisy in pairs:
        for entry, component in ((noisy, 0), (ideal, 1)):
            row = core.analyze_counts(entry["counts"][0], entry["manifest"])["results"][2]
            if row["outcome_counts"]["FF"] == 0:
                correction[component] += interval(0, row["shots"], 1-ALPHA/len(pairs), True)[1]/len(pairs)
    lower -= correction
    signs = rng.choice([-1., 1.], size=(draws, len(pairs), 1))
    null = ((observed-estimate)[None, :, :]*signs).mean(axis=1)
    p = (1+np.sum(null >= estimate, axis=0))/(draws+1)
    h1 = bool(lower[0] > 0)
    h2 = bool(lower[1] > 0 and lower[2] > 0)
    return {"estimate": estimate.tolist(), "lower_97_5": lower.tolist(), "zero_cell_correction": correction.tolist(),
            "contrasts": [".75*certified_product_f_lower-noisy_joint_f", "ideal_product_loss_lower-ideal_joint_loss-.005",
                          "noisy_joint_loss-noisy_attained_product_loss-.005"],
            "diagnostic_centered_sign_flip_p": p.tolist(), "H1": h1, "H2": h2, "both": h1 and h2,
            "n_instances": len(pairs), "replicate_for_primary": 0, "bootstrap_draws": draws, "seed": seed,
            "method": "paired nested instance-count basic bootstrap; independent local blocks; symmetric sign-flip diagnostic",
            "scope": "local approximation only; no independent science verdict"}


def resample_packed(raw_counts, layout, seed):
    """Resample one actual packed histogram as whole keys, preserving arm covariance."""
    from circuit_pack import unpack_counts
    unpack_counts(raw_counts, layout)  # Validate before generating anything.
    total = sum(raw_counts.values())
    if total <= 0:
        raise ValueError("empty packed histogram")
    keys = list(raw_counts)
    counts = np.random.default_rng(seed).multinomial(total, np.array(list(raw_counts.values()))/total)
    raw = {k: int(v) for k, v in zip(keys, counts) if v}
    return raw, unpack_counts(raw, layout)


def projected_power(entries, seed, outer=200, inner=200):
    pairs = paired_entries(entries)
    rng = np.random.default_rng(seed)
    successes = np.zeros(2, int)
    started = time.monotonic()
    for trial in range(outer):
        synthetic = []
        for number, index in enumerate(rng.integers(0, len(pairs), 8)):
            for source in pairs[index]:
                entry = dict(source, instance_id=f"projection-{number}")
                hist = {name: histogram(p, 4000, int(rng.integers(0, 2**63))) for name, p in source["probabilities"].items()}
                rows = core.analyze_counts(hist, source["manifest"])["results"]
                entry["counts"] = [hist]
                entry["paired_replicates"] = [{r["block"]: {k: r[k] for k in ("f", "m", "loss")} for r in rows}]
                synthetic.append(entry)
        decision = inference(synthetic, draws=inner, seed=int(rng.integers(0, 2**63)))
        successes += [decision["H1"], decision["H2"]]
        if (trial+1) % 10 == 0:
            eta = (time.monotonic()-started)/(trial+1)*(outer-trial-1)
            print(f"power [{trial+1}/{outer}] ETA={eta:.1f}s", flush=True)
    return {"H1": float(successes[0]/outer), "H2": float(successes[1]/outer),
            "outer": outer, "inner": inner, "seed": seed, "projected_cases": 8, "shots_per_arm": 4000,
            "mc_intervals": [interval(int(k), outer, .95) for k in successes],
            "source": "development exact local probabilities; optimistic after selection; cloud calibration required"}


def gate_decision(power, calibration_path, gate, selection_hash, calibration_power_path=None):
    reasons = []
    calibration = None
    if power is None:
        reasons.append("development projected power unavailable")
    elif min(power["H1"], power["H2"]) < .8:
        reasons.append("development projected power below .8")
    if not calibration_path:
        reasons.append("measured N02 4000-shot feasibility missing")
    else:
        from receipt import parse_records
        records, issues = parse_records(Path(calibration_path).read_text(encoding="utf-8"))
        matching = [r for r in records if r["case_id"] == 0 and r["noise_model"] == "aria-1" and r["shots"] == 4000
                    and abs(r["parameters"].get("alpha", -1)-math.pi/4) < 1e-12
                    and abs(r["parameters"].get("theta", -1)-math.pi/8) < 1e-12]
        if issues or len(matching) != 1:
            reasons.append("calibration must contain one valid anchor aria 4000-shot receipt")
        else:
            calibration = matching[0]
            export = ROOT / calibration["source_file"]
            if not export.is_file():
                reasons.append("original N02 source export missing")
            else:
                exported, errors = parse_records(export.read_text(encoding="utf-8"))
                if not any(digest(r) == digest(calibration) for r in exported):
                    reasons.append("N02 receipt absent from original source export")
    calibrated = None
    if gate == "g2":
        if not calibration_power_path:
            reasons.append("independent calibration power analysis missing")
        else:
            calibrated = read_json(calibration_power_path)
            if not isinstance(calibrated, dict) or calibrated.get("independent") is not True or not calibrated.get("author") or \
                    calibrated.get("selection_hash") != selection_hash or calibration is None or \
                    calibrated.get("calibration_hash") != digest(calibration):
                reasons.append("calibration power evidence identity invalid")
            elif any(not isinstance(calibrated.get(k), (int, float)) or not 0 <= calibrated[k] <= 1 for k in ("H1", "H2")):
                reasons.append("invalid calibration powers")
            elif min(calibrated["H1"], calibrated["H2"]) < .8:
                reasons.append("calibration projected power below .8")
    return {"gate": gate, "status": "BLOCKED" if reasons else "PASS", "reasons": reasons,
            "development_power": power, "calibration_power": calibrated,
            "calibration_hash": digest(calibration) if calibration else None,
            "scope": "resource gate only; never science PASS"}


def development_search(case_list, state, save, seed):
    ledger = state.setdefault("search", [])
    # Certificates are independent of joint recipe and lambda; solve once/game/regime.
    certificates = state.setdefault("development_certificates", {})
    for case in case_list:
        for regime in regimes(True):
            key = case["instance_id"]+":"+regime["id"]
            if key not in certificates:
                circuits, manifest = build_case(case, frozen_recipe(0), regime)
                try:
                    certificates[key] = certify(circuits, manifest, regime)
                except (ValueError, RuntimeError) as exc:
                    state["search_failure"] = {"instance_regime": key, "reason": str(exc), "utc": utc()}
                    save()
                    raise ValueError(f"development certification failed for {key}: {exc}") from exc
                save()
    expected = len(LAMBDA_MENU)*256
    start = time.monotonic()
    for li, lam in enumerate(LAMBDA_MENU):
        rng = np.random.default_rng(sample_seed(seed, "search", li))
        for ci in range(256):
            candidate = {"joint_phase": math.pi, "local_phase": 0., "local_rotation": 0., "lambda_star": lam}
            if ci:
                candidate.update(joint_phase=float(rng.uniform(0, 2*math.pi)), local_phase=float(rng.uniform(-math.pi, math.pi)),
                                 local_rotation=float(rng.uniform(-math.pi/4, math.pi/4)))
            index = li*256+ci
            if index < len(ledger):
                continue
            scores = []
            for case in case_list:
                results = []
                for regime in regimes(True):
                    circuits, manifest = build_case(case, candidate, regime)
                    cfg = simulation_config(regime)
                    # Product and joint get identical candidate/game/regime evaluation counts.
                    p = {name: probabilities(circuits[core.BLOCKS.index(name)], cfg, ideal=regime["id"] == "ideal")
                         for name in ("attained_product", "optimized_joint")}
                    reduced = dict(manifest, ordered_blocks=list(p), decoding_maps=[manifest["decoding_maps"][0]]*2)
                    results.append(metrics(p, reduced))
                i, n = results
                ip = certificates[case["instance_id"]+":ideal"]["certificate"]["dual_upper_bound"]
                npass = certificates[case["instance_id"]+":aria-s1"]["certificate"]["dual_upper_bound"]
                ib = product_tail_lower_bound(ip, ip, lambda_value=lam)
                nb = product_tail_lower_bound(npass, npass, lambda_value=lam)
                scores.append([.75*nb["double_failure_lower_bound"]-n["optimized_joint"]["f"],
                               ib["loss_lower_bound"]-i["optimized_joint"]["loss"]-.005,
                               n["optimized_joint"]["loss"]-n["attained_product"]["loss"]-.005])
            average = np.mean(scores, axis=0)
            ledger.append({"lambda_index": li, "candidate_index": ci, "parameters": candidate,
                           "margins": average.tolist(), "score": float(average.min())})
            save()
            if (index+1) % 16 == 0:
                elapsed = time.monotonic()-start
                print(f"search [{index+1}/{expected}] ETA={elapsed/max(1,index+1)*(expected-index-1):.1f}s", flush=True)
    winner = max(ledger, key=lambda row: row["score"])
    selection = {"schema": SCHEMA, "development_seeds": GENERATION["development"],
                 "parameters": dict(winner["parameters"], lambda_selection="development-only maximin margins",
                                    optimized_status="restricted joint search; no general optimality claim"),
                 "evaluations_per_class_per_lambda": 256,
                 "class_evaluations": {"attained_product": expected, "optimized_joint": expected},
                 "probability_evaluations_per_class": expected*len(case_list)*2,
                 "product_search": "identity singleton; repeated identical evaluations; CPTP certificates separate",
                 "certificate_solver_calls": len(case_list), "development_certificates": certificates,
                 "search_seed": seed, "search_ledger": ledger}
    selection["hash"] = digest(selection)
    return selection


def _figures(path, suite, entries):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pairs = paired_entries(entries)
    x = np.arange(len(pairs))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(x, [n["exact_metrics"]["optimized_joint"]["f"] for i, n in pairs], "o-", color="#0072B2", label="Joint, local aria")
    ax.plot(x, [n["certificate"]["bound"]["double_failure_lower_bound"] for i, n in pairs], "s--", color="#D55E00", label="Certified product lower bound")
    ax.set(xlabel="Generated game index (not shots)", ylabel="Double failure probability", title=f"{suite}: local approximation")
    ax.legend(); fig.tight_layout()
    fig.savefig(path / f"{suite}-tails.png", dpi=150)
    plt.close(fig)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="only anchor+2 development games, 128 shots, <=2 reps; no science verdict")
    p.add_argument("--suite", choices=("development", "frozen", "fresh"), help="FULL orchestrator-only campaign")
    p.add_argument("--gate", choices=("g1", "g2"), help="development power and measured calibration gate")
    p.add_argument("--recipe", help="hashed development selection JSON; required for frozen/fresh")
    p.add_argument("--independent-manifest", help="verifier-owned 24 fresh games and distinct sampling seeds")
    p.add_argument("--calibration", help="validated N02 RECORD_JSON file; no cloud submission")
    p.add_argument("--calibration-power", help="independent G2 calibration power JSON")
    p.add_argument("--resume", action="store_true", help="resume identical input/source/configuration checkpoint")
    p.add_argument("--output-dir", default="results", help="output directory; quick always uses quick-n-* filenames")
    p.add_argument("--replicates", type=int, help="quick only, 1 or 2; full budget is fixed at 200")
    p.add_argument("--draws", type=int, help="quick-only replicate bound, 1 or 2")
    p.add_argument("--seed", type=int, default=314159)
    return p


def validate_args(args):
    if args.quick == bool(args.suite):
        raise ValueError("choose exactly one of --quick or --suite")
    if args.seed < 0:
        raise ValueError("seed must be nonnegative")
    if args.quick:
        if any((args.resume, args.independent_manifest, args.gate, args.calibration, args.calibration_power, args.recipe)):
            raise ValueError("--quick conflicts with resume/manifest/gate/calibration/recipe")
        if any(n is not None and not 1 <= n <= 2 for n in (args.replicates, args.draws)):
            raise ValueError("quick draws/replicates must be 1 or 2")
    elif args.draws is not None or args.replicates is not None:
        raise ValueError("full suite budgets cannot be reduced with draws/replicates")
    if args.suite == "fresh" and not args.independent_manifest:
        raise ValueError("--suite fresh requires --independent-manifest PATH")
    if args.suite != "fresh" and args.independent_manifest:
        raise ValueError("independent manifest is fresh-only")
    if args.suite in ("frozen", "fresh") and not args.recipe:
        raise ValueError("frozen/fresh requires --recipe development-selection.json")
    if args.suite == "development" and args.recipe:
        raise ValueError("development selects its recipe; do not supply --recipe")
    if args.gate and args.suite != "development":
        raise ValueError("gate decisions run only with development suite")
    if (args.calibration or args.calibration_power) and not args.gate:
        raise ValueError("calibration inputs require --gate")


def run(args):
    validate_args(args)
    suite = "quick" if args.quick else args.suite
    selection = _selection(args.recipe) if args.recipe else None
    independent = _manifest_from_json(args.independent_manifest, selection["hash"], args.seed) if args.independent_manifest else None
    case_list = cases(suite, args.seed, independent)
    regime_list = regimes(args.quick)
    reps = min(args.draws or 2, args.replicates or 2) if args.quick else 200
    shots = 128 if args.quick else 4000
    source_paths = [ROOT / name for name in ("core.py", "strategies.py", "product_bounds.py", "experiments/run.py", "experiments/noise.py", "experiments/PLAN.md")]
    config = {"schema": SCHEMA, "suite": suite, "seed": args.seed, "shots": shots, "replicates": reps,
              "versions": {name: importlib.metadata.version(name) for name in ("qiskit", "numpy", "scipy", "matplotlib")},
              "regimes": regime_list, "cases": case_list, "selection_hash": selection["hash"] if selection else None,
              "independent_manifest": independent, "gate": args.gate,
              "calibration_file_hash": hashlib.sha256(Path(args.calibration).read_bytes()).hexdigest() if args.calibration else None,
              "calibration_power_file_hash": hashlib.sha256(Path(args.calibration_power).read_bytes()).hexdigest() if args.calibration_power else None,
              "sources": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}
    config_hash = digest(config)
    output = Path(args.output_dir)
    if not output.is_absolute():
        output = ROOT/output
    stem = "quick-n-dev" if args.quick else suite
    path = output/f"{stem}.json"
    checkpoint = output/f"{stem}-checkpoint.json"
    if not args.quick and not args.resume and (path.exists() or checkpoint.exists()):
        raise ValueError("existing full evidence: use --resume or another output-dir")
    output.mkdir(parents=True, exist_ok=True)
    state = {"started_utc": utc(), "configuration_hash": config_hash, "instances": [], "search": []}
    if args.resume:
        if not checkpoint.exists():
            raise ValueError("resume checkpoint missing")
        state = read_json(checkpoint)
        if state.get("configuration_hash") != config_hash:
            raise ValueError("checkpoint input/source/configuration mismatch")
    def save():
        if not args.quick:
            write_json(checkpoint, state)
    if suite == "development":
        selection = development_search(case_list, state, save, args.seed)
        write_json(output/"development-selection.json", selection)
    recipe = selection["parameters"] if selection else frozen_recipe(0)
    done = {(e["instance_id"], e["regime"]) for e in state["instances"]}
    total = len(case_list)*len(regime_list)
    started = time.monotonic()
    completed_now = 0
    for case in case_list:
        for regime in regime_list:
            if (case["instance_id"], regime["id"]) in done:
                continue
            entry = evaluate(case, recipe, regime, shots, reps, args.quick)
            state["instances"].append(entry)
            completed_now += 1
            save()
            count = len(state["instances"])
            eta = (time.monotonic()-started)/completed_now*(total-count)
            print(f"[{count}/{total}] {case['instance_id']} {regime['id']} ETA={eta:.1f}s", flush=True)
    entries = state["instances"]
    failures = [{"instance_id": e["instance_id"], "regime": e["regime"], "reason": e["failure"]} for e in entries if e["failure"]]
    decision, power, gate = None, None, None
    if not args.quick:
        try:
            if failures:
                raise ValueError("one or more regime certificates failed; no primary verdict")
            decision = state.get("decision") or inference(entries, seed=sample_seed(args.seed, "inference"))
            state["decision"] = decision; save()
            _figures(output, suite, entries)
            if args.gate:
                power = state.get("power") or projected_power(entries, sample_seed(args.seed, "power"))
                state["power"] = power; save()
        except ValueError as exc:
            decision = {"status": "INCONCLUSIVE", "reason": str(exc)}
        if args.gate:
            gate = gate_decision(power, args.calibration, args.gate, selection["hash"], args.calibration_power)
    doc = {"schema_version": SCHEMA, "suite": suite, "source": "local IonQ-like approximation",
           "science_verdict": "NONE: implementation handoff; independent verification and Qollab evidence required",
           "status": "COMPLETE_WITH_FAILURES" if failures else "COMPLETE",
           "started_utc": state["started_utc"], "finished_utc": utc(), "machine": platform.platform(),
           "versions": {name: importlib.metadata.version(name) for name in ("qiskit", "numpy", "scipy", "matplotlib")},
           "python": sys.version, "configuration": config, "configuration_hash": config_hash,
           "selection": selection, "instances": entries, "failed_cases": failures,
           "primary_local_decisions": decision, "projected_power": power, "gate_decision": gate,
           "resource_ledger": {"independent_games": len(case_list), "entries": len(entries),
                               "replicates_per_entry": reps, "shots_per_arm_per_replicate": shots,
                               "cloud_attempts_used": 0, "cloud_attempts_preregistered": 18},
           "assumptions": ["independent local block noise/sampling; not observed packed cloud covariance",
                           "submitted operation-shots are not native gates/cost", "product_control noisy circuit is diagnostic only"]}
    write_json(path, doc)
    print(f"saved {path}", flush=True)
    return path


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
