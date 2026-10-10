"""Runtime/helper tests: packing, counts, receipts, backend doubles.

All tests are local and deterministic; no external tools or cloud calls.
Synthetic recorded fixtures exist in memory only and are never shipped evidence.
"""
import io
import json
import math
import contextlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pytest
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.providers.basic_provider import BasicSimulator

import circuit_pack
import core
import figures
import main as runtime
import receipt
import recorded_ionq


class _ResultJob:
    def __init__(self, counts, job_id='test-job-1'):
        self._counts = counts
        self.job_id = job_id
        self.result_calls = 0
        self.counts_calls = 0

    def result(self):
        self.result_calls += 1
        if self.result_calls > 1:
            raise AssertionError('job.result() fetched more than once')
        return self

    def get_counts(self):
        self.counts_calls += 1
        if self.counts_calls > 1:
            raise AssertionError('get_counts() called more than once')
        return self._counts


class StoutBackend:
    """Built-in-style double: supports lists, counts accesses, no set_options."""

    name = 'builtin-fake'

    def __init__(self, counts_by_name, shots):
        self._storage = dict(counts_by_name)
        self.shots = shots
        self.run_calls = 0
        self.job = None

    def run(self, circuits, shots=None):
        self.run_calls += 1
        if not isinstance(circuits, list):
            raise AssertionError('built-in double expects a circuit list')
        counts = [self._storage[circuit.name] for circuit in circuits]
        self.job = _ResultJob(counts)
        return self.job


class IonqBackend:
    """IonQ-style double: one packed circuit, one job, cached single fetch."""

    name = 'ionq_simulator'

    def __init__(self, raw_counts, shots):
        self._raw = raw_counts
        self.shots = shots
        self.set = {}
        self.run_calls = 0
        self.job = None
        self.packed_circuit = None

    def set_options(self, **kwargs):
        self.set.update(kwargs)

    def run(self, circuit, shots=None):
        self.run_calls += 1
        if self.run_calls > 1:
            raise AssertionError('more than one job on the ionq double')
        if isinstance(circuit, list):
            raise AssertionError('ionq double rejects circuit lists')
        self.packed_circuit = circuit
        self.job = _ResultJob(dict(self._raw))
        return self.job


def _demo_manifest():
    _, manifest = core.make_demo(0)
    return manifest


def _zero_counts(manifest, shots):
    return {block['block_name']: {format(0, f"0{block['width']}b"): shots}
            for block in manifest['ordered_blocks']}


def _synthetic_record(case_id=0, shots=1000):
    layout = [{
        'block_name': 'case0_label0_collective', 'qubit_offset': 0,
        'qubit_width': 2, 'classical_offset': 0, 'classical_width': 2,
        'qubit_to_cbit_map': {0: 0, 1: 1}, 'manifest_hash': 'a' * 64,
    }]
    hashes = {'recipe': 'b' * 64, 'circuit': 'c' * 64,
              'layout': receipt.hash_layout(layout), 'manifest': 'd' * 64}
    return receipt.build_record(
        case_id=case_id, parameters={'seed': None}, construction_seed=None,
        shots=shots, noise_model='aria-1',
        packed_counts={'00': shots}, marginals=[{'00': shots}], layout=layout,
        hashes=hashes, uncertainty={'method': 'pointwise Wilson', 'confidence': 0.95},
        assumptions=['conditional on the ideal product source'],
        started_utc='2026-10-10T02:00:00Z', ended_utc='2026-10-10T02:05:00Z',
        job_id=None, environment={'operator': 'test only (in memory)'})


@pytest.fixture(autouse=True)
def _quiet_matplotlib_and_backend():
    runtime.backend = None
    yield
    runtime.backend = None
    plt.close('all')


# ------------------------------------------------------------------ built-in


def test_builtin_real_basic_simulator_nine_marginals(capsys):
    runtime.backend = BasicSimulator()
    summary = runtime.main(case=0, shots=128)
    assert summary['mode'] == 'built-in ideal'
    assert len(summary['marginals']) == 9
    for marginal in summary['marginals']:
        assert sum(marginal.values()) == 128
    entry = summary['analysis']['collective']
    assert entry['success_probability'] is not None
    assert 0.5 <= entry['success_probability'] <= 1.0
    assert 'RECORD_JSON' not in capsys.readouterr().out


def test_builtin_double_one_job_single_fetch_cached_counts():
    shots = 200
    backend = StoutBackend(_zero_counts(_demo_manifest(), shots), shots)
    runtime.backend = backend
    summary = runtime.main(case=0, shots=shots)
    assert backend.run_calls == 1
    assert backend.job.result_calls == 1
    assert backend.job.counts_calls == 1
    assert len(summary['marginals']) == 9
    for marginal in summary['marginals']:
        assert sum(marginal.values()) == shots


