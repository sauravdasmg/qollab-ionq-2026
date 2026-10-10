"""Local evidence harness. Full suites are implemented for orchestrator execution only."""
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
from scipy.stats import beta
import core
from product_bounds import ideal_product_pass
from strategies import frozen_recipe, DEVELOPMENT_SEEDS, LAMBDA_MENU
from experiments.noise import configuration, probabilities, histogram


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def interval(k, n, confidence=.95, one_sided=False):
    if n <= 0 or k < 0 or k > n:
        raise ValueError("invalid binomial observations")
    a = 1-confidence
    if one_sided:
        return [0. if k == 0 else float(beta.ppf(a, k, n-k+1)),
                1. if k == n else float(beta.ppf(confidence, k+1, n-k))]
    return [0. if k == 0 else float(beta.ppf(a/2, k, n-k+1)),
            1. if k == n else float(beta.ppf(1-a/2, k+1, n-k))]


def _canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _draw(marginals, manifest, *, reps, seed, cfg, ideal=False):
    totals = {n: {} for n in manifest["ordered_blocks"]}
    circuits, _ = core.make_demo(manifest["case_id"], recipe=manifest["parameters"])
    for rep in range(reps):
        for name, circuit in zip(manifest["ordered_blocks"], circuits):
            p = probabilities(circuit, cfg, ideal=ideal)
            h = histogram(p, 128, seed + rep * 101 + manifest["case_id"] * 1009 + len(name))
            for key, val in h.items(): totals[name][key] = totals[name].get(key, 0) + val
    return core.analyze_counts(totals, manifest)


def _manifest_from_json(path):
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load independent manifest: {exc}") from exc
    manifests = obj if isinstance(obj, list) else obj.get("manifests") if isinstance(obj, dict) else None
    if not manifests or not isinstance(manifests, list):
        raise ValueError("independent manifest file must contain a non-empty manifests list")
    required = {"case_id", "seed", "parameters", "recipe_hash"}
    for item in manifests:
        if not isinstance(item, dict) or not required <= item.keys():
            raise ValueError("each independent manifest requires case_id, seed, parameters, recipe_hash")
        if item["case_id"] in range(0, 33):
            raise ValueError("fresh case IDs must be distinct from anchor/development/frozen IDs")
        if item["seed"] is None:
            raise ValueError("fresh instances require independent sampling seeds")
        if not isinstance(item["recipe_hash"], str) or len(item["recipe_hash"]) != 64:
            raise ValueError("fresh recipe_hash must be sha256 hex")
    return manifests


def _suite_cases(suite, independent):
    if suite == "development": return list(range(1, 9))
    if suite == "frozen": return list(range(1, 9)) + list(range(9, 25))
    if suite == "fresh": return [int(x["case_id"]) for x in independent]
    return [0, 1, 2]


def _result_doc(suite, entries, *, seed, cfg, lambda_value, status, started, search_evals=0):
    return {"schema_version": "1.0.0", "suite": suite, "source": "local IonQ-like approximation",
            "science_verdict": "NONE — harness output; independent claim verification required",
            "started_utc": started, "finished_utc": utc(), "machine": platform.platform(),
            "python": sys.version, "numpy": np.__version__, "configuration": cfg,
            "configuration_hash": _canonical_hash(cfg), "sampling_seed": seed,
            "lambda": lambda_value, "search_evaluations": search_evals,
            "status": status, "instances": entries,
            "assumptions": ["local density-channel approximation", "IID multinomial shots within each block",
                            "packed-block covariance is unavailable locally", "operation-shot counts are not native gate cost"]}


