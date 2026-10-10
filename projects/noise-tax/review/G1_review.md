G1 REVIEW: HOLD

## Findings

- The ideal endpoint identity is correct for both games. At scale 0, direct density-matrix probabilities matched `Statevector` probabilities in little-endian order for the checked W joint-receiver labels and both N arms (maximum absolute discrepancies 8.9e-16 or less). The depolarizing conversion also matches the stated average-infidelity formula, `lambda = r*s/(1-1/d)`, and the frozen JSON rates/bases: Aria `(0.0005, 0.009, rz/sx/x/rxx)`, Forte `(0.000267, 0.012, rz/sx/x/rzz)`, and Forte Enterprise `(0.000267, 0.021, rz/sx/x/rzz)`. Readout is zero in this calibration. The implementation inserts channels after compiled `sx/x` and declared entanglers, leaves `rz` noiseless, and honors source-stage noise; this agrees with the gate/readout channel structure in `tools/qollab_local.py`. Local model is appropriately described as an approximation, not the remote simulator's pulse model.

- The advantage definitions in `experiments/PLAN.md` match the code: W uses ideal one-way word error minus joint word error; N uses attained-product loss minus hedge loss with the fixed 0.02 prize and all four joint outcomes. The recorded-anchor figures cited by the orchestrator match the imports. At scale 1, the computed advantages are W: Aria +0.00889, Forte +0.00465, FE -0.01719; N: Aria -0.01203, Forte -0.01641, FE -0.03292. The qualitative comparisons are consistent with the recorded cloud points; cloud and local executions are not paired, so these are only pointwise consistency checks, not validation of a shared noise distribution.

- Coarse crossover point estimates and outward grid brackets reproduce: W Aria 1.309 [1.25, 1.50], Forte 1.141 [1.00, 1.25], FE 0.684 [0.50, 0.75]; N Aria 0.427 [0.00, 0.75], Forte 0.352 [0.00, 0.75], FE 0.208 [0.00, 0.50]. The N intervals fail the planned width <=0.30 target, as the result file correctly records.

## Blocking issue: W uncertainty is degenerate

All 24 W instances have identical curves to floating-point precision: the reported bootstrap band radii are only 7.6e-17 to 8.3e-17, and all 4,000 resamples produce effectively the same root. Consequently the reported W intervals are only outward-rounded grid brackets; the `confidence_interval` label suggests statistical uncertainty that the paired-instance bootstrap did not estimate. This may reflect a genuine frame covariance of the chosen game and effective channel, but the current analysis has not established that those 24 instances support uncertainty inference. Before treating W as evidence, diagnose the invariance and revise the estimand/uncertainty design (or report the crossing as deterministic for the specified model and frame family, without claiming a sampling CI). G1 should remain HOLD pending this resolution and independent reproduction.

## N precision grid recommendation

Use the preregistered fine grid exactly: `s_k = k/40` for integer `k = 0, 1, ..., 80`, i.e. 81 points from 0 through 2 inclusive at increments of 0.025. Keep the current coarse grid results as pilot outputs; do not infer that the fine grid itself fixes N's statistical width target. On the current bootstrap radii, the uncertainty band, not just grid spacing, may dominate the interval. Recompute with the frozen inference procedure and preserve the explicit unmet-target status if width remains above 0.30.

## Reuse disclosure

`reuse_sources.json` gives source paths, hashes, transformation destinations and import timestamps, and `_reuse.py` documents transformations. I could not find the requested `REUSE_MANIFEST.md` in this submission folder. The recorded reuse appears traceable at a machine level, but the named disclosure input is absent; add/restore it before submission so reused algorithms, references and adaptations are plainly disclosed to reviewers.
