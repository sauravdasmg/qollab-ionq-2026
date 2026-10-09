"""circuit_pack.py: pack several terminally-measured sub-circuits onto disjoint wires and split counts back.

Shared helpers live in their own files: circuit_pack.py and receipt.py implement circuit packing,
count normalization, backend dispatch and evidence receipts. Written during Oct 9-11, 2026, with exact
UTC provenance and source/license attribution; used by Two Whispers Make a Word, Never Lose Twice and
Entanglement Court only where the shipped manifest lists the helper. Project-specific physics, decoding,
inference and presentation are described on each project page.

Only pure Python + Qiskit 2.x APIs are used (no qiskit-aer), so the module also runs in Qollab's
browser (Pyodide) runtime.
"""
from __future__ import annotations

import hashlib
import json
import numbers
from typing import Optional

from qiskit import QuantumCircuit

PACKED_NAME = "packed"
_DYNAMIC_OPS = ("if_else", "switch_case", "for_loop", "while_loop", "break", "continue",
                "reset", "store", "jump", "box", "control_flow")
_UINT_MAX = 1 << 63


def _format_param(value):
    if isinstance(value, bool):
        return "b:" + str(int(value))
    if isinstance(value, numbers.Integral):
        return "i:" + str(int(value))
    if isinstance(value, float):
        return "f:" + format(float(value), ".17g")
    return "s:" + str(value)


def _instruction_signature(circuit, instruction) -> list:
    """Deterministic, JSON-safe description of one circuit instruction (indices, names, parameters)."""
    qubits = [circuit.find_bit(q).index for q in instruction.qubits]
    clbits = [circuit.find_bit(c).index for c in instruction.clbits]
    params = [_format_param(p) for p in getattr(instruction.operation, "params", ())]
    return [instruction.operation.name, qubits, clbits, params]


