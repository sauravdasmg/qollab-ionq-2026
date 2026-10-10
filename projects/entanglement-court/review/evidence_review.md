EVIDENCE REVIEW: HOLD

Independent, bounded review of saved evidence and current implementation. No experiments, sweeps, cloud jobs, or full test suites were run. Only this report was written. Local mathematics and saved campaign summaries support the scoped educational claim; mandatory cloud subset confirmation is absent. This is not submission readiness approval.

## 1. Ideal near-threshold abstention is expected

“Ideal” disables the additional IonQ-like channel, not the preparation noise declared in the manifest. The frozen-before-sampling definition is independent per-wire phase flips after preparation, with easy p in [0,.015) and near-threshold p in [.12,.13). The population generator witness is 1-4p, close to .5; true graph fidelity is (1-p)^4 and remains above .5. These are population-witness strata, not finite-shot power promises (review/manifests/frozen.json:6; review/manifests/frozen.json:7; review/manifests/fresh.json:7; review/early_math.md:20; ../../research/plans/entanglement-court.md:25).

The current implementation applies the declared channel exactly once at experiments/run.py:174, before the additional model channels at experiments/run.py:175 and basis rotations at experiments/run.py:180. Its per-wire channel is (1-p)rho+p ZrhoZ (experiments/noise.py:52). For these graph stabilizers, mu_i=1-2p. The witness remains F_lower=1-sum(1-L_i)/2, with a strict F_lower>.5 test (witness.py:22; witness.py:23). There is no evidence of double-applied preparation noise, an incorrect threshold, or mislabeled strata.

Quick deterministic recomputation of one easy and one near-threshold manifest from each suite reproduced the independent phase-mask mixture reference: maximum distribution error 3.89e-16 and mean error 8.88e-16. Frozen near case 2026100212 gives means .751383173780334, matching 1-2p, rather than the earlier defective value 1. Across all saved cases, the maximum deviation from 1-2p is 1.22e-15; maximum saved independent distribution discrepancy is 5.00e-16. Reference construction is at experiments/run.py:249, experiments/run.py:258 and experiments/run.py:276; the representative saved near references are results/frozen.json:98145 and results/fresh.json:81845.

| Suite | Actual near p range | Population generator witness range | True graph fidelity range |
|---|---|---|---|
| Frozen | .1206988504–.1282422367 | .4870310532–.5172045985 | .5775416302–.5977926402 |
| Fresh | .1201150574–.1297175838 | .4811296646–.5195397705 | .5736418598–.5993817880 |

At 100 shots, even four representative 87/100 or 88/100 parity-success counts give F_lower=.0573095964 or .1060688323 with alpha_i=.00625. Finite-shot bounds readily make the witness inconclusive despite entanglement. Zero observed near-threshold certificates is therefore plausible and expected; it is not a claim that their certification probability is identically zero. Frozen and fresh both record 0/12,000 and 0/10,000 ideal near-threshold certificates, respectively, versus all easy draws certified. The original noise-implementation HOLD is repaired on these checks; its historical manifest status remains at review/manifests/frozen.json:8.

## 2. Comparator equality and scientific gate

Equality is built into the implementation: two_color_witness directly calls simultaneous_witness (witness.py:26), and analyze_counts supplies the same target parities and alpha to both (cases.py:45; cases.py:49). All 2,904 saved case/configuration/control rows have identical certificate counts and zero paired difference. This is an implementation identity, not evidence of algorithmic superiority or an independently implemented baseline.

Recomputed descriptive graph certification rates from saved certificate counts:

| Configuration | Frozen, all cases | Fresh, all cases | Frozen easy | Fresh easy |
|---|---:|---:|---:|---:|
| Ideal | .500000 | .500000 | 1.000000 | 1.000000 |
| aria@1 | .417333 | .427700 | .834667 | .855400 |
| forte@1 | .149250 | .155050 | .298500 | .310100 |
| forte-enterprise@1 | .002583 | .002550 | .005167 | .005100 |

