"""Tests for web/tax_bridge.py.

Pyodide-safe: no pytest import, no qiskit-aer imports, no interactive prompts,
one backend.run call site, and plain asserts so pytest can still collect them.
"""
import json
import math
from pathlib import Path

from qiskit.providers.basic_provider import BasicSimulator

import tax_bridge

MODELS = ('aria-1', 'forte-1', 'forte-enterprise-1')


def _roundtrip(value):
    return json.loads(json.dumps(value))


def test_meaning_exact_sentence():
    assert tax_bridge.get_meaning() == (
        'Noise charges a tax on every quantum advantage; '
        'here is where the bill exceeds the gain.')


def test_evidence_shape_and_labels():
    evidence = tax_bridge.get_evidence()
    assert set(evidence['games']) == {'W', 'N'}
    assert evidence['models'] == list(MODELS)
    for game in ('W', 'N'):
        for model in MODELS:
            entry = evidence['games'][game][model]
            assert entry['label'] == 'LOCAL MODEL'
            assert isinstance(entry['advantage'], list) and len(entry['advantage']) >= 2
            assert entry['grid'] and len(entry['grid']) == len(entry['advantage'])
            for value in entry['advantage']:
                assert math.isfinite(value)
            if entry['lower'] is not None:
                assert len(entry['lower']) == len(entry['advantage'])
                assert len(entry['upper']) == len(entry['advantage'])
    for label in evidence['labels']:
        assert label['label'] in ('LIVE', 'RECORDED IonQ simulator', 'LOCAL MODEL', 'THEORY')
        assert len(label['meaning']) > 0
    # JSON-serializable end to end.
    data = _roundtrip(evidence)
    assert data['models'] == list(MODELS)


def test_evidence_curve_source_present():
    evidence = tax_bridge.get_evidence()
    for game in ('W', 'N'):
        entry = evidence['games'][game]['aria-1']
        assert entry['crossing'] is not None
        assert entry['crossing'] > 0 and entry['crossing'] < 2
        assert 'LA' in entry['curve_source'] or 'LOCAL MODEL' in entry['curve_source']
    assert evidence['curve_files'] or 'computed' in evidence['games']['W']['aria-1']['curve_source']


def test_ideal_theory_values():
    evidence = tax_bridge.get_evidence()
    ideal = evidence['ideal']
    assert abs(ideal['W']['advantage'] - (0.5 + math.sqrt(2)/3 - 0.5 - math.sqrt(3)/4)) < 1e-12
    product_ff = (1 - math.cos(math.pi/8)**2)**2
    product_loss = product_ff + 0.02 * (2 - 2*math.cos(math.pi/8)**2)
    assert abs(ideal['N']['advantage'] - (product_loss - 0.02)) < 1e-12
    assert ideal['N']['product_pass_bound'] > 0 and ideal['N']['product_pass_bound'] <= 1


def test_recorded_anchors():
    recorded = tax_bridge.get_recorded()
    assert recorded['records'] == 6
    assert recorded['issues'] == []
    anchors = recorded['anchors']
    assert len(anchors) == 6
    by_game = {'W': [], 'N': []}
    for anchor in anchors:
        by_game[anchor['game']].append(anchor)
        assert anchor['label'] == 'RECORDED IonQ simulator'
        assert anchor['model'] in MODELS
        assert anchor['date'] is not None and '2026-10-' in anchor['date']
        assert anchor['shots'] in (1000, 4000)
        assert math.isfinite(anchor['advantage'])
        assert anchor['cloud_sampling']['uncertainty_source'] == 'CLOUD SAMPLING'
        ci = anchor['cloud_sampling']['advantage_interval']
        assert ci[0] <= anchor['advantage'] <= ci[1]
    assert len(by_game['W']) == 3 and len(by_game['N']) == 3
    for model in MODELS:
        wmodel = [a for a in by_game['W'] if a['model'] == model]
        nmodel = [a for a in by_game['N'] if a['model'] == model]
        assert len(wmodel) == 1 and len(nmodel) == 1
        assert 'word error' in wmodel[0]['detail']
        assert 'hedge FF' in nmodel[0]['detail']
    evidence_anchors = tax_bridge.get_evidence()['anchors']
    assert len(evidence_anchors) == 6


