"""Exact double-trine receivers. One-way bounds assume ideal product sources.

No general separable/LOCC bound or communication speedup is claimed.
Unrestricted classical two-bit labels transmit the three words perfectly.
"""
import itertools
import math
import numbers
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation


P_JOINT = 0.5 + math.sqrt(2)/3
P_SEQ = 0.5 + math.sqrt(3)/4
LABELS = (0, 1, 2)
FAMILIES = ('collective', 'textbook', 'deferred-sequential')
DEVELOPMENT_SEEDS = tuple(range(2026100900, 2026100908))
# Predeclared held-out cases: no runtime random case choice and no recipe tuning.
HELD_OUT_SEEDS = tuple(range(2026101000, 2026101020))
CASE_SEEDS = (None,) + DEVELOPMENT_SEEDS + HELD_OUT_SEEDS


def trine_states(frame=None):
    f = np.eye(2) if frame is None else np.asarray(frame, complex)
    if f.shape != (2, 2) or not np.allclose(f.conj().T@f, np.eye(2), atol=1e-12):
        raise ValueError('frame must be unitary')
    return [f @ (np.array([1, np.exp(2j*np.pi*k/3)])/math.sqrt(2)) for k in LABELS]


def double_trine_states(frame=None):
    return [np.kron(v, v) for v in trine_states(frame)]


def _complete_columns(columns):
    a = np.asarray(columns, complex)
    if not np.allclose(a.conj().T@a, np.eye(a.shape[1]), atol=1e-12):
        raise ValueError('columns are not an isometry')
    basis = [a[:, j].copy() for j in range(a.shape[1])]
    for axis in np.eye(a.shape[0], dtype=complex):
        v = axis.copy()
        for b in basis:
            v -= b*np.vdot(b, v)
        if np.linalg.norm(v) > 1e-10:
            basis.append(v/np.linalg.norm(v))
        if len(basis) == a.shape[0]:
            break
    return np.column_stack(basis)


def joint_povm(frame=None):
    states = np.column_stack(double_trine_states(frame))
    values, vectors = np.linalg.eigh(states.conj().T@states)
    invroot = (vectors*(1/np.sqrt(values)))@vectors.conj().T
    basis = _complete_columns(states@invroot)
    return basis, [np.outer(v, v.conj()) for v in basis.T]


def _parameters(recipe):
    if recipe is None:
        return {}
    raise ValueError('Noise Tax freezes the textbook recipe; no tuning')


def _permutation(params):
    return list(itertools.permutations(LABELS))[params.get('relabel', 0)]


def joint_receiver(frame=None, recipe=None):
    params = _parameters(recipe)
    basis, _ = joint_povm(frame)
    order = list(_permutation(params)) + [3]
    u = basis[:, order].conj().T
    phases = params.get('row_phases', [params.get('row_phase', 0.0)]*4)
    u = np.exp(1j*np.asarray(phases))[:, None]*u
    u[3] *= np.exp(1j*params.get('completion_phase', 0.0))
    return u, order[:3] + [0]


def joint_unitary(frame=None, recipe=None):
    return joint_receiver(frame, recipe)[0]


