"""Graph-state stabilizer primitives and circuit blocks."""
import numpy as np
def stabilizers(edge_list,n=4):
    out=[]
    for i in range(n):
        x=[0]*n; z=[0]*n; x[i]=1
        for u,v in edge_list:
            if u==i:z[v]=1
            if v==i:z[u]=1
        out.append((tuple(x),tuple(z)))
    return tuple(out)
def graph_state(edge_list,n=4):
    s=np.ones(1<<n,dtype=complex)/(2**(n/2))
    for u,v in edge_list:
        for k in range(1<<n):
            if (k>>u)&1 and (k>>v)&1:s[k]*=-1
    return s
def stabilizer_expectation(state,x,z):
    total=0j
    for k,amp in enumerate(state):
        target=k
        for i,b in enumerate(x):
            if b:target^=1<<i
        phase=(1j)**sum(a*b for a,b in zip(x,z))*(-1)**sum(b*((k>>i)&1) for i,b in enumerate(z))
        total+=np.conj(state[target])*phase*amp
    return float(total.real)
def product_equatorial_state(angles):
    s=np.array([1.+0j])
    for a in angles:
        s=np.kron(s,np.array([1.,np.exp(1j*float(a))],dtype=complex)/np.sqrt(2))
    return s
def biseparable_control_state():
    # Bell pair on qubits 0,1 and |+> product factors on 2,3.
    bell=np.array([1.,0.,0.,1.],dtype=complex)/np.sqrt(2)
    plus=np.array([1.,1.],dtype=complex)/np.sqrt(2)
    return np.kron(np.kron(bell,plus),plus)
def exact_density_matrix(state):
    state=np.asarray(state,dtype=complex)
    return np.outer(state,state.conj())
def append_preparation(qc,offset,edge_list,frame,angles=None,kind='graph'):
    if kind=='graph':
        for q in range(4):qc.h(offset+q)
        for u,v in edge_list:qc.cz(offset+u,offset+v)
    else:
        for q,a in enumerate(angles or (0.37,0.81,1.13,1.71)):qc.h(offset+q);qc.rz(float(a),offset+q)
    for q,p in enumerate(frame):qc.rz(float(p),offset+q)
def append_measurement(qc,offset,edge_list,frame,color):
    from graphs import validate_connected_bipartite
    centers=set(validate_connected_bipartite(edge_list)[color])
    for q,p in enumerate(frame):qc.rz(-float(p),offset+q)
    for q in centers:qc.h(offset+q)
