"""Shared helpers live in their own files: circuit_pack.py and receipt.py implement circuit packing, count normalization, backend dispatch and evidence receipts. Written during Oct 9-11, 2026, with exact UTC provenance and source/license attribution; used by Two Whispers Make a Word, Never Lose Twice and Entanglement Court only where the shipped manifest lists the helper. Project-specific physics, decoding, inference and presentation are described on each project page.

Independent implementation from HELPER_SPEC.md; project MIT license applies.
"""
import hashlib
import json
from numbers import Integral
from qiskit import QuantumCircuit


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def circuit_description(circuit):
    return {'qubits': circuit.num_qubits, 'clbits': circuit.num_clbits,
                   'global_phase': str(circuit.global_phase),
                   'operations': [[x.operation.name, [str(p) for p in x.operation.params],
                                   [circuit.find_bit(q).index for q in x.qubits],
                                   [circuit.find_bit(c).index for c in x.clbits]] for x in circuit.data]}


def circuit_hash(circuit):
    return digest(circuit_description(circuit))


def normalize_counts(counts, width):
    if not isinstance(counts, dict) or not isinstance(width, int) or width <= 0:
        raise ValueError('counts must be a dictionary with positive bit width')
    out = {}
    for key, count in counts.items():
        if isinstance(count, bool) or not isinstance(count, Integral) or count < 0:
            raise ValueError('shot counts must be nonnegative integers')
        if not isinstance(key, str):
            raise ValueError('count keys must be binary strings')
        bits = key.replace(' ', '')
        if not bits or set(bits) - {'0', '1'} or len(bits) > width:
            raise ValueError('invalid binary key or bit width')
        bits = bits.zfill(width)
        out[bits] = out.get(bits, 0) + int(count)
    return out


def pack_circuits(circuits, max_qubits=25):
    circuits = list(circuits)
    if not circuits or sum(c.num_qubits for c in circuits) > max_qubits:
        raise ValueError('empty circuits or qubit cap exceeded')
    packed = QuantumCircuit(sum(c.num_qubits for c in circuits), sum(c.num_clbits for c in circuits))
    layout, qo, co, names = [], 0, 0, set()
    for circuit in circuits:
        if circuit.name in names or circuit.num_clbits <= 0:
            raise ValueError('block names must be unique; blocks need classical bits')
        names.add(circuit.name)
        measured, mapping, cbits = False, {}, set()
        for item in circuit.data:
            op = item.operation
            if getattr(op, 'condition', None) is not None or op.name in {'reset', 'if_else', 'while_loop', 'for_loop', 'switch_case'}:
                raise ValueError('dynamic circuits and resets are unsupported')
            if op.name == 'measure':
                measured = True
                q, c = circuit.find_bit(item.qubits[0]).index, circuit.find_bit(item.clbits[0]).index
                if q in mapping or c in cbits:
                    raise ValueError('repeated measurement wiring')
                mapping[q] = c
                cbits.add(c)
            elif op.name != 'barrier' and (measured or item.clbits):
                raise ValueError('measurements must be terminal; classical operations unsupported')
        if len(mapping) != circuit.num_qubits:
            raise ValueError('every qubit must have a terminal measurement')
        layout.append({'block_name': circuit.name, 'qubit_offset': qo, 'qubit_width': circuit.num_qubits,
                       'clbit_offset': co, 'clbit_width': circuit.num_clbits,
                       'qubit_to_clbit_map': mapping, 'manifest_hash': circuit_hash(circuit)})
        # Defer all measurements to the end of the packed circuit.
        for item in circuit.data:
            if item.operation.name != 'measure':
                packed.append(item.operation, [qo + circuit.find_bit(q).index for q in item.qubits], [])
        qo += circuit.num_qubits
        co += circuit.num_clbits
    for block in layout:
        for q, c in block['qubit_to_clbit_map'].items():
            packed.measure(block['qubit_offset'] + q, block['clbit_offset'] + c)
    return packed, layout


def unpack_counts(raw_counts, layout):
    if not layout:
        raise ValueError('missing layout')
    expected_q = expected_c = 0
    names = set()
    for b in layout:
        if b['qubit_offset'] != expected_q or b['clbit_offset'] != expected_c or b['block_name'] in names:
            raise ValueError('layout must contain contiguous disjoint ordered blocks')
        if b['qubit_width'] <= 0 or b['clbit_width'] <= 0:
            raise ValueError('invalid block width')
        mapping = {int(q): int(c) for q, c in b['qubit_to_clbit_map'].items()}
        if set(mapping) != set(range(b['qubit_width'])) or len(set(mapping.values())) != len(mapping) or any(c < 0 or c >= b['clbit_width'] for c in mapping.values()):
            raise ValueError('invalid measurement map')
        expected_q += b['qubit_width']; expected_c += b['clbit_width']; names.add(b['block_name'])
    raw = normalize_counts(raw_counts, expected_c)
    out = {b['block_name']: {} for b in layout}
    for bits, count in raw.items():
        for b in layout:
            local = ''.join(bits[expected_c - 1 - (b['clbit_offset'] + i)] for i in reversed(range(b['clbit_width'])))
            hist = out[b['block_name']]
            hist[local] = hist.get(local, 0) + count
    return out


def demo_blocks(circuits, manifest):
    """Adapt the core's manifested disjoint aggregate without changing physics."""
    names = manifest['ordered_blocks']
    if len(circuits) == len(names):
        for circuit, name in zip(circuits, names):
            circuit.name = name
        return circuits
    if len(circuits) != 1:
        raise ValueError('core circuits do not match the manifested block interface')
    source = circuits[0]
    blocks = []
    covered = set()
    for name in names:
        spec = manifest['blocks'][name]
        offset, width = spec['offset'], spec['width']
        local = QuantumCircuit(width, width, name=name)
        for index, item in enumerate(source.data):
            qs = [source.find_bit(q).index for q in item.qubits]
            cs = [source.find_bit(c).index for c in item.clbits]
            if any(offset <= q < offset + width for q in qs):
                if any(not offset <= q < offset + width for q in qs + cs):
                    raise ValueError('cross-block operation in core aggregate')
                local.append(item.operation, [q - offset for q in qs], [c - offset for c in cs])
                covered.add(index)
        blocks.append(local)
    if len(covered) != len(source.data):
        raise ValueError('unmanifested core operations')
    return blocks
