"""Tiny deterministic regressions for WP-C-08; no campaign or noise sweep."""
import copy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator
from cases import make_demo, analyze_counts
from measurements import append_preparation, append_measurement
from experiments import run as harness
from witness import simultaneous_witness


def near_threshold_manifest():
    return harness.load_independent_manifest(ROOT / 'review/manifests/frozen.json')['instances'][12]['manifest']


def test_declared_noise_matches_independent_density_reference_for_all_controls():
    m = near_threshold_manifest(); params = m['generated_parameters']
    p = params['diagonal_preparation_noise']
    for kind in ('graph', 'product', 'biseparable'):
        prep = QuantumCircuit(4)
        if kind == 'biseparable':
            prep.h(0); prep.cx(0, 1); prep.h(2); prep.h(3)
            for q, angle in enumerate(params['frame_radians']):
                prep.rz(angle, q)
        else:
            append_preparation(prep, 0, params['edges'], params['frame_radians'],
                               params['product_angles_radians'], kind)
        state = Statevector.from_instruction(prep).data
        rho = np.outer(state, state.conj())
        # Independent Z-operator reference, rather than the channel helper.
        for q in range(4):
            z = QuantumCircuit(4); z.z(q); u = Operator(z).data
            rho = (1-p)*rho + p*u@rho@u.conj().T
        for name in m['ordered_blocks']:
            basis = QuantumCircuit(4)
            if not name.endswith('_Z'):
                append_measurement(basis, 0, params['edges'], params['frame_radians'],
                                   0 if name.endswith('_A') else 1)
            u = Operator(basis).data
            np.testing.assert_allclose(harness._probabilities(0, name, kind, manifest=m),
                                       np.diag(u@rho@u.conj().T).real, atol=1e-12)
    means = harness._exact_checks(m)['post_preparation_channel']['graph_means']
    np.testing.assert_allclose(means, [1-2*p]*4, atol=1e-12)


def test_exact_checks_use_manifest_parameters_and_reject_broken_maps():
    m = near_threshold_manifest(); p = m['generated_parameters']['diagonal_preparation_noise']
    ref = harness._exact_checks(m)
    assert ref['checked'] and ref['manifest_hash'] == harness.digest(m)
    assert ref['post_preparation_channel']['witness_reference'] == pytest.approx(1-4*p)
    assert ref['post_preparation_channel']['graph_fidelity'] == pytest.approx((1-p)**4)
    clean = copy.deepcopy(m); clean['generated_parameters']['diagonal_preparation_noise'] = 0.
    assert harness._exact_checks(clean)['post_preparation_channel']['witness_reference'] == pytest.approx(1.)
    altered = copy.deepcopy(m)
    altered['generated_parameters']['product_angles_radians'][0] += .7
    other = harness._exact_checks(altered)
    assert not np.allclose(ref['post_preparation_channel']['probabilities']['product']['target_A'],
                           other['post_preparation_channel']['probabilities']['product']['target_A'])
    bad = copy.deepcopy(m); bad['blocks']['target_A']['parity_maps'][0]['sign'] = -1
    with pytest.raises(ValueError, match='exact reference'):
        harness._exact_checks(bad)


def test_coverage_includes_impostor_bounds_from_same_draw():
    _, m = make_demo(0)
    probabilities = {kind: {name: harness._probabilities(0, name, kind, manifest=m)
                            for name in m['ordered_blocks']} for kind in ('graph', 'product')}
    marginals = harness._sample_marginals(probabilities, m, 'graph', 100, np.random.default_rng(7))
    # All-success impostor counts deliberately fail their true zero-mean bounds.
    for name in ('impostor_A', 'impostor_B'):
        marginals[name] = {'0000': 100}
    analysis = analyze_counts(marginals, m)
    covered = harness._round_coverage(analysis, probabilities, m, 'graph')
    assert len(covered) == 8 and all(covered[:4]) and not any(covered[4:])
    assert not all(covered)


def test_bias_bounds_reject_invalid_inputs_and_define_probability_semantics():
    parities = [{'successes': 100, 'shots': 100}]*4
    for bad in (-.6, float('nan'), float('inf'), -float('inf')):
        with pytest.raises(ValueError, match='finite and nonnegative'):
            simultaneous_witness(parities, bias_bounds=[bad]*4)
    clean = simultaneous_witness(parities)
    bounded = simultaneous_witness(parities, bias_bounds=[.01]*4)
    assert bounded['terms'][0]['L_lower'] == pytest.approx(clean['terms'][0]['L_lower']-.02)
    assert bounded['per_generator_alpha'] == .00625 and bounded['threshold'] == .5


def test_independent_smoke_is_bounded_without_relabeling_full_campaign(tmp_path):
    result = harness.run_suite('fresh', draws=1, shots=10,
                              output_dir=tmp_path/'quick-fresh',
                              manifest_path=ROOT/'review/manifests/fresh.json')
    assert result['config']['bounded_smoke'] and result['config']['staged_manifest_count'] == 20
    assert result['config']['sampled_case_ids'] == [20261011000, 20261011010]
    assert len(result['cases']) == 2
    assert all(len(case['noise_results']) == 1 for case in result['cases'])
    assert result['summary']['complete'] and not result['summary']['full_campaign_complete']
    assert result['summary']['science_verdict'] is None
