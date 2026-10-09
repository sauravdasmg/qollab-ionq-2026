"""Qubit CPTP certificates, unnormalized Choi order output tensor input.

For source rho on reference tensor input and effect E on reference tensor
output, W is defined by Tr(W J) = Tr(E (id tensor channel_J)(rho)).
Primal: J>=0, Tr_output J=I. Dual: I_output tensor Y>=W.
"""
import math
import numpy as np
from scipy.optimize import minimize

def ideal_product_pass(alpha,theta):
    if not 0<=alpha<=math.pi/2 or not 0<=theta<=math.pi/2: raise ValueError("angles outside first quadrant")
    # Fixed reference marginal diag(cos(alpha)^2,sin(alpha)^2): Uhlmann
    # fidelity with verifier marginal, attained by the identity channel.
    return math.cos(alpha-theta)**2

def partial_trace_output(j):
    return np.einsum('aiaj->ij',np.asarray(j,complex).reshape(2,2,2,2))

def _hermitian(a,n):
    a=np.asarray(a,complex)
    if a.shape!=(n,n) or not np.all(np.isfinite(a)) or np.linalg.norm(a-a.conj().T)>1e-9:
        raise ValueError("finite Hermitian matrix required")
    return (a+a.conj().T)/2

def choi_residuals(j):
    j=_hermitian(j,4)
    return {"hermiticity":float(np.linalg.norm(j-j.conj().T)),
        "minimum_eigenvalue":float(np.linalg.eigvalsh(j).min()),
        "trace_preserving":float(np.linalg.norm(partial_trace_output(j)-np.eye(2))),
        "trace_residual":float(abs(np.trace(j)-2))}

def acceptance_functional(source, effect):
    rho=_hermitian(source,4); e=_hermitian(effect,4)
    if np.linalg.eigvalsh(rho).min() < -1e-10 or abs(np.trace(rho)-1)>1e-9:
        raise ValueError("source must be a density matrix")
    if np.linalg.eigvalsh(e).min() < -1e-10 or np.linalg.eigvalsh(e).max()>1+1e-10:
        raise ValueError("acceptance effect must be between zero and identity")
    rho=rho.reshape(2,2,2,2); e=e.reshape(2,2,2,2)
    w=np.zeros((4,4),complex)
    for o in range(2):
        for i in range(2):
            for p in range(2):
                for j in range(2):
                    w[2*p+j,2*o+i]=sum(rho[r,i,s,j]*e[s,p,r,o] for r in range(2) for s in range(2))
    return _hermitian(w,4)

def certify_channel(acceptance,primal_choi,dual_input,max_gap=1e-4):
    w=_hermitian(acceptance,4); j=_hermitian(primal_choi,4); y=_hermitian(dual_input,2)
    res=choi_residuals(j)
    if res["minimum_eigenvalue"] < -1e-10 or res["trace_preserving"]>1e-9:
        raise ValueError("primal is not feasible CPTP")
    slack=np.kron(np.eye(2),y)-w
    minimum=float(np.linalg.eigvalsh(slack).min())
    correction=max(0.,-minimum)+1e-12
    corrected_y=y+correction*np.eye(2)
    corrected_slack=np.kron(np.eye(2),corrected_y)-w
    primal=float(np.trace(w@j).real); dual=float(np.trace(corrected_y).real)
    gap=dual-primal
    res.update({"tensor_order":"output tensor input; unnormalized Choi",
        "dual_slack_min_eigenvalue":minimum,"dual_slack_correction":correction,
        "corrected_slack_eigenvalues":np.linalg.eigvalsh(corrected_slack).tolist(),
        "primal_eigenvalues":np.linalg.eigvalsh(j).tolist(),
        "primal_value":primal,"dual_upper_bound":dual,"gap":gap,
        "dual_feasible":True,"certified":-1e-9<=gap<=max_gap,
        "primal_choi_real":j.real.tolist(),"primal_choi_imag":j.imag.tolist(),
        "dual_input_real":corrected_y.real.tolist(),"dual_input_imag":corrected_y.imag.tolist()})
    if not res["certified"]: raise ValueError(f"CPTP certificate gap {gap} exceeds {max_gap}")
    return res

