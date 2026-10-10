import json
import math
import numpy as np
import pytest
from qiskit.quantum_info import Statevector, Operator
import core
from synthesis import (bounded_search, equal_budget_search, haar_su2,
                       import_recipe, export_recipe, validate_recipe)


def _success(effects, decoder, states):
    return sum(np.vdot(v, effects[m]@v).real for k,v in enumerate(states)
               for m in range(len(effects)) if decoder[m] == k)/len(states)


def _legal(effects):
    assert np.allclose(sum(effects),np.eye(4),atol=1e-12)
    for effect in effects:
        assert np.allclose(effect,effect.conj().T,atol=1e-12)
        assert np.linalg.eigvalsh(effect).min() >= -1e-12


@pytest.mark.parametrize('frame',[None,haar_su2(2026100900),haar_su2(2026100901)])
def test_reference_identities_and_full_povms(frame):
    states = core.double_trine_states(frame)
    basis, joint = core.joint_povm(frame)
    _legal(joint)
    assert np.allclose(basis.conj().T@basis,np.eye(4),atol=1e-12)
    assert _success(joint,[0,1,2,0],states) == pytest.approx(.5+math.sqrt(2)/3,abs=1e-12)
    effects,decoder = core.sequential_povm(frame)
    _legal(effects)
    assert _success(effects,decoder,states) == pytest.approx(.5+math.sqrt(3)/4,abs=1e-12)
    assert np.linalg.norm(effects[5])+np.linalg.norm(effects[7]) < 1e-12
    first,control,_ = core.sequential_receiver(frame)
    assert np.allclose(first.conj().T@first,np.eye(4),atol=1e-12)
    assert np.allclose(control.conj().T@control,np.eye(8),atol=1e-12)
    # Independently derive all one-way effects E_j tensor H_{guess|j}.
    trines = core.trine_states(frame)
    for j in range(3):
        v = trines[j]
        efirst = (2/3)*(np.eye(2)-np.outer(v,v.conj()))
        assert abs(np.vdot(v,efirst@v)) < 1e-12
        alternatives = [k for k in range(3) if k != j]
        a,b = (trines[k] for k in alternatives)
        delta = np.outer(a,a.conj())-np.outer(b,b.conj())
        _,vecs = np.linalg.eigh(delta)
        for bit in (0,1):
            h = np.outer(vecs[:,1-bit],vecs[:,1-bit].conj())
            ix = j%2+4*(j//2)+2*bit
            assert decoder[ix] == alternatives[bit]
            assert np.allclose(effects[ix],np.kron(h,efirst),atol=1e-12)


@pytest.fixture(scope='module')
def demo():
    return core.make_demo()


def test_demo_order_terminal_measurement_and_actual_probabilities(demo):
    circuits,manifest = demo
    assert len(circuits) == 9
    assert manifest['widths'] == [2,2,3]*3
    assert manifest['packed_offsets'] == [0,2,4,7,9,11,14,16,18]
    assert manifest['total_qubits'] == 21
    json.dumps(manifest,allow_nan=False)
    for circuit,block in zip(circuits,manifest['ordered_blocks']):
        assert circuit.name == block['block_name']
        assert [op.operation.name for op in circuit.data[-block['width']:]] == ['measure']*block['width']
        assert all(op.operation.name in {'rx','ry','rz','cx','measure','barrier'} for op in circuit.data)
        probabilities = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False)).probabilities()
        assert sum(probabilities) == pytest.approx(1,abs=1e-12)
        success = sum(p for i,p in enumerate(probabilities) if block['decoder'][i] == block['label'])
        expected = core.P_SEQ if block['width'] == 3 else core.P_JOINT
        assert success == pytest.approx(expected,abs=1e-10)


