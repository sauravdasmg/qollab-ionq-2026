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
from synthesis import haar_su2, validate_recipe, recipe_hash

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
    validate_recipe(recipe)
    return recipe.get('parameters', {})


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


def _select_recipe(recipe, family):
    if recipe is None:
        return None
    if 'families' in recipe:
        validate_recipe(recipe)
        return recipe['families'].get(family)
    return recipe if recipe.get('family', family) == family else None


def _compile(qc, recipe):
    params = _parameters(recipe)
    if params.get('decomposition') == 'standard':
        # Explicit standard gate decomposition is a compiler variant available
        # to the budget-matched textbook comparator.
        qc = qc.decompose(reps=2)
    return transpile(qc, basis_gates=['rx', 'ry', 'rz', 'cx'],
                     optimization_level=params.get('optimization_level', 1),
                     seed_transpiler=params.get('compiler_seed', 0))


def _frame_for_case(case):
    if isinstance(case, bool) or not isinstance(case, numbers.Integral) or not 0 <= case < len(CASE_SEEDS):
        raise ValueError('case must be a frozen integer ID 0..28')
    seed = CASE_SEEDS[case]
    return (np.eye(2, dtype=complex) if seed is None else haar_su2(seed)), seed


def make_demo(case: int = 0, recipe=None):
    """Nine measured circuits, label-major collective/textbook/sequential.

    case=0 is the independent identity-frame anchor; cases 1..8 are frozen
    development frames; 9..28 are predeclared held-out frames, never tuning data.
    Recipe is a family recipe or {identity,families:{...}}.
    The default is untuned, never a claimed optimized winner. No runtime search.
    """
    frame, seed = _frame_for_case(case)
    circuits, blocks = [], []
    for label, state in enumerate(trine_states(frame)):
        for family in FAMILIES:
            selected = _select_recipe(recipe, family)
            width = 3 if family == FAMILIES[2] else 2
            name = f'case{case}_label{label}_{family}'
            source = QuantumCircuit(width, name='source')
            for signal in (0, 1):
                source.append(StatePreparation(state), [signal])
            receiver = QuantumCircuit(width, name='receiver')
            if width == 2:
                unitary, decoder = joint_receiver(frame, selected)
                receiver.unitary(unitary, [0, 1], label='square-root-receiver')
                unused = [3]
            else:
                first, control, decoder = sequential_receiver(frame, selected)
                receiver.unitary(first, [0, 2], label='first-elimination-POVM')
                receiver.unitary(control, [0, 1, 2], label='coherent-Helstrom')
                unused = [5, 7]
            source_compiled = _compile(source, selected)
            receiver_compiled = _compile(receiver, selected)
            circuit = QuantumCircuit(width, width, name=name)
            circuit.compose(source_compiled, inplace=True)
            circuit.barrier(label='receiver_start')
            circuit.compose(receiver_compiled, inplace=True)
            circuit.measure(range(width), range(width))
            circuits.append(circuit)
            blocks.append({'block_name': name, 'family': family, 'label': label,
                           'width': width, 'decoder': decoder,
                           'unused_outcomes': unused, 'unused_decoder_label': 0,
                           'source_gate_count': len(source_compiled.data),
                           'receiver_gate_count': len(receiver_compiled.data),
                           'receiver_recipe': selected,
                           'reference_status': 'frozen recipe' if selected else 'untuned reference',
                           'ordered_gates': ['source:two independent trines', 'receiver:'+family, 'terminal measurement']})
    manifest = {'schema_version': '1.0', 'case_id': int(case),
                'case_role': 'anchor' if case == 0 else ('development' if case <= 8 else 'held-out'),
                'parameters': {'ensemble': 'equiprobable double-trine', 'seed': seed,
                               'frame': [[[float(z.real), float(z.imag)] for z in row] for row in frame]},
                'ordered_blocks': blocks, 'widths': [b['width'] for b in blocks],
                'decoding_maps': [b['decoder'] for b in blocks],
                'packed_offsets': [7*j+i for j in LABELS for i in (0, 2, 4)],
                'total_qubits': 21, 'source_assumptions': 'ideal product-state preparation',
                'recipe_identity': recipe.get('identity', recipe_hash(recipe)) if recipe else 'default',
                'recipe': recipe, 'smoke_control_ids': [],
                'reference_probabilities': {'collective': P_JOINT, 'textbook': P_JOINT, 'deferred-sequential': P_SEQ},
                'comparison_scope': 'one-way bound conditional on ideal source; not a general LOCC or separable bound',
                'classical_two_bit_success': 1.0}
    return circuits, manifest