def sequential_receiver(frame=None, recipe=None):
    """Naimark U on [q0,q2], coherent Helstrom U on [q0,q1,q2], decoder.

    First outcome m=q0+2*q2 eliminates permutation[m]. First effects are
    (2/3)|t_j perpendicular><...|; fourth effect is zero on ancilla-zero.
    Every record is terminal; unused outcomes 5 and 7 decode to label zero.
    """
    params = _parameters(recipe)
    states = trine_states(frame)
    order = list(_permutation(params)) + [3]
    rows = []
    for j in order[:3]:
        v = states[j]
        perpendicular = np.array([-v[1].conjugate(), v[0].conjugate()])
        rows.append(math.sqrt(2/3)*perpendicular.conj())
    rows.append(np.zeros(2, complex))
    isometry = np.asarray(rows)
    phases = params.get('row_phases', [params.get('row_phase', 0.0)]*4)
    isometry *= np.exp(1j*np.asarray(phases))[:, None]
    first = _complete_columns(isometry)
    first[:, 2:] *= np.exp(1j*params.get('completion_phase', 0.0))
    control = np.zeros((8, 8), complex)
    decoder = [0]*8
    for m, eliminated in enumerate(order):
        indices = [m%2 + 4*(m//2) + 2*b for b in (0, 1)]
        if eliminated == 3:
            helstrom, guesses = np.eye(2), [0, 0]
        else:
            guesses = [j for j in LABELS if j != eliminated]
            a, b = (states[j] for j in guesses)
            delta = np.outer(a, a.conj()) - np.outer(b, b.conj())
            _, vectors = np.linalg.eigh(delta)
            helstrom = vectors[:, ::-1].conj().T
        control[np.ix_(indices, indices)] = helstrom
        for ix, guess in zip(indices, guesses):
            decoder[ix] = guess
    return first, control, decoder


def sequential_povm(frame=None, recipe=None):
    first, control, decoder = sequential_receiver(frame, recipe)
    embedded = np.zeros((8, 8), complex)
    for before in range(8):
        local = (before&1) + 2*((before>>2)&1)
        for m in range(4):
            after = (m&1) + (before&2) + 4*(m>>1)
            embedded[after, before] = first[m, local]
    amplitude = (control@embedded)[:, :4]
    effects = [np.outer(row.conj(), row) for row in amplitude]
    return effects, decoder



def haar_su2(seed):
    rng = np.random.default_rng(seed)
    z = (rng.normal(size=(2, 2)) + 1j*rng.normal(size=(2, 2)))/math.sqrt(2)
    q, r = np.linalg.qr(z)
    q = q @ np.diag(np.diag(r)/np.abs(np.diag(r)))
    return q/np.sqrt(np.linalg.det(q))

def make_instance(seed=None):
    frame = np.eye(2, dtype=complex) if seed is None else haar_su2(seed)
    return {'game': 'W', 'seed': seed,
            'frame': [[[float(z.real), float(z.imag)] for z in row] for row in frame]}

def frame_from_spec(spec):
    a = np.asarray(spec['frame'], float)
    return a[:, :, 0] + 1j*a[:, :, 1]

def make_demo(spec=None, include_oneway=False):
    spec = make_instance() if spec is None else spec
    frame = frame_from_spec(spec)
    circuits, blocks = [], []
    for label, state in enumerate(trine_states(frame)):
        for arm in (('joint', 'oneway') if include_oneway else ('joint',)):
            width = 2 if arm == 'joint' else 3
            qc = QuantumCircuit(width, width, name=f'W-{arm}-{label}')
            for signal in (0, 1):
                qc.append(StatePreparation(state), [signal])
            qc.barrier(label='receiver_start')
            if arm == 'joint':
                u, decoder = joint_receiver(frame)
                qc.unitary(u, [0, 1], label='fixed-square-root-receiver')
                unused = [3]
            else:
                first, control, decoder = sequential_receiver(frame)
                qc.unitary(first, [0, 2])
                qc.unitary(control, [0, 1, 2])
                unused = [5, 7]
            qc.measure(range(width), range(width))
            circuits.append(qc)
            blocks.append({'block_name': qc.name, 'arm': arm, 'label': label,
                           'width': width, 'decoder': decoder, 'unused_outcomes': unused})
    return circuits, {'game': 'W', 'specification': spec, 'ordered_blocks': blocks,
                      'reference_success': P_SEQ, 'reference': 'analytic optimal one-way ideal-source bound',
                      'recipe': 'fixed textbook square-root measurement, fourth outcome label 0'}

def analyze_counts(marginals, manifest):
    return analyze_probabilities(marginals, manifest)

def analyze_probabilities(distributions, manifest):
    if len(distributions) != len(manifest['ordered_blocks']):
        raise ValueError('distribution/manifest mismatch')
    rows = {}
    for dist, block in zip(distributions, manifest['ordered_blocks']):
        decoded = [0., 0., 0.]
        for bits, value in dist.items():
            ix = int(str(bits).replace(' ', ''), 2)
            if not 0 <= ix < 2**block['width'] or not math.isfinite(value) or value < 0:
                raise ValueError('invalid distribution')
            decoded[block['decoder'][ix]] += float(value)
        total = sum(decoded)
        if total <= 0:
            raise ValueError('empty distribution')
        rows.setdefault(block['arm'], []).append({'label': block['label'], 'total': total,
                    'decoded': [v/total for v in decoded], 'success': decoded[block['label']]/total})
    out = {}
    for arm, cells in rows.items():
        if sorted(c['label'] for c in cells) != [0, 1, 2]:
            raise ValueError('three equally weighted labels required')
        success = sum(c['success'] for c in cells)/3
        out[arm] = {'success': success, 'word_error': 1-success, 'rows': cells}
    out['advantage'] = out['joint']['success'] - P_SEQ if 'joint' in out else None
    return out
