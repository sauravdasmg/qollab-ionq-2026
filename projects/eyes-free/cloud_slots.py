"""Preregistered one-job IonQ slots from the Eyes-Free ledger."""
from circuit_pack import smoke_pack
from eyes_core import PHASES, WIDTHS, circuit
from qiskit import QuantumCircuit

FROZEN_HASH = "53438b090a1cba3ee6a442a6d4a84c8510c2512170c0096f0e299a46a4159d56"
FRESH_HASH = "91482c10b3664cac2d7b5916489d0307a588b432ce55236190addc0472000269"
SLOTS = {"E01": {"suite": "smoke", "frame": -1.0, "shots": 100, "manifest_hash": "smoke-v1"}}
for i in range(4):
    SLOTS["E%02d" % (i+2)] = {"suite": "frozen", "frame": i*3.141592653589793/2,
        "shots": 1000, "manifest_hash": FROZEN_HASH}
    SLOTS["E%02d" % (i+6)] = {"suite": "fresh", "frame": i*3.141592653589793/2+3.141592653589793/24,
        "shots": 1000, "manifest_hash": FRESH_HASH}
SLOTS["E10"] = {"suite": "acceptance", "frame": 0.0, "shots": 1000, "manifest_hash": FROZEN_HASH}
SLOTS["E11"] = {"suite": "retry", "frame": 0.0, "shots": 1000, "manifest_hash": FROZEN_HASH}
SLOTS["E12"] = {"suite": "retry", "frame": 3.141592653589793/24, "shots": 1000, "manifest_hash": FRESH_HASH}

def build_slot(slot):
    if slot not in SLOTS:
        raise ValueError("unknown cloud slot: %s" % slot)
    spec = SLOTS[slot]
    if slot == "E01":
        return smoke_pack()
    q = QuantumCircuit(21, 21)
    manifest = []
    for j in range(3):
        for n, local in zip(WIDTHS, (0, 1, 3)):
            offset = 7*j+local
            phase = float(PHASES[j]+spec["frame"])
            q.compose(circuit(n, phase), qubits=range(offset, offset+n),
                      clbits=range(offset, offset+n), inplace=True)
            manifest.append({"width": n, "offset": offset, "phase_rad": phase, "phase_index": j})
    return q, manifest