def _wilson(successes, n, z):
    if n == 0:
        return [0.0, 1.0]
    p = successes/n
    denom = 1+z*z/n
    center = (p+z*z/(2*n))/denom
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return [max(0.0, center-half), min(1.0, center+half)]


def analyze_counts(marginals, manifest, **options):
    """JSON primitive analysis; zero shots give null estimates.

    Pointwise Wilson 95% cells; averaged success uses Bonferroni row intervals
    valid without independence between packed blocks. No difference SE asserted.
    """
    blocks = manifest['ordered_blocks']
    if len(marginals) != len(blocks):
        raise ValueError('counts must match manifest block order')
    out = {}
    for family in FAMILIES:
        rows, totals, raw_rows, unused_counts, intervals, ses, simultaneous = [], [], [], [], [], [], []
        for label in LABELS:
            matches = [i for i,b in enumerate(blocks) if b['family'] == family and b['label'] == label]
            if len(matches) != 1:
                raise ValueError('manifest requires one block per family and label')
            i = matches[0]
            block = blocks[i]
            counts, row, unused = marginals[i], [0, 0, 0], 0
            for bits, count in counts.items():
                if isinstance(count, bool) or not isinstance(count, numbers.Integral) or count < 0:
                    raise ValueError('counts must be nonnegative integers')
                if isinstance(bits, str):
                    key = bits.replace(' ', '')
                    if not key or set(key)-{'0','1'}:
                        raise ValueError('count key must be binary')
                    ix = int(key, 2)
                elif isinstance(bits, numbers.Integral) and not isinstance(bits, bool):
                    ix = int(bits)
                else:
                    raise ValueError('invalid outcome key')
                if not 0 <= ix < 2**block['width']:
                    raise ValueError('outcome outside block width')
                row[block['decoder'][ix]] += int(count)
                if ix in block['unused_outcomes']:
                    unused += int(count)
            n = sum(row)
            p = [r/n for r in row] if n else [None]*3
            rows.append(p); totals.append(n); raw_rows.append(row); unused_counts.append(unused)
            ses.append([math.sqrt(v*(1-v)/n) for v in p] if n else [None]*3)
            intervals.append([_wilson(r, n, 1.959963984540054) for r in row])
            simultaneous.append(_wilson(row[label], n, 2.3939797998185104))
        complete = all(totals)
        success = sum(rows[k][k] for k in LABELS)/3 if complete else None
        out[family] = {'confusion_matrix': rows, 'decoded_counts': raw_rows, 'shots_per_label': totals,
                       'success_probability': success, 'word_error': 1-success if complete else None,
                       'per_label_error': [1-rows[k][k] if totals[k] else None for k in LABELS],
                       'standard_error': ses, 'confusion_intervals_95': intervals,
                       'success_interval_95': [sum(a[t] for a in simultaneous)/3 for t in (0, 1)],
                       'word_error_interval_95': [1-sum(a[t] for a in simultaneous)/3 for t in (1, 0)],
                       'per_label_error_intervals_95': [[1-intervals[k][k][1], 1-intervals[k][k][0]] for k in LABELS],
                       'unused_outcome_counts': unused_counts,
                       'unused_outcome_assignment': 'all unused outcomes map to fixed label 0 and are counted in matrix',
                       'data_complete': bool(complete)}
    out['assumptions'] = {'finite-shot uncertainty': 'pointwise Wilson cells; Bonferroni row bounds for mean success',
                          'source': 'cloud comparison conditional on ideal source; exact source-dependent one-way bounds not implemented',
                          'packing': 'blocks share one backend run; no independence asserted for paired differences',
                          'restriction': 'optimal one-way sequential, not every separable POVM or LOCC',
                          'synthesis': 'ideal collective/textbook tie is not synthesis improvement',
                          'classical': 'unrestricted classical two-bit labels transmit perfectly'}
    return out
