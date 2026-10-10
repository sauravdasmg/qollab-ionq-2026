EARLY_GATE: HOLD

WP-C-07 / S-02 C early mathematics review. Independent verifier; build-window receipt supplied by orchestrator. Manifest generation UTC: 2026-10-10T00:49:49.319305+00:00. Review executed during the same build-window session. I did not author or edit the implementation. Owned outputs are only this report and review/manifests/frozen.json and fresh.json. No child agents, cloud jobs, full campaign, or noise sweep were run.

The ideal mathematical subchecks PASS. Campaign execution remains HOLD because declared preparation noise is not implemented, manifest-specific exact references are not checked by the harness, and its coverage event omits the second preparation. This is neither complete G1 nor science/browser readiness approval. Existing development and browser/cloud exports were not independently audited in this work package.

Sources read: experiments/PLAN.md; cases.py; experiments/run.py; measurements.py; graphs.py; witness.py; counts.py; circuit_pack.py; tests/test_core.py and test_harness.py; ../../research/plans/entanglement-court.md; ../../research/kickoff/WP-S-02-independent-gates.md; hackathon rules, pipeline state, and verify-claims skill. build_window.py reported build phase. The work package limits supersede the skill's broader full-verification workflow.

## Frozen independent inputs

Both JSON documents identify owner independent_verifier, generated_utc, generator, source SHA-256 values, strata, distinct sampling seeds, and per-manifest hashes. Each nested manifest has exactly the make_demo top-level keys. Blocks/maps are freshly assembled with graphs.edges and cases._maps; development manifests were not copied or relabeled. Four labeled graph templates recur; these are not 44 graph isomorphism classes.

| Suite | Case IDs, generation seeds, sampling seeds | Easy / near-threshold |
|---|---|---|
| frozen | 2026100200 through 2026100223 | first 12 / last 12 |
| fresh | 20261011000 through 20261011019 | first 10 / last 10 |

Generation and sampling seeds equal the preregistered ID for each instance. All 44 sampling seeds are distinct and disjoint from the four development seeds. Generation is deterministic NumPy default_rng(case_id): draw four frame angles uniform[-pi,pi), four product angles uniform[0,2pi), then the noise probability. This was fixed before sampling, with no outcome-based selection.

The plans prescribe varied frames, angles and diagonal local preparation noise but do not give numerical noise ranges. This verifier explicitly operationalized the strata as independent per-qubit phase flips E_p(rho)=(1-p)rho+p Z rho Z on both preparations, after preparation and before basis rotations: easy p in [0,.015), near-threshold p in [.12,.13). This choice is recorded in each file; it is not falsely attributed to the preregistration. The population generator witness is 1-4p, so near-threshold cases surround .5, while the true graph fidelity (1-p)^4 exceeds .5 throughout both ranges. Product controls remain separable. Exact diagonal Z probabilities remain uniform. These strata do not promise finite-shot certification rates.

The manifests explicitly flag the current implementation HOLD. Do not silently interpret their nonzero p as zero. Changing parameter ranges after viewing outcomes would require a disclosed new manifest version, not overwriting these inputs.

Frozen SHA-256: 138f4e8a58778026ceeebf8698db44d73e92c9e7148d22f6a5b9b258536bd1fa.
Fresh SHA-256: 8a35cb25777dd374edfa86e3c0afc2e137e0f5c6e5370ec94378a1bec7ad216c.

## C mathematics and mapping

Deterministic four-qubit calculations covered all 44 manifests without multinomial campaigns.

| Check | Reproduced value | Finding |
|---|---:|---|
| Paired ideal Z total variation | maximum 2.914335439641036e-16 | PASS, <=1e-12 |
| Uniform Z reference error | maximum 1.1102230246251565e-16 | PASS |
| Arbitrary inverse RZ frame residual, global phase removed | maximum 2.2247786310271853e-16 | PASS |
| Ideal stabilizer discrepancy | maximum 1.6653345369377348e-15 | PASS, <=1e-10 |
| Independent phase-flip density reference versus mean 1-2p | maximum 2.220446049250313e-15 | PASS for reference, absent in harness |
| Independent phase-flip fidelity versus (1-p)^4 | maximum 1.7763568394002505e-15 | PASS for reference |
| Maximum squared Schmidt coefficient, all seven cuts of each graph | .5000000000000001 for each graph | PASS |
| Minimum eigenvalue of projector minus generator lower-bound operator | -2.639548152089765e-16 | PASS within roundoff |
| Packed parity checks, all four graphs, 24- and 16-wire layouts | 1024 exact checks | PASS for decoder offsets/signs |
| Focused existing core tests | 7 passed in 0.62 s | PASS |

