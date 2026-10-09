"""Tiny deterministic runtime checks; fixtures are TEST ONLY, never evidence."""
import importlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pytest
from qiskit import QuantumCircuit
from qiskit.providers.basic_provider import BasicSimulator
import main as runtime
from circuit_pack import pack_circuits, unpack_counts, normalize_counts, digest
from receipt import load_records, validate_record
from figures import parity_interval


class Result:
    def __init__(self, counts):
        self.counts, self.accesses = counts, 0
    def get_counts(self):
        self.accesses += 1
        assert self.accesses == 1
        return self.counts


class Job:
    def __init__(self, counts):
        self.cached, self.accesses = Result(counts), 0
    def result(self):
        self.accesses += 1
        assert self.accesses == 1
        return self.cached
    def job_id(self):
        return 'TEST ONLY'


class Backend:
    def __init__(self, ionq=False):
        self.name = 'ionq_simulator' if ionq else 'strict_builtin'
        self.options = {'noise_model': 'aria-1'}
        self.calls = 0
    def run(self, circuits, shots):
        self.calls += 1
        assert self.calls == 1
        if self.name == 'ionq_simulator':
            assert not isinstance(circuits, list)
            assert circuits.num_qubits <= 25
            counts = {'0' * circuits.num_clbits: shots}
        else:
            assert isinstance(circuits, list) and all(c.num_qubits == 4 for c in circuits)
            counts = [{'0000': shots} for c in circuits]
        self.job = Job(counts)
        return self.job


@pytest.fixture(autouse=True)
def quiet_plots(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda: None)
    yield
    plt.close('all')


def test_import_without_job(monkeypatch):
    backend = Backend()
    monkeypatch.setattr(runtime, 'backend', backend, raising=False)
    importlib.reload(runtime)
    assert backend.calls == 0


@pytest.mark.parametrize('ionq', [False, True])
@pytest.mark.parametrize('challenge,n', [('sealed', 6), ('audited16', 4)])
def test_dispatch_once(monkeypatch, capsys, ionq, challenge, n):
    backend = Backend(ionq)
    monkeypatch.setattr(runtime, 'backend', backend, raising=False)
    if ionq and challenge == 'audited16':
        with pytest.raises(ValueError, match='C27 smoke audit'):
            runtime.main(shots=10, challenge=challenge)
        assert backend.calls == 0
        return
    result = runtime.main(shots=10, challenge=challenge)
    assert len(result['marginals']) == n
    assert backend.calls == backend.job.accesses == backend.job.cached.accesses == 1
    assert all(sum(h.values()) == 10 for h in result['marginals'].values())
    text = capsys.readouterr().out
    assert 'No recorded IonQ runs yet' in text or 'Recorded:' in text
    assert 'systematic error unbounded' in text and 'Finite-shot' in text
    assert ('RECORD_JSON' in text) == ionq
    if ionq:
        validate_record(result['record'])
        assert [b['qubit_offset'] for b in result['layout']] == list(range(0, 4*n, 4))


def test_real_basic(monkeypatch):
    monkeypatch.setattr(runtime, 'backend', BasicSimulator(), raising=False)
    assert len(runtime.main(shots=8)['marginals']) == 6


def test_asymmetric_wiring():
    a = QuantumCircuit(1, 2, name='a'); a.x(0); a.measure(0, 1)
    b = QuantumCircuit(2, 2, name='b'); b.x(1); b.measure(0, 1); b.measure(1, 0)
    packed, layout = pack_circuits([a, b])
    assert layout[1]['qubit_to_clbit_map'] == {0: 1, 1: 0}
    raw = BasicSimulator().run(packed, shots=9).result().get_counts()
    assert unpack_counts(raw, layout) == {'a': {'10': 9}, 'b': {'01': 9}}
    assert unpack_counts({'1 10': 4}, layout) == {'a': {'10': 4}, 'b': {'01': 4}}
    assert normalize_counts({'1': 2, '00 01': 3}, 4) == {'0001': 5}


def test_nine_blocks_and_caps():
    blocks = []
    for i in range(9):
        c = QuantumCircuit(1, 1, name=str(i)); c.measure(0, 0); blocks.append(c)
    _, layout = pack_circuits(blocks)
    assert len(unpack_counts({'0': 5}, layout)) == 9
    c = QuantumCircuit(25, 25); c.measure(range(25), range(25))
    assert pack_circuits([c])[0].num_qubits == 25
    with pytest.raises(ValueError): pack_circuits([c] + blocks[:1])
    with pytest.raises(ValueError): pack_circuits([])
    c = QuantumCircuit(1, 1); c.measure(0, 0); c.x(0)
    with pytest.raises(ValueError): pack_circuits([c])


@pytest.mark.parametrize('counts', [{'2': 1}, {'': 1}, {'0': -1}, {'0': 1.1}, {'0': True}, {'00000': 1}])
def test_bad_counts(counts):
    with pytest.raises(ValueError): normalize_counts(counts, 4)


def test_validation_before_job(monkeypatch):
    b = Backend(True)
    monkeypatch.setattr(runtime, 'backend', b, raising=False)
    for args in [{'case': 4}, {'shots': False}, {'challenge': 'unknown'}, {'assume_trusted_measurements': 1}]:
        with pytest.raises(ValueError): runtime.main(**args)
    b.options = {}
    with pytest.raises(ValueError): runtime.main()
    assert b.calls == 0


def test_records_mixed_and_reanalysis(monkeypatch, capsys):
    monkeypatch.setattr(runtime, 'backend', Backend(True), raising=False)
    fixture = runtime.main(shots=8)['record']
    fixture['operator_environment'] = 'TEST ONLY synthetic in-memory fixture'
    valid, statuses = load_records('\n malformed\n RECORD_JSON ' + json.dumps(fixture) + '\n{}')
    assert len(valid) == 1 and any('Malformed' in x for x in statuses)
    import recorded_ionq
    monkeypatch.setattr(recorded_ionq, 'RECORDED', json.dumps(fixture))
    monkeypatch.setattr(runtime, 'backend', Backend(), raising=False)
    runtime.main(shots=8)
    assert 'Recorded Qollab IonQ' in capsys.readouterr().out
    for key, value in [('source', 'local noise approximation'), ('utc_start', '2026-10-01T00:00:00Z'), ('shots', 99), ('layout_hash', '0'*64), ('assumptions', [])]:
        bad = {**fixture, key: value}
        assert not load_records(json.dumps(bad))[0]
    assert load_records('')[0] == []


def test_boundary_interval():
    assert parity_interval(0, 10)[0] == -1
    assert parity_interval(10, 10)[1] == 1
    lo, hi = parity_interval(5, 10)
    assert lo < 0 < hi


def test_terminal_error_no_retry(monkeypatch, capsys):
    b = Backend(True)
    def fail(circuit, shots):
        b.calls += 1
        raise RuntimeError('TEST ONLY terminal failure')
    b.run = fail
    monkeypatch.setattr(runtime, 'backend', b, raising=False)
    with pytest.raises(RuntimeError): runtime.main(shots=8)
    assert b.calls == 1
    text = capsys.readouterr().out
    line = next(x for x in text.splitlines() if x.startswith('RECORD_JSON'))
    assert load_records(line)[0][0]['error'] == 'TEST ONLY terminal failure'
