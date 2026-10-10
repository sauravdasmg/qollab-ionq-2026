"""Local <=4-wire Pauli channels, independent of the shipped runtime."""
import hashlib
import itertools
import json
import math
from functools import lru_cache

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

VERSION = "HN-pauli-v2"
NOMINAL = {
    "aria": {"one_qubit": .0005, "two_qubit": .007, "readout": 0.},
    "forte": {"one_qubit": .000267, "two_qubit": .0125, "readout": 0.},
    "forte-enterprise": {"one_qubit": .000267, "two_qubit": .022, "readout": 0.},
}


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def configuration(model="aria", scale=1., *, readout=None, source_imbalance=0.,
                  one_factor=1., two_factor=1.):
    if model not in NOMINAL:
        raise ValueError("unknown model")
    cfg = dict(NOMINAL[model], model=model, scale=float(scale),
               source_imbalance=float(source_imbalance), version=VERSION,
               origin="local IonQ-like approximation; not official calibration")
    cfg["one_qubit"] *= one_factor
    cfg["two_qubit"] *= two_factor
    if readout is not None:
        cfg["readout"] = float(readout)
    validate(cfg)
    cfg["hash"] = digest(cfg)
    return cfg


def validate(cfg):
    values = [cfg[k] for k in ("one_qubit", "two_qubit", "readout", "scale")]
    values.append(cfg.get("source_imbalance", 0.))
    if not all(math.isfinite(x) for x in values) or cfg["scale"] < 0:
        raise ValueError("finite nonnegative noise parameters required")
    if any(not 0 <= cfg[k] * cfg["scale"] <= 1 for k in ("one_qubit", "two_qubit")):
        raise ValueError("gate error probability outside [0,1]")
    if not 0 <= cfg["readout"] <= .5 or abs(cfg.get("source_imbalance", 0.)) > .04:
        raise ValueError("readout/source imbalance outside preregistered range")


@lru_cache(maxsize=64)
def _paulis(n, wires):
    paulis = [np.eye(2), np.array([[0, 1], [1, 0]]),
              np.array([[0, -1j], [1j, 0]]), np.diag([1, -1])]
    operators = []
    for choice in itertools.product(range(4), repeat=len(wires)):
        if not any(choice):
            continue
        op = np.ones((1, 1), complex)
        for wire in reversed(range(n)):
            op = np.kron(op, paulis[choice[wires.index(wire)]] if wire in wires else paulis[0])
        operators.append(op)
    return operators


def _depolarize(rho, wires, probability):
    if not 0 <= probability <= 1:
        raise ValueError("invalid Pauli error probability")
    if not probability:
        return rho
    operators = _paulis(int(round(math.log2(len(rho)))), tuple(wires))
    return (1-probability)*rho + probability/len(operators)*sum(u@rho@u.conj().T for u in operators)


def _steps(circuit):
    if not 1 <= circuit.num_qubits <= 4:
        raise ValueError("local density simulator requires one to four wires")
    seen_measure = False
    for item in circuit.data:
        name = item.operation.name
        if name == "measure":
            seen_measure = True
            continue
        if name == "barrier":
            continue
        if seen_measure or name in {"reset", "if_else", "switch_case", "for_loop", "while_loop"}:
            raise ValueError("only unitary gates and terminal measurements are supported")
        wires = [circuit.find_bit(q).index for q in item.qubits]
        if len(wires) not in (1, 2):
            raise ValueError("only one/two-wire submitted gates supported")
        gate = QuantumCircuit(circuit.num_qubits)
        gate.append(item.operation, wires)
        yield Operator(gate).data, wires


def evolve(circuit, cfg, *, state=None, adjoint=False):
    validate(cfg)
    dim = 1 << circuit.num_qubits
    matrix = np.zeros((dim, dim), complex) if state is None else np.array(state, complex)
    if state is None:
        matrix[0, 0] = 1
    steps = list(_steps(circuit))
    for u, wires in reversed(steps) if adjoint else steps:
        rate = cfg["one_qubit"] if len(wires) == 1 else cfg["two_qubit"]
        if adjoint:
            matrix = u.conj().T @ _depolarize(matrix, wires, rate*cfg["scale"]) @ u
        else:
            matrix = _depolarize(u @ matrix @ u.conj().T, wires, rate*cfg["scale"])
    return matrix