def test_builtin_double_has_no_set_options_and_never_needs_it():
    shots = 100
    backend = StoutBackend(_zero_counts(_demo_manifest(), shots), shots)
    assert not hasattr(backend, 'set_options')
    runtime.backend = backend
    summary = runtime.main(case=0, shots=shots, noise_model='forte-1')
    assert summary['noise_used'] is False
    assert backend.run_calls == 1


@pytest.mark.parametrize('case,shots,noise', [
    (-1, 1024, 'aria-1'), (29, 1024, 'aria-1'), (True, 1024, 'aria-1'),
    (0, 0, 'aria-1'), (0, -5, 'aria-1'), (0, True, 'aria-1'),
    (0, 1024, 'juno-1'), (0, 1024, 3),
])
def test_invalid_inputs_raise_before_any_job(case, shots, noise):
    backend = StoutBackend({}, 100)
    runtime.backend = backend
    with pytest.raises(ValueError):
        runtime.main(case=case, shots=shots, noise_model=noise)
    assert backend.run_calls == 0


# ------------------------------------------------------------------- ionq


@pytest.mark.parametrize('model', ['aria-1', 'forte-1', 'forte-enterprise-1'])
def test_ionq_double_one_pack_single_fetch_and_record(model, capsys):
    shots = 1000
    backend = IonqBackend({'0' * 21: shots}, shots)
    runtime.backend = backend
    summary = runtime.main(case=0, shots=shots, noise_model=model)
    assert backend.run_calls == 1
    assert isinstance(backend.packed_circuit, QuantumCircuit)
    assert backend.packed_circuit.num_qubits == 21 <= 25
    assert backend.set['noise_model'] == model
    assert backend.job.result_calls == 1
    assert backend.job.counts_calls == 1
    for marginal in summary['marginals']:
        assert sum(marginal.values()) == shots
    assert summary['noise_used'] is True
    record = summary['record']
    assert receipt.validate_record(record) == []
    out = capsys.readouterr().out
    assert 'RECORD_JSON ' in out
    line = next(x for x in out.splitlines() if x.startswith('RECORD_JSON '))
    parsed = json.loads(line[len('RECORD_JSON '):].strip())
    assert receipt.validate_record(parsed) == []
    assert parsed['case_id'] == 0
    assert parsed['noise_model'] == model
    assert parsed['shots'] == shots
    reprocessed, statuses = receipt.parse_records(receipt.format_record(record))
    assert statuses == [{'line': 1, 'ok': True, 'error': None}]
    assert receipt._json(reprocessed[0]) == receipt._json(record)
    with pytest.raises(AssertionError):
        backend.job.result()
    with pytest.raises(AssertionError):
        backend.job.get_counts()
    with pytest.raises(AssertionError):
        backend.run(backend.packed_circuit, shots=shots)


# ------------------------------------------------------------ circuit packing


def test_pack_unpack_asymmetric_widths_and_nonidentity_map():
    a = QuantumCircuit(1, 1, name='a')
    a.x(0)
    a.measure([0], [0])
    b = QuantumCircuit(2, 2, name='b')
    b.x(0)
    b.measure([0, 1], [1, 0])
    packed, layout = circuit_pack.pack_circuits([a, b])
    assert packed.num_qubits == 3 and packed.num_clbits == 3
    assert layout[0]['qubit_width'] == 1 and layout[0]['classical_width'] == 1
    assert layout[1]['qubit_to_cbit_map'] == {0: 1, 1: 0}
    assert [inst.operation.name for inst in packed.data[-3:]] == [
        'measure', 'measure', 'measure']
    marginals = circuit_pack.unpack_counts({'001': 7, '111': 5}, layout)
    assert marginals[0] == {'1': 12}
    assert marginals[1] == {'00': 7, '11': 5}
    assert sum(marginals[0].values()) == 12
    assert sum(marginals[1].values()) == 12
    actual = BasicSimulator().run(packed, shots=10).result().get_counts()
    assert actual == {'101': 10}
    assert circuit_pack.unpack_counts(actual, layout) == [{'1': 10}, {'10': 10}]


