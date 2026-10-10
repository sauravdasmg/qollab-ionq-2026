"""Circuit packing, count normalization and shared-helper disclosure.

Shared helpers live in their own files: circuit_pack.py and receipt.py implement
circuit packing, count normalization, backend dispatch and evidence receipts.
Written during Oct 9-11, 2026, with exact UTC provenance and source/license
attribution. Each entry ships its own version of this helper; the files differ. The Noise Tax
imported the helper from the retired Two Whispers build-window entry.
Project-specific physics, decoding, inference and presentation are described
on each project page.
"""

import numbers

from qiskit import QuantumCircuit

# Control-flow and conditioned operations are not packable.
_CONTROL_NAMES = frozenset({
    'if_test', 'if_else', 'while_loop', 'for_loop',
    'switch_case', 'break', 'continue',
})

_LAYOUT_FIELDS = (
    'block_name', 'qubit_offset', 'qubit_width',
    'classical_offset', 'classical_width', 'qubit_to_cbit_map',
)


def _integer(value, name):
    if isinstance(value, bool):
        raise ValueError(f'{name} must be an integer')
    if isinstance(value, str) and value.lstrip('+-').isdigit():
        return int(value)
    if isinstance(value, numbers.Integral):
        return int(value)
    raise ValueError(f'{name} must be an integer')


def _analyze_block(circuit):
    """Return (prefix, measures, qubit_to_cbit) with terminal-measure checks."""
    if not isinstance(circuit, QuantumCircuit):
        raise TypeError('each block must be a QuantumCircuit')
    if circuit.num_qubits < 1:
        raise ValueError('circuit needs at least one qubit')
    if circuit.num_clbits < 1:
        raise ValueError('circuit needs a classical register for terminal measurement')
    prefix, measures = [], []
    seen_measure = False
    for inst in circuit.data:
        op = inst.operation
        name = op.name
        if name in _CONTROL_NAMES or (hasattr(op, 'condition') and op.condition is not None):
            raise ValueError(f'control flow or conditioned operation not packable: {name}')
        qi = [circuit.find_bit(q).index for q in inst.qubits]
        if name == 'measure':
            if not inst.clbits:
                raise ValueError('measurement without classical wire')
            ci = [circuit.find_bit(c).index for c in inst.clbits]
            seen_measure = True
            measures.append((op, qi, ci))
        else:
            if inst.clbits:
                raise ValueError(f'unsupported classical wiring on non-measure operation: {name}')
            if seen_measure:
                raise ValueError('nonterminal measurement: quantum operation after a measurement')
            prefix.append((op, qi))
    if not measures:
        raise ValueError('each block needs a terminal measurement')
    qmap, reverse = {}, {}
    for _, qi, ci in measures:
        for q, c in zip(qi, ci):
            if q in qmap or c in reverse:
                raise ValueError('ambiguous measurement wiring: repeated qubit or cbit measurement')
            qmap[q] = c
            reverse[c] = q
    return prefix, measures, qmap


def pack_circuits(circuits, max_qubits=25):
    """Pack disjoint qubit/clbit blocks into one terminally measured circuit.

    Returns (packed_circuit, layout). Layout is an ordered list with one entry
    per block: block_name, qubit_offset/width, classical_offset/width,
    qubit_to_cbit_map and manifest_hash (None until annotated by the receipt).
    """
    if not isinstance(circuits, (list, tuple)) or not circuits:
        raise ValueError('need a nonempty list of circuits')
    if isinstance(max_qubits, bool) or not isinstance(max_qubits, numbers.Integral) or max_qubits < 1:
        raise ValueError('max_qubits must be a positive integer')
    max_qubits = int(max_qubits)

    parsed = []
    q_total = c_total = 0
    for circuit in circuits:
        prefix, measures, qmap = _analyze_block(circuit)
        w = _integer(circuit.num_qubits, 'qubit width')
        cw = _integer(circuit.num_clbits, 'classical width')
        q_total += w
        c_total += cw
        if q_total > max_qubits:
            raise ValueError(f'summed qubit width {q_total} exceeds cap {max_qubits}')
        parsed.append((circuit, prefix, measures, qmap, w, cw))

    q_off = c_off = 0
    entries = []
    for circuit, prefix, measures, qmap, w, cw in parsed:
        entries.append({
            'circuit': circuit, 'prefix': prefix, 'measures': measures,
            'qmap': qmap, 'q_off': q_off, 'c_off': c_off,
            'width': w, 'classical_width': cw,
        })
        q_off += w
        c_off += cw

    packed = QuantumCircuit(q_total, c_total, name=f'packed-{len(parsed)}-blocks')
    for entry in entries:
        for op, qi in entry['prefix']:
            packed.append(op, [packed.qubits[entry['q_off'] + i] for i in qi], [])
    for entry in entries:
        for op, qi, ci in entry['measures']:
            packed.append(
                op,
                [packed.qubits[entry['q_off'] + i] for i in qi],
                [packed.clbits[entry['c_off'] + i] for i in ci],
            )

    layout = []
    for entry in entries:
        circuit = entry['circuit']
        layout.append({
            'block_name': circuit.name,
            'qubit_offset': entry['q_off'],
            'qubit_width': entry['width'],
            'classical_offset': entry['c_off'],
            'classical_width': entry['classical_width'],
            'qubit_to_cbit_map': dict(entry['qmap']),
            'manifest_hash': None,
        })
    return packed, layout