def test_equivalent_recipes_preserve_all_decoded_effects():
    frame = haar_su2(2026100900)
    recipe = {'parameters':{'relabel':4,'row_phases':[.2,-1.1,2.3,.4],'completion_phase':.7}}
    refu,refd = core.joint_receiver(frame)
    u,d = core.joint_receiver(frame,recipe)
    assert np.allclose(u.conj().T@u,np.eye(4),atol=1e-12)
    for k in range(3):
        ref = sum(np.outer(refu[i].conj(),refu[i]) for i in range(4) if refd[i] == k)
        new = sum(np.outer(u[i].conj(),u[i]) for i in range(4) if d[i] == k)
        assert np.allclose(ref,new,atol=1e-12)
    refe,refd = core.sequential_povm(frame)
    effects,decoder = core.sequential_povm(frame,recipe)
    _legal(effects)
    for k in range(3):
        assert np.allclose(sum(e for e,g in zip(refe,refd) if g == k),
                           sum(e for e,g in zip(effects,decoder) if g == k),atol=1e-12)
    # Actual compiled circuit uses decoder permutation, phases and frame.
    bundle = {'families': {f: dict(recipe, family=f) for f in core.FAMILIES}}
    bundle['families']['textbook'] = {'family':'textbook', 'parameters':dict(recipe['parameters'], decomposition='standard')}
    circuits,manifest = core.make_demo(1,bundle)
    for circuit,block in zip(circuits,manifest['ordered_blocks']):
        p = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False)).probabilities()
        assert sum(p[i] for i,g in enumerate(block['decoder']) if g == block['label']) == pytest.approx(
            core.P_SEQ if block['width']==3 else core.P_JOINT,abs=1e-10)


def test_analysis_unused_and_missing_counts(demo):
    _,manifest = demo
    counts = [{format(3 if b['width']==2 else 7,f"0{b['width']}b"):10} for b in manifest['ordered_blocks']]
    got = core.analyze_counts(counts,manifest)
    for family in core.FAMILIES:
        assert got[family]['confusion_matrix'] == [[1.,0.,0.]]*3
        assert got[family]['success_probability'] == pytest.approx(1/3)
        assert got[family]['unused_outcome_counts'] == [10]*3
        assert 'counted' in got[family]['unused_outcome_assignment']
    empty = core.analyze_counts([{}]*9,manifest)
    assert empty['collective']['success_probability'] is None
    json.dumps(empty,allow_nan=False)
    counts[0] = {'00':-1}
    with pytest.raises(ValueError): core.analyze_counts(counts,manifest)
    counts[0] = {'100':1}
    with pytest.raises(ValueError): core.analyze_counts(counts,manifest)


def test_binary_alphabet_negative_control():
    # Optimal adaptive local Helstrom saturates the joint binary bound;
    # the three-label advantage must not be described as universal.
    a,b = core.trine_states()[:2]
    rhoa,rhob = np.outer(a,a.conj()),np.outer(b,b.conj())
    _,vectors = np.linalg.eigh(rhoa-rhob)
    sequential = 0.0
    for v in vectors.T:
        wa = .5*abs(np.vdot(v,a))**2
        wb = .5*abs(np.vdot(v,b))**2
        delta = wa*rhoa-wb*rhob
        sequential += .5*(wa+wb+sum(abs(np.linalg.eigvalsh(delta))))
    joint = .5*(1+math.sqrt(1-abs(np.vdot(a,b))**4))
    assert sequential == pytest.approx(joint,abs=1e-12)
    assert joint == pytest.approx(.5+math.sqrt(15)/8,abs=1e-12)


def test_haar_and_equal_tiny_search_budget():
    for seed in (2026100900,2026100901):
        u = haar_su2(seed)
        assert np.allclose(u.conj().T@u,np.eye(2),atol=1e-12)
        assert np.linalg.det(u) == pytest.approx(1+0j,abs=1e-12)
    calls = {family:[] for family in core.FAMILIES}
    def objective(family):
        def evaluate(recipe):
            calls[family].append(recipe)
            if family == 'deferred-sequential':
                effects,decoder = core.sequential_povm(recipe=recipe)
                return _success(effects,decoder,core.double_trine_states())
            u,decoder = core.joint_receiver(recipe=recipe)
            effects = [np.outer(row.conj(),row) for row in u]
            return _success(effects,decoder,core.double_trine_states())
        return evaluate
    result = equal_budget_search({f:objective(f) for f in core.FAMILIES},budget=2)
    assert all(len(v)==2 for v in calls.values())
    assert all(r['evaluations']==2 for r in result['searches'].values())
    for f,search in result['searches'].items():
        expected = core.P_SEQ if f == 'deferred-sequential' else core.P_JOINT
        assert all(c['objective']==pytest.approx(expected,abs=1e-12) for c in search['candidates'])
    assert result['decisive_comparator'] == 'best budget-matched textbook'
    with pytest.raises(ValueError):
        equal_budget_search({f:objective(f) for f in core.FAMILIES},budget=2,seed=2026101000)
    assert import_recipe(export_recipe(result['recipe'])) == result['recipe']
    for bad in ({'parameters':{'relabel':6}}, {'parameters':{'completion_phase':float('nan')}},
                {'parameters':{'row_phases':[0,1]}}, {'parameters':{'unknown':1}}):
        with pytest.raises(ValueError): validate_recipe(bad)
