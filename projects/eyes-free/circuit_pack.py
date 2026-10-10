"""Phase-major disjoint-wire packs and little-endian marginalization."""
from qiskit import QuantumCircuit
from eyes_core import WIDTHS, PHASES, circuit, normalized_counts


def pack(phase_frame=0.0):
    q = QuantumCircuit(21, 21)
    manifest = []
    for j in range(3):
        for n, offset in zip(WIDTHS, (0, 1, 3)):
            offset += 7*j
            phi = float(PHASES[j]+phase_frame)
            q.compose(circuit(n, phi), qubits=list(range(offset, offset+n)),
                      clbits=list(range(offset, offset+n)), inplace=True)
            manifest.append({"width": n, "offset": offset, "phase_rad": phi, "phase_index": j})
    return q, manifest


def unpack(counts, manifest, total_width=21):
    counts = normalized_counts(counts, total_width)
    outputs = []
    for block in manifest:
        offset, width = block["offset"], block["width"]
        if offset < 0 or width < 1 or offset+width > total_width:
            raise ValueError("invalid block")
        out = {}
        for key, value in counts.items():
            bits = key[total_width-offset-width:total_width-offset]
            out[bits] = out.get(bits, 0)+value
        outputs.append(out)
    return outputs


def smoke_pack():
    q = QuantumCircuit(19, 19)
    blocks = [{"offset": 0, "width": 4, "expected": "0101", "kind": "asymmetric-X"},
              {"offset": 4, "width": 4, "expected": "1111", "kind": "all-X"},
              {"offset": 8, "width": 4, "expected": "0000", "kind": "zero"},
              {"offset": 12, "width": 7, "expected": "1010011", "kind": "asymmetric-X"}]
    for b in blocks:
        for k, bit in enumerate(reversed(b["expected"])):
            if bit == "1":
                q.x(b["offset"]+k)
    q.measure(range(19), range(19))
    return q, blocks
