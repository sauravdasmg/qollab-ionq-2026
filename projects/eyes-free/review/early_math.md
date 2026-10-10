EARLY_GATE: HOLD

Independent WP-E-03 review, 2026-10-10 UTC. Reviewer authored none of the implementation and changed only the two requested manifests and this report. Quick checks establish correct fringe mathematics, count inference, equal-shot text comparison, and digital round-trip behavior. They do not establish the full science gate, empirical interval coverage, cloud confirmation, or browser accessibility.

## Blocking findings

1. `experiments.run.configuration` ignores `--independent-manifest` for frozen, returning hard-coded seeds and a null manifest hash. Even a nonexistent frozen manifest is accepted. For fresh, the only required JSON keys are `seeds` (the exact ordered 20-seed range) and `phase_frame` (pi/24 within 1e-12); there is no owner/count/ID validation. An in-memory manifest with owner `implementation_author`, count 1, no instances, widths [8], scales [99], and shots 1 was accepted and silently replaced by hard-coded settings. The requested manifests are internally consistent, but the harness cannot currently authenticate either complete manifest contract. Builder action: validate both suites, owner, unique IDs/seeds, count and settings, and preserve the consumed manifest hash in evidence. Reviewer did not edit the loader.
2. The plan requires numerical contrast error against exact noisy-channel truth and interval coverage. The harness stores truth width/frequency only; exact noisy probabilities are cached transiently, not saved, and contrast bias/coverage are not evaluated. Ideal reference controls and WAV-versus-fit errors do not fill that gap. Builder/orchestrator must define the contrast target when a single sinusoid is misspecified, save the reference probabilities, and report fit residuals, contrast errors and coverage before science PASS. Profile/Wald intervals are asymptotic, with physical boundaries and frequency selection; their coverage is not proved by this smoke.
3. The mandatory full frozen/fresh per-cell results and Qollab confirmation are outside this quick review. Existing `results/quick-frozen-smoke` and `results/quick-fresh-smoke` directories predated this task. They were preserved. Consequently the prescribed fresh seed range is disjoint from development, but cannot honestly be described as never previously sampled. Any claim of outcome-unseen holdout status needs the orchestrator's provenance audit; no seed was replaced after observing an outcome.

Additional runtime finding: `main.py` calls `sendFile(audio, name)` with two arguments, while the supplied binding platform document specifies `sendFile(name, content_type, data)`. The existing test mocks the two-argument form, so its PASS does not validate the documented platform interface. Verify/fix through the implementation owner before accepting the download fallback. No browser or cloud call was made here.

## Independently generated manifests

The requested paths already contained earlier manifests. They were regenerated from the plan in this review, preserving the prescribed seed ranges, not copied from measured results. Each instance spans all widths, phases and scales; it is not one width/noise block.

| Property | Frozen | Fresh |
| --- | --- | --- |
| Owner | independent_verifier | independent_verifier |
| Instances | 24 | 20 |
| Sampling seeds | 2026100500..2026100523 | 20261011500..20261011519 |
| IDs | eyes-free-frozen-01..24 | eyes-free-fresh-01..20 |
| Phase frame | 0 | pi/24 = 0.1308996938995747 |
| Generated UTC | 2026-10-10T03:26:50.068865Z | 2026-10-10T03:26:50.069488Z |

Both use widths [1,2,4], scales [0,0.5,0.75,1,1.5,2], phases 2*pi*j/12 + frame for j=0..11, and 1,000 shots per phase. All 44 IDs and sampling seeds are unique across suites and exclude development 2026100400..2026100403. The harness restarts `default_rng(seed)` at each scale: these paired settings are correlated, not extra independent instances. The manifest documents the implemented identity wire layout; no unsupported random layout variation was invented.

Loading each file through `configuration` returned the expected seeds, scales, frame and shots. Frozen returned hash `None`; fresh returned the full canonical manifest digest below. These outcomes validate compatibility, not enforcement of the metadata.

| Manifest | Canonical digest (`eyes_core.digest`) | File SHA-256 |
| --- | --- | --- |
| frozen.json | dd41699d8896339a35254f0e9c9e7c58e783f3127d438c13e5567d732992e55c | 53438b090a1cba3ee6a442a6d4a84c8510c2512170c0096f0e299a46a4159d56 |
| fresh.json | 89b26a2f42d09cedfb39527aa695a7f005b759c0fa0655c54cf4e79fbaae8b8f | 91482c10b3664cac2d7b5916489d0307a588b432ce55236190addc0472000269 |

## Mathematics and inference

RZ(phi) on every qubit changes GHZ to `(exp(-i*n*phi/2)|0...0> + exp(i*n*phi/2)|1...1>)/sqrt(2)`. Final H gates turn measured Z parity into X tensor parity. Therefore `E[(-1)^popcount] = cos(n*phi)`, with positive contrast 1, zero offset, and frequency n. At phases 0, pi/n, 2*pi/n the sign is +1,-1,+1 for each tested width. Bit order does not change total parity; packed marginal extraction still needs the little-endian layout tests.

