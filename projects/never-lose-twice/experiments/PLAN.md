# Preregistered evidence plan — Never Lose Twice

## Question and hypothesis

This is a measurement of a two test channel game, not a claim about every strategy. The product channel class has the exact ideal reference bound in `product_bounds.py`; the joint candidate is the frozen `optimized_joint` strategy. H1 asks whether its double failure rate improves over the strongest certified product strategy at equal shots. At aria scale 1, the one sided 97.5% lower bound for `0.75 * f_product - f_joint` must exceed zero. H2 is an intersection union claim at the same lambda and frozen recipe: the ideal loss must favor joint by >.005 and noisy loss must favor attained product by >.005. Both decisions are required; alpha=.025 per primary decision. This preregistration does not itself imply a verdict.

## Baselines, outcomes, and thresholds

Compare attained product, strongest product CPTP bound, published hedge, frozen joint candidate, and the named product control. Same instance, source parameters, shot budget, and noise regime are paired across strategies. Loss is `f + lambda*(2-m)`. Product bounds require separately certified primal/dual values with gap <=1e-4 for every single test; report failures and do not substitute uncertified optimizer output. Lambda is selected from [.005,.01,.02,.03,.04,.06] and recipe pair using development cases only, 256 evaluations per strategy class and lambda; freeze the winner before frozen data. No reversal of direction or lambda after observing evaluation results.

## Manifests and campaign

Anchor case 0 is the mathematical check. Development IDs are 2026102900..07; frozen IDs 2026103000..23; fresh IDs 2026103100..23, with 24 held as a separately reported frozen/fresh comparison. Freeze alpha in pi/4 +/- .04 and theta in pi/8 +/- .04, using the same specified game for both tests. Fresh manifests and independent sampling seeds are supplied by a non-author verifier and are not derived from frozen recipes. Full local evaluation covers 200 count replicates per case and regime; the local channel acts on <=4-wire blocks and never forms a 16-wire density matrix. All three local models at scales .5,.75,1,1.25,1.5,1.75,2, ideal, +/-25% noise, readout .001/.005, and source imbalance are sensitivity regimes, not IonQ evidence. Cloud plan is 18 attempts: N01 smoke/100; N02 anchor/4000 aria; N03-04 anchor/1000 forte/FE; N05-08 first four frozen aria and N09-12 first four fresh aria, 4000 each. Primary family is equally weighted eight cases (32,000 games per arm, not independent instances). N13-14 are transfer; N15 order and N16 export are excluded; N17-18 are failed-case retries only. No unbudgeted trials.

## Uncertainty and multiplicity

Treat packed arm outcomes as paired: resample whole packed histograms stratified by case, preserving arm covariance and including uncertainty in the product bound. Report frozen/fresh separately and pooled only as predeclared. Use paired permutation and nested instance-count bootstrap for primary contrasts; document seeds, interval algorithm and multiplicity. A zero FF cell gets exact one-sided upper bound `1-alpha^(1/shots)`; it is never reported as zero risk. Shot-level uncertainty does not turn packed blocks into independent instances. G1/G2 are gate decisions only if both have >=80% projected development/calibration power and measured N02 4000-shot feasibility; do not reduce shots or add trials to rescue power.

## Noise assumptions and resource ledger

The local density-channel model is an IonQ-like approximation, not Qollab evidence or official calibration. Orchestrator-staged rates/hash/version must be recorded before evaluation; preliminary nominal rates are aria 1q=.0005/2q=.007, forte .000267/.0125, FE .000267/.022, readout0. Raw gate errors approximate server-compiled noise. Report submitted operation-shots separately from native gates/cost. Physical packing is a cloud/runtime concern; local simulation uses individual small blocks. Preserve source imbalance, readout sensitivity, all failures, and deviations. The quick run is anchor plus two development games, ideal and nominal aria only, <=2 replicates and tiny search; it is engineering smoke only and creates quick-prefixed outputs.

## Kill rules

Stop the claim if the product certificate is missing/infeasible or gap exceeds 1e-4; if H1 lower limit is not >0; if either H2 component fails its .005 threshold; if projected power/4000-shot feasibility gate fails; if fresh manifests are absent/invalid or tuned; or if source/noise coupling invalidates product factorization. Report negative and inconclusive results plainly. Never call local results Qollab evidence. Full campaigns require orchestrator execution; workers run only tests and quick smoke.

