"""Tiny shipped-evidence and cloud-contract checks; no sweeps or cloud jobs."""
import importlib.util
import json
from pathlib import Path
import time
import pytest
from qiskit.providers.basic_provider import BasicSimulator
import main
import nt_curves
from cloud_slots import SLOTS, resolve_slot
from experiments.make_curves import render

ROOT = Path(__file__).resolve().parents[1]


def test_generated_module_exactly_matches_summary():
    assert (ROOT / 'nt_curves.py').read_text(encoding='utf-8') == render(ROOT / 'results/summary.json')
    assert nt_curves.CURVES == json.loads((ROOT / 'results/summary.json').read_text())
    for suite in ('frozen', 'fresh'):
        data = nt_curves.CURVES['suites'][suite]
        assert len(data['grid']) == 81
        for game in ('W', 'N'):
            for a in data['analysis'][game].values():
                assert len(a['mean_advantage']) == 81
                if game == 'W':
                    assert a['reporting'] == 'DETERMINISTIC'
                    assert a['calibration_sensitivity']
                else:
                    assert len(a['lower_band']) == len(a['upper_band']) == 81


def test_bridge_reads_flat_module_without_result_files(monkeypatch):
    spec = importlib.util.spec_from_file_location('tax_bridge_test', ROOT / 'web/tax_bridge.py')
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    monkeypatch.setattr(Path, 'read_text', lambda *a, **kw: pytest.fail('runtime file read'))
    evidence = bridge.get_evidence()
    assert evidence['suites'] == nt_curves.CURVES['suites']
    assert evidence['source_sha256'] == nt_curves.SOURCE_SHA256
    assert evidence['games']['N']['aria-1']['n_instances'] == 24
    fresh = bridge.get_evidence('fresh')
    assert fresh['games']['N']['aria-1']['advantage'] == nt_curves.CURVES['suites']['fresh']['analysis']['N']['aria-1']['mean_advantage']


def test_slot_budgets_and_retry_guards():
    assert list(SLOTS) == [f'T{i:02d}' for i in range(1, 11)]
    assert sum(SLOTS[f'T{i:02d}']['shots'] for i in range(1, 11)) == 28000
    assert SLOTS['T01']['noise_model'] == SLOTS['T02']['noise_model'] == 'aria-2'
    assert resolve_slot('T09', 'T01')['shots'] == 1000
    with pytest.raises(ValueError):
        resolve_slot('T09')
    with pytest.raises(ValueError):
        main.run_slot(BasicSimulator(), 'T01')


@pytest.mark.parametrize('slot', ['T01', 'T02', 'T07', 'T08', 'T09'])
def test_slot_one_packed_job_one_result(slot, capsys):
    class Result:
        def get_counts(self):
            return {'0' * backend.circuit.num_clbits: backend.shots}

    class Job:
        def result(self):
            backend.fetches += 1
            return Result()

    class Backend:
        name = 'ionq_simulator'
        fetches = 0
        runs = 0

        def set_options(self, **options):
            self.options = options

        def run(self, circuit, shots):
            self.runs += 1
            self.circuit, self.shots = circuit, shots
            return Job()

    backend = Backend()
    main.run_slot(backend, slot, 'T01' if slot == 'T09' else '')
    assert backend.runs == backend.fetches == 1
    assert backend.circuit.num_qubits <= 25
    line = next(line for line in capsys.readouterr().out.splitlines() if line.startswith('RECORD_JSON '))
    record = json.loads(line.removeprefix('RECORD_JSON '))
    assert record['slot'] == slot
    assert record['noise_model'] == backend.options['noise_model']
    assert record['shots'] == backend.shots


def test_default_quick_under_40_seconds(monkeypatch):
    import matplotlib
    matplotlib.use('Agg')
    monkeypatch.setattr(main, 'backend', BasicSimulator(), raising=False)
    started = time.perf_counter()
    result = main.main()
    assert set(result) == {'W', 'N'}
    assert time.perf_counter() - started < 40
