"""Preregistered local evidence harness. Full campaigns are orchestrator-invoked."""
import argparse
import hashlib
import json
import math
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np
import core
from experiments import noise
from synthesis import bounded_search, equal_budget_search, FAMILIES


SUITES = {'development': tuple(range(1, 9)), 'frozen': tuple(range(9, 29))}
FAMILIES_LOCAL = ('collective', 'textbook', 'deferred-sequential')
Z975 = 1.959963984540054


def wilson(successes, n, z=Z975):
    if n <= 0 or successes < 0 or successes > n:
        raise ValueError('require 0 <= successes <= n and n > 0')
    p = successes/n
    den = 1+z*z/n
    center = (p+z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0, center-half), min(1, center+half)]


def paired_bootstrap(differences, seed=0, replicates=2000):
    """Percentile interval resampling generated instances, never packed blocks."""
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
        raise ValueError('need at least two finite paired instance differences')
    if replicates < 100:
        raise ValueError('at least 100 bootstrap replicates are required')
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(replicates, len(values)))
    means = values[indices].mean(axis=1)
    return {'mean': float(values.mean()), 'interval_95': [float(x) for x in np.quantile(means, [.025, .975])],
            'replicates': int(replicates), 'seed': int(seed), 'resampling_unit': 'generated instance'}


def paired_permutation(differences, seed=0, replicates=10000):
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
        raise ValueError('need at least two finite paired differences')
    rng = np.random.default_rng(seed)
    observed = float(values.mean())
    signs = rng.choice((-1.0, 1.0), size=(replicates, len(values)))
    p = (1+np.count_nonzero((signs*values).mean(axis=1) >= observed))/(replicates+1)
    return {'mean': observed, 'one_sided_p': float(p), 'replicates': int(replicates), 'seed': int(seed)}


def gate_decisions(results, alpha=.025):
    """Conservative paired t lower bounds, adjusted separately at alpha=.025."""
    from scipy.stats import t
    h1 = np.asarray(results['seq_minus_joint'], dtype=float)
    h2 = np.asarray(results['relative_textbook_margin'], dtype=float)
    def lower(x):
        if x.ndim != 1 or len(x) < 2 or not np.all(np.isfinite(x)):
            raise ValueError('gate requires at least two finite paired instances')
        return float(x.mean()-t.ppf(1-alpha, len(x)-1)*x.std(ddof=1)/math.sqrt(len(x)))
    lo1, lo2 = lower(h1), lower(h2)
    return {'alpha_per_test': alpha, 'h1_lower': lo1, 'h1_threshold': .010, 'h1_pass': lo1 > .010,
            'h2_lower': lo2, 'h2_threshold': 0.0, 'h2_pass': lo2 > 0,
            'gate_pass': lo1 > .010 and lo2 > 0,
            'method': 'one-sided Student t lower bounds, alpha .025 each (Bonferroni family alpha .05)'}


def _measurement_probabilities(circuit):
    from qiskit.quantum_info import Statevector
    sv = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
    n = circuit.num_qubits
    return {format(i, f'0{n}b'): float(abs(v)**2) for i, v in enumerate(sv.data)}


def _density_probabilities(circuit, model, scale, readout=None, staged=None, source_noise=True):
    from qiskit.quantum_info import DensityMatrix, Operator
    config = noise.effective_config(model, scale, readout, staged)
    qc = noise.compile_circuit(circuit.remove_final_measurements(inplace=False), model)
    rho = DensityMatrix.from_int(0, 2**qc.num_qubits)
    rates = config['rates']
    in_source = any(item.operation.name == 'barrier' and
                    item.operation.label == 'receiver_start' for item in qc.data)
    for item in qc.data:
        op = item.operation
        if op.name == 'barrier':
            if op.label == 'receiver_start':
                in_source = False
            continue
        qubits = [qc.find_bit(q).index for q in item.qubits]
        rho = rho.evolve(Operator(op), qargs=qubits)
        if in_source and not source_noise:
            continue
        if op.name in ('sx', 'x'):
            lam = min(1.0, 2*rates['one_qubit'])
        elif op.name == noise.CALIBRATION[noise.MODEL_KEYS[model]]['two_qubit_gate']:
            lam = min(1.0, 4*rates['two_qubit']/3)
        else:
            continue
        if lam:
            rho = rho.evolve(noise.joint_channel(lam, len(qubits)), qargs=qubits)
    probs = {format(i, f'0{qc.num_qubits}b'): float(max(0, value))
             for i, value in enumerate(rho.probabilities())}
    err = rates['readout']
    return noise.readout_probabilities(probs, err) if err else probs


