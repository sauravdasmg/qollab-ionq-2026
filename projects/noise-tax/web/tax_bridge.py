"""Thin Python adapter for The Noise Tax interactive web page.

main.js calls every function here through .callPromising(backend, ...).
This effort is supported by Qollab & IonQ. Qiskit 2.x + NumPy/SciPy only, injected
backend, no qiskit-aer, no interactive prompts, no module-level main() call, and a
single backend.run call site (one packed job on IonQ).

Numbers carry an explicit provenance label on every path:
  LIVE             fresh shot counts from the injected backend during this run
  RECORDED         stored receipts of earlier Qollab IonQ simulator jobs
  LOCAL MODEL      exact density-matrix curve under the calibrated IonQ-like channel
  THEORY           closed-form noiseless value
"""
import json
import math
import numbers
import sys
from pathlib import Path

from qiskit import transpile

# Publish layout is one flat folder next to this file; during the local build the
# shared modules live one level up in projects/noise-tax/.
_PARENT = Path(__file__).resolve().parent.parent
if (_PARENT / 'whispers_core.py').is_file() and str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

import whispers_core as w
import hedging_core as n
import hedging_strategies as hs
import product_bounds as pb
import noise_channel as nc
import crossover as co
from recorded_parser import summarize_record
import recorded_ionq
from circuit_pack import pack_circuits, unpack_counts
from receipt import utc_now, make_record, format_record, digest

MODELS = ('aria-1', 'forte-1', 'forte-enterprise-1')
DEFAULT_SHOTS = 512
MAX_SHOTS = 4000
GRID_MAX = 2.0
SLIDER_STEP = 0.05
PRIZE = 0.02
MEANING = ('Noise charges a tax on every quantum advantage; '
           'here is where the bill exceeds the gain.')
# Fixed, reproducible demo specification: no random instance is drawn per page load.
N_SPEC = {'game': 'N', 'seed': 2026104200, 'alpha': math.pi/4, 'theta': math.pi/8}
_DEMO_CACHE = None
_CURVE_CACHE = {}

GAMES = {
    'W': {
        'title': 'Two Whispers',
        'subtitle': 'read both qubits together vs one at a time',
        'positive': 'quantum joint recipe wins',
        'negative': 'one-way reference wins',
        'metric': 'equal-prior word error',
        'reference': 'analytic optimal one-way ideal-source bound (noiseless reference)',
    },
    'N': {
        'title': 'Never Lose Twice',
        'subtitle': 'quantum hedge vs normal play',
        'positive': 'quantum hedge wins',
        'negative': 'product strategy wins (also a quantum strategy)',
        'metric': 'fixed-prize loss, prize 0.02',
        'reference': 'attained legal product strategy (itself a quantum strategy)',
    },
}


def _demos():
    """Cached demo blocks: 3 W joint label circuits + 2 N arm circuits."""
    global _DEMO_CACHE
    if _DEMO_CACHE is None:
        wc, wm = w.make_demo()
        ncircuits, nm = n.make_instance_demo(dict(N_SPEC))
        _DEMO_CACHE = ((wc, wm), (ncircuits, nm))
    return _DEMO_CACHE


def _backend_name(backend):
    name = getattr(backend, 'name', '')
    return name() if callable(name) else name


def _effective_model(backend):
    options = getattr(backend, 'options', None)
    model = options.get('noise_model') if isinstance(options, dict) else getattr(options, 'noise_model', None)
    if isinstance(model, dict):
        model = model.get('model') or model.get('name')
    if model not in MODELS:
        raise ValueError('actual effective IonQ noise_model must be aria-1, forte-1 or forte-enterprise-1; got %r'
                         % (model,))
    return model


