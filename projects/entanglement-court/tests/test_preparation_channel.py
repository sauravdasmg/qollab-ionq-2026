"""Bounded exact checks for WP-C-14; no full sampling campaigns."""
import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Statevector, partial_trace
from scipy.stats import binom

from campaign import SLOTS, build_slot, slot_data
from circuit_pack import pack_circuits, unpack_counts
from cases import analyze_counts
from experiments.noise import apply_local_depolarizing, apply_local_phase_flips, RATES
from experiments.run import _probabilities, _counts
from measurements import append_preparation, append_measurement
from witness import cp_lower, allocate_alpha


def data_density(circuit):
    # Exact reduced density matrix of the purification, not sampled counts.
    state = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
    return partial_trace(state, list(range(4, circuit.num_qubits))) if circuit.num_qubits > 4 else DensityMatrix(state)


def test_all_manifest_distributions_and_cloud_cap():
    for row in SLOTS:
        circuits, manifest, _ = build_slot(row['slot'])
        packed, _ = pack_circuits(circuits)
        assert packed.num_qubits == 24
        assert set(manifest['dropped_Z_exhibits']) == {'target_Z', 'impostor_Z'}
        p = row['manifest']['generated_parameters']['diagonal_preparation_noise']
        assert manifest['prep_noise'] == 'ancilla phase-flip channel'
        assert manifest['prep_noise_per_wire_p'] == [p] * 4
        for circuit in circuits:
            rho = data_density(circuit)
            reference = _probabilities(0, circuit.name, manifest=row['manifest'])
            np.testing.assert_allclose(rho.probabilities(), reference, atol=1e-10, rtol=0)
            maps = manifest['blocks'][circuit.name]['parity_maps']
            assert circuit.count_ops()['ry'] == len(maps)
            assert {circuit.find_bit(op.qubits[0]).index for op in circuit.data if op.operation.name == 'measure'} == set(range(circuit.num_qubits))


def test_z_wire_flips_commute_with_full_measurement_distribution():
    # A generic entangled mixed state tests the projector argument independently
    # of graph uniformity: Z on a non-center commutes with RZ and Z measurement.
    rng = np.random.default_rng(14)
    a = rng.normal(size=(16, 16)) + 1j * rng.normal(size=(16, 16))
    rho = a @ a.conj().T
    rho /= np.trace(rho)
    for row in SLOTS[:4]:
        m = row['manifest']; params = m['generated_parameters']
        for color, name in enumerate(('target_A', 'target_B')):
            centers = {x['generator'] for x in m['blocks'][name]['parity_maps']}
            basis = QuantumCircuit(4)
            append_measurement(basis, 0, params['edges'], params['frame_radians'], color)
            reference = DensityMatrix(rho).evolve(basis).probabilities()
            for q in set(range(4)) - centers:
                z = 1 - 2 * ((np.arange(16) >> q) & 1)
                flipped = z[:, None] * rho * z[None, :]
                np.testing.assert_allclose(DensityMatrix(flipped).evolve(basis).probabilities(), reference, atol=1e-10, rtol=0)
        for kind in ('graph', 'product'):
            prep = QuantumCircuit(4)
            append_preparation(prep, 0, params['edges'], params['frame_radians'], params['product_angles_radians'], kind)
            state = DensityMatrix.from_instruction(prep)
            np.testing.assert_allclose(np.diag(apply_local_phase_flips(state.data, .49)), np.diag(state.data), atol=1e-10)
            np.testing.assert_allclose(state.probabilities(), np.ones(16)/16, atol=1e-10)


def expected_f(probabilities, manifest, shots):
    result = -3.
    k = np.arange(shots + 1)
    lower = np.array([cp_lower(int(s), shots, allocate_alpha()) for s in k])
    for name in ('target_A', 'target_B'):
        for mapping in manifest['blocks'][name]['parity_maps']:
            mask = [sum((j >> q) & 1 for q in mapping['bits']) % 2 == 0 for j in range(16)]
            success = probabilities[name][mask].sum()
            result += float(binom.pmf(k, shots, success) @ lower)
    return result


