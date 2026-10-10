"""Shared circuits and small-state reference/noise simulation; little-endian wires."""
import hashlib
import json
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, Statevector

WIDTHS = (1, 2, 4)
PHASES = 2 * np.pi * np.arange(12) / 12
ARIA = {"r_1q": 0.0005, "r_2q": 0.009, "readout": 0.0,
        "basis": ["rz", "sx", "x", "rxx"], "noise_model": "aria-1"}


def fringe(n, phi, control="ghz"):
    if n not in WIDTHS:
        raise ValueError("width must be 1, 2, or 4")
    if control == "ghz":
        return float(np.cos(n * phi))
    if control == "product":
        return float(np.cos(phi) ** n)
    if control == "incoherent":
        return 0.0
    raise ValueError("unknown control")


def circuit(n, phi, control="ghz", measure=True):
    if n not in WIDTHS or control not in ("ghz", "product", "incoherent"):
        raise ValueError("invalid circuit specification")
    if control == "incoherent":
        raise ValueError("incoherent control is a density-matrix reference, not a dynamic circuit")
    q = QuantumCircuit(n, n) if measure else QuantumCircuit(n)
    if control == "product":
        q.h(range(n))
    else:
        q.h(0)
        for k in range(1, n):
            q.cx(0, k)
    for k in range(n):
        q.rz(float(phi), k)
    q.h(range(n))
    if measure:
        q.measure(range(n), range(n))
    return q


def circuits(phase_frame=0.0):
    return [circuit(n, p + phase_frame) for n in WIDTHS for p in PHASES]


def normalized_counts(counts, width):
    out = {}
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
            raise ValueError("counts must be nonnegative integers")
        key = str(key).replace(" ", "")
        if key.startswith("0x"):
            key = format(int(key, 16), "b")
        if not key or set(key) - {"0", "1"} or len(key) > width:
            raise ValueError("invalid count key")
        key = key.zfill(width)
        out[key] = out.get(key, 0) + int(value)
    if sum(out.values()) <= 0:
        raise ValueError("empty counts")
    return out


def parity_counts(counts):
    total = sum(counts.values())
    even = sum(v for k, v in counts.items() if k.count("1") % 2 == 0)
    if total <= 0:
        raise ValueError("empty counts")
    return even, total


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode("utf-8")).hexdigest()


def _embed(op, wires, n):
    c = QuantumCircuit(n)
    c.append(op, wires)
    return Operator(c).data


def probabilities(n, phi, scale=0.0, control="ghz"):
    """Exact <=4-wire evolution. Noise channels match calibrated local emulator.

    Aria basis compilation uses level 1, seed 0. rz is noiseless; sx/x
    receive lambda=2*r1; rxx receives lambda=4*r2/3. This is an approximation.
    """
    if control == "incoherent":
        rho = np.zeros((2**n, 2**n), complex)
        rho[0, 0] = rho[-1, -1] = 0.5
        q = QuantumCircuit(n)
        for k in range(n):
            q.rz(float(phi), k)
        q.h(range(n))
    else:
        q = circuit(n, phi, control, measure=False)
        if scale == 0:
            return Statevector.from_instruction(q).probabilities()
        rho = np.zeros((2**n, 2**n), complex)
        rho[0, 0] = 1
    q = transpile(q, basis_gates=ARIA["basis"], optimization_level=1, seed_transpiler=0)
    for item in q.data:
        wires = [q.find_bit(b).index for b in item.qubits]
        u = _embed(item.operation, wires, n)
        rho = u @ rho @ u.conj().T
        lam = min(1.0, scale * (2 * ARIA["r_1q"] if item.operation.name in ("sx", "x")
                               else 4 * ARIA["r_2q"] / 3 if item.operation.name == "rxx" else 0))
        if lam:
            # Complete Pauli twirl on the affected subsystem implements depolarization.
            mixed = np.zeros_like(rho)
            import itertools
            paulis = (np.eye(2), np.array([[0, 1], [1, 0]]),
                      np.array([[0, -1j], [1j, 0]]), np.diag([1, -1]))
            for labels in itertools.product(range(4), repeat=len(wires)):
                mats = [paulis[labels[wires.index(k)]] if k in wires else paulis[0]
                        for k in reversed(range(n))]
                v = mats[0]
                for mat in mats[1:]:
                    v = np.kron(v, mat)
                mixed += v @ rho @ v.conj().T / (4 ** len(wires))
            rho = (1 - lam) * rho + lam * mixed
    p = np.maximum(np.diag(rho).real, 0)
    return p / p.sum()


def sample_counts(n, phi, shots, rng, scale=0.0, control="ghz"):
    values = rng.multinomial(shots, probabilities(n, phi, scale, control))
    return {format(k, "0%db" % n): int(v) for k, v in enumerate(values) if v}