def _labels():
    return [
        {'label': 'LIVE', 'meaning': 'fresh shot counts from the injected backend during this run'},
        {'label': 'RECORDED IonQ simulator', 'meaning': 'stored receipt of an earlier Qollab IonQ '
                                                        'simulator job; shots and date shown next to every point'},
        {'label': 'LOCAL MODEL', 'meaning': 'exact density-matrix curve under the calibrated '
                                            'IonQ-like channel; an approximation, not the server pulse model'},
        {'label': 'THEORY', 'meaning': 'closed-form noiseless value; no shots, no noise'},
    ]


def _record_date(record):
    timestamps = record.get('timestamps')
    if isinstance(timestamps, dict):
        for key in ('started_utc', 'ended_utc'):
            value = timestamps.get(key)
            if value:
                return str(value)
    for key in ('utc_start', 'utc_end'):
        value = record.get(key)
        if value:
            return str(value)
    return None


def get_recorded():
    """Parsed RECORDED IonQ anchors (aria-1, forte-1, forte-enterprise-1)."""
    records, statuses = recorded_ionq.parse_records()
    anchors, issues = [], []
    for record in records:
        date = _record_date(record)
        for anchor in summarize_record(record):
            item = {'game': anchor['game'], 'model': anchor['model'],
                    'shots': int(anchor['shots']), 'advantage': float(anchor['advantage']),
                    'label': 'RECORDED IonQ simulator', 'date': date,
                    'case_id': anchor.get('case_id'),
                    'source_file': anchor.get('source_file'),
                    'receipt_schema': record.get('schema_version')}
            if anchor['game'] == 'W':
                item['detail'] = 'joint word error %.5f' % anchor['word_error']
            else:
                metrics = anchor['metrics']
                item['detail'] = ('hedge FF %.5f / product FF %.5f; mean passes hedge %.4f / product %.4f'
                                  % (metrics['published_hedge']['double_failure'],
                                     metrics['attained_product']['double_failure'],
                                     metrics['published_hedge']['mean_passes'],
                                     metrics['attained_product']['mean_passes']))
            anchors.append(item)
    for status in statuses:
        if not status['ok']:
            issues.append({'line': status.get('line'), 'error': status.get('error')})
    return {'anchors': anchors, 'issues': issues, 'records': len(records),
            'label': 'RECORDED IonQ simulator', 'parsed_utc': utc_now(),
            'source_module': 'recorded_ionq.py'}


def _development_path():
    for candidate in (Path('results') / 'development.json',
                      _PARENT / 'results' / 'development.json',
                      Path(__file__).resolve().parent / 'development.json'):
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def _development():
    path = _development_path()
    if path is None:
        return None, None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, None
    if not isinstance(data, dict) or 'analysis' not in data or 'grid' not in data:
        return None, None
    return data, str(path).replace('\\', '/')


def _local_curve(game, model, step=SLIDER_STEP):
    """Exact LOCAL MODEL advantage curve computed on the five small demo blocks."""
    key = (game, model, round(float(step), 6))
    if key in _CURVE_CACHE:
        return dict(_CURVE_CACHE[key])
    if game == 'W':
        circuits, manifest = _demos()[0]
    elif game == 'N':
        circuits, manifest = _demos()[1]
    else:
        raise ValueError('game must be W or N')
    if model not in MODELS:
        raise ValueError('unknown IonQ noise model')
    if (isinstance(step, bool) or not isinstance(step, numbers.Real)
            or not math.isfinite(float(step)) or not 0.01 <= step <= 1.0):
        raise ValueError('step must be a finite number in 0.01..1.0')
    compiled = [nc.compile_circuit(c, model) for c in circuits]
    prepared = [nc.prepare_steps(c) for c in compiled]
    steps = int(round(GRID_MAX / float(step)))
    grid = [round(k * float(step), 6) for k in range(steps + 1)]
    curve = []
    for scale in grid:
        cfg = nc.configuration(model, scale)
        distributions = [nc.probabilities(c, cfg, p) for c, p in zip(compiled, prepared)]
        if game == 'W':
            advantage = w.analyze_probabilities(distributions, manifest)['advantage']
        else:
            advantage = n.analyze_probabilities(distributions, manifest)['advantage']
        curve.append(float(advantage))
    point = co.crossing(grid, curve)
    entry = {'grid': grid, 'advantage': curve, 'lower': None, 'upper': None,
             'crossing': point['estimate'], 'status': point['status'], 'ci': None,
             'grid_resolution': float(step),
             'curve_source': 'computed live by tax_bridge on the five small demo blocks',
             'confidence': None, 'n_instances': None, 'label': 'LOCAL MODEL'}
    _CURVE_CACHE[key] = entry
    return dict(entry)


