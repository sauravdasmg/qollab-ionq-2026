"""Core identity tests for whispers and hedging games."""
import math
import numpy as np
from qiskit.quantum_info import Statevector
import whispers_core as w
import hedging_core as n
import hedging_strategies as hs


def test_whispers_joint_success_identity():
    """Joint success probability equals 1/2 + sqrt(2)/3."""
    circuits, manifest = w.make_demo()
    probs = []
    for c in circuits:
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        p = sv.probabilities()
        probs.append({format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(p)})
    result = w.analyze_probabilities(probs, manifest)
    assert math.isclose(result['joint']['success'], w.P_JOINT, rel_tol=1e-10)


def test_whispers_oneway_success_identity():
    """One-way success probability equals 1/2 + sqrt(3)/4."""
    circuits, manifest = w.make_demo(include_oneway=True)
    oneway = [(c, b) for c, b in zip(circuits, manifest['ordered_blocks']) if b['arm'] == 'oneway']
    probs = []
    for c, b in oneway:
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        p = sv.probabilities()
        probs.append({format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(p)})
    ref_manifest = {'ordered_blocks': [b for c, b in oneway]}
    result = w.analyze_probabilities(probs, ref_manifest)
    assert math.isclose(result['oneway']['success'], w.P_SEQ, rel_tol=1e-10)


def test_hedging_hedge_double_failure_zero():
    """Hedge strategy double failure is exactly 0 in ideal case."""
    circuits, manifest = n.make_instance_demo()
    probs = []
    for c in circuits:
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        p = sv.probabilities()
        probs.append({format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(p)})
    result = n.analyze_probabilities(probs, manifest)
    assert math.isclose(result['published_hedge']['double_failure'], 0.0, abs_tol=1e-10)


def test_hedging_product_double_failure_identity():
    """Product double failure equals (1 - cos^2(pi/8))^2."""
    circuits, manifest = n.make_instance_demo()
    probs = []
    for c in circuits:
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        p = sv.probabilities()
        probs.append({format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(p)})
    result = n.analyze_probabilities(probs, manifest)
    expected = (1 - math.cos(math.pi/8)**2)**2
    assert math.isclose(result['attained_product']['double_failure'], expected, rel_tol=1e-10)


def test_whispers_make_instance_structure():
    """make_instance returns correct structure."""
    spec = w.make_instance(seed=2026100900)
    assert spec['game'] == 'W'
    assert spec['seed'] == 2026100900
    assert 'frame' in spec
    frame = w.frame_from_spec(spec)
    assert frame.shape == (2, 2)
    assert np.allclose(frame.conj().T @ frame, np.eye(2), atol=1e-10)


def test_hedging_make_instance_structure():
    """make_instance returns correct structure."""
    spec = n.make_instance(seed=2026102900)
    assert spec['game'] == 'N'
    assert spec['seed'] == 2026102900
    assert 'alpha' in spec
    assert 'theta' in spec
    assert 0 <= spec['alpha'] <= math.pi/2
    assert 0 <= spec['theta'] <= math.pi/2


def test_whispers_held_out_seeds():
    """HELD_OUT_SEEDS are distinct from DEVELOPMENT_SEEDS."""
    dev = set(w.DEVELOPMENT_SEEDS)
    held = set(w.HELD_OUT_SEEDS)
    assert dev.isdisjoint(held)


def test_hedging_frozen_recipe_anchor():
    """frozen_recipe case 0 returns anchor parameters."""
    recipe = hs.frozen_recipe(0)
    assert recipe['identity'] == 'anchor-v2'
    assert recipe['seed'] is None
    assert math.isclose(recipe['alpha'], math.pi/4, rel_tol=1e-10)
    assert math.isclose(recipe['theta'], math.pi/8, rel_tol=1e-10)
    assert recipe['lambda_star'] == 0.02


def test_whispers_analyze_probabilities_validates():
    """analyze_probabilities rejects invalid distributions."""
    circuits, manifest = w.make_demo()
    probs = []
    for c in circuits:
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        p = sv.probabilities()
        probs.append({format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(p)})
    probs[0]['00'] = -0.1
    try:
        w.analyze_probabilities(probs, manifest)
        assert False, "should raise ValueError"
    except ValueError:
        pass


def test_hedging_analyze_probabilities_validates():
    """analyze_probabilities rejects invalid distributions."""
    circuits, manifest = n.make_instance_demo()
    probs = []
    for c in circuits:
        sv = Statevector.from_instruction(c.remove_final_measurements(inplace=False))
        p = sv.probabilities()
        probs.append({format(i, f'0{c.num_qubits}b'): float(v) for i, v in enumerate(p)})
    probs[0]['0000'] = -0.1
    try:
        n.analyze_probabilities(probs, manifest)
        assert False, "should raise ValueError"
    except ValueError:
        pass