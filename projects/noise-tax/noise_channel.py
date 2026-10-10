"""Shared calibrated effective-basis approximation, Qiskit little endian.

Both games compile with stage barriers, opt=1, seed=1234 before noise.
Infidelity r becomes joint-depolarizing lambda=r*s/(1-1/d).
This population-calibrated channel is not the remote IonQ pulse model.
"""
import hashlib
import json
import math
from pathlib import Path
from functools import lru_cache
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator

PARAMETER_PATH = Path(__file__).resolve().parents[2] / 'tools' / 'ionq_noise_params.json'
# Uploaded Qollab files cannot reach repository tools. Freeze exact calibration
# bytes in a top-level Python module during the local build, rather than refit.
if PARAMETER_PATH.is_file():
    PARAMETER_BYTES = PARAMETER_PATH.read_bytes()
else:
    from calibration_snapshot import PARAMETER_TEXT
    PARAMETER_BYTES = PARAMETER_TEXT.encode('utf-8')
CALIBRATION = json.loads(PARAMETER_BYTES)
CALIBRATION_SHA256 = hashlib.sha256(PARAMETER_BYTES).hexdigest()
MODEL_KEYS = {'aria-1': 'ionq-aria', 'forte-1': 'ionq-forte',
              'forte-enterprise-1': 'ionq-forte-enterprise'}
MODELS = tuple(MODEL_KEYS)
COMPILER_SEED = 1234
SEMANTICS = 'joint depolarization after sx/x and declared entangler; rz noiseless; full source; stage barriers'

def configuration(model='aria-1', scale=1., source_noise=True, calibration_shift=None):
    if model not in MODEL_KEYS or not math.isfinite(scale) or not 0 <= scale <= 2:
        raise ValueError('unknown model or scale outside [0,2]')
    p = CALIBRATION[MODEL_KEYS[model]]
    cfg = {'model': model, 'scale': float(scale), 'r_1q': p['r_1q'], 'r_2q': p['r_2q'],
           'readout': p['readout']*scale, 'basis': p['basis'], 'entangler': p['two_qubit_gate'],
           'compiler_seed': COMPILER_SEED, 'optimization_level': 1,
           'source_noise': bool(source_noise), 'calibration_sha256': CALIBRATION_SHA256,
           'semantics': SEMANTICS, 'label': 'LOCAL MODEL: calibrated IonQ-like approximation'}
    if calibration_shift is not None:
        if calibration_shift not in (-.001, .001):
            raise ValueError('calibration sensitivity uses only +/-0.001 edges')
        cfg['r_2q'] = p['r_2q'] + calibration_shift
        cfg['calibration_shift'] = calibration_shift
        cfg['uncertainty_source'] = 'CALIBRATION SENSITIVITY; scenario, not confidence interval'
    for width, rate in ((1, cfg['r_1q']), (2, cfg['r_2q'])):
        if not 0 <= rate*scale/(1-1/2**width) <= 1:
            raise ValueError('joint depolarizing lambda outside [0,1]')
    if not 0 <= cfg['readout'] <= .5:
        raise ValueError('invalid readout')
    return cfg

def compile_circuit(circuit, model='aria-1'):
    cfg = configuration(model)
    compiled = transpile(circuit, basis_gates=cfg['basis'], optimization_level=1,
                         seed_transpiler=COMPILER_SEED)
    before = [i.operation.label for i in circuit.data if i.operation.name == 'barrier']
    after = [i.operation.label for i in compiled.data if i.operation.name == 'barrier']
    if before != after:
        raise ValueError('compiler changed stage barriers')
    return compiled

@lru_cache(maxsize=256)
def _replacement_map(n, wires):
    """Linear index map for I_w/d tensor Tr_w(rho), arbitrary LE wires."""
    d = 1 << len(wires)
    size = 1 << n
    mask = sum(1 << q for q in wires)
    def local_bits(value):
        return sum(((value >> q) & 1) << j for j, q in enumerate(wires))
    def embed(value):
        return sum(((value >> j) & 1) << q for j, q in enumerate(wires))
    dst, src = [], []
    for a in range(size):
        for b in range(size):
            if local_bits(a) == local_bits(b):
                for k in range(d):
                    dst.append(a*size+b)
                    src.append(((a & ~mask) | embed(k))*size + ((b & ~mask) | embed(k)))
    return np.asarray(dst), np.asarray(src), d