Near-threshold rates are zero for every configuration in this table. Aggregation inputs start at results/frozen.json:251 and results/fresh.json:251; suite sizes and overall ideal means are results/frozen.json:195664 and results/fresh.json:163060. Each suite contains 22 configurations per case, 1,000 draws per configuration, and 100 shots per block (results/frozen.json:195613; results/frozen.json:195657; results/fresh.json:163013; results/fresh.json:163053).

The honest claim is the preregistered matched-Z adversarial corpus, measured additional-basis evidence, valid per-round simultaneous confidence, and clear conditional certificates/abstentions. The research plan explicitly permits tied witnesses and disclaims a better theorem or superiority over a sound witness (../../research/plans/entanglement-court.md:19; :23; :31). Computational-Z guessing is an educational foil. The implemented comparator is the same generator witness measured in two colors; it does not independently test a distinct color-projector witness. Calling it the “strongest” baseline without qualification is unsupported (experiments/PLAN.md:9).

Local power and impostor audit checks support proceeding: nominal aria easy rates exceed 80%, and all saved product and biseparable target false-certificate counts are zero. Each control has 528,000 frozen and 440,000 fresh rounds across configurations. This does not establish zero underlying false-certification probability or exhaustive adversarial soundness. Product-impostor intervals are included in coverage, but the saved certificate counters concern the chosen target control; they are not separate cloud impostor audits (experiments/run.py:342; experiments/run.py:348).

**The requested >=4/6 frozen cloud gate cannot pass from these files.** Only C01 is present, so verified frozen-subset evidence is 0/6 available easy receipts, not six observed failures. The plan requires C02–C13 at 200 shots and at least 4/6 frozen plus 4/6 fresh easy targets, at least 8/12 combined, with an impostor audit (../../research/plans/entanglement-court.md:70; :72; :74). Its schedule calls local coverage/power G2 and frozen cloud confirmation G3 (same plan:137; :142; :174). Under either gate naming, local evidence does not satisfy the cloud requirement. results/g1.json:9 reports development-only projection 1.0, and results/g1.json:13 explicitly names development; it cannot substitute for frozen cloud data. recorded_ionq.py:2 is still empty.

## 3. Coverage covers both preparations, with sampling qualifications

The repaired event is the conjunction of eight lower-bound coverage indicators from the same round: four target and four product-impostor intervals, aligned by generator ID (experiments/run.py:306; :309; :315; :318; :355; :357). It no longer checks only the target. CP uses alpha=.05/(2*4)=.00625 per interval (witness.py:4; :9; :14). For IID shots with fixed parity probabilities and trusted stated measurements, each marginal failure probability is at most .00625; the union bound gives at least .95 simultaneous coverage. It requires no independence between generators or preparations and gives no campaign-wide .95 event.

| Target control | Frozen covered/rounds | Frozen descriptive coverage | Fresh covered/rounds | Fresh descriptive coverage |
|---|---|---:|---|---:|
| Graph plus product impostor | 509508/528000 | .964977 | 424600/440000 | .965000 |
| Product plus product impostor | 503514/528000 | .953625 | 419866/440000 | .954241 |
| Biseparable plus product impostor | 503582/528000 | .953754 | 419817/440000 | .954130 |

These pooled rates exceed .95. They do **not** mean every empirical cell achieves .95: below-.95 cells number 21/141/145 frozen and 20/107/99 fresh, respectively for graph/product/biseparable. Frozen product case 2026100203 at aria@1.5 has 929/1000 coverage, exact 95% binomial interval [.911386,.943330] (results/frozen.json:26559). Fresh graph case 20261011018 at forte-enterprise@.5 has 936/1000, interval [.919099,.949564] (results/fresh.json:152373). Across 2,904 cells, 14 unadjusted cell intervals have upper endpoints below .95. Such isolated findings among many comparisons do not independently refute coverage; no multiplicity-adjusted global rejection was established here. Show the individual intervals and negative cells instead of claiming every observed cell passes 95%.