Independent comparison of actual circuit statevectors with these analytic formulas, over both twelve-phase grids and all three widths, gave maximum absolute errors:

| Control | Analytic expectation | Maximum error |
| --- | --- | --- |
| GHZ | cos(n*phi) | 9.992007221626409e-16 |
| Product | cos(phi)^n | 1.887379141862766e-15 |
| Incoherent GHZ mixture | 0 (also for n=1 here) | 6.938893903907228e-17 |

The incoherent density result was compared with zero directly, not with `fringe()`. Product n=2 has `(1+cos(2*phi))/2`; n=4 has `(3+4*cos(2*phi)+cos(4*phi))/8`. Thus higher harmonics do not certify entanglement. Twelve equally spaced points have Nyquist frequency 6; the fitted [0.5,4.5] range includes n=4 without the integer alias n=8. This does not guarantee identifiability at low contrast.

For counts, `y = 2*k_even/m - 1`; a direct check on counts {00:10,01:20,10:30,11:40} returned (50 even,100 total), hence y=0. The fit uses binomial probabilities `(1+b0+bc*cos(f*x)+bs*sin(f*x))/2`, constrained by `abs(b0)+hypot(bc,bs)<=1-1e-8`. Reported contrast is `hypot(bc,bs)` and phase is `atan2(-bs,bc)`, consistent with `C*cos(f*x+theta)`. Frequency is profiled over the whole grid and locally refined; width is never passed into `fit_counts`. Width is used only later to score correctness.

A separate deterministic count probe used 1,000 shots/phase, x=PHASES+pi/24, f=1.73, C=0.61, offset=-0.07, phase=-0.29, and rounded even counts. It recovered:

| Quantity | Value |
| --- | --- |
| Frequency | 1.7299851317368098 |
| Contrast | 0.6098338885384493 |
| Offset | -0.07003109790550505 |
| Phase | -0.2904898724504999 |
| Frequency interval | [1.6750000000000003,1.775] |
| Contrast interval | [0.47353317608378753,0.7461625149760907] |
| Maximum parity residual | 0.0008623260243840192 |
| Informative | true |
| Samples-only decoded frequency | 1.7299851273573403 |
| Samples-only decoded contrast | 0.609833774495508 |

This noninteger probe rules out simply returning a recipe width. Uniform 500/500 counts at all phases gave contrast 0, frequency interval [0.5,4.5], contrast interval [0,0.14997788780131802], and `inconclusive`. Its arbitrary frequency estimate is not an identified frequency. Flat profile ties are numerically refined rather than returning the literal lowest grid boundary; the inconclusive flag prevents treating that number as a result.

## Baseline, decoder and main/harness agreement

Baseline and audio consume the identical fit object and sampled counts: 12,000 shots/series, zero additional quantum shots and zero resampling. Transcript JSON round-tripped exactly for all ten smoke records, including counts, intervals, diagnostics and flags. This is a strong exact-value baseline; the audio metric measures approximate transfer of frequency/contrast, not improvement over text. Encoding/decoding adds classical work; equal wall-clock compute has not been demonstrated. Semantic UI and screen-reader usability were not tested.

`decode` receives WAV bytes only and uses the public 48 kHz/16-bit/mono protocol, central samples excluding fades, an FFT peak and sinusoidal least squares. Its inferred frequency is carrier/220; contrast is twice fitted amplitude. No recipe, width, seed, truth or fit JSON enters the decoder. PCM conveys only frequency and contrast; uncertainty, phase, offset and provenance remain available through the accompanying transcript. The harness also writes clips for abstentions, whereas main's fallback selects informative estimates only; abstention clips must not be presented as confident results.

`experiments.run.evaluate` directly calls `main.analyze`; independent calls with identical first-seed counts agreed exactly for frozen and shifted fresh grids. Main's built-in path constructs the same width-major, phase-major 36 circuits; its default is 256 shots versus 1,000 in the evidence suites. Recorded cloud analysis uses the same fitter after assembling four phase-major packs. Cloud correctness and actual backend execution were not established by these local equality checks.

## Five-record smoke outcomes

Both commands completed successfully, at noise scale zero only, with five saved records each. The cap truncates after n=2 of the second seed; it is not five complete independent instances and exercises no nonzero-noise cell. The harness fits a whole three-width group before truncating stored records. `implementation_handoff_only=true`, `independent_science_pass=false`, and `cloud_confirmation=false` remain appropriate. Partial seed-summary denominators include unvisited seeds and must not be used as full-suite success estimates.

