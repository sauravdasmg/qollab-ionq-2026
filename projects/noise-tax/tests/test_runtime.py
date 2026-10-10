"""Runtime behavior tests for noise channel, crossover, and recorded parsers."""
import json
import numpy as np
from qiskit.quantum_info import Statevector
import noise_channel as channel
import crossover
import recorded_ionq
import recorded_parser
import whispers_core as w
import hedging_core as n


def test_noise_channel_scale_zero_equals_statevector_whispers():
    """At scale 0, noise_channel probabilities equal ideal Statevector for all W blocks."""
    circuits, manifest = w.make_demo()
    for c in circuits:
        compiled = channel.compile_circuit(c)
        cfg = channel.configuration(scale=0.0)
        probs = channel.probabilities(compiled, cfg)
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        sv_probs = {format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(sv.probabilities())}
        for k in sorted(probs):
            assert math.isclose(probs[k], sv_probs.get(k, 0.0), abs_tol=1e-10)


def test_noise_channel_scale_zero_equals_statevector_hedging():
    """At scale 0, noise_channel probabilities equal ideal Statevector for all N blocks."""
    circuits, manifest = n.make_instance_demo()
    for c in circuits:
        compiled = channel.compile_circuit(c)
        cfg = channel.configuration(scale=0.0)
        probs = channel.probabilities(compiled, cfg)
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        sv_probs = {format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(sv.probabilities())}
        for k in sorted(probs):
            assert math.isclose(probs[k], sv_probs.get(k, 0.0), abs_tol=1e-10)


def test_noise_channel_params_match_ionq_noise_params():
    """Channel configuration parameters match ../../tools/ionq_noise_params.json."""
    import os
    param_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools', 'ionq_noise_params.json')
    with open(param_path, 'r') as f:
        expected = json.load(f)
    for model_key in channel.MODEL_KEYS:
        cfg = channel.configuration(model_key)
        expected_model = expected[channel.MODEL_KEYS[model_key]]
        assert math.isclose(cfg['r_1q'], expected_model['r_1q'], rel_tol=1e-10)
        assert math.isclose(cfg['r_2q'], expected_model['r_2q'], rel_tol=1e-10)
        assert math.isclose(cfg['readout'], expected_model['readout'], rel_tol=1e-10)
        assert cfg['basis'] == expected_model['basis']
        assert cfg['entangler'] == expected_model['two_qubit_gate']


def test_crossover_finds_known_zero_crossing():
    """crossing() finds a zero crossing on a synthetic monotonic curve."""
    grid = np.linspace(0, 1, 21)
    curve = 0.5 - grid  # crosses zero at 0.5
    result = crossover.crossing(grid, curve)
    assert result['status'] == 'resolved'
    assert math.isclose(result['estimate'], 0.5, abs_tol=1e-6)


def test_crossover_reports_censoring_when_no_crossing():
    """crossing() reports right-censored when curve is always positive."""
    grid = np.linspace(0, 1, 21)
    curve = grid + 0.1  # always positive
    result = crossover.crossing(grid, curve)
    assert result['status'] == 'right-censored'
    assert result['right_censored'] is True
    assert result['estimate'] is None


def test_crossover_reports_left_censored():
    """crossing() reports left-censored when curve is always negative."""
    grid = np.linspace(0, 1, 21)
    curve = -grid - 0.1  # always negative
    result = crossover.crossing(grid, curve)
    assert result['status'] == 'left-censored'


def test_recorded_ionq_parses_shipped_records():
    """recorded_ionq.parse_records() parses all RECORD_JSON lines."""
    records, statuses = recorded_ionq.parse_records()
    assert len(records) == 14  # 6 legacy W/N receipts + 8 cloud slots T01-T08
    for i, (r, s) in enumerate(zip(records, statuses)):
        assert s['ok'] is True
        assert r.get('schema_version') in ('1.0', '1.0.0', 'noise-tax-1')
        assert r.get('source') == 'Qollab IonQ simulator run'
        backend = r.get('backend')
        if isinstance(backend, dict):
            assert backend.get('name') == 'ionq_simulator'
        else:
            assert backend == 'ionq_simulator'
        # Records may have 'counts' (with marginals/packed), 'raw_packed_counts', 
        # 'raw_counts', or be job receipts with 'job_id' and 'layout'
        has_counts = ('counts' in r) or ('raw_packed_counts' in r) or ('raw_counts' in r)
        has_job_info = ('job_id' in r) and ('layout' in r)
        assert has_counts or has_job_info, f"Record {i} missing both counts and job info"
        assert 'manifest' in r


def test_recorded_ionq_rejects_malformed_line():
    """parse_records() rejects a malformed line cleanly."""
    bad_text = 'RECORD_JSON {"invalid": true}\n'
    records, statuses = recorded_ionq.parse_records(bad_text)
    assert len(records) == 0
    assert len(statuses) == 1
    assert statuses[0]['ok'] is False
    assert 'error' in statuses[0]


def test_recorded_ionq_rejects_wrong_schema():
    """parse_records() rejects unsupported schema versions."""
    bad_text = 'RECORD_JSON {"schema_version": "2.0", "source": "Qollab IonQ simulator run", "backend": {"name": "ionq_simulator"}, "shots": 1000}\n'
    records, statuses = recorded_ionq.parse_records(bad_text)
    assert len(records) == 0
    assert len(statuses) == 1
    assert statuses[0]['ok'] is False


def test_recorded_parser_summarize_record():
    """summarize_record extracts correct fields from W and N records."""
    records, _ = recorded_ionq.parse_records()
    for r in records:
        summaries = recorded_parser.summarize_record(r)
        for s in summaries:
            assert 'model' in s
            assert 'shots' in s
            assert 'case_id' in s
            if s['game'] == 'W':
                assert 'advantage' in s
                assert 'word_error' in s
            else:
                assert 'advantage' in s
                assert 'metrics' in s


import math