The stabilizer test is for the ideal pre-noise state with inverse frame rotations. Declared noisy graph means are 1-2p, not one. Frame inverses are actual RZ(-angle) gates; sign changes alone cannot remove arbitrary angles.

Independent theorem derivation: for a graph state across A|B, remove all CZ gates internal to each side, since they are local relative to that cut. The remaining coefficient matrix has entries proportional to (-1)^(x^T Gamma_AB y). Orthogonality of binary characters gives equal squared Schmidt coefficients 2^(-r), with r the binary rank of Gamma_AB. A connected graph has at least one crossing edge on every nontrivial cut, hence r>=1 and maximum squared overlap with any product vector across that cut is <=1/2. A single-vertex cut has rank one, so the maximum over cuts is exactly 1/2. Convex mixtures of states separable across possibly different cuts cannot exceed this linear fidelity bound. Arbitrary local RZ frames preserve it. This argument assumes a connected graph with at least two vertices; the numerical audit covers the four supported graphs and all seven cuts each.

For commuting graph generators, the common +1 projector is P=product_i (I+K_i)/2. In a joint eigenvector with t negative generator eigenvalues, B=I-sum_i(I-K_i)/2 has eigenvalue 1-t. P has eigenvalue one at t=0 and zero otherwise. Thus P-B is positive semidefinite and F>=1-sum_i(1-mu_i)/2. Replacing each mu_i by a valid simultaneous lower bound L_i preserves the lower bound. The implementation uses that formula and certifies only strictly above .5; a mocked exact threshold test gives .4999999599999998 -> false, .5 -> false, .5000000400000002 -> true. A disconnected-graph flag prevents certification. Negative F_lower is an allowed conservative bound.

For Bernoulli parity-success counts k of N IID shots, the one-sided lower CP bound is 0 for k=0, beta.ppf(a,k,N-k+1) otherwise, with a^(1/N) at k=N. For a=.05/(2*4)=.00625 and N=100, bounds at k=0,1,50,99,100 are 0, .00006269416477466069, .37256190587283894, .9304117886779315, .9505146177581021. The nonzero bounds solve P_p(X>=k)=a with maximum residual 3.729655473350135e-17. Four all-success generators yield F_lower=.8020584710324083.

A union bound over eight one-sided intervals gives <=.05 failure probability per two-preparation round. It does not require independence between generators or packed blocks; the marginal binomial model still requires IID shots with fixed success probability. This does not provide campaign-wide 95% control. The mathematical allocation is valid; the current empirical harness does not measure the entire eight-interval event, as detailed below.

Trusted rotations and readout remain assumptions. main.py:21 defaults assume_trusted_measurements=False. The successful untrusted witness receipt explicitly says measurement systematic error is unbounded. No calibration or hardware inference was justified by this review. Inconclusive does not imply separability. The two_color_witness function currently delegates to the same generator witness (witness.py:23); ties are expected, not evidence of independent baseline superiority.

## Blocking findings and exact repair requests

1. **Ignored declared preparation noise.** experiments/run.py:173 says `rho = DensityMatrix.from_instruction(prep).data`; lines 174-178 apply only model-dependent depolarizing channels, then lines 179-182 start basis rotations. The function never reads diagonal_preparation_noise. For frozen case 2026100212, p=.12430841310983293: zeroing p changes the returned distribution by exactly 0; the computed generator mean is 1.0 instead of the declared .7513831737803341. Apply the manifest's declared local phase-flip channel consistently to both preparations and controls before basis rotation. Verify against the supplied independent density reference before campaign execution. The near-threshold manifests cannot presently be executed faithfully.

2. **Development-only exact references.** experiments/run.py:233 says `gs = graph_state(edges(case_index)); prod = product_equatorial_state(__import__("cases").ANGLES[case_index])`. The caller at line 287 supplies `_exact_checks(idx)`. These references ignore the manifest's frames, angles and noise. The current numbers can agree trivially while failing to validate the actual preparation. Accept the manifest and separate pre-noise uniform/stabilizer checks from post-channel truth; compare actual basis distributions and frame-adjusted means. The deterministic verifier checks above cover the staged manifests independently, but do not repair this harness defect.