def _sample(probs, draws, seed):
    keys = list(probs)
    p = np.asarray([probs[k] for k in keys], dtype=float)
    p = np.maximum(p, 0); p /= p.sum()
    counts = np.random.default_rng(seed).multinomial(draws, p)
    return {k: int(v) for k, v in zip(keys, counts) if v}


def _analyze(circuits, manifest, regime, draws, seed, source_noise=True):
    marginals = []
    for i, (circuit, block) in enumerate(zip(circuits, manifest['ordered_blocks'])):
        if regime['model'] == 'ideal':
            probs = _measurement_probabilities(circuit)
        else:
            probs = _density_probabilities(circuit, regime['model'], regime['scale'],
                                            regime.get('readout'), regime.get('staged'), source_noise)
        marginals.append(_sample(probs, draws, seed + i))
    return core.analyze_counts(marginals, manifest)


def _error_by_family(analysis):
    return {family: analysis[family]['word_error'] for family in FAMILIES_LOCAL}


def hypothesis_margins(errors):
    return (1-core.P_SEQ)-errors['collective'], .9*errors['textbook']-errors['collective']


def _quick_search(seed):
    # Bounded tiny search exercises the real recipe interface; same tiny budget per arm.
    objectives = {family: (lambda recipe: 1.0) for family in FAMILIES_LOCAL}
    return equal_budget_search(objectives, budget=2, seed=seed)


def _hash_json(value):
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _suite_config(args):
    return {'suite': args.suite, 'gate': args.gate, 'draws': args.draws,
            'models': args.models, 'scales': args.scales, 'readout_stresses': args.readout_stresses,
            'source_noise': args.source_noise, 'recipe_file': args.recipe,
            'fresh_manifest': args.independent_manifest, 'sampling_seed': args.sampling_seed}


def _load_manifest(path):
    try:
        with open(path, encoding='utf-8') as stream:
            value = json.load(stream)
        manifests = value if isinstance(value, list) else value.get('manifests')
        if not isinstance(manifests, list) or not manifests:
            raise ValueError('must contain a nonempty manifests array')
        ids, seeds = set(), set()
        for item in manifests:
            if not isinstance(item, dict) or not isinstance(item.get('manifest'), dict):
                raise ValueError('each entry needs manifest and sampling_seed')
            m = item['manifest']; sid = item.get('sampling_seed')
            if isinstance(sid, bool) or not isinstance(sid, int):
                raise ValueError('each manifest requires an independent integer sampling_seed')
            cid = m.get('case_id'); construction = m.get('parameters', {}).get('seed')
            if cid in ids or sid in seeds or sid == construction:
                raise ValueError('duplicate case/seed or sampling seed equals construction seed')
            ids.add(cid); seeds.add(sid)
            if not m.get('ordered_blocks') or len(m['ordered_blocks']) != 9:
                raise ValueError('invalid fresh manifest blocks')
        return manifests
    except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
        raise ValueError(f'invalid independent manifest: {exc}') from exc


