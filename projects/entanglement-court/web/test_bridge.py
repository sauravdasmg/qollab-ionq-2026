"""Tests for court_bridge.py."""
import pytest
from qiskit.providers.basic_provider import BasicSimulator
import court_bridge


def test_get_case_metadata():
    meta = court_bridge.get_case_metadata(0)
    assert meta['case_id'] == 0
    assert meta['exact_Z_uniform'] is True
    assert meta['exact_tv_distance'] == 0.0
    assert 'edges' in meta
    assert 'frame_radians' in meta
    assert 'product_angles_radians' in meta
    assert 'color_partitions' in meta


def test_get_case_metadata_invalid():
    with pytest.raises(ValueError):
        court_bridge.get_case_metadata(-1)
    with pytest.raises(ValueError):
        court_bridge.get_case_metadata(4)


def test_get_measurement_meaning():
    meaning = court_bridge.get_measurement_meaning()
    assert isinstance(meaning, str)
    assert len(meaning) > 0
    assert "Matching Z statistics" in meaning


def test_get_circuit_text():
    text = court_bridge.get_circuit_text(0, "sealed")
    assert isinstance(text, str)
    assert "QuantumCircuit" in text or "H " in text or "CZ" in text or "RZ" in text


def test_get_circuit_text_block():
    text = court_bridge.get_circuit_text(0, "sealed", "target_Z")
    assert isinstance(text, str)
    assert len(text) > 0


def test_load_recorded():
    result = court_bridge.load_recorded()
    assert 'records' in result
    assert 'statuses' in result
    assert isinstance(result['records'], list)
    assert isinstance(result['statuses'], list)


def test_run_demo_builtin():
    backend = BasicSimulator()
    result = court_bridge.run_demo(backend, case=0, shots=100, challenge="sealed", assume_trusted_measurements=False)
    assert 'manifest' in result
    assert 'marginals' in result
    assert 'analysis' in result
    assert 'source' in result
    assert result['source'].startswith('Live built-in ideal')
    assert result['shots'] == 100
    assert result['trusted'] is False
    assert 'target_Z' in result['marginals']
    assert 'impostor_Z' in result['marginals']
    assert 'simultaneous_witness' in result['analysis']
    assert 'F_lower' in result['analysis']['simultaneous_witness']


def test_run_demo_builtin_trusted():
    backend = BasicSimulator()
    result = court_bridge.run_demo(backend, case=0, shots=100, challenge="sealed", assume_trusted_measurements=True)
    assert result['trusted'] is True
    assert result['analysis']['simultaneous_witness']['trust_flag'] is True


def test_run_demo_invalid_case():
    backend = BasicSimulator()
    with pytest.raises(ValueError):
        court_bridge.run_demo(backend, case=-1, shots=100)
    with pytest.raises(ValueError):
        court_bridge.run_demo(backend, case=4, shots=100)


def test_run_demo_invalid_shots():
    backend = BasicSimulator()
    with pytest.raises(ValueError):
        court_bridge.run_demo(backend, case=0, shots=0)
    with pytest.raises(ValueError):
        court_bridge.run_demo(backend, case=0, shots=10001)


def test_run_demo_invalid_challenge():
    backend = BasicSimulator()
    with pytest.raises(ValueError):
        court_bridge.run_demo(backend, case=0, shots=100, challenge="invalid")


def test_run_demo_invalid_trust_flag():
    backend = BasicSimulator()
    with pytest.raises(ValueError):
        court_bridge.run_demo(backend, case=0, shots=100, challenge="sealed", assume_trusted_measurements="true")