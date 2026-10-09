# Preregistered local evidence plan

## Scope and hypothesis

Entanglement Court uses matched four-qubit graph and equatorial-product preparations, computational-Z controls, and a simultaneous stabilizer witness. The hypothesis is that the graph preparation can be certified above the connected-graph biseparable overlap threshold with useful frequency at the declared shot budgets, while known product controls are not falsely certified. The certificate is conditional on trusted rotations and readout unless explicit bounded-bias assumptions are supplied. This is a local simulator study, not evidence of hardware performance.

## Baselines and metric

The strongest equal-budget baseline is the predeclared two-color witness using the same marginal counts and shots as the simultaneous witness. Also report the exact statevector/density-matrix reference, Z-distribution total variation, and the known product/separable controls; these are mathematical controls, not competing shot-efficient algorithms. Primary metric: fraction of graph instances receiving a conditional GME certificate. Companion metrics: false certificates among known separable controls, inconclusive rate, paired difference from the two-color baseline, and runtime/resource accounting. Local 100-shot target is at least 80% easy-case certification; 60–79% is an honest threshold miss and below 60% kills the claim. The 200-shot cloud development projection target is 80%.

## Inputs and manifests

Development IDs/seeds are 2026100100–2026100103. Frozen campaign IDs/seeds are 2026100200–2026100223: first 12 easy, next 12 near-threshold. Fresh independent IDs/seeds are 20261011000–20261011019: first 10 easy and last 10 near-threshold; fresh manifests and sampling seeds must be generated and held by a nonauthor verifier, with no tuning. Freeze human-readable labels, full parameters, recipes and hashes before sampling. The current shared factory exposes only its four development cases; it does not itself implement or validate the frozen/fresh campaigns. Do not represent development cases as frozen or fresh. Blocked campaign execution until the complete signed manifests are staged and independently checked.

## Sampling, uncertainty and multiplicity

Full campaign: 24 frozen plus 20 fresh paired local instances. Every case/noise configuration receives at least 1000 independent multinomial draws, with separable and known-biseparable controls. Preserve within-shot and packed-run correlations when resampling. Report empirical binomial intervals and paired same-draw witness comparisons. Per-round alpha is .05, Bonferroni allocated as .00625 per generator for n=4 (and split over two preparations as implemented by the core); this is not campaign-wide familywise control. A campaign-wide claim requires a new allocation and power analysis. Report the full simultaneous coverage event, not only marginal coverage. Uniform Z TV targets are at most 1e-12; stabilizer expectations at most 1e-10. Investigate false certificates under actual declared assumptions and binomial uncertainty; a possible tail event alone does not refute a theorem.

## Noise and resource assumptions

Study ideal plus local small-block density-channel approximations at scales .5, .75, 1, 1.25, 1.5, 1.75 and 2, with measurement-bias sensitivity. Cross-check four-wire exact statevector and density-matrix results. Rates are preliminary approximations, not official calibration: aria 1q=.0005/2q=.007; forte .000267/.0125; forte-enterprise .000267/.022; readout 0. The local raw gate errors approximate server-compiled noise and omit compilation/device effects. Distinguish submitted operation-shots from native gates and cost. Local noise evidence must be labeled “local IonQ-like approximation,” never Qollab evidence. Only actual Qollab receipts count as Qollab simulator evidence.

## Campaign and stop rules

The harness's full runs are orchestrator-only. Cloud plan: C01 smoke 100 shots; C02–13 frozen seeds 2026100200–05 and 2026100212–17; C14–25 fresh seeds 20261011000–05 and 20261011010–15, 200 shots each on aria; C26 export 200 excluded; C27–30 exact failed retries only. Require at least 8/12 easy cloud targets, at least 4/6 frozen and 4/6 fresh, and no certified known-separable impostor without independent hold/review. Retain every inconclusive and near-threshold outcome. Twenty-four cloud pairs are subset confirmations, not 44 local instances or a measured 5% guarantee. Keep trusted-measurement conditional scope adjacent to each verdict; witness baselines may tie. The audited 16-wire fallback does not split jobs; exact Z references retain a distinct label.

Kill or pause the claim for local easy certification below 60%, a product-control certificate, broken exact references, invalid manifests, or missing data integrity. Treat 60–79% as an explicit target miss. No result can be promoted to a science pass by this harness; independent verification and Qollab confirmation remain required.

## Resource ledger and saved evidence

Quick mode is development-only: exactly two paired development inputs, at most 10 draws each, ideal and nominal aria only, separate `quick-*` output, no suite, sweep, fresh evaluation, or full-evidence overwrite. Full local campaign is owned by the orchestrator. Save configs, software versions, machine and UTC, generation/sample seeds, full parameters, recipe/search cost, raw counts/probabilities, hashes, per-instance paired outcomes, uncertainty, shot/qubit/gate accounting, failures and negative decisions. Resume only from deterministic validated checkpoints. Cloud console exports stay in `results/exports/`; receipts must not be synthesized by this harness.