| Suite | Seed | n | Fitted frequency | Fitted contrast |
| --- | --- | --- | --- | --- |
| frozen | 2026100500 | 1 | 0.996065105476 | 0.999999990000 |
| frozen | 2026100500 | 2 | 2.000922898914 | 0.999999990000 |
| frozen | 2026100500 | 4 | 3.992739700247 | 0.998124308040 |
| frozen | 2026100501 | 1 | 0.995222324562 | 0.999999990000 |
| frozen | 2026100501 | 2 | 1.999246063296 | 0.999999990000 |
| fresh | 20261011500 | 1 | 1.017457880783 | 0.991677471963 |
| fresh | 20261011500 | 2 | 2.001376788172 | 0.996330445450 |
| fresh | 20261011500 | 4 | 3.991135890819 | 0.994938790288 |
| fresh | 20261011501 | 1 | 1.002388790170 | 0.992976112146 |
| fresh | 20261011501 | 2 | 1.996668832330 | 0.998776769739 |

All ten were informative and passed frequency identification and audio precision. Maximum audio errors were 1.5229639771519032e-08 in frequency and 4.565994844440979e-07 in contrast, below 0.02 and 0.01 respectively. Frozen harness elapsed 0.7759 s; fresh 0.7192 s (local machine only). All 19 existing focused tests passed in 2.74 s. Local versions: Qiskit 2.5.2, NumPy 2.5.3, SciPy 1.18.1.

Local ideal records are labeled `live built-in ideal` by the harness even though counts come from its NumPy/Qiskit reference sampler. This review treats them as local ideal simulations; correct that provenance label before presenting them as evidence of Qollab built-in execution.

## Reproduction

From the project directory, PowerShell:

```powershell
$py = 'D:/Quantum Projects/Qollab/.venv/Scripts/python.exe'
$env:PYTHONDONTWRITEBYTECODE='1'
& $py experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --draws 5 --output-dir results/quick-frozen-smoke-wp-e-03
& $py experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json --draws 5 --output-dir results/quick-fresh-smoke-wp-e-03
& $py -m pytest tests -q -p no:cacheprovider
```

The `-wp-e-03` suffix avoids overwriting the pre-existing smoke directories named in the work order. Only this review's two suffixed smoke directories were removed after extracting the values above. Full 24/20-seed experiments were not run. Reruns can use these now-empty output paths. Do not delete or resume someone else's results to bypass the harness's overwrite guard.

Independent math/count probe, using the same interpreter with Python stdin:

```python
import math
import numpy as np
from qiskit.quantum_info import Statevector
from eyes_core import PHASES, WIDTHS, circuit, probabilities
from fit import fit_counts
from sonify import wav_bytes
from experiments.decode import decode

errors = dict.fromkeys(('ghz', 'product', 'incoherent'), 0.0)
for n in WIDTHS:
    for x in list(PHASES) + list(PHASES + math.pi/24):
        for control in errors:
            if control == 'incoherent':
                p = probabilities(n, float(x), control=control)
                target = 0.0
            else:
                p = Statevector.from_instruction(
                    circuit(n, float(x), control, measure=False)).probabilities()
                target = math.cos(n*x) if control == 'ghz' else math.cos(x)**n
            parity = sum((-1)**k.bit_count()*v for k,v in enumerate(p))
            errors[control] = max(errors[control], abs(parity-target))
print(errors)
x = PHASES + math.pi/24
y = -0.07 + 0.61*np.cos(1.73*x - 0.29)
k = np.rint(1000*(1+y)/2).astype(int)
e = fit_counts(x, [{'00':int(a), '01':int(1000-a)} for a in k])
print({key:e[key] for key in ('frequency','contrast','offset','phase_rad',
                             'frequency_ci','contrast_ci','informative')})
print(decode(wav_bytes(e)))
z = fit_counts(PHASES, [{'0':500,'1':500}]*12)
print({key:z[key] for key in ('contrast','frequency_ci','contrast_ci','flag')})
```

Implementation SHA-256 at review:

```text
eyes_core.py         b92f04e5882046dac9ebee9ee5ef01066a4a2b48f5d2b9dea9a70307e20fe76f
fit.py               61efeea6ce61f3428efabf42da89f03ede0cc415c094733fd67bff95c9053693
main.py              c593ffe75e9b07be5e99599c74f6c64af02a6d11e14e759147fd120294e8a6ab
experiments/run.py   4765b89a59605bed4e95c0c271b572aa44cd6509c68448d6f613bf702d4782fa
experiments/decode.py 3e6596e612b10c5dbe3d3c06ad9282732031fa8fd3d13c5094fd49d2df17f631
sonify.py            02fbc7a552c44d46a4cbe24a456cc9c67879da1492cb66261d66e94039da1e19
receipt.py           e8030197aab5d90248d91e53cf4ac3d2e07f7b5d6ea6cb2995e949e3f8e1d87b
```

Orchestrator owns any global provenance/process/state updates; this work order authorizes only these three durable review files. No implementation, global documentation, full experiment or cloud receipt was altered.