def probabilities(circuit, cfg=None, *, ideal=False):
    cfg = configuration() if cfg is None else dict(cfg)
    # Source shifts must be applied by reconstructing the shared core recipe.
    if cfg.get("source_imbalance", 0.):
        raise ValueError("apply source_imbalance to recipe alpha before simulation")
    cfg = dict(cfg, scale=0., readout=0.) if ideal else cfg
    rho = evolve(circuit, cfg)
    p = np.real(np.diag(rho)).copy()
    if ideal:
        reference = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False)).probabilities()
        if not np.allclose(p, reference, atol=1e-11):
            raise ValueError("density/statevector cross-check failed")
    for bit in range(circuit.num_qubits):
        p = (1-cfg["readout"])*p + cfg["readout"]*p[np.arange(len(p)) ^ (1 << bit)]
    # Explicit measurement map; reject partial/duplicate measurements.
    mapping = [(circuit.find_bit(i.qubits[0]).index, circuit.find_bit(i.clbits[0]).index)
               for i in circuit.data if i.operation.name == "measure"]
    if mapping:
        if len(mapping) != circuit.num_qubits or circuit.num_clbits != circuit.num_qubits or \
                len({q for q, c in mapping}) != len(mapping) or len({c for q, c in mapping}) != len(mapping):
            raise ValueError("complete bijective terminal measurement required")
        measured = np.zeros_like(p)
        for i, value in enumerate(p):
            measured[sum(((i >> q) & 1) << c for q, c in mapping)] += value
        p = measured
    if p.min() < -1e-10 or not np.isclose(p.sum(), 1., atol=1e-10):
        raise ValueError("invalid channel probabilities")
    return np.maximum(p, 0.)/p.sum()


def product_tester(circuit, cfg):
    """Extract one identical test from the shared attained_product circuit.

    Assert the core layout instead of silently drifting when its physics changes.
    Source slice: RY(ref), CX(ref,prover); verifier: CX, RY(ref).
    The returned matrices use reference tensor prover, as product_bounds expects.
    """
    items = [i for i in circuit.data if i.operation.name not in ("measure", "barrier")]
    local = []
    for item in items:
        wires = [circuit.find_bit(q).index for q in item.qubits]
        if set(wires) <= {0, 2}:
            local.append((item.operation, [0 if q == 0 else 1 for q in wires]))
        elif not set(wires) <= {1, 3}:
            raise ValueError("coupled tests invalidate product tester")
    if [op.name for op, wires in local] != ["ry", "cx", "cx", "ry"]:
        raise ValueError("shared core product source/verifier interface changed")
    source = QuantumCircuit(2)
    verifier = QuantumCircuit(2)
    for op, wires in local[:2]:
        source.append(op, wires)
    for op, wires in local[2:]:
        verifier.append(op, wires)
    rho = evolve(source, cfg)
    e = cfg["readout"]
    effect = evolve(verifier, cfg, state=np.diag([(1-e)**2, e*(1-e), e*(1-e), e*e]), adjoint=True)
    order = [0, 2, 1, 3]
    return rho[np.ix_(order, order)], effect[np.ix_(order, order)]


def histogram(prob, shots, seed):
    p = np.asarray(prob, float)
    if isinstance(shots, bool) or int(shots) != shots or shots <= 0:
        raise ValueError("shots must be a positive integer")
    if p.ndim != 1 or len(p) < 2 or len(p) & (len(p)-1) or \
            not np.isfinite(p).all() or p.min() < 0 or not np.isclose(p.sum(), 1):
        raise ValueError("normalized power-of-two probability vector required")
    values = np.random.default_rng(seed).multinomial(int(shots), p)
    return {format(i, f"0{int(math.log2(len(values)))}b"): int(v) for i, v in enumerate(values) if v}