def test_pack_four_and_six_blocks_return_matching_marginals():
    for widths in ([1, 2, 3, 1], [2, 2, 2, 2, 2, 2]):
        circuits = []
        for index, width in enumerate(widths):
            circuit = QuantumCircuit(width, width, name=f'b{index}')
            circuit.x(0)
            circuit.measure(range(width), range(width))
            circuits.append(circuit)
        packed, layout = circuit_pack.pack_circuits(circuits)
        assert len(layout) == len(widths)
        marginals = circuit_pack.unpack_counts(
            {'1' * packed.num_clbits: 10, '0' * packed.num_clbits: 6}, layout)
        assert len(marginals) == len(widths)
        for marginal in marginals:
            assert sum(marginal.values()) == 16


def test_normalization_spaces_leading_zeros_and_merge():
    layout = [{'block_name': 'x', 'qubit_offset': 0, 'qubit_width': 1,
               'classical_offset': 0, 'classical_width': 3,
               'qubit_to_cbit_map': {0: 0}}]
    marginals = circuit_pack.unpack_counts(
        {' 1 ': 3, '1': 2, '01': 1, ' 0 0 1 ': 4, '011': 0}, layout)
    assert marginals[0] == {'001': 10, '011': 0}
    with pytest.raises(ValueError):
        circuit_pack.unpack_counts({'': 1}, layout)
    with pytest.raises(ValueError):
        circuit_pack.unpack_counts({'2': 1}, layout)
    with pytest.raises(ValueError):
        circuit_pack.unpack_counts({'1111': 1}, layout)
    with pytest.raises(ValueError):
        circuit_pack.unpack_counts({'00': -1}, layout)
    with pytest.raises(ValueError):
        circuit_pack.unpack_counts({'00': 1.5}, layout)
    with pytest.raises(ValueError):
        circuit_pack.unpack_counts({'00': True}, layout)


def test_cap_and_layout_validation():
    circuits = []
    for index in range(3):
        circuit = QuantumCircuit(1, 1, name=str(index))
        circuit.x(0)
        circuit.measure(0, 0)
        circuits.append(circuit)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits(circuits, max_qubits=2)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([])
    layout = [{'block_name': 'x', 'qubit_offset': 0, 'qubit_width': 1,
               'classical_offset': 0, 'classical_width': 1,
               'qubit_to_cbit_map': {0: 0}},
              {'block_name': 'y', 'qubit_offset': 0, 'qubit_width': 1,
               'classical_offset': 1, 'classical_width': 1,
               'qubit_to_cbit_map': {0: 0}}]
    with pytest.raises(ValueError):
        circuit_pack.unpack_counts({'11': 1}, layout)
    broken = dict(layout[0])
    del broken['block_name']
    with pytest.raises(ValueError):
        circuit_pack.validate_layout([broken])


def test_nonterminal_and_control_flow_rejected():
    c = QuantumCircuit(2, 2)
    c.h(0)
    c.measure(0, 0)
    c.cx(0, 1)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([c])
    qr, cr = QuantumRegister(1, 'q'), ClassicalRegister(1, 'c')
    conditioned = QuantumCircuit(qr, cr)
    conditioned.h(0)
    with conditioned.if_test((cr[0], 1)):
        conditioned.x(0)
    conditioned.measure(0, 0)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([conditioned])
    looped = QuantumCircuit(1, 1)
    with looped.for_loop(range(2)):
        looped.x(0)
    looped.measure(0, 0)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([looped])
    without_measure = QuantumCircuit(1, 1)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([without_measure])


# ----------------------------------------------------------- receipts / records


def test_recorded_initial_empty():
    records, statuses = receipt.parse_records(recorded_ionq.RECORDED)
    assert all(status['ok'] for status in statuses)
    assert receipt.recap(records) == ['No recorded IonQ runs yet'] if not records else all(
        line.startswith('Recorded ') for line in receipt.recap(records))


def test_parse_records_mixed_prefix_bare_malformed_missing(capsys):
    record = _synthetic_record()
    good_prefixed = 'RECORD_JSON ' + json.dumps(record)
    good_bare = json.dumps(record)
    missing = {key: value for key, value in record.items() if key != 'counts'}
    text = '\n\n'.join(['', good_prefixed, good_bare, 'not json {{{',
                        json.dumps(missing)])
    records, statuses = receipt.parse_records(text)
    assert len(records) == 2
    assert [status['ok'] for status in statuses] == [True, True, False, False]
    assert any('malformed JSON' in status['error'] for status in statuses if not status['ok'])
    assert any('counts' in status['error'] for status in statuses if not status['ok'])


def _mutate(record, change):
    out = json.loads(json.dumps(record))
    change(out)
    return out