def run_campaign(args):
    config = _suite_config(args)
    config_hash = _hash_json(config)
    output_dir = args.output_dir or os.path.join(ROOT, 'results')
    os.makedirs(output_dir, exist_ok=True)
    smoke = args.quick or (args.draws <= 5 and os.path.basename(os.path.normpath(output_dir)).startswith('quick-'))
    if args.quick and not os.path.basename(args.output_dir or '').startswith('quick-') and args.output_dir:
        raise ValueError('--quick output directory must have a quick- prefix')
    suite_name = 'quick-' + (args.suite or 'development') if args.quick else args.suite
    target = os.path.join(output_dir, suite_name + '.json')
    checkpoint = os.path.join(output_dir, suite_name + '.checkpoint.json')
    if not smoke and os.path.exists(target):
        raise FileExistsError(f'refusing to overwrite full evidence: {target}')
    if args.resume and os.path.exists(checkpoint):
        with open(checkpoint, encoding='utf-8') as stream:
            saved = json.load(stream)
        if saved.get('config_hash') != config_hash:
            raise ValueError('checkpoint config mismatch; choose a new output directory')
        rows = saved['rows']
    else:
        rows = []
    start = time.monotonic()
    if args.suite == 'fresh':
        entries = _load_manifest(args.independent_manifest)
        cases = [(entry['manifest']['case_id'], entry['sampling_seed'], entry['manifest']) for entry in entries]
    else:
        ids = SUITES[args.suite]
        if args.quick:
            ids = ids[:2]
        cases = [(case, args.sampling_seed + j*100000, None) for j, case in enumerate(ids)]
    if args.quick and args.recipe:
        raise ValueError('--quick cannot use frozen recipes')
    recipe = None
    if args.recipe:
        from synthesis import import_recipe
        recipe = import_recipe(args.recipe)
    selection_complete = bool(recipe and recipe.get('selection', {}).get('full_budget_completed'))
    if args.suite in ('frozen', 'fresh') and not selection_complete:
        raise ValueError('held-out evaluation requires a completed 128-candidate development selection recipe')
    if args.quick:
        recipe = _quick_search(2026100900)
        recipe = recipe['recipe']
    regimes = [{'model': 'ideal', 'scale': 0.0}]
    if 'aria' in args.models:
        regimes.extend([{'model': 'aria', 'scale': x} for x in ([1.0] if args.quick else args.scales)])
    if not args.quick:
        for model in ('forte', 'fe'):
            if model in args.models:
                regimes.extend({'model': model, 'scale': x} for x in args.scales)
        for e in args.readout_stresses:
            regimes.append({'model': 'aria', 'scale': 1.0, 'readout': e})
    draws = min(args.draws, 2) if args.quick else args.draws
    jobs = len(cases)*len(regimes)
    for ci, (case, sample_seed, supplied_manifest) in enumerate(cases):
        circuits, generated_manifest = core.make_demo(case, recipe)
        if supplied_manifest is not None:
            if supplied_manifest.get('case_id') != generated_manifest['case_id']:
                raise ValueError('fresh manifest case ID does not match frozen core registry')
            # Verify identity by exact generated manifest and never substitute a frozen frame.
            if supplied_manifest != generated_manifest:
                raise ValueError('fresh manifests must be generated by the independent verifier for this core version')
            manifest = supplied_manifest
        else:
            manifest = generated_manifest
        for regime in regimes:
            row_seed = sample_seed + int(regime.get('scale', 0)*10000) + len(regime['model'])
            analysis = _analyze(circuits, manifest, regime, draws, row_seed, args.source_noise)
            row = {'case_id': case, 'construction_seed': manifest['parameters']['seed'],
                   'sampling_seed': row_seed, 'manifest_hash': _hash_json(manifest),
                   'recipe_hash': _hash_json(recipe) if recipe else 'default', 'regime': regime,
                   'draws_per_circuit': draws, 'analysis': analysis,
                   'word_errors': _error_by_family(analysis)}
            rows.append(row)
            with open(checkpoint, 'w', encoding='utf-8') as stream:
                json.dump({'config_hash': config_hash, 'rows': rows}, stream, indent=2, allow_nan=False)
            elapsed = time.monotonic()-start
            done = len(rows)
            eta = (elapsed/max(done, 1))*(jobs-done)
            print(f'[{done}/{jobs}] case={case} regime={regime} elapsed={elapsed:.1f}s ETA={eta:.1f}s', flush=True)
    paired = {}
    by_regime = {}
    for row in rows:
        by_regime.setdefault(json.dumps(row['regime'], sort_keys=True), []).append(row)
    for key, group in by_regime.items():
        if len(group) < 2:
            continue
        diffs1, diffs2 = [], []
        for row in group:
            e = row['word_errors']
            diffs1.append(hypothesis_margins(e)[0])
            diffs2.append(hypothesis_margins(e)[1])
        paired[key] = {'seq_minus_joint': diffs1, 'relative_textbook_margin': diffs2,
                       'h1_baseline_error': 1-core.P_SEQ,
                       'h1_scope': 'conditional on ideal sources' if args.source_noise else 'ideal source model',
                       'noisy_sequential_reference_errors': [r['word_errors']['deferred-sequential'] for r in group],
                       'bootstrap_seq_minus_joint': paired_bootstrap(diffs1, args.sampling_seed),
                       'bootstrap_textbook_margin': paired_bootstrap(diffs2, args.sampling_seed+1),
                       'permutation_seq_minus_joint': paired_permutation(diffs1, args.sampling_seed),
                       'permutation_textbook_margin': paired_permutation(diffs2, args.sampling_seed+1)}
    decisions = {k: gate_decisions(v) for k, v in paired.items()} if not args.quick else None
    if decisions and not selection_complete:
        for decision in decisions.values():
            decision['h2_numeric_pass'] = decision['h2_pass']
            decision['h2_pass'] = False
            decision['gate_pass'] = False
            decision['reason'] = 'no completed equal-budget development synthesis selection; H2 not certified'
    result = {'schema_version': '1.1', 'evidence_label': 'development smoke only; not science evidence' if smoke else 'local IonQ-like approximation; not Qollab evidence',
              'configuration': config, 'configuration_hash': config_hash,
              'environment': {'utc_start': datetime.now(timezone.utc).isoformat(),
                              'machine': platform.platform(), 'python': sys.version,
                              'numpy': np.__version__, 'qiskit': __import__('qiskit').__version__},
              'generation_seeds': [x[2]['parameters']['seed'] if x[2] else core.CASE_SEEDS[x[0]] for x in cases],
              'sampling_seeds': [x[1] for x in cases], 'recipe': recipe,
              'noise_configurations': [noise.effective_config(r['model'], r['scale'], r.get('readout')) for r in regimes if r['model'] != 'ideal'],
              'rows': rows, 'paired_statistics': paired,
              'gate_decisions': decisions, 'synthesis_selection_complete': selection_complete,
              'operation_accounting': {'submitted_shots': draws*len(rows), 'packed_qubits': 21,
                                       'note': 'local tiny-block density approximation; native gate count/cost not asserted'},
              'science_verdict': None if args.quick else 'gate result only; independent verification and Qollab evidence remain required'}
    with open(target, 'w' if smoke else 'x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    if os.path.exists(checkpoint):
        os.remove(checkpoint)
    print(f'Saved {target}; no independent science PASS.', flush=True)
    return result


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--quick', action='store_true', help='tiny development smoke only; outputs quick-*')
    p.add_argument('--suite', choices=('development', 'frozen', 'fresh'), default='development')
    p.add_argument('--gate', choices=('g1',), default=None)
    p.add_argument('--independent-manifest')
    p.add_argument('--resume', action='store_true')
    p.add_argument('--output-dir')
    p.add_argument('--draws', type=int, default=200)
    p.add_argument('--models', nargs='+', choices=('aria', 'forte', 'fe'), default=['aria', 'forte', 'fe'])
    p.add_argument('--scales', nargs='+', type=float, default=[.5, .75, 1, 1.25, 1.5, 1.75, 2])
    p.add_argument('--readout-stresses', nargs='+', type=float, default=[.001, .005])
    p.add_argument('--sampling-seed', type=int, default=2026101100)
    p.add_argument('--recipe')
    p.add_argument('--source-noise', action=argparse.BooleanOptionalAction, default=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.draws < 1 or args.sampling_seed < 0 or any(not 0 <= x <= 2 for x in args.scales):
        raise SystemExit('draws/seeds/scales outside supported range')
    if args.suite == 'fresh' and not args.independent_manifest:
        raise SystemExit('--suite fresh requires --independent-manifest PATH')
    if args.suite != 'fresh' and args.independent_manifest:
        raise SystemExit('--independent-manifest is only valid with --suite fresh')
    if args.quick and (args.suite == 'fresh' or args.gate or args.resume or args.independent_manifest):
        raise SystemExit('--quick conflicts with fresh, --gate and --resume')
    if args.gate and args.suite != 'development':
        raise SystemExit('--gate g1 requires --suite development')
    if args.gate == 'g1' and args.quick:
        raise SystemExit('--quick cannot run a gate decision')
    if args.suite == 'development' and not args.quick and args.gate != 'g1':
        raise SystemExit('full development is a power job; specify --gate g1')
    if args.quick and args.output_dir and not os.path.basename(os.path.normpath(args.output_dir)).startswith('quick-'):
        raise SystemExit('--quick output directory must have a quick- prefix')
    return run_campaign(args)


if __name__ == '__main__':
    main()