def run(args):
    started = utc(); t0 = time.monotonic()
    output = Path(args.output_dir)
    if not output.is_absolute(): output = ROOT / output
    output.mkdir(parents=True, exist_ok=True)
    if args.quick and (args.suite or args.resume or args.independent_manifest or args.gate):
        raise ValueError("--quick conflicts with suite, resume, gate, or independent-manifest options")
    if args.quick and not output.name.startswith("quick-"):
        raise ValueError("--quick requires --output-dir whose final component starts with quick-")
    if args.suite is None and not args.quick:
        raise ValueError("choose --quick or --suite")
    independent = _manifest_from_json(args.independent_manifest) if args.independent_manifest else None
    if args.suite == "fresh" and independent is None:
        raise ValueError("--suite fresh requires --independent-manifest PATH")
    if args.suite != "fresh" and args.independent_manifest:
        raise ValueError("--independent-manifest is valid only with --suite fresh")
    if args.gate and (args.suite != "development" or args.gate != "g1"):
        raise ValueError("--gate g1 is defined only for the development suite")
    if args.quick:
        cases, reps, regimes = [0, 1, 2], min(args.replicates, 2), [("ideal", None), ("aria", configuration("aria"))]
        suite, seed = "quick-n-dev", args.seed
    else:
        cases, reps = _suite_cases(args.suite, independent), args.replicates
        regimes = [(name, configuration(name, scale)) for name in ("aria", "forte", "forte-enterprise")
                   for scale in (.5,.75,1,1.25,1.5,1.75,2)]
        regimes = [("ideal", None)] + regimes + [("aria-readout-001", configuration("aria", readout=.001)),
                   ("aria-readout-005", configuration("aria", readout=.005))]
        suite, seed = args.suite, args.seed
    if args.draws is not None:
        reps = min(reps, max(1, args.draws))
    if args.resume:
        checkpoint = output / f"{suite}-checkpoint.json"
        if checkpoint.exists():
            prior = json.loads(checkpoint.read_text(encoding="utf-8"))
            if prior.get("configuration_hash") != _canonical_hash([suite, seed, reps, regimes, cases]):
                raise ValueError("checkpoint configuration does not match requested deterministic run")
            done = {(e["case_id"], e["regime"]) for e in prior.get("instances", [])}
        else: prior, done = {"instances": []}, set()
    else:
        prior, done = {"instances": []}, set()
    entries = list(prior["instances"]); total = len(cases) * len(regimes); finished = len(done)
    for case in cases:
        for regime, cfg in regimes:
            if (case, regime) in done: continue
            started_case = time.monotonic()
            if args.quick:
                circuits, manifest = core.make_demo(case)
            elif regime == "ideal":
                circuits, manifest = core.make_demo(case)
            elif args.suite == "fresh":
                source = next(x for x in independent if x["case_id"] == case)
                if int(source["seed"]) == seed: raise ValueError("independent sampling seed must differ from worker seed")
                manifest = source
            else:
                manifest = core.make_demo(case)[1] if case <= 8 else None
                if manifest is None:
                    raise ValueError("frozen IDs 9..24 require verifier-staged complete recipe manifests")
                circuits, manifest = core.make_demo(case)
            if args.suite == "fresh":
                circuits, generated = core.make_demo(0, recipe=manifest["parameters"])
                manifest = dict(generated, case_id=case, seed=source["seed"], recipe_hash=source["recipe_hash"])
            analysis = _draw(None, manifest, reps=reps, seed=seed, cfg=cfg, ideal=regime == "ideal")
            entry = {"case_id": case, "regime": regime, "manifest": manifest,
                     "manifest_hash": _canonical_hash(manifest), "results": analysis["results"],
                     "generation_seed": manifest.get("seed"), "sampling_seed": seed,
                     "shots_per_strategy": 128 * reps, "operation_shots": 128 * reps * len(manifest["ordered_blocks"]),
                     "elapsed_seconds": time.monotonic()-started_case}
            entries.append(entry); finished += 1
            eta = (time.monotonic()-t0) / max(finished,1) * (total-finished)
            print(f"[{finished}/{total}] case={case} regime={regime} ETA={eta:.1f}s", flush=True)
            doc = _result_doc(suite, entries, seed=seed, cfg=cfg, lambda_value=args.lambda_value,
                              status="INCOMPLETE" if finished < total else "COMPLETE; no science verdict", started=started)
            doc["configuration_hash"] = _canonical_hash([suite, seed, reps, regimes, cases])
            (output / f"{suite}-checkpoint.json").write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    doc = _result_doc(suite, entries, seed=seed, cfg={"regimes": [x[0] for x in regimes]},
                      lambda_value=args.lambda_value, status="COMPLETE; no science verdict", started=started)
    path = output / f"{suite}.json"
    path.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    print(f"saved {path}", flush=True)
    if args.gate:
        raise RuntimeError("G1 power gate requires preregistered paired power analysis; it is not inferred from smoke results")
    return path


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="bounded engineering smoke; no science verdict")
    p.add_argument("--suite", choices=("development", "frozen", "fresh"))
    p.add_argument("--gate", choices=("g1",))
    p.add_argument("--independent-manifest")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--output-dir", default="results")
    p.add_argument("--replicates", type=int, default=200)
    p.add_argument("--draws", type=int)
    p.add_argument("--seed", type=int, default=314159)
    p.add_argument("--lambda-value", type=float, default=.02)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.replicates <= 0 or (args.draws is not None and args.draws <= 0):
        raise SystemExit("replicates/draws must be positive")
    try: run(args)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
