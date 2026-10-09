import math
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator
from core import make_demo, analyze_counts
from strategies import audit_prover_ownership, frozen_recipe, DEVELOPMENT_SEEDS, basis_measure_prepare_choi
from product_bounds import (ideal_product_pass,ideal_certificate,partial_trace_output,
    acceptance_functional,solve_product_tester,certify_channel,product_tail_lower_bound)

def joint(circuit):
    probs=Statevector.from_instruction(circuit.remove_final_measurements(inplace=False)).probabilities()
    out=dict.fromkeys(('FF','FP','PF','PP'),0.)
    for n,p in enumerate(probs):
        key=('P' if n&5==0 else 'F')+('P' if n&10==0 else 'F')
        out[key]+=p
    return out

def test_anchor_actual_circuits():
    cs,m=make_demo(); p=math.cos(math.pi/8)**2
    prod=joint(cs[0]); hedge=joint(cs[1])
    assert list(prod.values())==pytest.approx([(1-p)**2,p*(1-p),p*(1-p),p*p])
    assert list(hedge.values())==pytest.approx([0,.5,.5,0],abs=1e-12)
    assert prod['PF']+prod['FP']+2*prod['PP']==pytest.approx(2*p)
    assert hedge['PF']+hedge['FP']+2*hedge['PP']==pytest.approx(1)
    assert m['offsets']==[0,4,8,12] and m['total_width']==16

def test_full_projector_and_accounting():
    _,m=make_demo()
    # 0100: second pass, first fail despite a zero reference bit.
    # 0001: same classification, demonstrating full pair check.
    h={n:{'0000':2,'0100':3,'0010':4,'1111':1} for n in m['ordered_blocks']}
    r=analyze_counts(h,m)['results'][0]
    assert r['outcome_counts']=={'FF':1,'FP':3,'PF':4,'PP':2}
    assert r['marginal_pass']==[.6,.5]
    assert r['mean']==pytest.approx(1.1)
    assert r['loss']==pytest.approx(.1+.02*.9)
    assert len(r['histogram'])==16

def test_zero_ff_and_bad_counts():
    _,m=make_demo(); h={n:{'0000':100} for n in m['ordered_blocks']}
    r=analyze_counts(h,m)['results'][0]
    assert r['double_failure_upper_if_zero']==pytest.approx(1-.05**.01)
    for bad in ({'0000':-1},{'0000':1.5},{'0000':0},{'10000':1}):
        with pytest.raises(ValueError): analyze_counts({n:bad for n in m['ordered_blocks']},m)

def test_off_anchor_and_frozen_cases():
    for case in (0,1,8):
        cs,m=make_demo(case); a=m['parameters']['alpha']; t=m['parameters']['theta']
        p=ideal_product_pass(a,t)
        assert joint(cs[0])['PP']==pytest.approx(p*p)
        assert ideal_certificate(a,t)['gap']<1e-9
    assert frozen_recipe(1)['seed']==DEVELOPMENT_SEEDS[0]
    assert frozen_recipe(8)['seed']==DEVELOPMENT_SEEDS[-1]
    with pytest.raises(ValueError): frozen_recipe(9)

def test_nested_strategy_references_and_legal_mapping():
    inner=QuantumCircuit(2); inner.cx(0,1)
    outer=QuantumCircuit(4); outer.append(inner.to_gate(),[2,0])
    with pytest.raises(ValueError,match='illegal strategy wire'): audit_prover_ownership(outer,0,{2,3})
    legal=QuantumCircuit(4); legal.append(inner.to_gate(),[2,3])
    audit_prover_ownership(legal,0,{2,3})

def state(a):
    v=np.array([math.cos(a),0,0,math.sin(a)],complex)
    return np.outer(v,v.conj())

def test_choi_convention_general_channel():
    rho=state(.63); effect=state(.19); w=acceptance_functional(rho,effect)
    # Independently contract a complex unitary channel on the source.
    u=Operator(QuantumCircuit(1)).data
    qc=QuantumCircuit(1); qc.ry(.37,0); qc.rz(.29,0); u=Operator(qc).data
    v=u.reshape(4); j=np.outer(v,v.conj())
    actual=np.kron(np.eye(2),u)@rho@np.kron(np.eye(2),u.conj().T)
    assert np.trace(w@j).real==pytest.approx(np.trace(effect@actual).real)
    assert np.allclose(partial_trace_output(j),np.eye(2))
    with pytest.raises(ValueError,match='primal'): certify_channel(w,j*.8,np.eye(2))

def test_noisy_cptp_certificate():
    # Independent depolarized local source and noisy verifier effect.
    rho=.91*state(.73)+.09*np.eye(4)/4
    effect=.94*state(.36)+.06*np.eye(4)/4
    c=solve_product_tester(rho,effect)
    assert c['gap']<=1e-4 and c['gap']>=-1e-9
    assert c['trace_preserving']<1e-9
    assert min(c['corrected_slack_eigenvalues'])>=-1e-10
    assert c['primal_value']<=c['dual_upper_bound']+1e-9
    assert not product_tail_lower_bound(.9,.9,independent=False)['valid']
    assert product_tail_lower_bound(.9,.8,lambda_value=.02)['loss_lower_bound']==pytest.approx(.026)

def test_control_ideal_outcome_equivalence():
    control=basis_measure_prepare_choi(.23,(.1,.2))
    assert np.allclose(partial_trace_output(control),np.eye(2))
    assert np.linalg.eigvalsh(control).min()>=-1e-12
    cs,m=make_demo(); a=m['parameters']['alpha']; t=m['parameters']['theta']
    # Physical constant-output CPTP channel has mixed reference diag marginal.
    rho=np.kron(np.diag([math.cos(a)**2,math.sin(a)**2]),np.diag([1.,0.]))
    qc=QuantumCircuit(2); qc.cx(0,1); qc.ry(-2*t,0)
    # Operator basis Qiskit order p tensor r; convert to r tensor p.
    swap=np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
    u=swap@Operator(qc).data@swap
    p=(u@rho@u.conj().T)[0,0].real
    assert joint(cs[3])['PP']==pytest.approx(p*p)