def _basis(n):
    b=[]
    for i in range(n):
        a=np.zeros((n,n),complex); a[i,i]=1; b.append(a)
    for i in range(n):
        for k in range(i+1,n):
            a=np.zeros((n,n),complex); a[i,k]=a[k,i]=1; b.append(a)
            a=np.zeros((n,n),complex); a[i,k]=1j; a[k,i]=-1j; b.append(a)
    return np.array(b)

def solve_product_tester(source,effect,max_gap=1e-4):
    """Small SDP via SLSQP; numerical search is accepted only with certificate.

    Supply the effective noisy source and verifier POVM after independent local
    preparation/verifier/readout noise. Noise on the prover's channel requires
    composing its adjoint with W externally; inter-test noise invalidates this.
    """
    w=acceptance_functional(source,effect); b4=_basis(4); b2=_basis(2)
    def jmat(x): return np.einsum('k,kij->ij',x,b4)
    def ymat(x): return np.einsum('k,kij->ij',x,b2)
    def tp(x):
        d=partial_trace_output(jmat(x))-np.eye(2)
        return np.array([d[0,0].real,d[1,1].real,d[0,1].real,d[0,1].imag])
    opts={"ftol":1e-12,"maxiter":1200}
    px=np.zeros(16); px[:4]=.5
    pr=minimize(lambda x:-float(np.trace(w@jmat(x)).real),px,method="SLSQP",
        constraints=[{"type":"eq","fun":tp},{"type":"ineq","fun":lambda x:np.linalg.eigvalsh(jmat(x))}],options=opts)
    # PSD clipping then congruence normalization gives an independently feasible
    # channel even if the numerical search left tiny constraint residuals.
    vals,vec=np.linalg.eigh(jmat(pr.x)); j=(vec*np.maximum(vals,1e-14))@vec.conj().T
    vals,vec=np.linalg.eigh(partial_trace_output(j))
    if vals.min()<=0: raise ValueError("cannot normalize primal")
    inv=(vec*(vals**-.5))@vec.conj().T; c=np.kron(np.eye(2),inv); j=c@j@c.conj().T
    dx=np.zeros(4); dx[:2]=max(1.,float(np.linalg.eigvalsh(w).max()))
    dr=minimize(lambda x:float(np.trace(ymat(x)).real),dx,method="SLSQP",
        constraints=[{"type":"ineq","fun":lambda x:np.linalg.eigvalsh(np.kron(np.eye(2),ymat(x))-w)}],options=opts)
    cert=certify_channel(w,j,ymat(dr.x),max_gap)
    cert["solver_status"]={"primal":str(pr.message),"dual":str(dr.message)}
    return cert

def ideal_certificate(alpha,theta):
    a=math.cos(alpha)*math.cos(theta); b=math.sin(alpha)*math.sin(theta)
    v=np.array([a,0,0,b]); w=np.outer(v,v)
    v=np.array([1.,0,0,1.]); j=np.outer(v,v)
    return certify_channel(w,j,np.diag([a*(a+b),b*(a+b)]))

def product_tail_lower_bound(p1_upper,p2_upper,independent=True,lambda_value=0.):
    if not independent:
        return {"valid":False,"reason":"test/source/noise coupling invalidates product factorization"}
    if not all(math.isfinite(x) for x in (p1_upper,p2_upper,lambda_value)) or lambda_value<0:
        raise ValueError("invalid bounds/lambda")
    p1,p2=np.clip([p1_upper,p2_upper],0,1)
    f=float((1-p1)*(1-p2))
    return {"valid":True,"double_failure_lower_bound":f,"loss_lower_bound":float(f+lambda_value*(2-p1-p2)),
            "assumption":"independent test sources, product channels, and independent per-test noise"}
