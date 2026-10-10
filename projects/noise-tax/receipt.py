"""Build-window receipt and whole-packed-shot uncertainty helpers.

Adapted from Two Whispers' receipt conventions; raw W/N receipts stay intact.
This effort is supported by Qollab & IonQ.
"""
import hashlib
import json
from datetime import datetime, timezone
import numpy as np
from qiskit import qpy
from io import BytesIO
from circuit_pack import unpack_counts

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8')).hexdigest()

def hash_circuit(circuit):
    stream = BytesIO(); qpy.dump(circuit, stream)
    return hashlib.sha256(stream.getvalue()).hexdigest()

def make_record(packed, layout, counts, manifest, shots, model, started, ended, job_id=None):
    marginals = unpack_counts(counts, layout)
    if sum(counts.values()) != shots:
        raise ValueError('packed shots mismatch')
    return {'schema_version': 'noise-tax-1', 'project': 'The Noise Tax',
            'source': 'Qollab IonQ simulator run', 'backend': {'name': 'ionq_simulator'},
            'noise_model': model, 'shots': shots, 'utc_start': started, 'utc_end': ended,
            'manifest': manifest, 'layout': layout, 'raw_packed_counts': dict(counts),
            'marginals': marginals, 'hashes': {'manifest': digest(manifest), 'layout': digest(layout),
                                             'circuit': hash_circuit(packed)},
            'job_id': job_id, 'physical_qubit_shots': packed.num_qubits*shots,
            'submitted_operations': dict(packed.count_ops()),
            'assumptions': ['simulator, not QPU', 'remote compiler differs from local effective basis',
                            'all packed bitstrings retained; no arm independence assumed']}

def format_record(record):
    return 'RECORD_JSON ' + json.dumps(record, sort_keys=True, allow_nan=False)

def packed_bootstrap(counts, layout, statistic, draws=4000, seed=2026104403, confidence=.975):
    """Resample full packed bitstrings; retain cross-arm/label covariance."""
    keys = list(counts); n = sum(counts.values())
    if n <= 0 or draws < 1:
        raise ValueError('positive shots/draws required')
    rng = np.random.default_rng(seed)
    weights = np.asarray([counts[k] for k in keys], float)/n
    values = []
    for _ in range(draws):
        sample = rng.multinomial(n, weights)
        marginal = unpack_counts({k: int(v) for k, v in zip(keys, sample)}, layout)
        values.append(statistic(marginal))
    tail = (1-confidence)/2
    return {'interval': np.quantile(values, [tail, 1-tail]).tolist(), 'draws': draws,
            'seed': seed, 'confidence': confidence, 'method': 'whole packed bitstring bootstrap; IID shots'}
