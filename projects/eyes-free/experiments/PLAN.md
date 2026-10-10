# Frozen evidence protocol (written before experiments)

Question: does WAV transmission preserve the measured frequency/contrast available in an
accessible equal-budget table/chart/transcript? This evaluates digital fidelity and frequency
inference, not learner benefit, quantum advantage, entanglement certification or physical noise.
No literature novelty or solved-limitation claim is established by this package.

Fit procedure is frozen in fit.SPEC and HELPER_SPEC.md before held-out runs. All seeds get
frequency-blind full-grid reselection; no answer read from width. Alpha=.05/6 for the three
frozen and three fresh cloud series. Contrast must exceed zero. Identified frequency requires
nearest width correct, |f_hat-n|<=.25 and entire frequency interval within n+/- .5.
All trials, including precision failures and abstentions, remain in denominators.

Baseline and candidate use identical counts, fit objects, full precision, 12*1000 shots per
series and analysis procedure. Table retains all values, units, intervals, diagnostics, flags.
Mono 48 kHz, 2 s PCM encodes 220*f Hz with peak .5*C and 50 ms fades.
Samples-only FFT/least-squares decoder cannot access recipe/counts/metadata/truth.
Digital success: |df|<=.02 and |dC|<=.01 for >=95% informative records overall AND in
EACH width/noise cell, in each suite. Inference correct >=90% informative with error<=.25,
interval criterion above, and >=80% informative availability in each cell. Uncertainty does
not excuse precision misses. Report full-denominator success and abstentions, failures and
binomial CIs at seed level. Overall correlated cells are collapsed to per-seed success flags.
Exact incoherent/product/GHZ controls expose that product harmonics are not entanglement.

Quick: one development seed 2026100400, ideal and nominal Aria, 128 shots/phase, zero
resamples; quick-* files only. No independent science PASS. Full frozen: 24 seeds
2026100500..2026100523. Fresh: independent supplied JSON manifest with seeds
20261011500..20261011519 and phase_frame=pi/24, 20 seeds. Both use scales 0,.5,.75,1,1.5,2,
1000 shots/phase, saved manifest/config hashes. Exact <=4-wire density simulation uses
calibrated Aria r1=.0005, r2=.009, readout=0, compiled rz/sx/x/rxx basis, level1 seed0;
sx/x depolarization lambda=2*r1, rxx lambda=4*r2/3, rz noiseless. Matches channel
structure of local tooling but remains explicitly a local approximation, never cloud evidence.

Full orchestrator commands:
`python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json`
`python experiments/run.py --suite fresh --independent-manifest PATH`
These save counts, truth, configs, fit CIs/residuals, PCM, text, decoded estimates,
errors, abstentions, timings and seed summaries. Existing full JSON is never overwritten.
Quick command: `python experiments/run.py --quick`.

KILL/HOLD: failure of any per-cell criterion is reported as threshold failure, never repaired
by dropping records. Independent verifier and full Qollab IonQ confirmation are required
before science PASS. Scheduling, spare capacity, attempt ledger and provenance belong to
orchestrator; this package does not authorize cloud runs or submission.

## WP-E-04 truth/coverage amendment ? 2026-10-10T03:31:54.141546+00:00

Written before new evaluation output. Frozen and fresh both require an independent
manifest; its exact file bytes are SHA-256 hashed and its validated settings consumed.
Each record saves the complete exact channel bit-string probability vectors in
little-endian integer index order, the phase grid, even probabilities and parity.
For scale zero the population frequency/contrast targets are analytically n and 1.
For nonzero scales a single sinusoid can be misspecified. Its contrast target is
hypot(bc,bs) of the constrained binomial KL projection of the exact even probabilities
onto b0+bc*cos(f*x)+bs*sin(f*x), with the frozen SPEC grid, refinement, tie rule
and physical numerical guard. Compute this deterministic projection using fractional
expected counts (1000*p_even, 1000*(1-p_even)), without sampling or rounding.
Its frequency is the pseudo-true fitted frequency; recipe frequency n remains the
physical target. Save projection coefficients, frequency, convergence and parity
residuals so model mismatch is visible. Projection intervals/flags are not evidence.

Report signed and absolute contrast error against this target, physical frequency
error against n, and frequency error against the projection. Save sampled-fit
residuals and exact-channel-versus-fitted parity residuals (vectors, RMSE, maximum).
Empirical coverage is inclusive interval containment of physical frequency n,
projection frequency and population contrast. Denominators include every record,
including abstentions. Per width/scale cells report successes, trials, fractions
and binomial CIs; overall fractions pool correlated records and have no binomial CI.
No coverage threshold was specified previously; report observed coverage at nominal
1-alpha (alpha=.05/6), including boundary/misspecification failures, without claiming
calibrated intervals. Full science PASS still requires independent verification,
full suites and Qollab confirmation. Quick truncations are partial evidence only.
Local ideal samples are labelled local ideal simulation, not live Qollab execution.


## WP-E-06 cloud slot amendment (2026-10-10T03:42:34Z)

The executable slot ledger is `cloud_slots.py`. E01 is the 19-wire asymmetric mapping smoke (100 shots); E02-E05 are frozen phase triples at k*pi/2 (1000 shots); E06-E09 are fresh triples at k*pi/2+pi/24 (1000 shots). E10 is the single representative logged-out acceptance/export pack; E11/E12 are reserved frozen/fresh repair slots. Frozen and fresh hashes are SHA-256 of the exact independent manifest bytes in `review/manifests/frozen.json` and `fresh.json`; E01 has the explicit marker `smoke-v1`. All ordinary phase packs hold nine disjoint blocks in phase-major n=1,2,4 order (21 qubits). A single slot has only three phase points, so frequency and contrast estimates are explicitly pending until all four batches of that suite have been joined; no partial fit is reported as an estimate. IonQ slot execution is one circuit, one job and one result fetch, with `aria-1` guarded by backend identity. Built-in slot execution uses the same circuit ideally.
