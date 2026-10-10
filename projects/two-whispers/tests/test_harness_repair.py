import json
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Statevector
import core
from experiments import noise
from experiments.run import _density_probabilities, _measurement_probabilities, hypothesis_margins
from synthesis import development_search


@pytest.mark.parametrize('case', [0, 1])
def test_every_block_zero_noise_and_analytic_success(case):
    circuits, manifest = core.make_demo(case)
    for circuit, block in zip(circuits, manifest['ordered_blocks']):
        actual = _density_probabilities(circuit, 'aria', 0)
        assert actual == pytest.approx(_measurement_probabilities(circuit), abs=1e-12)
        success = sum(p for bits, p in actual.items() if block['decoder'][int(bits, 2)] == block['label'])
        assert success == pytest.approx(core.P_SEQ if block['width'] == 3 else core.P_JOINT, abs=1e-12)


def test_asymmetric_nonadjacent_qargs_and_local_pauli_order():
    c = QuantumCircuit(3)
    c.ry(.42, 0)
    c.rx(.91, 2)
    c.cx(2, 0)
    c.ry(.17, 1)
    assert _density_probabilities(c, 'forte', 0) == pytest.approx(_measurement_probabilities(c), abs=1e-12)
    rho = DensityMatrix.from_int(0, 8).data
    got = noise.depolarize(rho, 1, [0])
    assert got[1, 1] == pytest.approx(2/3)
    assert got[4, 4] == 0


@pytest.mark.parametrize('model', ['aria', 'forte', 'fe'])
def test_calibration_and_aer_density_agree(model):
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    circuits, _ = core.make_demo(0)
    for circuit in (circuits[0], circuits[2]):
        rates = noise.effective_config(model)['rates']
        params = noise.CALIBRATION[noise.MODEL_KEYS[model]]
        nm = NoiseModel(basis_gates=params['basis'])
        nm.add_all_qubit_quantum_error(depolarizing_error(2*rates['one_qubit'], 1), ['sx', 'x'])
        nm.add_all_qubit_quantum_error(depolarizing_error(4*rates['two_qubit']/3, 2), [params['two_qubit_gate']])
        qc = noise.compile_circuit(circuit.remove_final_measurements(inplace=False), model)
        qc.save_density_matrix()
        data = AerSimulator(method='density_matrix', noise_model=nm).run(qc, shots=1).result().data(0)['density_matrix']
        expected = {format(i, f'0{circuit.num_qubits}b'): float(p) for i, p in enumerate(data.probabilities())}
        assert _density_probabilities(circuit, model, 1) == pytest.approx(expected, abs=1e-12)
    assert noise.PRELIMINARY['aria']['two_qubit'] == .009
    assert noise.PRELIMINARY['forte']['two_qubit'] == .012
    assert noise.PRELIMINARY['fe']['two_qubit'] == .021


def test_source_noise_boundary_and_readout():
    c = QuantumCircuit(2)
    c.x(0)
    c.barrier(label='receiver_start')
    c.rz(.5, 1)
    rates = {'one_qubit': .2, 'two_qubit': 0, 'readout': 0}
    assert _density_probabilities(c, 'aria', 1, staged=rates, source_noise=False)['01'] == pytest.approx(1)
    assert _density_probabilities(c, 'aria', 1, staged=rates, source_noise=True)['01'] == pytest.approx(.8)
    assert _density_probabilities(c, 'aria', 1, readout=.1, staged=rates, source_noise=False)['01'] == pytest.approx(.81)
    circuits, _ = core.make_demo(1)
    a = _density_probabilities(circuits[0], 'aria', 1, source_noise=False)
    b = _density_probabilities(circuits[0], 'aria', 1, source_noise=True)
    assert max(abs(a[k]-b[k]) for k in a) > 1e-5


def test_h1_grants_ideal_bound_h2_keeps_factor():
    errors = {'collective': .05, 'textbook': .06, 'deferred-sequential': .4}
    assert hypothesis_margins(errors) == pytest.approx((1-core.P_SEQ-.05, .9*.06-.05))


def test_real_tiny_development_search_and_frozen_recipe(tmp_path):
    result = development_search(budget=2, cases=(1,), output_dir=tmp_path)
    assert result['held_out_tuning'] is False
    assert result['settings']['full_budget_completed'] is False
    assert json.loads((tmp_path/'recipe.json').read_text(encoding='utf-8')) == result['recipe']
    for family, search in result['searches'].items():
        assert search['evaluations'] == 2
        assert all(np.isfinite(c['objective']) for c in search['candidates'])
        for record in result['verification'][family]:
            assert all(c['probability_residual'] < 1e-10 and c['unitary_residual'] < 1e-10 for c in record['checks'])
    for candidate in result['searches']['textbook']['candidates']:
        p = candidate['recipe']['parameters']
        assert p['relabel'] == 0 and p['row_phases'] == [0.0]*4 and p['completion_phase'] == 0
    with pytest.raises(ValueError):
        development_search(budget=1, cases=(9,))