def circuit_digest(circuit: QuantumCircuit) -> str:
    """Stable SHA-256 of the constituent instructions of a circuit (used as layout manifest_hash)."""
    digest = hashlib.sha256()
    for instruction in circuit.data:
        digest.update(json.dumps(_instruction_signature(circuit, instruction), sort_keys=True).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _validate_sub_circuit(circuit: QuantumCircuit, index: int) -> None:
    """Reject dynamic wiring, resets and anything after a measurement; every qubit measured at most once."""
    if not isinstance(circuit, QuantumCircuit):
        raise TypeError(f"item {index} of pack_circuits is not a QuantumCircuit ({type(circuit).__name__})")
    name = circuit.name or f"block_{index}"
    seen_measure = False
    measured_qubits = set()
    measured_clbits = set()
    for instruction in circuit.data:
        op = instruction.operation
        op_name = op.name
        if getattr(op, "condition", None) is not None:
            raise ValueError(f"circuit {name!r} has a conditional operation {op_name!r}; dynamic circuits are rejected")
        if op_name in _DYNAMIC_OPS:
            raise ValueError(f"circuit {name!r} contains unsupported nonterminal/dynamic operation {op_name!r}")
        if op_name == "measure":
            if seen_measure is False:
                seen_measure = True
            if len(instruction.qubits) != 1 or len(instruction.clbits) != 1:
                raise ValueError(f"circuit {name!r} has a measurement with unexpected wiring")
            q_local = circuit.find_bit(instruction.qubits[0]).index
            c_local = circuit.find_bit(instruction.clbits[0]).index
            if q_local in measured_qubits:
                raise ValueError(f"circuit {name!r} measures qubit {q_local} more than once")
            if c_local in measured_clbits:
                raise ValueError(f"circuit {name!r} writes classical bit {c_local} more than once")
            measured_qubits.add(q_local)
            measured_clbits.add(c_local)
        else:
            if seen_measure and op_name not in ("barrier", "delay"):
                raise ValueError(
                    f"circuit {name!r} has {op_name!r} after a measurement; measurements must be terminal"
                )
            if instruction.clbits:
                raise ValueError(f"circuit {name!r} wires {op_name!r} to a classical bit; unsupported")
    if not measured_qubits:
        raise ValueError(f"circuit {name!r} has no terminal measurement")


def pack_circuits(circuits, max_qubits: int = 25):
    """Place circuits side by side onto disjoint quantum and classical register slices.

    Returns ``(packed_circuit, layout)`` where ``layout`` is an ordered list with, per sub-circuit,
    ``name``, ``qubit_offset``, ``qubit_width``, ``clbit_offset``, ``clbit_width``,
    ``local_qubit_to_cbit_map`` and a deterministic ``manifest_hash``.
    """
    if isinstance(circuits, QuantumCircuit):
        raise ValueError("pack_circuits expects a sequence of circuits, not a single circuit")
    circuits = list(circuits)
    if not circuits:
        raise ValueError("pack_circuits received no circuits")
    if isinstance(max_qubits, bool) or not isinstance(max_qubits, numbers.Integral) or max_qubits <= 0:
        raise ValueError("max_qubits must be a positive integer")
    total_qubits = sum(circuit.num_qubits for circuit in circuits)
    if total_qubits > max_qubits:
        raise ValueError(f"packed circuit needs {total_qubits} qubits, which exceeds max_qubits={max_qubits}")
    for index, circuit in enumerate(circuits):
        _validate_sub_circuit(circuit, index)
    total_clbits = sum(circuit.num_clbits for circuit in circuits)
    names = [c.name or f"block_{i}" for i, c in enumerate(circuits)]
    if len(set(names)) != len(names):
        raise ValueError("block names must be unique")
    packed = QuantumCircuit(total_qubits, total_clbits, name=PACKED_NAME)
    layout = []
    qubit_offset = 0
    clbit_offset = 0
    for index, circuit in enumerate(circuits):
        qubit_width = circuit.num_qubits
        clbit_width = circuit.num_clbits
        body = circuit.copy()
        body.data = [item for item in body.data if item.operation.name != "measure"]
        packed.compose(
            body,
            qubits=range(qubit_offset, qubit_offset + qubit_width),
            clbits=range(clbit_offset, clbit_offset + clbit_width),
            inplace=True,
        )
        local_map = [
            [circuit.find_bit(instruction.qubits[0]).index, circuit.find_bit(instruction.clbits[0]).index]
            for instruction in circuit.data
            if instruction.operation.name == "measure"
        ]
        layout.append(
            {
                "name": circuit.name or f"block_{index}",
                "qubit_offset": qubit_offset,
                "qubit_width": qubit_width,
                "clbit_offset": clbit_offset,
                "clbit_width": clbit_width,
                "local_qubit_to_cbit_map": sorted(local_map),
                "manifest_hash": circuit_digest(circuit),
            }
        )
        qubit_offset += qubit_width
        clbit_offset += clbit_width
    for entry in layout:
        for q, c in entry["local_qubit_to_cbit_map"]:
            packed.measure(entry["qubit_offset"] + q, entry["clbit_offset"] + c)
    return packed, layout


def _normalize_key(key, width: int) -> str:
    """Normalise a raw count key (spaces, hex, leading zeros) to exactly ``width`` 0/1 characters."""
    if isinstance(key, bool):
        raise ValueError(f"count key {key!r} is not a bitstring")
    text = "".join(str(key).split())
    if not text:
        raise ValueError("empty count key")
    if text[:2].lower() == "0x":
        try:
            value = int(text, 16)
        except ValueError as exc:
            raise ValueError(f"invalid hex count key {key!r}") from exc
        if value < 0 or value >= (1 << width):
            raise ValueError(f"count key {key!r} exceeds width {width}")
        return format(value, f"0{width}b")
    if any(char not in "01" for char in text):
        raise ValueError(f"invalid bit key {key!r}")
    if len(text) > width:
        raise ValueError(f"count key {key!r} exceeds width {width}")
    return text.zfill(width)


def _as_int_count(value) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise ValueError(f"count {value!r} is not an integer")
    value = int(value)
    if value < 0:
        raise ValueError(f"negative count {value} is not allowed")
    if value > _UINT_MAX:
        raise ValueError(f"count {value} overflows the integer range")
    return value


def unpack_counts(raw_counts, layout) -> dict:
    """Split packed count bitstrings back into one histogram per sub-circuit, keyed by layout name.

    Qiskit displays the highest classical bit index on the left; decoding uses explicit ``clbit_offset``
    and ``clbit_width`` register slices. Every shot is preserved: each marginal histogram sums to the
    packed total shot count.
    """
    if isinstance(layout, (str, bytes)):
        raise ValueError("layout must be an ordered sequence of block dicts")
    layout = list(layout)
    if not layout:
        raise ValueError("layout is empty")
    if not isinstance(raw_counts, dict) or not raw_counts:
        raise ValueError("raw_counts must be a non-empty mapping of bitstring to shot count")
    total_clbits = sum(int(entry["clbit_width"]) for entry in layout)
    offset = 0
    names = set()
    for entry in layout:
        width = entry["clbit_width"]
        if isinstance(width, bool) or not isinstance(width, numbers.Integral) or width <= 0:
            raise ValueError("invalid classical width")
        if entry["clbit_offset"] != offset or entry["name"] in names:
            raise ValueError("layout must have contiguous disjoint offsets and unique names")
        names.add(entry["name"])
        offset += width
    marginals = {}
    total = 0
    for key, raw_value in raw_counts.items():
        text = _normalize_key(key, total_clbits)
        count = _as_int_count(raw_value)
        total += count
        for entry in layout:
            offset = int(entry["clbit_offset"])
            width = int(entry["clbit_width"])
            name = entry["name"]
            piece = "" if width == 0 else text[total_clbits - offset - width: total_clbits - offset]
            bucket = marginals.setdefault(name, {})
            bucket[piece] = bucket.get(piece, 0) + count
    for name, bucket in marginals.items():
        if sum(bucket.values()) != total:
            raise ValueError(f"marginal {name!r} does not conserve total shot count ({sum(bucket.values())} != {total})")
    return marginals