def test_w_web_does_not_present_sampling_ci():
    evidence = tax_bridge.get_evidence()
    for entry in evidence['games']['W'].values():
        assert entry['ci'] is None and entry['confidence'] is None
        assert entry['lower'] is None and entry['upper'] is None
        assert 'DETERMINISTIC' in entry['uncertainty_source']


def test_web_preserves_revised_uncertainty_fields():
    from unittest.mock import patch
    from crossover import deterministic, analyze
    grid = [0., 1., 2.]
    curves = [[1., 0., -1.], [1., 0., -1.]]
    wa = deterministic(grid, curves)
    wa['calibration_sensitivity'] = {'s_star_range': [.9, 1.1]}
    na = analyze(grid, curves, draws=5)
    data = {'grid': grid, 'analysis': {
        'W': {m: wa for m in MODELS}, 'N': {m: na for m in MODELS}}}
    with patch.object(tax_bridge, '_development', return_value=(data, 'test.json')):
        evidence = tax_bridge.get_evidence()
    assert evidence['games']['W']['aria-1']['calibration_sensitivity']['s_star_range'] == [.9, 1.1]
    assert evidence['games']['W']['aria-1']['numerical_grid_bracket'] == wa['inversion']['numerical_grid_bracket']
    assert evidence['games']['N']['aria-1']['ci'] == na['inversion']['confidence_interval']


