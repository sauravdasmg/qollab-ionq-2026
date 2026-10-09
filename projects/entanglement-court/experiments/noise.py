"""Small-block local density-channel approximation for research harness only."""
from __future__ import annotations

import numpy as np


RATES = {
    "aria": {"1q": 0.0005, "2q": 0.007, "readout": 0.0},
    "forte": {"1q": 0.000267, "2q": 0.0125, "readout": 0.0},
    "forte-enterprise": {"1q": 0.000267, "2q": 0.022, "readout": 0.0},
}
LABEL = "local IonQ-like approximation"


def _validate_density(rho):
    a = np.asarray(rho, dtype=complex)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or a.shape[0] & (a.shape[0] - 1):
        raise ValueError("density matrix must be square with power-of-two dimension")
    if not np.allclose(a, a.conj().T, atol=1e-10) or not np.isclose(np.trace(a), 1, atol=1e-10):
        raise ValueError("density matrix must be Hermitian and trace one")
    return a


def depolarize(rho, probability):
    """Apply the dimension-d depolarizing channel (1-p)rho + p I/d."""
    a = _validate_density(rho)
    p = float(probability)
    if not 0 <= p <= 1:
        raise ValueError("probability must be in [0, 1]")
    return (1 - p) * a + p * np.eye(a.shape[0], dtype=complex) / a.shape[0]


def apply_local_depolarizing(rho, qubits, probability):
    """Apply independent one-qubit depolarization on listed little-endian wires."""
    out = _validate_density(rho)
    n = out.shape[0].bit_length() - 1
    p = float(probability)
    if not 0 <= p <= 1 or any(type(q) is not int or q < 0 or q >= n for q in qubits):
        raise ValueError("invalid probability or wire")
    for q in qubits:
        reduced = np.zeros_like(out)
        for pauli in (np.eye(2), np.array([[0, 1], [1, 0]]), np.array([[0, -1j], [1j, 0]]), np.diag([1, -1])):
            ops = [np.eye(2)] * n
            ops[q] = pauli
            u = ops[-1]
            for op in reversed(ops[:-1]):
                u = np.kron(u, op)
            reduced += u @ out @ u.conj().T
        out = (1 - p) * out + (p / 4) * reduced
    return out


def readout_probabilities(rho, n=None, bias=None):
    """Return computational probabilities after independent classical readout flips."""
    a = _validate_density(rho)
    n = a.shape[0].bit_length() - 1
    probs = np.real(np.diag(a)).copy()
    if bias is None:
        rates = [0.0] * n
    elif isinstance(bias, (int, float)):
        rates = [float(bias)] * n
    else:
        rates = [float(x) for x in bias]
    if len(rates) != n or any(x < 0 or x > 1 for x in rates):
        raise ValueError("readout bias must give one probability in [0,1] per wire")
    out = np.zeros_like(probs)
    for source, mass in enumerate(probs):
        for target in range(1 << n):
            likelihood = 1.0
            for q, rate in enumerate(rates):
                if ((source >> q) & 1) != ((target >> q) & 1):
                    likelihood *= rate
                else:
                    likelihood *= 1 - rate
            out[target] += mass * likelihood
    return out / out.sum()


def config(model="aria", scale=1.0, readout_bias=0.0):
    if model not in RATES or float(scale) < 0 or not 0 <= float(readout_bias) <= 1:
        raise ValueError("unknown model or invalid scale/bias")
    rates = RATES[model]
    return {"label": LABEL, "model": model, "scale": float(scale),
            "one_qubit_error": rates["1q"] * float(scale),
            "two_qubit_error": rates["2q"] * float(scale),
            "readout_bias": float(readout_bias),
            "assumption": "Raw gate errors approximate server-compiled noise; not official calibration."}


def ideal_probabilities(state):
    """Exact statevector computational distribution for ideal cross-checks."""
    s = np.asarray(state, dtype=complex)
    if s.ndim != 1 or not np.isclose(np.vdot(s, s).real, 1, atol=1e-10):
        raise ValueError("statevector must be a normalized vector")
    return np.abs(s) ** 2