The pooled table is descriptive. Random streams are derived from the same case seed across configurations (experiments/run.py:339); configurations and controls should not be treated as independent replications for a pooled binomial confidence interval. Mathematical CP/union-bound validity, not pooled sample size, supplies the per-round guarantee. Measurement systematic errors remain outside that guarantee unless explicitly bounded.

## 4. C01 reproduces, but confirms only the development smoke

Source: results/exports/C01-2026-10-09T23-58-48Z-ionq-aria1.html:1 (the export is one line). It records ionq_simulator, aria-1, Qiskit 2.5.2, 100 packed shots, development case 0 / seed 2026100100, preparation p=0, and job 01a1231a-ba7a-7cbe-a546-e1572f835c77. Its own assumptions say the anchor is not the prescribed campaign.

Independently decoded raw 24-bit counts reproduce every saved marginal exactly; each marginal totals 100. Target generator IDs 0,2,1,3 give successes 100,99,98,100 and parities 1.00,.98,.96,1.00. Reanalysis gives conditional F_lower=.7445653814>.5. Product successes are 48,49,52,49, with F_lower=-1.5285857519 and no certificate. The trust flag is false, so the certificate remains conditional on ideal/trusted rotations and readout; systematic error is unbounded.

This agrees with strong easy-anchor signal and does not conflict with abstention for different, preparation-noisy near-threshold cases. The local aria approximation predicts C01 means .957483,.936907,.936907,.957483; the cloud smoke appears cleaner. One sample cannot validate the approximation or transfer its atlas to cloud. C01 has neither the frozen manifest nor the 200-shot budget required for the cloud gate, and does not validate arbitrary frozen frames or noise recipes.

## Exact fixes and remaining evidence

1. Keep the frozen/fresh manifests, p ranges, and all near-threshold negative outcomes unchanged. Explain “ideal backend with declared preparation phase noise,” population-witness threshold versus true fidelity, and finite-shot abstention beside reported rates. Do not tune strata after seeing results.
2. Label the comparator as the identical two-color implementation of the generator witness, show its formula, threshold and interval widths, and remove any superiority or unqualified strongest-baseline claim. A distinct color-projector comparison requires a separately specified and audited implementation before claiming such a comparison.
3. Publish the eight-interval coverage definition, per-cell intervals, below-.95 cells and descriptive pooled rates. Do not claim empirical >=95% in every cell, campaign-wide 95% control, or zero underlying false-positive risk.
4. Retain original C01 as a smoke receipt. Obtain the already planned C02–C13 frozen and C14–C25 fresh 200-shot aria-1 exports within the orchestrator's account ledger, preserving all outcomes and retries. For every receipt audit manifest identity, preparation-noise realization, frame/basis correction, packed counts, both preparations' witnesses, assumptions and provenance. If the declared noisy manifest cannot actually be realized on cloud, hold the gate and resolve that mismatch explicitly; a clean case must not silently stand in for it. Then verify >=4/6 frozen, >=4/6 fresh and >=8/12 total easy certificates plus the impostor audit. Populate shipped recorded evidence only from original records.
5. Saved local aggregate files omit per-draw counts: experiments/run.py:353 appends them and :368 removes them. Preserve draw-level outcomes/counts or a separately hashed replay record as required by experiments/PLAN.md:31 and the research plan:41, and have the orchestrator commission independent fresh-stream reproduction. This review checks saved counts, manifest/hash agreement and four deterministic density references; it does not reproduce the full campaigns or independently approve browser/readiness claims.

Data identity checks passed for every stored case: saved manifests and hashes equal the independent manifest entries, sampling seeds match, and all rows have the stated draw/shot budgets. Reviewed SHA-256: results/frozen.json = 548677ec1476f70f83f4a33112fb2d2a0afd25fcff746821bcf1a06df48400e9; results/fresh.json = f240500074d21aaa0fceb9a4a9c22a2a3dfb2d62d8582bc69bc1daf946f4d2dc. HOLD is for absent decisive cloud/replay evidence, not the expected near-threshold abstention or comparator tie.