def depolarize(rho, wires, lam):
    if not math.isfinite(lam) or not 0 <= lam <= 1:
        raise ValueError('lambda must lie in [0,1]')
    n = int(math.log2(len(rho)))
    wires = tuple(wires)
    if not wires or len(set(wires)) != len(wires) or any(q < 0 or q >= n for q in wires):
        raise ValueError('invalid wires')
    if lam == 0:
        return rho
    dst, src, d = _replacement_map(n, wires)
    mixed = np.zeros(rho.size, complex)
    np.add.at(mixed, dst, rho.reshape(-1)[src]/d)
    return (1-lam)*rho + lam*mixed.reshape(rho.shape)

def prepare_steps(compiled):
    """Cache gate matrices once per block/model for the entire scale grid."""
    n = compiled.num_qubits
    if not 1 <= n <= 4:
        raise ValueError('only individual 1..4-qubit blocks allowed')
    steps, stage, seen = [], 'source', False
    for item in compiled.data:
        name = item.operation.name
        if name == 'measure':
            seen = True
            continue
        if name == 'barrier':
            stage = item.operation.label or 'receiver'
            continue
        if seen or name in {'reset', 'if_else', 'switch_case', 'for_loop', 'while_loop'}:
            raise ValueError('unitary prefix and terminal measurements required')
        wires = tuple(compiled.find_bit(q).index for q in item.qubits)
        if name not in {'rz', 'sx', 'x', 'rxx', 'rzz'}:
            raise ValueError('circuit must be compiled in calibrated basis')
        gate = QuantumCircuit(n)
        gate.append(item.operation, wires)
        steps.append((Operator(gate).data, wires, name, stage))
    mapping = [(compiled.find_bit(i.qubits[0]).index, compiled.find_bit(i.clbits[0]).index)
               for i in compiled.data if i.operation.name == 'measure']
    if mapping and (compiled.num_clbits != n or len(mapping) != n or
                    len({q for q, c in mapping}) != n or len({c for q, c in mapping}) != n):
        raise ValueError('complete bijective terminal measurement required')
    return {'width': n, 'steps': steps, 'mapping': mapping}

def probabilities(compiled, cfg=None, prepared=None):
    cfg = configuration() if cfg is None else cfg
    # Validate even externally provided configurations, never silently clip.
    checked = configuration(cfg['model'], cfg['scale'], cfg.get('source_noise', True),
                            cfg.get('calibration_shift'))
    if cfg != checked:
        raise ValueError('configuration does not match frozen calibrated channel')
    block = prepare_steps(compiled) if prepared is None else prepared
    n = block['width']; dim = 1 << n
    rho = np.zeros((dim, dim), complex); rho[0, 0] = 1
    for unitary, wires, name, stage in block['steps']:
        rho = unitary @ rho @ unitary.conj().T
        if stage == 'source' and not cfg['source_noise']:
            continue
        if name in ('sx', 'x'):
            rate = cfg['r_1q']; width = 1
        elif name == cfg['entangler']:
            rate = cfg['r_2q']; width = 2
        else:
            continue
        rho = depolarize(rho, wires, rate*cfg['scale']/(1-1/2**width))
    if not np.allclose(rho, rho.conj().T, atol=1e-10) or not np.isclose(np.trace(rho), 1, atol=1e-10):
        raise ValueError('density trace/hermiticity failure')
    p = np.diag(rho).real.copy()
    for bit in range(n):
        e = cfg['readout']
        p = (1-e)*p + e*p[np.arange(dim) ^ (1 << bit)]
    if block['mapping']:
        measured = np.zeros(dim)
        for ix, value in enumerate(p):
            target = sum(((ix >> q) & 1) << c for q, c in block['mapping'])
            measured[target] += value
        p = measured
    if p.min() < -1e-10 or not np.isclose(p.sum(), 1, atol=1e-10):
        raise ValueError('probability normalization failure')
    # Roundoff-only negative values are explicitly bounded above; no bad rates clipped.
    p[p < 0] = 0
    return {format(i, f'0{n}b'): float(v) for i, v in enumerate(p)}

def histogram(probabilities, shots, seed):
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise ValueError('positive integer shots required')
    keys = sorted(probabilities)
    p = np.asarray([probabilities[k] for k in keys])
    if not np.isfinite(p).all() or p.min() < 0 or not np.isclose(p.sum(), 1, atol=1e-10):
        raise ValueError('normalized probabilities required')
    values = np.random.default_rng(seed).multinomial(shots, p/p.sum())
    return {k: int(v) for k, v in zip(keys, values)}