def validate_layout(layout):
    """Validate packed layout structure and nonoverlapping offsets."""
    if not isinstance(layout, (list, tuple)) or not layout:
        raise ValueError('layout must be a nonempty ordered list')
    q_seen = []
    c_seen = []
    for entry in layout:
        if not isinstance(entry, dict):
            raise ValueError('layout entries must be objects')
        for field in _LAYOUT_FIELDS:
            if field not in entry:
                raise ValueError(f'layout entry missing {field}')
        for field in ('qubit_offset', 'qubit_width', 'classical_offset', 'classical_width'):
            if isinstance(entry[field], bool) or not isinstance(entry[field], numbers.Integral):
                raise ValueError(f'{field} must be an integer')
            value = _integer(entry[field], field)
            if value < 0:
                raise ValueError(f'{field} must be nonnegative')
        if entry['qubit_width'] < 1 or entry['classical_width'] < 1:
            raise ValueError('block widths must be positive')
        qmap = entry['qubit_to_cbit_map']
        if not isinstance(qmap, dict):
            raise ValueError('qubit_to_cbit_map must be an object')
        if not qmap or not isinstance(entry['block_name'], str) or not entry['block_name']:
            raise ValueError('block name and measurement map must be nonempty')
        values = []
        keys = []
        for key, value in qmap.items():
            k = _integer(key, 'qubit index')
            v = _integer(value, 'cbit index')
            if not 0 <= k < entry['qubit_width']:
                raise ValueError('qubit index outside block width')
            if not 0 <= v < entry['classical_width']:
                raise ValueError('cbit index outside block width')
            values.append(v)
            keys.append(k)
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate normalized qubit index')
        if len(values) != len(set(values)):
            raise ValueError('qubit_to_cbit_map must be injective')
        q_seen.append((entry['qubit_offset'], entry['qubit_width']))
        c_seen.append((entry['classical_offset'], entry['classical_width']))
    for spans in (q_seen, c_seen):
        spans = sorted(spans)
        for (s1, w1), (s2, _) in zip(spans, spans[1:]):
            if s2 < s1 + w1:
                raise ValueError('overlapping block offsets')
    return layout
def _normalize_key(key, width):
    if isinstance(key, str):
        bits = key.replace(' ', '')
        if not bits or set(bits) - {'0', '1'}:
            raise ValueError('count keys must be binary strings')
    elif isinstance(key, numbers.Integral) and not isinstance(key, bool):
        value = int(key)
        if value < 0 or value >= (1 << width):
            raise ValueError('integer outcome outside packed classical width')
        bits = format(value, f'0{width}b')
    else:
        raise ValueError('invalid count key')
    if len(bits) > width:
        raise ValueError('count key wider than packed classical width')
    return bits.zfill(width)


def unpack_counts(raw_counts, layout):
    """Return ordered block histograms from packed raw counts.

    Keys are normalized (spaces removed, short keys left-padded), equivalent
    keys are merged, and every shot is conserved across every marginal.
    """
    if not isinstance(raw_counts, dict):
        raise ValueError('raw_counts must be an object of binary keys to counts')
    validate_layout(layout)
    packed_width = max(
        entry['classical_offset'] + entry['classical_width'] for entry in layout)
    merged = {}
    for key, count in raw_counts.items():
        if isinstance(count, bool) or not isinstance(count, numbers.Integral) or count < 0:
            raise ValueError('counts must be nonnegative integers')
        normalized = _normalize_key(key, packed_width)
        merged[normalized] = merged.get(normalized, 0) + int(count)
    total = sum(merged.values())
    marginals = []
    for entry in layout:
        local = {}
        offset = entry['classical_offset']
        text_width = entry['classical_width']
        mask = (1 << text_width) - 1
        for key, count in merged.items():
            value = (int(key, 2) >> offset) & mask
            local_key = format(value, f'0{text_width}b')
            local[local_key] = local.get(local_key, 0) + count
        if sum(local.values()) != total:
            raise RuntimeError('shot conservation violated across a marginal')
        marginals.append(local)
    return marginals
