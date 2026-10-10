G1 REVIEW: HARNESS BUG

The noisy G1 evidence is invalid because the density evaluator uses the wrong global and local qubit ordering. Its zero-noise limit does not reproduce the actual circuits. This verdict does not establish a science PASS: the untuned collective and textbook circuits are identical, so the required H2 synthesis improvement is absent independently of this bug.

Review performed independently with small computations only: cases 0 and 1, nine-block exact statevectors, case-0 small-block density simulations, and the requested main.py local Aria run at 1,000 shots. No full campaign or synthesis search was run. Only this report was written. Local emulator evidence is not Qollab cloud confirmation.

## 1. Physics and zero-noise sanity

The Statevector branch reproduces the supplied analytical probabilities to floating-point precision:

| Case | Collective success | Textbook success | Sequential success |
|---|---:|---:|---:|
| 0 | 0.9714045207910319 | 0.9714045207910319 | 0.9330127018922206 |
| 1 | 0.9714045207910317 | 0.9714045207910317 | 0.9330127018922202 |

These equal `1/2+sqrt(2)/3` and `1/2+sqrt(3)/4`. Every source label individually attains the corresponding success. The terminal receiver rotations and decoder are therefore consistent on these anchor/development checks (`core.py:185`, `core.py:189`, `core.py:190`, `core.py:197`, `core.py:276`).

However, `_density_probabilities(circuit, 'aria', 0)` fails spectacularly on the same case-0 circuits:

| Sent label | Joint density success at scale 0 | Sequential density success at scale 0 |
|---|---:|---:|
| 0 | 0.512472096 | 0.516202468 |
| 1 | 0.354732151 | 0.540429791 |
| 2 | 0.105104946 | 0.123792461 |

Joint mean is 0.324103064 and sequential mean is 0.393474907. Maximum individual outcome-probability discrepancy from Statevector is 0.866299575 for both cases 0 and 1. The ideal campaign branch bypasses this faulty evaluator (`experiments/run.py:130`), explaining why ideal results look correct while all nominal noisy regimes fail.

**Root cause:** Qiskit indexes computational states as `q0 + 2*q1 + ...`; an operation's first qarg is its least significant local bit. The embedding at `experiments/run.py:104-110` instead treats both the first global qubit and first local qarg as most significant. For a CX, this reverses the matrix's local control/target interpretation as well as the global indexing. Reversing output strings alone cannot fix it. The Pauli embedding at `experiments/noise.py:48` also treats q0 as the leftmost tensor factor.

An independent zero-noise evaluator using `DensityMatrix.evolve(Operator(op), qargs=actual_qarg_indices)` agrees with Statevector on every case-0 block: maximum probability difference below 5.0e-16.

## 2. Case-0 Aria comparison, block by block

Command: `../../.venv/Scripts/python.exe -B ../../tools/qollab_local.py run . --backend ionq-aria --shots 1000` (default seed 1234, default case 0, no frozen recipe). It completed in 76.96 seconds. An additional in-memory run using Aer's matrix-product-state method completed in 2.33 seconds and returned the same decoded block successes. No source file was changed for that check.

The exact local-emulator probabilities below come from independently transpiling each small block with the runner's basis, optimization level 1 and seed 1234, then applying its Aer density-matrix noise model. Gate counts are for that compilation, not IonQ's server compiler. Each joint block has **3 rxx gates**; each sequential block has **13 rxx gates**. Joint sx counts are 14, 15, 15 across labels; sequential blocks have 47 sx and 1 x each.

| Block | Family | Label | Harness Aria scale 1 success | Exact emulator success | main.py success (1,000 shots) |
|---|---|---:|---:|---:|---:|
| 0 | collective | 0 | 0.512553 | 0.949691 | 0.950 |
| 1 | textbook | 0 | 0.512553 | 0.949691 | 0.950 |
| 2 | sequential | 0 | 0.527323 | 0.867843 | 0.873 |
| 3 | collective | 1 | 0.349224 | 0.938303 | 0.924 |
| 4 | textbook | 1 | 0.349224 | 0.938303 | 0.939 |
| 5 | sequential | 1 | 0.490279 | 0.828094 | 0.844 |
| 6 | collective | 2 | 0.114405 | 0.937905 | 0.935 |
| 7 | textbook | 2 | 0.114405 | 0.937905 | 0.941 |
| 8 | sequential | 2 | 0.145824 | 0.844908 | 0.860 |

main.py agrees with the exact emulator within sampling error (largest absolute standardized residual approximately 1.88 binomial standard deviations). The harness clearly does not agree.

Exact emulator mean joint error is **0.058033807**, sequential error **0.153051633**. main.py reports collective error **0.063667**, textbook **0.056667**, sequential **0.141000**. An error near 0.13 is plausible for this expensive sequential implementation; it is not the observed joint error on case 0. Three Aria entanglers with r_2q=0.009, plus about 15 noisy single-qubit operations, give a modest loss from the ideal joint error 0.028595, consistent with the exact value near 0.058.