def test_validate_rejects_tampered_records():
    record = _synthetic_record()
    bad_records = [
        _mutate(record, lambda r: r.__setitem__('source', 'edited')),
        _mutate(record, lambda r: r.__setitem__('schema_version', '9.9')),
        _mutate(record, lambda r: r.__setitem__('noise_model', 'juno-1')),
        _mutate(record, lambda r: r.__setitem__('shots', 0)),
        _mutate(record, lambda r: r['timestamps'].__setitem__('ended_utc',
                                                              '2026-10-10T01:59:59Z')),
        _mutate(record, lambda r: r['timestamps'].__setitem__(
            'started_utc', '2026-09-01T00:00:00Z')),
        _mutate(record, lambda r: r['counts'].__setitem__('packed', {'00': 1})),
        _mutate(record, lambda r: r['counts']['marginals'].__setitem__(0, {'11': 1000})),
        _mutate(record, lambda r: r['hashes'].__setitem__('layout', 'z' * 64)),
        _mutate(record, lambda r: r['hashes'].__setitem__('recipe', 'short')),
        _mutate(record, lambda r: r['layout'][0].pop('block_name')),
        _mutate(record, lambda r: r.__setitem__('environment', {})),
        _mutate(record, lambda r: r.__setitem__('status', 'failure')),
        _mutate(record, lambda r: (r.__setitem__('status', 'failure'),
                                   r.__setitem__('attempt_id', 'R-0001'),
                                   r.__setitem__('error', 'TooManyGates'))),
        _mutate(record, lambda r: r['paths'].__setitem__('source_file', '')),
    ]
    for index, candidate in enumerate(bad_records):
        assert receipt.validate_record(candidate) != [], f'case {index} passed'


def test_format_parse_round_trip_and_uncertainty_math():
    record = _synthetic_record()
    records, statuses = receipt.parse_records(receipt.format_record(record))
    assert len(records) == 1 and statuses == [{'line': 1, 'ok': True, 'error': None}]
    assert receipt._json(records[0]) == receipt._json(record)


def test_finite_shot_intervals_and_boundary_handling():
    circuits, manifest = core.make_demo(0)
    counts = [{format(3 if block['width'] == 2 else 7, f"0{block['width']}b"): 40}
              for block in manifest['ordered_blocks']]
    first = core.analyze_counts(counts, manifest)
    second = core.analyze_counts(counts, manifest)
    assert first == second
    for family in core.FAMILIES:
        lo, hi = first[family]['success_interval_95']
        assert 0.0 <= lo <= hi <= 1.0
        assert first[family]['success_probability'] == pytest.approx(1 / 3, abs=1e-12)
    empty = core.analyze_counts([{}] * 9, manifest)
    assert empty['collective']['success_probability'] is None
    lo, hi = empty['collective']['success_interval_95']
    assert lo == 0.0 and hi == 1.0  # honest full uncertainty for zero shots
    full = [{format(0, f"0{block['width']}b"): 40} for block in manifest['ordered_blocks']]
    analysed = core.analyze_counts(full, manifest)
    for family in core.FAMILIES:
        lo, hi = analysed[family]['success_interval_95']
        assert lo <= 1 / 3 <= hi  # interval covers the estimate for this toy counts


def test_recorded_status_before_and_after(monkeypatch, capsys):
    shots = 100
    backend = StoutBackend(_zero_counts(_demo_manifest(), shots), shots)
    runtime.backend = backend
    monkeypatch.setattr(recorded_ionq, 'RECORDED', '')
    runtime.main(case=0, shots=shots)
    assert 'No recorded IonQ runs yet' in capsys.readouterr().out
    records, _ = receipt.parse_records('')
    assert receipt.recap(records) == ['No recorded IonQ runs yet']
    monkeypatch.setattr(recorded_ionq, 'RECORDED',
                        'RECORD_JSON ' + json.dumps(_synthetic_record()))
    runtime.main(case=0, shots=shots)
    out = capsys.readouterr().out
    assert 'Recorded SUCCESS' in out
    assert 'source_file=results/exports/ionq_console_export.txt' in out


# ------------------------------------------------------------------- figures


def test_figure_text_labels():
    circuits, manifest = core.make_demo(0)
    counts = [{format(0, f"0{block['width']}b"): 100}
              for block in manifest['ordered_blocks']]
    analysis = core.analyze_counts(counts, manifest)
    figs = figures.render(analysis, manifest)
    assert len(figs) == 3
    titles = ' '.join(axis.get_title() for fig in figs for axis in fig.axes)
    suptitles = ' '.join(title.get_text() for fig in figs if fig._suptitle
                         for title in [fig._suptitle])
    labels = ' '.join(text.get_text() for fig in figs for axis in fig.axes
                      for text in axis.texts)
    assert 'TWO WHISPERS MAKE A WORD' in titles
    assert 'Confusion' in suptitles
    assert 'Word-error' in titles
    assert 'LABEL 0' in labels and 'COLLECTIVE' in labels
    del circuits


