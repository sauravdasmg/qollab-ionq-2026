# Eyes-Free Entanglement

## Evidence files in this project

`evidence_summary.json` is the compact LOCAL MODEL summary of the saved local results; `recorded_ionq.py` contains the recorded Qollab IonQ simulator runs. Regenerate the summary from the full files in `results/` with `python experiments/make_summary.py`.

Explore a measured GHZ parity fringe as a chart, a screen-reader-ready receipt, and optional sound. Pitch encodes fitted frequency; digital amplitude encodes contrast.

**Key local result:** in the LOCAL MODEL frozen suite, audio preserved the fitted frequency and contrast within the stated tolerances for 432/432 records; in the fresh suite, 360/360. These are calibrated IonQ-like simulations, not cloud or device results.

**Run it (judges):** select the built-in simulator, keep defaults, press **Run**, about [[CLOUD: measured built-in default runtime in seconds]]; then inspect the parity chart, text receipt, and WAV download.

**RECORDED (Qollab IonQ simulator):** [[CLOUD: date, effective noise model, shots, and result summary]].  
Theme: **Quantum Unlocked** · [Repository](https://github.com/sauravdasmg/Qollab) · [Video]([[VIDEO LINK]])

## Summary

Eyes-Free teaches phase-dependent parity measurements with a compact GHZ example. It makes the same fitted frequency, contrast, uncertainty, and fit status available visually, in structured text, and as a sound mapping. The sound is generated from measured data; it is not acoustic emission from qubits. No sound starts automatically.

## The problem

Charts alone can make it harder to inspect exact values, uncertainty, or inconclusive results in a nonvisual workflow. This project builds an accessible result presentation for one quantum experiment, without claiming the barrier is universal or that learning improves. Related quantum sonification work includes arXiv:2504.04624 and arXiv:2203.07879.

## How it works

Prepare GHZ states with widths 1, 2, and 4; apply a shared phase; measure parity at twelve phase points; fit frequency and contrast without giving the fitting procedure the width label. The fit also retains phase, offset, intervals, and diagnostics. The sound uses a 220-times-frequency carrier and an amplitude proportional to contrast, with fades at the clip edges. A table/transcript, plot, and audio use the same fit data.

IonQ simulator mode packs nine small circuits into disjoint blocks of a 21-qubit circuit. Each cloud job covers three phase points; four batches are needed for a full sweep. Partial data are labeled pending rather than shown as a fitted answer.

## Results

All numbers in this table are **LOCAL MODEL** results from saved evidence JSON; they are not live Qollab measurements. Full details, cell breakdowns, and uncertainty summaries are in `results/frozen-evidence.json` and `results/fresh-evidence.json`.

| Local suite | Seeded instances | Records | Digital audio fidelity | Frequency identified |
| --- | ---: | ---: | ---: | ---: |
| Frozen | 24 | 432 | 432/432 | 432/432 |
| Fresh | 20 | 360 | 360/360 | 360/360 |

Audio fidelity means frequency error no greater than 0.02 and contrast error no greater than 0.01 against the values used to generate the audio. Frequency identification uses a 0.25 error bound plus an interval criterion; per-cell definitions and counts are in the evidence files. Records within a suite share seeded simulation settings and are not independent cloud trials. Sampling noise may shift estimates or confidence bounds across a threshold; inconclusive results remain results and are not silently removed.

**Figure / alt text:** Data-flow figure: phase/parity counts → fitted result and uncertainty → chart, receipt, WAV. Alt text: “The three outputs are generated from one measured fit, with audio encoding frequency and contrast.” `figures.py` creates the live chart; the evidence files contain data tables rather than a saved standalone figure.

**Cloud evidence:** [[CLOUD: completed Qollab IonQ simulator date, noise model, shots, and measured results]].

## How to run (and replicate)

**Built-in:** Open in Qollab, choose its built-in simulator, leave `shots=256` and all other defaults unchanged, and press **Run**. Inspect the ideal parity chart, text receipt, and WAV download if `sendFile` is available. Runtime: [[CLOUD: measured built-in default runtime in seconds]]. The built-in simulator is the judges’ required run path.

**IonQ simulator:** choose an IonQ noise-model simulator, select a fixed slot, and run one slot per Qollab Run. Preserve the printed record and enter each `RECORD_JSON` line in the top-level `recorded_ionq.py`. Four phase batches make one complete sweep; do not interpret an incomplete batch as a frequency estimate. Recorded facts will be labeled with acquisition date, effective noise model, and shots: [[CLOUD: record details]].

**Local reproduction** (local simulation only):

```powershell
python experiments/run.py --quick
python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json
python experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json
```

### Replicate and extend

To replicate the local evidence, run `python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json` (and `--suite fresh`). To extend it, add more GHZ widths or another sonification mapping in `sonify.py`, keeping the text/table alternative for every sound.

## What is new

This entry joins an uncertainty-aware measured fringe with three equivalent ways to inspect it, including a WAV round-trip check that decodes from samples alone. It is an educational presentation and measurement exercise, not a new quantum algorithm. Prior sonification examples are acknowledged; uniqueness is not claimed as established.

## Limits

No speedup, learner benefit, human usability result, physical device claim, or validated noise estimate is shown. The local IonQ-like noise model is an approximation. A product-state fringe can contain harmonics, so frequency alone does not prove entanglement; contrast is not GHZ fidelity. The comparator exposes the same fitted information in chart and structured text. Audio is checked for digital fidelity, not for being better than text or perceptually equivalent to it. Confidence-interval coverage is descriptive and may be sensitive to model mismatch and sampling. The local simulation is not cloud confirmation.

## Judging criteria summary

- **Novelty and creativity:** links measured phase data to optional sound while keeping uncertainty and a complete text path; adjacent sonification prior art exists.
- **Technical execution:** Qiskit GHZ measurements, one-circuit cloud packing, constrained binomial fit, structured receipts, and a samples-only audio decoder.
- **Impact potential:** could make this example easier to explore in audio and screen-reader workflows; impact on learners has not been measured.
- **Documentation quality:** evidence files, commands, data labels, figure alternative text, and scope limits support inspection and reproduction.

## Accessibility

Use keyboard-operable controls with visible focus, readable contrast, semantic headings and tables, and screen-reader announcements for pending, error, and completed states. Keep audio user-triggered and provide Stop plus a text equivalent. Chart axes are labeled; the receipt lists the underlying phase/parity values. Demo narration should have captions or a transcript. Actual browser and assistive-technology behavior remains to be confirmed.

## Disclosure

AI assistance is routed through AgentMesh using OpenCode free models and OpenAI Codex models; Claude Code is named as a reserve in project instructions. Consult the provenance log for task-specific records. Project-specific Python implementation, experiment harness, and copy were created within the build window. The unrelated pre-window “JS audio probe (test)” was only a platform capability check; its code and text were not reused.

`circuit_pack.py` is the shared phase-major packing and marginal-count helper, created during the window and shared with related entries. Circuit recipes, fitting, sonification, receipts, and evidence protocol are Eyes-Free-specific. Libraries: Qiskit 2.x (Apache-2.0), NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), Matplotlib (PSF-based licence), and Python standard library. No Aer. Qollab runtime documentation and hackathon rules were consulted; no Qollab template code is claimed as reused.

**Theme tag:** Quantum Unlocked  
**MIT licence:** included as `LICENSE`  
**Repository:** https://github.com/sauravdasmg/Qollab  
**Demo video:** [[VIDEO LINK]]  
This effort is supported by Qollab & IonQ.