The supplied negative H1 lower bound must not be inverted to infer joint error: it is a confidence lower bound, and the current harness subtracts a noisy sequential error. In `results/development.json`, nominal Aria mean errors actually are collective **0.722083333**, textbook **0.733333333**, sequential **0.739791667**; H1 mean is positive **0.017708333**, despite lower bound **-0.078881441**. These large errors are consistent with broken zero-noise evolution, not a modest physical degradation.

## 3. Additional model/baseline defects

* **Mismatched H1 baseline.** `experiments/run.py:274` uses the noisy deferred-sequential implementation from the same regime. The requested H1 and `experiments/PLAN.md` require the ideal one-way bound, error `1-core.P_SEQ = 0.0669872981`. A noisy, 13-entangler implementation is not that bound. Even a repaired channel cannot make the current H1 estimand the requested one.
* **Noise model mismatch.** `experiments/noise.py:4-8` uses preliminary Aria 2q=.007, Forte=.0125, FE=.022, whereas `../../tools/ionq_noise_params.json` has .009, .012, .021. The harness applies independent single-qubit Pauli errors to every rx/ry/rz and each leg of CX (`experiments/run.py:113-116`). The runner recompiles to rz/sx/x/rxx or rzz, leaves rz noiseless, applies a joint two-qubit depolarizing channel to the entangler, and converts infidelity to lambda (`../../tools/qollab_local.py:85-91`, `../../tools/qollab_local.py:123`). They are different channels, even after endian repair.
* **Source-noise flag is ineffective.** `core.py:192-195` already decomposes StatePreparation into rotations. Thus the exclusion of operations named state_preparation/initialize at `experiments/run.py:113` never excludes those source gates. The saved configuration uses source_noise=True; this flag defect does not cause that run's endian failure, but invalidates a claimed ideal-source rerun with the flag disabled.
* **No synthesized realization was evaluated.** The saved recipe is null and configuration recipe_file is null. Both joint families use the same default receiver and compilation (`core.py:185`, `core.py:152`). No tuned winner or equal-budget search evidence is present in this development result.

No missing terminal basis rotation or decoder bug was found in the checked ideal circuits. Packed marginal extraction uses the correct integer right shift and mask (`circuit_pack.py:227-233`), and main.py's block agreement supports its ordering. Noise is applied once per operation in the harness; no duplicate noise pass was found. Its over/differently applied gate noise is a model mismatch, not two passes through the same model.

## 4. H2 interpretation and exact fixes

H1 and H2 signs are correct for error reduction. H2 is **0.9*e_textbook - e_joint**, not merely the difference between equivalent errors (`experiments/run.py:275`). If the realizations tie, H2 equals **-0.1*e**, so ideal H2 is exactly **-0.002859548** before sampling. A negative ideal lower bound (-0.014440409 in the saved campaign) is expected. Do not change the 0.9 factor or reverse the sign to obtain a pass. Under the exact local case-0 Aria model, untuned H2 is **-0.005803381**. The required synthesis payoff is genuinely absent in this untuned comparison.

Required implementation fixes, without changing preregistered thresholds:

1. Replace the manual embedding with Qiskit's DensityMatrix evolution using actual qarg indices. Alternatively fix all four integer expressions to `bits[j]=(col>>j)&1`, `local_in=sum(bits[q]<<k for k,q in enumerate(qubits))`, `new_bits[q]=(out>>k)&1`, `row=sum(bit<<j for j,bit in enumerate(new_bits))`. Change Pauli tensor placement to `factors[n-1-q]` if retaining that helper with Qiskit qubit indices. Require noisy-branch scale-zero distributions to match Statevector, including asymmetric and nonadjacent-qarg circuits.
2. For emulator agreement, compile to the exact model basis and seed/optimization settings used by qollab_local, load its calibrated parameter JSON, and use its lambda conversion and **joint** two-qubit depolarizing channel. Apply single-qubit error only on sx/x and readout once. Prefer reusing the runner's model on small-block density simulations rather than maintaining a second implementation.
3. Set H1's per-instance differences to `(1-core.P_SEQ)-e['collective']` for the requested ideal-source bound. Keep measured noisy sequential performance as a separate descriptive comparator. Preserve source/receiver boundaries to make source-noise selection work; if noisy sources are included, label the ideal-source bound conditional and do not claim an unconditional source-dependent certification.
4. Preserve H2 as written. Stage genuinely development-selected, equal-budget recipes before evaluating a synthesis claim. Recreate affected evidence under a new path/configuration after orchestrator-authorized full runs; do not reinterpret or overwrite this faulty campaign as valid evidence.

Repair is necessary but does not guarantee G1 will pass. Case-0 exact emulator H1 against the ideal sequential bound is **0.008953491**, already below the +0.010 point threshold, and H2 remains negative. Full seeded uncertainty analysis and cloud confirmation remain outstanding; this small review cannot decide the repaired campaign's outcome.
