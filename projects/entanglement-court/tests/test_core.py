import numpy as np
from graphs import edges,validate_connected_bipartite
from measurements import graph_state,stabilizers,stabilizer_expectation,product_equatorial_state,biseparable_control_state,exact_density_matrix
from counts import parity_estimates
from witness import cp_lower,allocate_alpha,simultaneous_witness
from cases import make_demo
def test_connected_bipartite():
    for c in range(4):assert len(validate_connected_bipartite(edges(c)))==2
def test_uniform_z_and_stabilizers():
    for c in range(4):
        s=graph_state(edges(c));assert np.max(np.abs(np.abs(s)**2-1/16))<1e-12
        for x,z in stabilizers(edges(c)):assert abs(stabilizer_expectation(s,x,z)-1)<1e-10
def test_cp_and_alpha():
    assert cp_lower(0,100,.05)==0 and cp_lower(100,100,.05)==.05**.01
    assert allocate_alpha(.05,4,2)==.00625
def test_witness_threshold():
    p=[{'successes':100,'shots':100} for _ in range(4)];assert simultaneous_witness(p)['conditional_gme']
    q=[{'successes':50,'shots':100} for _ in range(4)];assert not simultaneous_witness(q)['conditional_gme']
def test_factory():
    circuits,m=make_demo(0);assert len(circuits)==1 and m['total_width']==24 and len(m['ordered_blocks'])==6
    packed,m16=make_demo(0,{'audited16':True});assert packed[0].num_qubits==16 and m16['total_width']==16
def test_arbitrary_equatorial_and_exact_controls():
    for angles in ((.1,.7,1.4,2.8),):
        s=product_equatorial_state(angles);assert np.max(np.abs(np.abs(s)**2-1/16))<1e-12
    rho=exact_density_matrix(biseparable_control_state());assert np.isclose(np.trace(rho),1) and np.isclose(np.trace(rho@rho),1)
def test_asymmetric_signed_parity_map():
    out=parity_estimates({'001':3,'100':1},3,[{'bits':[1,2],'sign':1}])[0]
    assert out['shots']==4 and out['successes']==3 and out['estimate']==.5