def get_evidence():
    """Stored LOCAL MODEL curves + crossover intervals + RECORDED anchors.

    Falls back to a curve computed live on the five small demo blocks when the
    stored results file is not part of the upload.
    """
    data, data_path = _development()
    models = list(MODELS)
    games = {}
    for game in ('W', 'N'):
        per_model = {}
        for model in models:
            entry = {'grid': None, 'advantage': None, 'lower': None, 'upper': None,
                     'crossing': None, 'status': 'not measured', 'ci': None,
                     'grid_resolution': None, 'curve_source': 'not measured',
                     'confidence': None, 'n_instances': None, 'label': 'LOCAL MODEL'}
            analysis = None
            if isinstance(data, dict):
                analysis = data.get('analysis', {}).get(game, {}).get(model)
            grid = data.get('grid') if isinstance(data, dict) else None
            if (isinstance(analysis, dict) and isinstance(grid, list)
                    and len(grid) == len(analysis.get('mean_advantage') or ())):
                point = analysis.get('point') or {}
                inversion = analysis.get('inversion') or {}
                lower = analysis.get('lower_band') or analysis['mean_advantage']
                upper = analysis.get('upper_band') or analysis['mean_advantage']
                crossing = point.get('estimate')
                ci = inversion.get('confidence_interval')
                resolution = point.get('grid_resolution')
                confidence = analysis.get('confidence')
                instances = analysis.get('n_instances')
                entry.update({
                    'grid': [float(x) for x in grid],
                    'advantage': [float(x) for x in analysis['mean_advantage']],
                    'lower': [float(x) for x in lower],
                    'upper': [float(x) for x in upper],
                    'crossing': float(crossing) if crossing is not None else None,
                    'status': str(point.get('status', 'unknown')),
                    'ci': [float(x) for x in ci] if ci else None,
                    'grid_resolution': float(resolution) if resolution is not None else None,
                    'curve_source': 'LOCAL MODEL results in ' + data_path,
                    'confidence': float(confidence) if confidence is not None else None,
                    'n_instances': int(instances) if instances is not None else None,
                })
            else:
                entry.update(_local_curve(game, model))
            per_model[model] = entry
        games[game] = per_model
    product_ff = (1 - math.cos(math.pi/8)**2)**2
    product_loss = product_ff + PRIZE * (2 - 2*math.cos(math.pi/8)**2)
    return {
        'games': games,
        'models': models,
        'game_info': GAMES,
        'anchors': get_recorded()['anchors'],
        'ideal': {
            'W': {'joint_success': float(w.P_JOINT), 'oneway_success': float(w.P_SEQ),
                  'advantage': float(w.P_JOINT - w.P_SEQ), 'label': 'THEORY'},
            'N': {'product_ff': float(product_ff), 'product_loss': float(product_loss),
                  'hedge_loss': float(PRIZE), 'advantage': float(product_loss - PRIZE),
                  'product_pass_bound': float(pb.ideal_product_pass(N_SPEC['alpha'], N_SPEC['theta'])),
                  'label': 'THEORY'},
        },
        'meaning': MEANING,
        'labels': _labels(),
        'slider': {'min': 0.0, 'max': GRID_MAX, 'step': SLIDER_STEP, 'today': 1.0},
        'curve_files': [data_path] if data_path else [],
        'generated_utc': utc_now(),
    }


