"""Orchestrator-run exact small-block suites. Worker invokes quick/smoke only."""
import argparse
import json
import os
import platform
from pathlib import Path
import sys
import time
import hashlib
import numpy as np
import qiskit
from qiskit.quantum_info import Statevector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import whispers_core as w
import hedging_core as n
import noise_channel as channel
import crossover
from product_bounds import ideal_certificate, ideal_product_pass
from receipt import digest, utc_now
from figures import plot_results, plot_cloud_comparison
import recorded_ionq
from recorded_parser import summarize_record

SUITES = {'development': (2026104500, 2026104600, 2026104700),
          'frozen': (2026104000, 2026104200, 2026104800),
          'fresh': (2026104100, 2026104300, 2026104900)}
IMPLEMENTATION_FILES = ('whispers_core.py', 'hedging_core.py', 'hedging_strategies.py',
                        'product_bounds.py', 'noise_channel.py', 'calibration_snapshot.py',
                        'crossover.py', 'circuit_pack.py', 'receipt.py', 'main.py',
                        'recorded_ionq.py', 'recorded_parser.py', 'figures.py',
                        'experiments/run.py', 'experiments/PLAN.md')

def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    os.replace(temporary, path)

def build_manifest(suite, quick=False, gate=None):
    ws, ns, sampling = SUITES[suite]
    count = 2 if quick else 24
    grid = [0., 2.] if quick else [k/40 for k in range(81)]
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in IMPLEMENTATION_FILES}
    configuration = {'suite': suite, 'quick': quick, 'gate': gate, 'grid': grid,
        'models': list(channel.MODELS), 'primary_model': 'aria-1', 'n_instances': count,
        'construction_rng': 'NumPy default_rng PCG64 Gaussian QR SU2 / uniform alpha theta',
        'instances': {'W': [w.make_instance(ws+i) for i in range(count)],
                      'N': [n.make_instance(ns+i) for i in range(count)]},
        'sampling_base': sampling, 'sampling_rng': 'SeedSequence [base,game,seed,model,scale,arm] / PCG64',
        'shots': {'W_per_label_per_arm': 1000, 'N_per_arm': 4000},
        'fixed_prize': .02, 'channel': {m: channel.configuration(m) for m in channel.MODELS},
        'uncertainty_design': {'W': 'DETERMINISTIC; numerical grid bracket plus calibration sensitivity',
                               'N': 'paired-instance bootstrap', 'cloud': 'binomial shot sampling',
                               'calibration_r_2q_shifts': [-.001, .001]},
        'calibration_sha256': channel.CALIBRATION_SHA256, 'implementation_sha256': hashes,
        'versions': {'qiskit': qiskit.__version__, 'numpy': np.__version__, 'python': platform.python_version()},
        'recipe': {'W': 'fixed textbook square-root, decoder [0,1,2,0], one-way ideal-source reference',
                   'N': 'identity product; X X CP(pi) X X on prover wires only; full 00 projector'},
        'machine': platform.node(), 'simulator': 'exact NumPy small-block density evolution',
        'independent_verification': 'fresh seeds only; reviewer validation pending'}
    return {'frozen_utc': utc_now(), 'configuration': configuration, 'configuration_sha256': digest(configuration)}

def sampling_seed(cfg, game, seed, model_index, scale_index, arm_index):
    return np.random.SeedSequence([cfg['sampling_base'], int(game == 'N'), seed,
                                  model_index, scale_index, arm_index]).generate_state(4).tolist()

def audit_compiled_strategy(circuit):
    stage = 'source'
    for item in circuit.data:
        if item.operation.name == 'barrier':
            stage = item.operation.label
        elif stage == 'strategy_start':
            wires = [circuit.find_bit(q).index for q in item.qubits]
            if not set(wires) <= {2, 3}:
                raise ValueError('compiled strategy touches reference wire')

def gate_stats(circuit):
    stages = {}; stage = 'source'
    for item in circuit.data:
        name = item.operation.name
        if name == 'barrier':
            stage = item.operation.label
        elif name != 'measure':
            stages.setdefault(stage, {})[name] = stages.setdefault(stage, {}).get(name, 0)+1
    return {'operations': dict(circuit.count_ops()), 'stages': stages,
            'effective_basis_only': True, 'remote_native_count': None}