## Required artifact fields

Save suite/configuration, package versions, machine and UTC, generation/sample seeds, full parameters and frozen recipe, search cost, raw counts and probabilities, hashes, paired per-instance metrics, uncertainty, shots/qubits/gate accounting, failures, gate decisions and negative decisions. Checkpoints are deterministic and resumable; each output records the actual noise configuration and its origin.

## HN-2 implementation preregistration (before this revision's evidence)

This section resolves implementation choices and supersedes ambiguous wording
above. There are exactly 24 frozen and 24 fresh games, not an additional case 24.
The generation seed ranges end at 2026103023 and 2026103123 respectively.
NumPy default_rng generates alpha then theta using uniform(-.04,.04).
External games use core.make_demo(0, recipe=...), preserving its manifest and
recording a separate campaign instance_id; core's positive IDs cover only development.

No staged WORK_ORDER exists. Use the preliminary rates above, version HN-pauli-v2,
as total nonidentity Pauli error probabilities per submitted gate, not average
gate infidelities. Save actual rates and canonical hash. Source sensitivity is
an alpha shift of +/- .01 radians applied equally to both tests before core
construction. For each model additionally vary 1q and 2q rates individually by
+/-25%, and readout .001/.005. These are exploratory sensitivities.

Extract the shared core's source and verifier per-test slices for noisy CPTP
certificates; compose adjoint verifier/readout channels, in reference-tensor-prover
order. The inserted unrestricted CPTP channel upper-bounds any noisy product
channel. Same-game tests share one certificate, applied twice; use dual upper
pass probabilities for conservative tail/loss bounds, including certificate gap.
Quick uses analytical ideal certificates only, no noisy SDP.

Development search: candidate zero is the published recipe; other joint candidates
use seeded phase uniform[0,2*pi], local_phase uniform[-pi,pi], local_rotation
uniform[-pi/4,pi/4]. Score is the minimum of the three expected primary margins,
subtracting .005 for both H2 contrasts. Choose candidate then lambda by maximal
score, menu-order tie breaking. Exactly 256 evaluations/class/lambda; the exposed
product class is the identity singleton, evaluated repeatedly and explicitly
reported as such, not described as an optimized general CPTP family. Its strongest
CPTP certificate is separate. Save every candidate, score and evaluation cost.
Frozen/fresh require the hashed development selection via --recipe PATH.

Fresh schema: author, independent=true, selection_hash, manifests (24 entries).
Each entry: instance_id, generation_seed, sampling_seed, alpha, theta. Verify
parameters against the declared seed generator. Require unique IDs/seeds, the
specified fresh generation seed set, independent sampling seeds, selection hash
match. Author independence is an attestation, not something software can prove.

Full count replicates are 200 x 4000 shots per strategy/case/regime. Save every
replicate; use replicate zero for primary inference so replicates cannot inflate
the independent sample size. Bootstrap 2000 draws: resample instances then
counts from each selected instance's replicate-zero marginal histogram, keeping
the instance paired across all arms and ideal/noisy regimes. Local arm independence
is an explicit model assumption. Basic 97.5% one-sided limits; conservative exact
FF upper bounds protect zero-cell H1 and H2-ideal boundaries. Centered sign-flip
p-values are diagnostics requiring symmetric contrasts, not replacement decisions.
Cloud resampling must use whole packed keys; a separate utility preserves covariance.

Projected development power: 200 outer eight-case 4000-shot campaigns with 200
inner bootstrap draws. G1/G2 require both primary powers >=.8 and an actual
validated N02 anchor aria-1 4000-shot receipt and its source export. G2 additionally
requires an independently authored calibration-power file with both powers >=.8,
N02 receipt hash and selection hash; absent inputs yield BLOCKED, never a pass.
No cloud calls or recorded evidence are generated by the harness.

Full paths, selection, checkpoints and figures are implemented for orchestrator
execution. Resume hashes inputs, plan and code; mismatched or non-resumed existing
evidence is rejected. Quick writes only quick-n-*.json, anchor plus two development
games, ideal/nominal aria, <=2 replicates at 128 shots; no search or figures.
--draws is quick-only. No local result constitutes independent science PASS.
