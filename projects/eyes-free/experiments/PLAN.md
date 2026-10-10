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
`python experiments/run.py --suite frozen`
`python experiments/run.py --suite fresh --independent-manifest PATH`
These save counts, truth, configs, fit CIs/residuals, PCM, text, decoded estimates,
errors, abstentions, timings and seed summaries. Existing full JSON is never overwritten.
Quick command: `python experiments/run.py --quick`.

KILL/HOLD: failure of any per-cell criterion is reported as threshold failure, never repaired
by dropping records. Independent verifier and full Qollab IonQ confirmation are required
before science PASS. Scheduling, spare capacity, attempt ledger and provenance belong to
orchestrator; this package does not authorize cloud runs or submission.