def ideal_oneway(spec):
    circuits, manifest = w.make_demo(spec, include_oneway=True)
    selected = [(c, b) for c, b in zip(circuits, manifest['ordered_blocks']) if b['arm'] == 'oneway']
    probs = []
    for c, b in selected:
        p = Statevector.from_instruction(c.remove_final_measurements(inplace=False)).probabilities()
        probs.append({format(i, '03b'): float(v) for i, v in enumerate(p)})
    return probs, {'ordered_blocks': [b for c, b in selected]}

def evaluate_case(game, spec, cfg, model, model_index, checkpoint, resume=False):
    expected = digest({'configuration_sha256': cfg['_hash'], 'game': game, 'spec': spec, 'model': model})
    if resume and checkpoint.exists():
        partial = json.loads(checkpoint.read_text(encoding='utf-8'))
        if partial['checkpoint_sha256'] != expected:
            raise ValueError('checkpoint configuration mismatch: '+str(checkpoint))
    else:
        if checkpoint.exists() and not resume:
            raise FileExistsError('checkpoint exists; use --resume or a new output directory')
        partial = {'checkpoint_sha256': expected, 'game': game, 'specification': spec,
                   'model': model, 'points': [], 'complete': False}
    if partial['complete']:
        return partial
    if game == 'W':
        circuits, manifest = w.make_demo(spec)
        reference_probs, reference_manifest = ideal_oneway(spec)
        reference = w.analyze_probabilities(reference_probs, reference_manifest)['oneway']['success']
        if not np.isclose(reference, w.P_SEQ, atol=1e-10):
            raise ValueError('ideal one-way identity failed')
        partial['oneway_reference_success'] = reference
        partial['oneway_reference_manifest'] = reference_manifest
    else:
        circuits, manifest = n.make_instance_demo(spec)
        certificate = ideal_certificate(spec['alpha'], spec['theta'])
        partial['ideal_product_certificate'] = certificate
        if not certificate['certified'] or abs(certificate['primal_value']-ideal_product_pass(spec['alpha'], spec['theta'])) > 1e-9:
            raise ValueError('ideal product certificate/identity mismatch')
    compiled = [channel.compile_circuit(c, model) for c in circuits]
    if game == 'N':
        for c in compiled:
            audit_compiled_strategy(c)
    prepared = [channel.prepare_steps(c) for c in compiled]
    partial['manifest'] = manifest
    partial['submitted_operations'] = [dict(c.count_ops()) for c in circuits]
    partial['locally_compiled_effective_gates'] = [gate_stats(c) for c in compiled]
    partial['block_widths'] = [c.num_qubits for c in circuits]
    for j in range(len(partial['points']), len(cfg['grid'])):
        scale = cfg['grid'][j]; noise = channel.configuration(model, scale)
        probs = [channel.probabilities(c, noise, p) for c, p in zip(compiled, prepared)]
        seeds = [sampling_seed(cfg, game, spec['seed'], model_index, j, a) for a in range(len(probs))]
        shots = 1000 if game == 'W' else 4000
        counts = [channel.histogram(p, shots, seed) for p, seed in zip(probs, seeds)]
        if game == 'W':
            exact = w.analyze_probabilities(probs, manifest)
            sampled = w.analyze_counts(counts, manifest)
            extra_seeds = [sampling_seed(cfg, game, spec['seed'], model_index, j, a+3) for a in range(3)]
            reference_counts = [channel.histogram(p, shots, seed) for p, seed in zip(reference_probs, extra_seeds)]
            reference_sampled = w.analyze_counts(reference_counts, reference_manifest)
            extra = {'ideal_oneway_probabilities': reference_probs, 'ideal_oneway_synthetic_counts': reference_counts,
                     'ideal_oneway_sampling_seeds': extra_seeds, 'oneway_sampled_metrics': reference_sampled,
                     'sampled_arm_difference': sampled['joint']['success']-reference_sampled['oneway']['success'],
                     'reference_noiseless': True}
        else:
            exact = n.analyze_probabilities(probs, manifest)
            sampled = n.analyze_probabilities(counts, manifest)
            legacy = n.analyze_counts(dict(zip(n.BLOCKS, counts)), manifest)
            extra = {'count_uncertainty': legacy['results']}
        if scale == 0:
            for c, dist in zip(circuits, probs):
                sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False)).probabilities()
                if not np.allclose([dist[k] for k in sorted(dist)], sv, atol=1e-10):
                    raise ValueError('scale-zero density != uncompiled Statevector')
        partial['points'].append({'scale': scale, 'probabilities': probs, 'synthetic_counts': counts,
                                  'sampling_seeds': seeds, 'shots_per_block': shots, 'exact_metrics': exact,
                                  'sampled_metrics': sampled, 'exact_advantage': exact['advantage'], **extra})
        atomic_json(checkpoint, partial)
    partial['complete'] = True
    atomic_json(checkpoint, partial)
    return partial