def test_hash_captures_gate_parameters_and_wires():
    from qiskit import QuantumCircuit
    a = QuantumCircuit(2, 2)
    a.rx(0.1, 0)
    a.measure([0, 1], [0, 1])
    b = QuantumCircuit(2, 2, name=a.name)
    b.rx(0.2, 0)
    b.measure([0, 1], [0, 1])
    assert receipt.hash_circuits([a]) != receipt.hash_circuits([b])


def test_callable_job_identifier_and_unavailable():
    class Job:
        def job_id(self):
            return 'TEST ONLY'
    assert receipt.job_identifier(Job()) == 'TEST ONLY'
    assert receipt.job_identifier(None) is None


def test_import_defines_entry_without_jobs(monkeypatch):
    import importlib
    monkeypatch.setattr(BasicSimulator, 'run', lambda *args, **kwargs: pytest.fail('import submitted a job'))
    importlib.reload(runtime)


def test_layout_validation_does_not_mutate_hash_input():
    record = _synthetic_record()
    record = json.loads(json.dumps(record))
    before = receipt._json(record['layout'])
    circuit_pack.validate_layout(record['layout'])
    assert receipt._json(record['layout']) == before


def test_repeated_measurement_rejected():
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)
    circuit.measure(0, 0)
    with pytest.raises(ValueError, match='repeated'):
        circuit_pack.pack_circuits([circuit])


def test_malformed_nested_records_do_not_discard_valid_lines():
    good = _synthetic_record()
    malformed = [
        _mutate(good, lambda r: r['counts'].__setitem__('marginals', [{'00': True}])),
        _mutate(good, lambda r: r['layout'][0].__setitem__('manifest_hash', None)),
        _mutate(good, lambda r: r['job'].__setitem__('available', True)),
        _mutate(good, lambda r: r['parameters'].__setitem__('x', float('nan'))),
        _mutate(good, lambda r: r['layout'][0].__setitem__('qubit_width', '2')),
    ]
    records, statuses = receipt.parse_records('\n'.join(json.dumps(r) for r in malformed + [good]))
    assert len(records) == 1
    assert [s['ok'] for s in statuses] == [False] * len(malformed) + [True]


def test_campaign_status_does_not_substitute_default_budget():
    assert all('readiness gap' in line for line in receipt.campaign_status([]))
    anchor = _synthetic_record(shots=1024)
    anchor['manifest'] = {'case_role': 'anchor', 'smoke_control_ids': []}
    assert all('readiness gap' in line for line in receipt.campaign_status([anchor]))
    anchor['shots'] = 1000
    lines = receipt.campaign_status([anchor])
    assert 'W02: Recorded' in lines[1]
    assert 'W01: readiness gap' in lines[0]


def test_figure_source_shots_assumptions_and_zero_counts():
    _, manifest = core.make_demo(0)
    analysis = core.analyze_counts([{}] * 9, manifest)
    figs = figures.render(analysis, manifest, source='recorded Qollab IonQ', shots=1000,
                          backend='ionq_simulator', noise_model='aria-1')
    captions = ' '.join(text.get_text() for fig in figs for text in fig.texts)
    assert 'recorded Qollab IonQ' in captions
    assert '1000' in captions and 'aria-1' in captions
    assert '95%' in captions and 'ideal product-state preparation' in captions


def test_terminal_error_records_attempt_without_retry(capsys):
    class FailedBackend(IonqBackend):
        def run(self, circuit, shots=None):
            job = super().run(circuit, shots=shots)
            def fail():
                job.result_calls += 1
                raise RuntimeError('TEST ONLY terminal error')
            job.result = fail
            return job
    backend = FailedBackend({}, 1000)
    runtime.backend = backend
    with pytest.raises(RuntimeError, match='TEST ONLY'):
        runtime.main(shots=1000)
    assert backend.run_calls == backend.job.result_calls == 1
    output = capsys.readouterr().out
    line = next(line for line in output.splitlines() if line.startswith('RECORD_JSON '))
    records, statuses = receipt.parse_records(line)
    assert statuses[0]['ok']
    assert records[0]['status'] == 'failure'
    assert records[0]['attempt_id'] == 'test-job-1'
    assert 'counts' not in records[0]
