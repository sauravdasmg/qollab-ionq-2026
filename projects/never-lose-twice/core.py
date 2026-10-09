"""Two-question game; pair t consists of reference t and prover t+2."""
import math
import hashlib
import json
import numbers
from qiskit import QuantumCircuit
from scipy.stats import beta
from strategies import frozen_recipe, strategy_angles, audit_prover_ownership, OWNERSHIP, LAMBDA_MENU

BLOCKS = ("attained_product", "published_hedge", "optimized_joint", "product_control")

def _block(name, recipe, case):
    qc = QuantumCircuit(4,4,name=name)
    for r,p in ((0,2),(1,3)):
        qc.ry(2*recipe["alpha"],r)
        if name != "product_control":
            qc.cx(r,p)
        # Control circuit is outcome-equivalent to fixed-output measure/prepare:
        # inverse verifier's CX tags the reference basis in the prover; hence
        # every measured POVM effect annihilates reference off-diagonal terms.
        # Its intermediate pure reference state is NOT the physical mixed source.
    start = len(qc.data)
    strategy_angles(qc,recipe,name)
    audit_prover_ownership(qc,start,{2,3})
    for r,p in ((0,2),(1,3)):
        qc.cx(r,p); qc.ry(-2*recipe["theta"],r)
    qc.measure(range(4),range(4))
    return qc

def make_demo(case: int = 0, recipe=None):
    params = frozen_recipe(case)
    if recipe is not None: params.update(dict(recipe))
    for key in ("alpha","theta"):
        if not math.isfinite(params[key]) or not 0 <= params[key] <= math.pi/2:
            raise ValueError("angles must be finite in [0,pi/2]")
    if params["lambda_star"] not in LAMBDA_MENU: raise ValueError("lambda outside development menu")
    manifest = {"case_id":case,"seed":params["seed"],"parameters":params,
        "ordered_blocks":list(BLOCKS),"widths":[4]*4,"offsets":[0,4,8,12],"total_width":16,
        "decoding_maps":[{"test_pass_cbits":[[0,2],[1,3]],"accepted_pair_outcome":"00",
                         "classical_bits":[0,1,2,3]} for _ in BLOCKS],
        "ownership":OWNERSHIP,"smoke_control_ids":["product_control"],
        "source_assumptions":["same alpha and theta for both tests","independent reference/prover source pairs",
           "product factorization requires independent per-test noise","control ideal histogram is outcome-equivalent to fixed-output measure/prepare; not a noisy implementation of that channel",
           "optimized_joint is a frozen candidate, not an optimality claim"],
        "recipe_identity":params["identity"],
        "recipe_hash":hashlib.sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()}
    return [_block(n,params,case) for n in BLOCKS],manifest

def analyze_counts(marginals, manifest, **options):
    lam=float(options.get("lambda_value",manifest["parameters"]["lambda_star"]))
    confidence=float(options.get("confidence",.95)); alpha=1-confidence
    if not 0<confidence<1 or not math.isfinite(lam) or lam<0: raise ValueError("invalid confidence/lambda")
    results=[]
    for name,decode in zip(manifest["ordered_blocks"],manifest["decoding_maps"]):
        hist={format(i,"04b"):0 for i in range(16)}
        for key,value in marginals[name].items():
            if isinstance(value,bool) or not isinstance(value,numbers.Integral) or value<0: raise ValueError("invalid count")
            k=str(key).replace(" ","")
            if k.startswith("0x"):
                n=int(k,16)
            else:
                if not k or any(c not in "01" for c in k): raise ValueError("invalid bit key")
                n=int(k,2)
            if not 0<=n<16: raise ValueError("count key exceeds block width")
            hist[format(n,"04b")]+=int(value)
        shots=sum(hist.values())
        if shots<=0: raise ValueError("empty counts are not evidence")
        joint=dict.fromkeys(("FF","FP","PF","PP"),0)
        for k,v in hist.items():
            n=int(k,2)
            status="".join("P" if all(not ((n>>b)&1) for b in bits) else "F" for bits in decode["test_pass_cbits"])
            joint[status]+=v
        p1=(joint["PF"]+joint["PP"])/shots; p2=(joint["FP"]+joint["PP"])/shots
        f=joint["FF"]/shots; m=p1+p2
        def interval(k):
            return [0. if k==0 else float(beta.ppf(alpha/2,k,shots-k+1)),
                    1. if k==shots else float(beta.ppf(1-alpha/2,k+1,shots-k))]
        results.append({"block":name,"shots":shots,"histogram":hist,"outcome_counts":joint,
            "joint_probabilities":{k:v/shots for k,v in joint.items()},"marginal_pass":[p1,p2],
            "double_failure":f,"f":f,"mean":m,"m":m,"loss":f+lam*(2-m),"lambda":lam,
            "double_failure_upper_if_zero":1-alpha**(1/shots) if joint["FF"]==0 else None,
            "uncertainties":{"confidence":confidence,"ff_interval":interval(joint["FF"]),
                "marginal_pass_intervals":[interval(joint["PF"]+joint["PP"]),interval(joint["FP"]+joint["PP"])],
                "method":"individual exact binomial intervals; not simultaneous; IID shots assumed"},
            "assumptions":["full two-bit projector; all outcomes retained","no independence between tests assumed in observed joint histogram"]})
    return {"results":results,"manifest":manifest,"assumptions":["IID shots for binomial uncertainty"]}