def test_fallback_w_curve_ideal_evenly_spaced():
    curve = tax_bridge._local_curve('W', 'aria-1', step=0.25)
    assert curve['grid'] == [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    assert abs(curve['advantage'][0] - (0.5 + math.sqrt(2)/3 - 0.5 - math.sqrt(3)/4)) < 1e-6
    assert curve['advantage'][-1] < 0
    assert curve['status'] == 'resolved'
    assert 1.0 < curve['crossing'] < 2.0
    assert curve['ci'] is None
    assert curve['lower'] is None and curve['upper'] is None


def test_fallback_n_curve_ideal_evenly_spaced():
    curve = tax_bridge._local_curve('N', 'aria-1', step=0.25)
    assert curve['grid'][0] == 0.0 and curve['grid'][-1] == 2.0
    product_ff = (1 - math.cos(math.pi/8)**2)**2
    product_loss = product_ff + 0.02 * (2 - 2*math.cos(math.pi/8)**2)
    assert abs(curve['advantage'][0] - (product_loss - 0.02)) < 1e-6
    assert curve['advantage'][-1] < 0
    assert 0 < curve['crossing'] < 2


def test_fallback_curve_invalid():
    try:
        tax_bridge._local_curve('Z', 'aria-1')
    except ValueError:
        pass
    else:
        raise AssertionError('unknown game must raise ValueError')
    try:
        tax_bridge._local_curve('W', 'nope-model')
    except ValueError:
        pass
    else:
        raise AssertionError('unknown model must raise ValueError')


def test_run_demo_builtin():
    backend = BasicSimulator()
    result = tax_bridge.run_demo(backend, shots=64, model='aria-1')
    assert result['label'] == 'LIVE'
    assert 'built-in' in result['source']
    assert result['backend_name'] == 'basic_simulator'
    assert result['model'] is None
    assert result['shots'] == 64
    assert len(result['blocks']) == 5
    assert 0 <= result['W']['joint_word_error'] <= 1
    assert math.isfinite(result['W']['advantage'])
    assert math.isfinite(result['N']['advantage'])
    assert result['N']['prize'] == 0.02
    assert result['receipt_line'] is None
    assert result['W']['label'] == 'LIVE' and result['N']['label'] == 'LIVE'
    # Noiseless built-in LIVE should sit near the THEORY ideal at s=0.
    assert abs(result['W']['advantage'] - result['ideal']['W_advantage']) < 0.15
    assert abs(result['N']['advantage'] - result['ideal']['N_advantage']) < 0.15
    data = _roundtrip(result)
    assert data['shots'] == 64


def test_run_demo_live_is_deterministic_demo():
    text_w = tax_bridge.get_circuit_text('W')
    assert 'two copies of the trine signal state' in text_w['stages'][0]
    text_n = tax_bridge.get_circuit_text('N')
    owned = tax_bridge.hs.OWNERSHIP['prover']
    assert ('prover wires %s' % owned) in text_n['stages'][1]
    # Re-running the demo uses the same cached instance, so results are stable for equal shots.
    first = tax_bridge.get_circuit_text('N')['text']
    second = tax_bridge.get_circuit_text('N')['text']
    assert first == second


def test_run_demo_invalid():
    backend = BasicSimulator()
    for bad in (True, 0, -3, 4001, 1.5, '50'):
        try:
            tax_bridge.run_demo(backend, shots=bad)
        except ValueError:
            continue
        raise AssertionError('invalid shots must raise ValueError: %r' % (bad,))
    try:
        tax_bridge.run_demo(backend, shots=16, model='bogus-model')
    except ValueError:
        pass
    else:
        raise AssertionError('invalid model must raise ValueError')


class _FakeJob:
    def __init__(self, counts, job_id='fake-job-id'):
        self._counts = counts
        self.job_id = job_id

    def result(self):
        class _Result:
            def __init__(self, counts):
                self._counts = counts

            def get_counts(self, experiment=None):
                return self._counts

        return _Result(self._counts)


class _FakeIonqBackend:
    """Minimal ionq_simulator stand-in; counts come from BasicSimulator on the packed circuit."""

    def __init__(self, shots):
        self._shots = shots
        self.options = {}

    def name(self):
        return 'ionq_simulator'

    def set_options(self, **kwargs):
        self.options.update(kwargs)

    def run(self, circuit, shots):
        assert self.options.get('noise_model') in MODELS
        result = BasicSimulator().run(circuit, shots=shots).result()
        return _FakeJob(result.get_counts(0))


def test_run_demo_ionq_pack_path():
    shots = 64
    fake = _FakeIonqBackend(shots)
    result = tax_bridge.run_demo(fake, shots=shots, model='aria-1')
    assert 'IonQ' in result['source']
    assert result['model'] == 'aria-1'
    assert fake.options['noise_model'] == 'aria-1'
    assert result['receipt_line'] is not None
    assert result['receipt_line'].startswith('RECORD_JSON ')
    record = json.loads(result['receipt_line'][len('RECORD_JSON '):])
    assert record['project'] == 'The Noise Tax'
    assert record['shots'] == shots
    assert record['noise_model'] == 'aria-1'
    assert record['job_id'] == 'fake-job-id'
    assert result['W']['label'] == 'LIVE'
    # The pasted receipt must re-parse through the shared validator.
    from recorded_parser import parse_records, summarize_record
    records, statuses = parse_records(result['receipt_line'])
    assert len(records) == 1 and statuses[0]['ok']
    anchors = summarize_record(records[0])
    assert {a['game'] for a in anchors} == {'W', 'N'}


def test_circuit_text():
    for game, expected in (('W', 'Two Whispers'), ('N', 'Never Lose Twice')):
        info = tax_bridge.get_circuit_text(game)
        assert info['title'] == expected
        assert len(info['stages']) >= 3
        assert info['text'].startswith(expected)
        assert len(info['diagram']) > 40
    try:
        tax_bridge.get_circuit_text('Z')
    except ValueError:
        pass
    else:
        raise AssertionError('unknown game must raise ValueError')


def test_gate_costs():
    for game in ('W', 'N'):
        costs = tax_bridge.get_gate_costs(game)
        assert 'MS' in costs['summary'] and 'ZZ' in costs['summary']
        assert len(costs['ionq_facts']) == 3
        assert set(costs['compiled_effective_gates']) == {'aria-1', 'forte-1'}
        aria = costs['compiled_effective_gates']['aria-1']
        forte = costs['compiled_effective_gates']['forte-1']
        assert aria['rxx'] >= 1
        assert forte['rzz'] >= 1
        assert 'measure' not in aria and 'barrier' not in aria
    try:
        tax_bridge.get_gate_costs('Z')
    except ValueError:
        pass
    else:
        raise AssertionError('unknown game must raise ValueError')


def test_published_structure_constraints():
    source = Path(__file__).with_name('tax_bridge.py').read_text(encoding='utf-8')
    assert source.count('backend.run(') == 1
    assert 'input(' not in source and 'input (' not in source
    assert 'qiskit_aer' not in source and 'from qiskit_aer' not in source
    assert 'from __future__' not in source
    assert not source.startswith('\ufeff')
    assert 'import pytest' not in source
    main_js = Path(__file__).with_name('main.js').read_text(encoding='utf-8')
    assert '.callKwargs' not in main_js
    assert 'await new Promise' in main_js and 'once: true' in main_js
    assert not main_js.startswith('\ufeff')
