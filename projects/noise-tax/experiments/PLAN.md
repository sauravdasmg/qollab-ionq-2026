# The Noise Tax prospective follow-up freeze

The full plan is `research/plans/noise-tax.md` in the parent repository. This
is the prospective follow-up to failed historical W/N hypotheses, not their
original preregistration. Full runs belong to the orchestrator. This worker
runs only tests, two-case endpoint `--quick`, and the requested G1 smoke.

Primary W: A(s) = ideal one-way word error - equally weighted mean joint word
error. Fixed textbook square-root recipe, complete decoder including outcome
3 assigned label 0. One-way reference is analytic optimal sequential performance
on ideal product sources; primary noise includes source preparation. This does
not certify the best one-way receiver on the noisy ensemble, all LOCC, or a
classical communication advantage. Both arms use two copies and equal priors.

Primary N: A(s) = mean attained-product loss - published-hedge loss, with
loss = FF + 0.02*(2 - mean passes). Same alpha/theta for the two tests, independent
source pairs, strategy only on prover wires 2,3. Acceptance requires decoded
00 on reference/prover pairs (0,2) and (1,3); every FF/FP/PF/PP retained. Product
is a quantum identity-channel recipe with a per-instance ideal CPTP certificate,
not a globally optimal noisy product channel. Neither arm receives tuning.

For each primary Aria-calibrated curve, require positive at 0, negative at 2,
one persistent interior zero, and resolved 97.5% simultaneous-band interval.
Forte and Forte Enterprise are descriptive replications, never replacement
primaries. Grid frozen/fresh: k/40, k=0..80. G1 pilot: k/4, k=0..8. Quick:
two pilot cases per game, endpoints 0 and 2 only. Diagnostic standard W frame
and N analytic anchor are separate, never included among the 24.

Instance construction is NumPy default_rng/PCG64. W common Haar SU(2) frame:
complex Gaussian QR, normalize diagonal R phases then determinant to one.
N: independently uniform alpha in pi/4 +/-0.04, theta in pi/8 +/-0.04.

| Suite | W construction seeds | N construction seeds | sampling base |
| --- | --- | --- | --- |
| development pilot | 2026104500..2026104523 | 2026104600..2026104623 | 2026104700 |
| frozen | 2026104000..2026104023 | 2026104200..2026104223 | 2026104800 |
| fresh independent | 2026104100..2026104123 | 2026104300..2026104323 | 2026104900 |

Shot sampling uses SeedSequence([base, game index, construction seed, model
index, scale index, arm index]); streams independent of construction RNG.
W budgets 1000 words per label/arm; N 4000 games/arm/scale/instance. Save all
probabilities and synthetic counts. These counts are not additional instances.
W one-way probabilities are ideal-source reference, never passed through noise.

ONE shared channel reads ../../tools/ionq_noise_params.json once and hashes
the exact bytes, with a byte-identical top-level snapshot for Qollab uploads.
Aria r1/r2/readout = 0.0005/0.009/0; Forte = 0.000267/0.012/0;
FE = 0.000267/0.021/0. Compile each small block before noise, opt=1,
compiler seed 1234, model JSON basis. Noise follows sx/x and declared rxx/rzz;
rz virtual. Joint depolarization lambda = r*s/(1-1/d), no clipping. Full-source
primary applies to both games. Source/strategy/verifier barriers prevent fusion
between physical stages and are audited after compilation. Individual blocks
only, never a packed cloud circuit in the density harness. Local pulse costs
and population calibration approximate remote IonQ noise; FE undocumented.

Whole paired curves (all arms/outcomes/scales of each instance) resampled 4000
times. Analysis seeds W 2026104401, N 2026104402 (fresh uses same analysis
procedure and seeds on independent instances). Max absolute deviation gives
97.5% simultaneous bands per primary; Bonferroni nominal >=95% family coverage
under bootstrap assumptions. Invert bands, retain disjoint feasible sets, hull
expanded outward to grid brackets. Grid uncertainty is 0.025 in fine suites.
First persistent root is first after which mean never returns positive to 2;
all roots displayed, multiple roots fail single-threshold presentation. No
monotonic smoothing. Unresolved/boundary/nonunique/constant/censored curves
remain explicit, including every bootstrap draw's status. No conditional finite
root percentile estimate. Calibration uncertainty is excluded. Cloud models
are discrete anchors; do not fit a cloud noise-scale crossing.

G1: all quick identity/bit-order/projector/legal-wire/channel/trace checks;
24-case coarse Aria pilot endpoints and persistent bracket with paired
uncertainty, recorded receipt import, short default startup. Small draws are
smoke only and cannot pass an evidence gate. G2: both 24-case fine Aria curves
resolve unique interior crossings; finite CI width <=0.30. G3: independent
fresh manifest/24-case fine run; frozen/fresh estimates must independently
resolve and agree within absolute 0.10 and their combined interval bounds;
independent reviewer must reproduce. No self-certification. Missing crossing,
endpoint reversal, legality, shared channel, capacity or review -> HOLD/KILL;
negative results retained. Local PASS is not a final gate/reviewer decision.

Commands (repository Python):

    python experiments/run.py --quick
    python experiments/run.py --suite development --gate g1 --draws 5 --output-dir results/quick-g1-smoke
    python experiments/run.py --suite frozen --gate g2 --resume
    python experiments/run.py --suite fresh --independent-manifest --resume

`--independent-manifest [PATH]`: on fresh, freeze independent seed specifications
before running, or validate/load supplied frozen fresh manifest. It does not
claim independent human/model verification. All manifests/hashes are written
before any new numerical output, and resumes reject mismatched configurations.
Progress includes ETA; atomic checkpoint per instance/model plus per-scale
progress enables interrupted runs to resume. Optional sensitivities are deferred
and must never replace the primary. UI, publication/video, and science gates
remain orchestrator-owned.
