# Entanglement Court

Entanglement Court turns a subtle quantum question into a courtroom challenge: can measurements distinguish entanglement when two preparations look identical in the computational basis?

**Key result (LOCAL MODEL):** over 24 frozen and 20 fresh cases, graph certification was 0.50/0.50 in ideal simulation and 0.42/0.43 in an aria-like local approximation. Product and biseparable controls had zero false certificates in the recorded local campaign summary. The two-color comparator is the same witness implementation and ties by construction.

**Run it (judges): Built-in simulator, default settings, press Run, about [[CLOUD: measured live built-in runtime will go here]] s; then inspect the matched Z histograms and conditional witness receipt.**

## The problem

A graph-state witness can support a claim of genuine multipartite entanglement, but finite measurements are uncertain. A point estimate alone can make evidence look stronger than it is. Entanglement Court pairs a graph state with a separable product state that has the same ideal Z-basis distribution. The Z exhibit alone therefore cannot decide the case. The scientific context includes finite-copy entanglement-witness work, doi:10.1038/s41534-024-00810-3.

## How it works

The program prepares a four-qubit connected graph state and a separable equatorial product state. Both have uniform ideal Z probabilities, with exact total-variation distance zero. It shows the sampled Z histograms, then measures stabilizer parities in two coloring bases. A simultaneous confidence receipt combines parity lower bounds into a conservative fidelity lower bound. It reports a graph-state entanglement certificate only when the lower bound is above 1/2.

Every successful receipt states its assumptions. Cloud inference is conditional on trusted measurement rotations and readout unless a justified error bound is supplied. An inconclusive receipt is not evidence that the state is separable. A finite sample can cross a theoretical bound through sampling variation; the intervals show that uncertainty.

## Results

| Measure | Evidence label | Finding |
|---|---|---|
| Graph certification, frozen / fresh cases | LOCAL MODEL | Ideal simulation: 0.50 / 0.50; aria-like approximation: 0.42 / 0.43. |
| Product and biseparable controls | LOCAL MODEL | Zero false certificates reported in the provenance summary. |
| Two-color comparison | LOCAL MODEL | Same witness implementation as the simultaneous generator method; the methods tie. |
| IonQ simulator subset | RECORDED | [[CLOUD: actual run date, model, shots, and subset findings will go here]] |

![Frozen cases.](figures/frozen.png)

*Alt text: Frozen-case chart showing easier cases certify more often than cases near the witness threshold.*

![Fresh cases.](figures/fresh.png)

*Alt text: Fresh-case chart summarizing certification across newly generated cases and difficulty strata.*

![Interactive exhibit.](figures/development.png)

*Alt text: A sample courtroom display with paired Z histograms, parity intervals, and a witness-bound panel.*

## How to run (and replicate)

**Judging run:** select Qollab's Built-in simulator, keep the default form settings, and press Run. Check the paired Z exhibits and whether the finite-shot witness receipt is conditional or inconclusive. The live runtime will be recorded here: [[CLOUD: built-in run duration in seconds]].

**IonQ simulator:** cloud subset outcomes remain pending: [[CLOUD: actual dates, noise model, shots, and results]]. For a recorded run, select the IonQ simulator and follow the preregistered slot instructions. A cloud result must be labeled RECORDED with its run date, noise model, and shot count.

**Local reproduction commands** (commands only; their output is not asserted here):

```powershell
..\..\.venv\Scripts\python.exe experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --draws 1000 --output-dir results/frozen-reproduction
..\..\.venv\Scripts\python.exe experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json --draws 1000 --output-dir results/fresh-reproduction
```

The local IonQ-like noise model is an approximation and is not hardware or Qollab cloud evidence.

**Evidence files in this project:** `evidence_summary.json` contains compact LOCAL MODEL statistics and source hashes; `recorded_ionq.py` holds the Qollab IonQ runs. Regenerate the summary with `python experiments/make_summary.py`.

### Replicate and extend

To replicate the local evidence, run `python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json` (and `--suite fresh` with `fresh.json`) from the repository. To extend it, add new graph/product preparations in `cases.py` or new witness terms in `witness.py`, then add matching independent manifests.

## What is new

The original educational contribution is a preregistered adversarial exhibit: a connected graph-state preparation and a known separable preparation share the same ideal Z distribution, then face a stabilizer challenge and finite-copy receipt. The witness mathematics is established; no speedup or stronger-baseline advantage is claimed.

## Limits

This project does not show a quantum speedup. It does not show that its witness beats a stronger baseline: the comparator is the same witness measured two ways. Local noise results are approximate, and cloud conclusions depend on trusted measurement assumptions. Near-threshold cases can be inconclusive. Zero observed control failures in a finite sample is not a zero-risk guarantee; per-round error control is not campaign-wide control.

## Judging criteria

- **Novelty and creativity:** turns matched preparations and witness assumptions into an adversarial courtroom interaction; novelty is in the teaching artifact and case set, not the witness theorem.
- **Technical execution:** count-based stabilizer measurements, finite-sample bounds, and packed execution for the IonQ one-circuit job limit.
- **Impact potential:** helps learners understand why observed distributions and uncertainty assumptions matter in entanglement claims.
- **Documentation quality:** supplies run steps, labeled evidence, figures with alt text, reproduction commands, disclosures, and explicit limits.

## Accessibility

The web interface is keyboard-operable and uses text and symbols alongside high-contrast color. Exhibit data and status are available as text for screen readers. Audio is not needed for interaction; captions should accompany any video narration.

## Disclosure and submission details

AI tools: AgentMesh routing to OpenCode free models, OpenAI Codex models, and Claude Code. The shared `circuit_pack.py` and `receipt.py` helpers were written during Oct 9–11, 2026 and are also used by Two Whispers Make a Word and Never Lose Twice; the project-specific physics and presentation are distinct. Libraries: Qiskit 2.x (Apache-2.0), NumPy and SciPy (BSD-3-Clause), Matplotlib (PSF-based license). Qollab runtime documentation and hackathon rules informed the implementation; no Qollab starter template or outside project code is represented as original work.

**Theme tag:** Quantum Unlocked  
**License:** MIT ([LICENSE](LICENSE))

This effort is supported by Qollab & IonQ.

**Repository:** https://github.com/sauravdasmg/Qollab  
**Video:** [[VIDEO LINK]]