def diagnostic_controls():
    """Two analytic controls, separate from all seeded inference."""
    controls = {}
    for game in ('W', 'N'):
        circuits, manifest = w.make_demo() if game == 'W' else n.make_instance_demo()
        for scale in (0., 2.):
            probs = [channel.probabilities(channel.compile_circuit(c), channel.configuration(scale=scale)) for c in circuits]
            metrics = w.analyze_probabilities(probs, manifest) if game == 'W' else n.analyze_probabilities(probs, manifest)
            controls[game+':'+str(scale)] = {'exact_metrics': metrics, 'probabilities': probs,
                                           'counted_in_primary': False}
    return controls

def calibration_sensitivity(spec, grid, model):
    """Recompute W at the calibration-grid edges, keeping fitted 1q unchanged."""
    circuits, manifest = w.make_demo(spec)
    compiled = [channel.compile_circuit(c, model) for c in circuits]
    prepared = [channel.prepare_steps(c) for c in compiled]
    edges = []
    for shift in (-.001, .001):
        curve = []
        for scale in grid:
            cfg = channel.configuration(model, scale, calibration_shift=shift)
            probs = [channel.probabilities(c, cfg, p) for c, p in zip(compiled, prepared)]
            curve.append(w.analyze_probabilities(probs, manifest)['advantage'])
        root = crossover.crossing(grid, curve)
        edges.append({'r_2q': cfg['r_2q'], 'shift': shift, 'r_1q': cfg['r_1q'],
                      'mean_advantage': curve, 'point': root})
    resolved = all(e['point']['status'] == 'resolved' for e in edges)
    roots = [e['point']['estimate'] for e in edges]
    return {'uncertainty_source': 'CALIBRATION SENSITIVITY',
            'method': 'fitted r_2q +/-0.001; fitted r_1q unchanged; not a confidence interval',
            'representative_seed': spec['seed'], 'edges': edges,
            's_star_range': [min(roots), max(roots)] if resolved else None,
            'status': 'resolved' if resolved else 'unresolved',
            'excludes': 'remote pulse-model mismatch and statistical calibration coverage'}