def run_demo(backend, shots=DEFAULT_SHOTS, model='aria-1'):
    """Run the five small default blocks on the injected backend. Exactly one job.

    Built-in simulator: five small circuits in one run. IonQ simulator: one packed
    14-qubit circuit, one run, one result fetch, and a pasteable RECORD_JSON line.
    """
    if isinstance(shots, bool) or not isinstance(shots, numbers.Integral) or not 1 <= shots <= MAX_SHOTS:
        raise ValueError('shots must be an integer in 1..%d' % MAX_SHOTS)
    shots = int(shots)
    if model not in MODELS:
        raise ValueError('unknown IonQ simulator model')
    name = str(_backend_name(backend))
    ionq = name == 'ionq_simulator'
    (wc, wm), (ncircuits, nm) = _demos()
    circuits = transpile(list(wc) + list(ncircuits), basis_gates=['rx', 'ry', 'rz', 'cx'],
                         optimization_level=1, seed_transpiler=1234)
    manifests = {'W': wm, 'N': nm}
    if ionq:
        backend.set_options(noise_model=model)
    effective = _effective_model(backend) if ionq else None
    started = utc_now()
    if ionq:
        submitted, layout = pack_circuits(circuits, max_qubits=25)
        for entry, block in zip(layout, wm['ordered_blocks'] + [{'arm': a} for a in n.BLOCKS]):
            entry['manifest_hash'] = digest(block)
        print('LIVE IonQ simulator: one packed %d-qubit job, effective model=%s, shots=%d'
              % (submitted.num_qubits, effective, shots))
    else:
        submitted, layout = circuits, None
        print('LIVE built-in simulator: five small circuit blocks, shots per block=%d' % shots)
    job = backend.run(submitted, shots=shots)
    result = job.result()
    if ionq:
        raw = result.get_counts()
        counts = unpack_counts(raw, layout)
        source = 'LIVE IonQ simulator, effective noise model ' + effective
    else:
        raw = None
        counts = [result.get_counts(i) for i in range(len(circuits))]
        source = 'LIVE built-in ideal simulator (noiseless)'
    wa = w.analyze_counts(counts[:3], wm)
    na = n.analyze_probabilities(counts[3:], nm)
    ended = utc_now()
    record = None
    if ionq:
        job_id = getattr(job, 'job_id', None)
        record = make_record(submitted, layout, raw, manifests, shots, effective, started, ended,
                             job_id() if callable(job_id) else job_id)
        print(format_record(record))
    product_ff = (1 - math.cos(math.pi/8)**2)**2
    product_loss = product_ff + PRIZE * (2 - 2*math.cos(math.pi/8)**2)
    return {
        'label': 'LIVE',
        'source': source,
        'backend_name': name,
        'model': effective if ionq else None,
        'shots': shots,
        'started_utc': started,
        'ended_utc': ended,
        'W': {'joint_word_error': float(wa['joint']['word_error']),
              'joint_success': float(wa['joint']['success']),
              'oneway_reference_error': float(1 - w.P_SEQ),
              'advantage': float(wa['advantage']), 'label': 'LIVE',
              'reference_label': 'THEORY'},
        'N': {'published_hedge': {'double_failure': float(na['published_hedge']['double_failure']),
                                  'mean_passes': float(na['published_hedge']['mean_passes']),
                                  'loss': float(na['published_hedge']['loss'])},
              'attained_product': {'double_failure': float(na['attained_product']['double_failure']),
                                   'mean_passes': float(na['attained_product']['mean_passes']),
                                   'loss': float(na['attained_product']['loss'])},
              'advantage': float(na['advantage']), 'prize': PRIZE, 'label': 'LIVE'},
        'ideal': {'W_advantage': float(w.P_JOINT - w.P_SEQ),
                  'N_advantage': float(product_loss - PRIZE), 'label': 'THEORY'},
        'blocks': [{'name': c.name, 'qubits': int(c.num_qubits), 'clbits': int(c.num_clbits)}
                   for c in circuits],
        'receipt_line': format_record(record) if record is not None else None,
    }


def get_meaning():
    """One-line meaning for the side panel."""
    return MEANING


