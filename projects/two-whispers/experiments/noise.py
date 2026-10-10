"""Small-block local density-channel approximation for evidence harness only."""
import numpy as np
import json
from pathlib import Path
from functools import lru_cache

PARAMETER_PATH = Path(__file__).resolve().parents[3] / 'tools' / 'ionq_noise_params.json'
CALIBRATION = json.loads(PARAMETER_PATH.read_text(encoding='utf-8'))
MODEL_KEYS = {'aria': 'ionq-aria', 'forte': 'ionq-forte', 'fe': 'ionq-forte-enterprise'}
PRELIMINARY = {name: {'one_qubit': CALIBRATION[key]['r_1q'],
                      'two_qubit': CALIBRATION[key]['r_2q'],
                      'readout': CALIBRATION[key]['readout']} for name, key in MODEL_KEYS.items()}
COMPILER_SEED = 1234


def compile_circuit(circuit, model):
    from qiskit import transpile
    return transpile(circuit, basis_gates=CALIBRATION[MODEL_KEYS[model]]['basis'],
                     optimization_level=1, seed_transpiler=COMPILER_SEED)


@lru_cache(maxsize=256)
def joint_channel(lam, width):
    """Aer depolarizing convention: (1-lambda)rho + lambda I/d Tr(rho)."""
    from qiskit.quantum_info import SuperOp
    d = 2**width
    ident = np.eye(d).reshape(-1, order='F')
    return SuperOp((1-lam)*np.eye(d*d) + lam*np.outer(ident, ident)/d)


def _validate_density(rho):
    a = np.asarray(rho, dtype=complex)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or a.shape[0] not in (2, 4, 8):
        raise ValueError('density matrix must describe a block of at most three qubits')
    if not np.allclose(a, a.conj().T, atol=1e-10) or not np.isclose(np.trace(a), 1, atol=1e-9):
        raise ValueError('invalid density matrix')
    if np.linalg.eigvalsh(a).min() < -1e-9:
        raise ValueError('density matrix is not positive')
    return a


def unitary_channel(rho, unitary):
    a = _validate_density(rho)
    u = np.asarray(unitary, dtype=complex)
    if u.shape != a.shape or not np.allclose(u.conj().T @ u, np.eye(len(u)), atol=1e-9):
        raise ValueError('unitary dimension mismatch')
    return u @ a @ u.conj().T


def depolarize(rho, probability, qubits=None):
    """Apply independent local Pauli depolarization on selected qubits."""
    a = _validate_density(rho)
    p = float(probability)
    if not 0 <= p <= 1:
        raise ValueError('probability must lie in [0, 1]')
    n = int(np.log2(len(a)))
    selected = tuple(range(n)) if qubits is None else tuple(qubits)
    if len(set(selected)) != len(selected) or any(isinstance(q, bool) or not isinstance(q, int) or q < 0 or q >= n for q in selected):
        raise ValueError('invalid qubit indices')
    result = a.copy()
    paulis = (np.array([[0, 1], [1, 0]], complex),
              np.array([[0, -1j], [1j, 0]], complex),
              np.diag([1, -1]).astype(complex))
    for q in selected:
        result = (1-p)*result
        for operator in paulis:
            factors = [np.eye(2, dtype=complex) for _ in range(n)]
            factors[n-1-q] = operator
            full = factors[0]
            for factor in factors[1:]:
                full = np.kron(full, factor)
            result += (p/3) * full @ a @ full.conj().T
        a = result
    return result


def readout_probabilities(probabilities, error):
    """Symmetric independent bit-flip readout channel on a bitstring distribution."""
    p = float(error)
    if not 0 <= p <= .5:
        raise ValueError('readout error must lie in [0, .5]')
    keys = list(probabilities)
    if not keys or any(not isinstance(k, str) or not k or set(k)-{'0', '1'} for k in keys):
        raise ValueError('probability keys must be binary strings')
    width = len(keys[0])
    if any(len(k) != width for k in keys) or any(float(v) < 0 for v in probabilities.values()):
        raise ValueError('invalid distribution')
    total = sum(float(v) for v in probabilities.values())
    if not np.isclose(total, 1):
        raise ValueError('probabilities must sum to one')
    out = {k: 0.0 for k in keys}
    for source, mass in probabilities.items():
        for target in keys:
            distance = sum(a != b for a, b in zip(source, target))
            out[target] += float(mass)*(p**distance)*((1-p)**(width-distance))
    return out


def probabilities_from_statevector(state, width):
    """Exact terminal computational probabilities, used to cross-check channels."""
    v = np.asarray(state, dtype=complex)
    if width not in (1, 2, 3) or v.shape != (2**width,):
        raise ValueError('statevector width must be one to three qubits')
    norm = np.vdot(v, v).real
    if not np.isclose(norm, 1):
        raise ValueError('statevector must be normalized')
    return {format(i, f'0{width}b'): float(abs(x)**2) for i, x in enumerate(v)}


def effective_config(name, scale=1.0, readout=None, staged=None):
    """Return an explicitly approximate, serializable local-channel record."""
    if name not in PRELIMINARY:
        raise ValueError('unknown local model')
    if not 0 <= float(scale) <= 2:
        raise ValueError('scale must lie in [0, 2]')
    base = dict(PRELIMINARY[name] if staged is None else staged)
    if set(base) != {'one_qubit', 'two_qubit', 'readout'} or any(not 0 <= float(v) <= 1 for v in base.values()):
        raise ValueError('invalid staged rates')
    base['one_qubit'] *= float(scale)
    base['two_qubit'] *= float(scale)
    base['readout'] *= float(scale)
    if readout is not None:
        base['readout'] = float(readout)
    if base['one_qubit'] > 1 or base['two_qubit'] > 1 or not 0 <= base['readout'] <= .5:
        raise ValueError('effective rate out of range')
    return {'label': 'local IonQ-like approximation', 'model': name, 'scale': float(scale),
            'rates': base, 'basis': CALIBRATION[MODEL_KEYS[name]]['basis'],
            'compiler_seed': COMPILER_SEED, 'optimization_level': 1,
            'source': str(PARAMETER_PATH),
            'channel': 'infidelity to joint depolarizing lambda; sx/x only, rz noiseless'}