def run(args):
    if args.independent_manifest and args.suite != 'fresh':
        raise ValueError('--independent-manifest is for the fresh suite only')
    if args.gate == 'g1' and args.suite != 'development':
        raise ValueError('G1 uses development pilot seeds only')
    if args.gate == 'g2' and args.suite != 'frozen':
        raise ValueError('G2 uses frozen evaluation seeds only')
    output = Path(args.output_dir) if args.output_dir else ROOT/'results'
    output.mkdir(parents=True, exist_ok=True)
    suite_name = 'quick' if args.quick else args.suite
    manifest_path = output/(suite_name+'-manifest.json')
    candidate = build_manifest(args.suite, args.quick, args.gate)
    if args.independent_manifest and args.independent_manifest != 'generate':
        manifest_path = Path(args.independent_manifest)
    if manifest_path.exists():
        if not args.resume and not args.independent_manifest:
            raise FileExistsError('manifest exists; use --resume or a new output directory')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['configuration_sha256'] != digest(manifest['configuration']) or manifest['configuration_sha256'] != candidate['configuration_sha256']:
            raise ValueError('frozen manifest differs from current implementation/configuration')
    else:
        manifest = candidate; atomic_json(manifest_path, manifest)
    cfg = dict(manifest['configuration'], _hash=manifest['configuration_sha256'])
    analysis_config = {'draws': args.draws, 'confidence': .975, 'seeds': {'W': 2026104401, 'N': 2026104402}}
    atomic_json(output/(suite_name+'-analysis-config.json'), analysis_config)
    total = 2*cfg['n_instances']*len(channel.MODELS); done = 0; start = time.monotonic()
    print(f"LOCAL MODEL {suite_name}: frozen manifest {manifest['configuration_sha256']}; {total} small-block case/model tasks, {len(cfg['grid'])} scales", flush=True)
    results = {'suite': suite_name, 'source_suite': args.suite, 'grid': cfg['grid'], 'manifest': manifest,
               'analysis_config': analysis_config, 'cases': {'W': {}, 'N': {}}, 'analysis': {},
               'started_utc': utc_now(), 'label': 'LOCAL MODEL approximate IonQ effective-basis channel'}
    for game in ('W', 'N'):
        for mi, model in enumerate(channel.MODELS):
            cases = []
            for spec in cfg['instances'][game]:
                checkpoint = output/'checkpoints'/suite_name/(game+'-'+model+'-'+str(spec['seed'])+'.json')
                case = evaluate_case(game, spec, cfg, model, mi, checkpoint, args.resume)
                cases.append(case); done += 1
                elapsed = time.monotonic()-start; eta = elapsed/done*(total-done)
                print(f'LOCAL MODEL {suite_name} {game}/{model} {done}/{total}; elapsed={elapsed:.1f}s ETA={eta:.1f}s', flush=True)
            results['cases'][game][model] = cases
            curves = [[p['exact_advantage'] for p in case['points']] for case in cases]
            if game == 'W':
                analysis = crossover.deterministic(cfg['grid'], curves)
                analysis['calibration_sensitivity'] = calibration_sensitivity(
                    cfg['instances'][game][0], cfg['grid'], model)
            else:
                analysis = crossover.analyze(cfg['grid'], curves, draws=args.draws,
                                             seed=analysis_config['seeds'][game])
            results['analysis'].setdefault(game, {})[model] = analysis
    results['diagnostic_controls'] = diagnostic_controls()
    records, statuses = recorded_ionq.parse_records()
    anchors = [a for r in records for a in summarize_record(r)]
    results['recorded_anchors'] = anchors; results['receipt_statuses'] = statuses
    primary = {game: results['analysis'][game]['aria-1'] for game in ('W', 'N')}
    adequate = not args.quick and args.draws >= 4000 and cfg['n_instances'] >= 24
    valid = all(a['valid_interior_crossing'] for a in primary.values())
    precision = all(a['precision_target_met'] for a in primary.values())
    results['gate'] = {'requested': args.gate, 'numerical_conditions_met': bool(valid),
                       'precision_target_met': bool(precision), 'inference_adequate': bool(adequate),
                       'decision': ('PASS_LOCAL_CONDITIONS' if adequate and valid and
                                    (args.gate != 'g2' or precision) else
                                    'SMOKE_ONLY' if not adequate else 'HOLD_FAIL'),
                       'independent_reviewer': 'pending', 'cloud_crossover': 'not measured',
                       'admission_capacity_and_default_runtime': 'orchestrator must audit'}
    frozen_path = ROOT/'results'/'frozen.json'
    if args.suite == 'fresh' and frozen_path.exists():
        frozen = json.loads(frozen_path.read_text(encoding='utf-8'))
        results['fresh_comparison'] = {game: crossover.compare_fresh(frozen['analysis'][game]['aria-1'], primary[game])
                                       for game in ('W', 'N')}
    results['ended_utc'] = utc_now(); results['elapsed_seconds'] = time.monotonic()-start
    results['figure_paths'] = [plot_results(results, output/'figures'),
                               plot_cloud_comparison(results, anchors, output/'figures')]
    atomic_json(output/(suite_name+'.json'), results)
    # Compact top-level data for Qollab (full raw JSON can exceed upload limits).
    if args.suite == 'frozen' and not args.quick:
        compact = {k: results[k] for k in ('suite', 'grid', 'manifest', 'analysis', 'started_utc', 'ended_utc', 'gate')}
        (ROOT/'recorded_local.py').write_text('"""LOCAL MODEL frozen curves; exact receipt remains in repository results/frozen.json."""\nLOCAL = '+repr(compact)+'\n', encoding='utf-8')
    print(f"LOCAL MODEL saved {output/(suite_name+'.json')}; decision={results['gate']['decision']}; reviewer pending", flush=True)
    return results

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--suite', choices=tuple(SUITES), default='development')
    parser.add_argument('--gate', choices=('g1', 'g2'))
    parser.add_argument('--draws', type=int, default=4000)
    parser.add_argument('--independent-manifest', nargs='?', const='generate')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--output-dir')
    args = parser.parse_args()
    if args.draws < 1:
        parser.error('--draws must be positive')
    if args.quick and args.draws == 4000:
        args.draws = 40  # focused mechanics only, no statistical evidence
    run(args)

if __name__ == '__main__':
    main()