3. **Incomplete two-preparation coverage event.** cases.py:46 says `for name in ('target_A','target_B'):pars.extend(r['blocks'].get(name,[]))`; line 49 passes only these four target terms into simultaneous_witness. experiments/run.py:273-275 says `covered = [t["L_lower"] <= mu + 1e-12 for t, mu in zip(w["terms"], true_means)]`, then `rec["simultaneous_coverage"] += int(all(covered))`. The second preparation's four bounds are absent. Sampling a separate product-control target run does not recreate the paired eight-bound event for the same draw. Compute both preparations' bounds from the same packed/marginal draw, keep generator identity aligned with truth, and record the conjunction of all eight coverage indicators.

4. **Invalid bias inputs can increase a lower bound.** witness.py:12-13 only defaults/checks the bias list length. Line 18 applies `max(-1.,2*lo-1-2*float(d))` without checking d is finite and nonnegative. Four 50/100 parity counts with bias_bounds=[-.6]*4 produce F_lower=.8902476234913557 and conditional_gme=true. This is a malformed-input defect, not evidence of a false certificate under valid nonnegative assumptions. Reject negative/nonfinite bounds before calculating any receipt. Document whether d bounds probability error (subtract 2d) or expectation error (the research plan's delta requires subtracting delta). For a nonnegative expectation bound, subtracting twice delta is conservative but unnecessarily weak. Do not expose corrected certificates before these semantics and validation are fixed.

5. **Requested CLI smoke is not bounded by --draws 5.** experiments/run.py:243-245 constructs one ideal plus three models times seven scales for every supplied case. The requested frozen and fresh commands would process all 44 cases, 22 configurations each, and three controls: 14,520 control draws in total. That violates this worker's explicit no-sweeps/no-many-seeds instruction and would create files outside the three owned outputs. Those two exact CLI commands were NOT run. A clearly bounded substitute below exercises the real loader/specs and _draw_record for two cases per suite with five draws and an in-memory ideal-only configuration override; no implementation files or result files are changed.

After fixes, the orchestrator must execute the requested smoke and full campaign, retain all outcomes, and commission the remaining independent checks. Do not promote this HOLD to a science pass from five draws, the 7 core tests, or the mathematical proof alone.

## Reproduction and execution record

Use the repository interpreter from the submission folder. The following requested loader/spec commands ran successfully:

```powershell
& '../../.venv/Scripts/python.exe' -B -c "from experiments.run import load_independent_manifest, _case_specs; p='review/manifests/frozen.json'; assert len(load_independent_manifest(p)['instances']) == 24; assert len(_case_specs('frozen', p)) == 24"
& '../../.venv/Scripts/python.exe' -B -c "from experiments.run import load_independent_manifest, _case_specs; p='review/manifests/fresh.json'; assert len(load_independent_manifest(p)['instances']) == 20; assert len(_case_specs('fresh', p)) == 20"
& '../../.venv/Scripts/python.exe' -B -m pytest tests/test_core.py -q -p no:cacheprovider
```

Deferred exact commands for the orchestrator after repair (NOT executed in this review):

```powershell
& '../../.venv/Scripts/python.exe' -B experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --draws 5 --output-dir results/quick-frozen-smoke
& '../../.venv/Scripts/python.exe' -B experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json --draws 5 --output-dir results/quick-fresh-smoke
```

The bounded substitute used frozen 2026100200 / 2026100212 and fresh 20261011000 / 20261011010, five ideal-only draws per case. All four returned 5/5 graph certificates and 0/5 product false certificates. These are plumbing results from the defective noise implementation, not evidence about the declared near-threshold preparations. The complete numeric output is embedded below, rather than writing unowned result artifacts.

To repeat the independent quick checks without adding a script file, execute the first Python block from this report:

```powershell
& '../../.venv/Scripts/python.exe' -B -c "from pathlib import Path; t=Path('review/early_math.md').read_text(encoding='utf-8'); code=t.split(chr(96)*3+'python\n',1)[1].split(chr(96)*3,1)[0]; exec(compile(code,'early_math_quick_checks','exec'))"
```

```python
import copy, hashlib, inspect, json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from scipy.stats import binom
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator
from cases import make_demo, SEEDS
from graphs import edges
from measurements import append_preparation, append_measurement, graph_state
from counts import block_parities
from witness import allocate_alpha, cp_lower, simultaneous_witness
from circuit_pack import digest
import experiments.run as harness

metrics = {}
datasets = {s:harness.load_independent_manifest('review/manifests/'+s+'.json') for s in ('frozen','fresh')}
all_rows = [r for d in datasets.values() for r in d['instances']]
assert len({r['manifest']['case_id'] for r in all_rows}) == 44
assert len({r['sampling_seed'] for r in all_rows}) == 44
assert not set(SEEDS) & {r['sampling_seed'] for r in all_rows}
for suite,count,neasy in (('frozen',24,12),('fresh',20,10)):
    specs = harness._case_specs(suite,'review/manifests/'+suite+'.json')
    assert len(specs) == count
    for j,row in enumerate(datasets[suite]['instances']):
        m = row['manifest']
        assert row['stratum'] == ('easy' if j<neasy else 'near-threshold')
        assert row['manifest_hash'] == digest(m)
        assert set(m) == set(make_demo(m['case_id']%4)[1])
        assert m['generated_parameters']['edges'] == [list(e) for e in edges(m['case_id']%4)]
metrics['manifest_counts'] = {s:len(d['instances']) for s,d in datasets.items()}

max_tv=max_uniform=max_frame=max_stab=max_noise_error=max_formula_error=0.
for row in all_rows:
    m=row['manifest']; p=m['generated_parameters']; g=p['edges']
    frame=p['frame_radians']; angle=p['product_angles_radians']
    states={}
    for kind in ('graph','product'):
        qc=QuantumCircuit(4)
        append_preparation(qc,0,g,frame,angle,kind)
        states[kind]=Statevector.from_instruction(qc).data
    gp=np.abs(states['graph'])**2; pp=np.abs(states['product'])**2
    max_tv=max(max_tv,float(.5*abs(gp-pp).sum()))
    max_uniform=max(max_uniform,float(max(abs(gp-1/16).max(),abs(pp-1/16).max())))
    undo=QuantumCircuit(4)
    for q,a in enumerate(frame): undo.rz(-a,q)
    recovered=Operator(undo).data @ states['graph']
    ref=graph_state(g)
    phase=np.vdot(ref,recovered); aligned=recovered*np.exp(-1j*np.angle(phase))
    max_frame=max(max_frame,float(abs(aligned-ref).max()))
    rho=np.outer(states['graph'],states['graph'].conj())
    noise=p['diagonal_preparation_noise']
    for q in range(4):
        z=np.array([(-1)**((k>>q)&1) for k in range(16)])
        rho=(1-noise)*rho+noise*(z[:,None]*rho*z[None,:])
    exact_fidelity=float(np.vdot(states['graph'],rho@states['graph']).real)
    max_formula_error=max(max_formula_error,abs(exact_fidelity-(1-noise)**4))
    max_uniform=max(max_uniform,float(abs(np.diag(rho).real-1/16).max()))
    for color,name in enumerate(('target_A','target_B')):
        basis=QuantumCircuit(4); append_measurement(basis,0,g,frame,color)
        u=Operator(basis).data
        clean=np.abs(u@states['graph'])**2
        noisy=np.diag(u@rho@u.conj().T).real
        for mapping in m['blocks'][name]['parity_maps']:
            signs=np.array([(-1)**sum((k>>q)&1 for q in mapping['bits']) for k in range(16)])
            max_stab=max(max_stab,abs(float(clean@signs)-1))
            max_noise_error=max(max_noise_error,abs(float(noisy@signs)-(1-2*noise)))
metrics.update(z_tv_max=max_tv,z_uniform_max_error=max_uniform,arbitrary_frame_inverse_max_error=max_frame,
               ideal_stabilizer_max_error=max_stab,declared_phase_flip_mean_max_error=max_noise_error,
               declared_phase_flip_fidelity_max_error=max_formula_error)
assert max_tv<=1e-12 and max_uniform<=1e-12 and max_stab<=1e-10 and max_frame<=1e-10

cutmax=[]; operator_min=[]; map_checks=0
for case in range(4):
    g=edges(case); state=graph_state(g); ks=[]
    for center in range(4):
        k=np.zeros((16,16),complex)
        neighbors=[v if u==center else u for u,v in g if center in (u,v)]
        for b in range(16):
            k[b^(1<<center),b]=(-1)**sum((b>>q)&1 for q in neighbors)
        ks.append(k)
    lower=np.eye(16)-sum((np.eye(16)-k) for k in ks)/2
    operator_min.append(float(np.linalg.eigvalsh(np.outer(state,state.conj())-lower).min()))
    cuts=[]
    for mask in range(1,8):
        aa=[q for q in range(4) if (mask>>q)&1]; bb=[q for q in range(4) if not (mask>>q)&1]
        mat=np.zeros((2**len(aa),2**len(bb)),complex)
        for k in range(16):
            i=sum(((k>>q)&1)<<j for j,q in enumerate(aa))
            j=sum(((k>>q)&1)<<j for j,q in enumerate(bb))
            mat[i,j]=state[k]
        cuts.append(float(np.linalg.svd(mat,compute_uv=False)[0]**2))
    cutmax.append(max(cuts))
    for recipe in ({},{'audited16':True}):
        _,m=make_demo(case,recipe)
        for name,b in m['blocks'].items():
            for value in range(16):
                raw={format(value<<b['offset'],'0'+str(m['total_width'])+'b'):1}
                got=block_parities(raw,m,name)
                for term,mapping in zip(got,b['parity_maps']):
                    expected=(-1)**sum((value>>q)&1 for q in mapping['bits'])
                    assert term['estimate']==expected
                    map_checks+=1
assert max(abs(x-.5) for x in cutmax)<1e-12 and min(operator_min)>-1e-12
metrics.update(max_squared_schmidt_by_graph=cutmax,projector_inequality_min_eigenvalues=operator_min,
               deterministic_packed_parity_checks=map_checks)

a=allocate_alpha(.05,4,2); assert a==.00625
cpvals={k:cp_lower(k,100,a) for k in (0,1,50,99,100)}
residual=max(abs(float(binom.sf(k-1,100,cpvals[k]))-a) for k in (1,50,99,100))
assert cpvals[0]==0 and cpvals[100]==a**.01 and residual<1e-12
parities=[{'successes':100,'shots':100}]*4
all_success=simultaneous_witness(parities)
assert abs(all_success['F_lower']-(1-sum(1-t['L_lower'] for t in all_success['terms'])/2))<1e-14
boundary=[]
for plower in (.875-1e-8,.875,.875+1e-8):
    with patch('witness.cp_lower',return_value=plower):
        result=simultaneous_witness(parities)
        boundary.append([result['F_lower'],result['conditional_gme']])
assert [r[1] for r in boundary]==[False,False,True]
assert not simultaneous_witness(parities,graph_connected=False)['conditional_gme']
assert not all_success['trust_flag'] and 'systematic error unbounded' in all_success['receipt']
metrics.update(cp_alpha=a,cp_lower_100_shots=cpvals,cp_tail_equation_max_error=residual,
               all_success_F_lower=all_success['F_lower'],strict_threshold_checks=boundary)

# Direct deterministic reproduction of the ignored preparation-noise defect.
m=datasets['frozen']['instances'][12]['manifest']; clean=copy.deepcopy(m)
clean['generated_parameters']['diagonal_preparation_noise']=0.
def probs(mm):
    return harness._probabilities(mm['case_id']%4,'target_A','graph',0.,None,0.,mm)
actual=probs(m); no_noise=probs(clean)
mapping=m['blocks']['target_A']['parity_maps'][0]
signs=np.array([(-1)**sum((k>>q)&1 for q in mapping['bits']) for k in range(16)])
metrics['ignored_noise_reproduction']={'case_id':m['case_id'],'p':m['generated_parameters']['diagonal_preparation_noise'],
    'max_probability_change_when_p_zeroed':float(abs(actual-no_noise).max()),'actual_generator_mean':float(actual@signs),
    'declared_expected_mean':1-2*m['generated_parameters']['diagonal_preparation_noise']}
negative=simultaneous_witness([{'successes':50,'shots':100}]*4,bias_bounds=[-.6]*4)
metrics['negative_bias_input_reproduction']={'F_lower':negative['F_lower'],'conditional_gme':negative['conditional_gme']}

# Bounded substitute only: two selected cases/suite, one ideal configuration, five draws.
# No file writes, no full-suite execution, no noise-scale sweep, no claimed science evidence.
metrics['bounded_smoke']=[]
with patch.object(harness,'NOISE_SCALES',()):
    for suite,indices in (('frozen',(0,12)),('fresh',(0,10))):
        specs=harness._case_specs(suite,'review/manifests/'+suite+'.json')
        for idx in indices:
            rows=harness._draw_record(specs[idx],draws=5,shots=100,base_seed=specs[idx]['sampling_seed'])
            assert len(rows)==1 and rows[0]['draws']==5
            metrics['bounded_smoke'].append({'suite':suite,'case_id':specs[idx]['case_id'],'draws':5,
                'configuration':'ideal-only','graph_certificates':rows[0]['controls']['graph']['certificates'],
                'product_false_certificates':rows[0]['controls']['product']['false_certificates']})
metrics['versions']={'numpy':np.__version__,'scipy':__import__('scipy').__version__,'qiskit':__import__('qiskit').__version__}
metrics['sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('review/manifests/frozen.json'),Path('review/manifests/fresh.json')]}
print(json.dumps(metrics,indent=2,allow_nan=False))
```

Recorded output:

```json
{
  "manifest_counts": {
    "frozen": 24,
    "fresh": 20
  },
  "z_tv_max": 2.914335439641036e-16,
  "z_uniform_max_error": 1.1102230246251565e-16,
  "arbitrary_frame_inverse_max_error": 2.2247786310271853e-16,
  "ideal_stabilizer_max_error": 1.6653345369377348e-15,
  "declared_phase_flip_mean_max_error": 2.220446049250313e-15,
  "declared_phase_flip_fidelity_max_error": 1.7763568394002505e-15,
  "max_squared_schmidt_by_graph": [
    0.5000000000000001,
    0.5000000000000001,
    0.5000000000000001,
    0.5000000000000001
  ],
  "projector_inequality_min_eigenvalues": [
    -2.639548152089765e-16,
    -2.639548152089765e-16,
    -2.639548152089765e-16,
    -2.639548152089765e-16
  ],
  "deterministic_packed_parity_checks": 1024,
  "cp_alpha": 0.00625,
  "cp_lower_100_shots": {
    "0": 0.0,
    "1": 6.269416477466069e-05,
    "50": 0.37256190587283894,
    "99": 0.9304117886779315,
    "100": 0.9505146177581021
  },
  "cp_tail_equation_max_error": 3.729655473350135e-17,
  "all_success_F_lower": 0.8020584710324083,
  "strict_threshold_checks": [
    [
      0.4999999599999998,
      false
    ],
    [
      0.5,
      false
    ],
    [
      0.5000000400000002,
      true
    ]
  ],
  "ignored_noise_reproduction": {
    "case_id": 2026100212,
    "p": 0.12430841310983293,
    "max_probability_change_when_p_zeroed": 0.0,
    "actual_generator_mean": 1.0,
    "declared_expected_mean": 0.7513831737803341
  },
  "negative_bias_input_reproduction": {
    "F_lower": 0.8902476234913557,
    "conditional_gme": true
  },
  "bounded_smoke": [
    {
      "suite": "frozen",
      "case_id": 2026100200,
      "draws": 5,
      "configuration": "ideal-only",
      "graph_certificates": 5,
      "product_false_certificates": 0
    },
    {
      "suite": "frozen",
      "case_id": 2026100212,
      "draws": 5,
      "configuration": "ideal-only",
      "graph_certificates": 5,
      "product_false_certificates": 0
    },
    {
      "suite": "fresh",
      "case_id": 20261011000,
      "draws": 5,
      "configuration": "ideal-only",
      "graph_certificates": 5,
      "product_false_certificates": 0
    },
    {
      "suite": "fresh",
      "case_id": 20261011010,
      "draws": 5,
      "configuration": "ideal-only",
      "graph_certificates": 5,
      "product_false_certificates": 0
    }
  ],
  "versions": {
    "numpy": "2.5.3",
    "scipy": "1.18.1",
    "qiskit": "2.5.2"
  },
  "sha256": {
    "review\\manifests\\frozen.json": "138f4e8a58778026ceeebf8698db44d73e92c9e7148d22f6a5b9b258536bd1fa",
    "review\\manifests\\fresh.json": "8a35cb25777dd374edfa86e3c0afc2e137e0f5c6e5370ec94378a1bec7ad216c"
  }
}
```