def get_circuit_text(game='W'):
    """The selected game's circuits as accessible text with named stages."""
    if game == 'W':
        circuits, manifest = _demos()[0]
        stages = [
            'Preparation: for word k, two copies of the trine signal state are prepared on qubits 0 and 1.',
            'Receiver: one fixed textbook square-root measurement unitary reads both copies together '
            '(no tuning, no synthesis search; the recipe is frozen).',
            'Measurement: both qubits are measured; the complete four-outcome decoder maps every outcome '
            'to a word, and the unused outcome counts as an error.',
            'Reference arm: the one-way receiver reads one copy at a time and is credited with its '
            'noiseless analytic bound (the conservative comparison budget).',
        ]
        shown = [circuits[0]]
        note = 'Three identical-structure blocks run, one per word label; the first is shown.'
    elif game == 'N':
        circuits, manifest = _demos()[1]
        stages = [
            'Preparation: reference wires 0 and 1 take RY(2*alpha); CX(0,2) and CX(1,3) build the '
            'independent reference/prover source pairs (alpha and theta are fixed per instance).',
            'Strategy: the frozen recipe writes only on prover wires %s (ownership audited by '
            'hedging_strategies.audit_prover_ownership).' % (hs.OWNERSHIP['prover'],),
            'Verification: CX(0,2), CX(1,3) then RY(-2*theta) on the reference wires; all four wires measured.',
            'Decode: a test passes when its pair (0,2) or (1,3) reads 00; double failure is FF; '
            'loss = P(FF) + 0.02 * (2 - mean passes).',
        ]
        shown = list(circuits)
        note = 'Both arms run: %s then %s.' % tuple(manifest['ordered_blocks'])
    else:
        raise ValueError('game must be W or N')
    header = '%s (%s)\n' % (GAMES[game]['title'], GAMES[game]['subtitle'])
    diagram = '\n\n'.join(str(c) for c in shown)
    return {'game': game, 'title': GAMES[game]['title'], 'stages': list(stages),
            'note': note, 'diagram': diagram,
            'text': header + '\n'.join('%d. %s' % (i + 1, s) for i, s in enumerate(stages))
                    + '\n\n' + note + '\n\n' + diagram,
            'labels': ['LOCAL MODEL compiled effective basis',
                       'RECORDED IonQ receipts printed below each run']}


def get_gate_costs(game='W'):
    """Which gates cost most on IonQ: the two-qubit MS/ZZ entangler, with counts."""
    if game not in ('W', 'N'):
        raise ValueError('game must be W or N')
    circuits = _demos()[0][0] if game == 'W' else _demos()[1][0]
    compiled_counts = {}
    for model in ('aria-1', 'forte-1'):
        totals = {}
        for circuit in circuits:
            for name, value in dict(nc.compile_circuit(circuit, model).count_ops()).items():
                if name in ('measure', 'barrier'):
                    continue
                totals[name] = totals.get(name, 0) + int(value)
        compiled_counts[model] = totals
    return {
        'game': game,
        'title': GAMES[game]['title'],
        'summary': ('Two-qubit entanglers carry the noise tax on IonQ: the MS (XX) gate on Aria and the '
                    'native ZZ gate on Forte are the expensive operations, and every extra one you add '
                    'buys back part of the quantum advantage.'),
        'compiled_effective_gates': compiled_counts,
        'ionq_facts': [
            'H costs one GPi2 pulse; a generic RY costs two GPi2 pulses (special angles are cheaper).',
            'A CX has one native two-qubit entangler; Forte RZZ has one native ZZ, while the Aria '
            'equivalent adds pulses.',
            'IonQ recompiles circuits server-side, so these are locally compiled effective-gate counts, '
            'not native pulse counts.',
        ],
        'note': ('Counts are the locally compiled effective basis for this game (%s), one block set. '
                 'Readout error is 0 in the calibrated local model.' % game),
        'label': 'LOCAL MODEL compiled effective basis + published IonQ gate facts',
    }