def test_near_threshold_aria_reference_and_bounded_draws():
    row = slot_data('C08')
    circuits, manifest, _ = build_slot('C08')
    probabilities = {}
    rates = RATES['aria']
    for circuit in circuits:
        rho = data_density(circuit).data
        # Same aggregate local Aria approximation as the harness. This is not
        # server compilation or a gate-by-gate model of the added ancilla gates.
        rho = apply_local_depolarizing(rho, list(range(4)), rates['1q'])
        rho = apply_local_depolarizing(rho, list(range(4)), rates['2q'] * 3)
        probabilities[circuit.name] = np.real(np.diag(rho))
        reference = _probabilities(0, circuit.name, scale=1., model='aria', manifest=row['manifest'])
        np.testing.assert_allclose(probabilities[circuit.name], reference, atol=1e-10, rtol=0)
    frozen = json.loads((Path(__file__).resolve().parents[1] / 'results/frozen.json').read_text(encoding='utf-8'))
    saved_case = next(c for c in frozen['cases'] if c['case_id'] == row['case_id'])
    saved = next(r for r in saved_case['noise_results'] if r['noise']['name'] == 'aria@1')
    measured_mean = saved['controls']['graph']['summary']['mean_F_lower']
    assert abs(expected_f(probabilities, manifest, saved['shots_per_block']) - measured_mean) < .025
    assert saved['controls']['graph']['summary']['certification_rate'] < .01
    assert expected_f(probabilities, manifest, 200) < .5
    # Ten draws only: a regression smoke check, never a certification-rate claim.
    certificates = 0
    for draw in range(10):
        marginals = {name: _counts(prob, 200, 14000 + 10*draw + i) for i, (name, prob) in enumerate(probabilities.items())}
        certificates += analyze_counts(marginals, manifest)['simultaneous_witness']['conditional_gme']
    assert certificates == 0


def test_ancilla_marginalization_in_analysis():
    _, manifest, _ = build_slot('C08')
    hist = {name: {'000000': 100, '110000': 100} for name in manifest['ordered_blocks']}
    analysis = analyze_counts(hist, manifest)
    assert all(row['successes'] == 200 for rows in analysis['blocks'].values() for row in rows)


def test_builtin_retains_z_exhibits():
    circuits, manifest, _ = build_slot('C08', include_z=True)
    assert sum(c.num_qubits for c in circuits) == 32
    assert manifest['dropped_Z_exhibits'] == []
    for circuit in circuits[:2]:
        np.testing.assert_allclose(data_density(circuit).probabilities(), np.ones(16)/16, atol=1e-10)


def test_campaign_record_and_legacy_exclusion(monkeypatch, capsys):
    import main as runtime
    from types import SimpleNamespace
    from circuit_pack import digest
    from receipt import load_records, validate_record

    class Backend:
        name = 'ionq_simulator'
        options = {'noise_model': 'aria-1'}
        def run(self, circuit, shots):
            counts = {'0' * circuit.num_clbits: shots}
            return SimpleNamespace(result=lambda: SimpleNamespace(get_counts=lambda: counts), job_id=lambda: 'TEST ONLY')

    monkeypatch.setattr(runtime, 'backend', Backend(), raising=False)
    monkeypatch.setattr(runtime, 'present', lambda *a: None)
    result = runtime.main(slot='C08', shots=200)
    record = result['record']
    validate_record(record)
    assert record['prep_noise'] == 'ancilla phase-flip channel'
    output = capsys.readouterr().out
    lines = [json.loads(line[len('RECORD_JSON '):]) for line in output.splitlines() if line.startswith('RECORD_JSON ')]
    assert len(lines) == 2
    assert all(r['prep_noise'] == 'ancilla phase-flip channel' for r in lines)
    assert all(r['prep_noise_per_wire_p'] == record['prep_noise_per_wire_p'] for r in lines)
    # Original 24-data-wire layout fixture; never cloud evidence.
    anchor = runtime.main(shots=8)['record']
    for slot in ('C08', 'C02'):
        old = json.loads(json.dumps(anchor))
        m = slot_data(slot)['manifest']
        old['settings']['manifest'] = m
        old.update(case_id=str(m['case_id']), construction_seed=m['seed'], recipe_hash=digest(m))
        kept, statuses = load_records(json.dumps(old))
        assert any('prep-noise omitted' in s for s in statuses)
        if slot == 'C08':
            assert kept == []
            assert any('superseded' in s for s in statuses)
        else:
            assert len(kept) == 1
            assert 'small documented deviation' in kept[0]['prep_noise']
