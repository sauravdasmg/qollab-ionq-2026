# Eyes-Free Entanglement

Turn measured GHZ parity fringes into a chart, a screen-reader-ready receipt, and optional sound.
Sound encodes the fitted fringe frequency as pitch and contrast as digital amplitude.
LOCAL MODEL: the saved frozen suite preserved both values within the preregistered tolerances in 432/432 records; the fresh suite did so in 360/360.
Those are local calibrated-noise simulations, not live Qollab or device results.
**Run it (judges):** choose the built-in simulator, keep default settings, press **Run**, about [[CLOUD: measured built-in default runtime in seconds]]; then check the parity chart, text receipt, and WAV download.
RECORDED (Qollab IonQ simulator): [[CLOUD: date, effective noise model, shots, and measured result summary]].
Theme: Quantum Unlocked · MIT · [Repository](https://github.com/sauravdasmg/Qollab) · [Demo video]([[VIDEO LINK]])
This effort is supported by Qollab & IonQ.

## Summary

Eyes-Free makes a small quantum phase experiment easier to explore without relying on a plot alone. It prepares GHZ states of widths 1, 2, and 4, measures parity across a phase sweep, fits the fringe frequency and contrast, and presents the same fit in a chart, a detailed text receipt, and downloadable WAV audio. The audio is a designed encoding of measured data, not sound emitted by a quantum processor. Width 1 is a reference; frequency by itself does not certify entanglement.

## The problem

Quantum outputs are often shown as charts, while important details such as uncertainty, fit quality, and inconclusive status need explicit text. This project explores a practical accessible presentation for one phase-measurement example. Prior sonification work is relevant context: arXiv:2504.04624 and arXiv:2203.07879. The project does not establish how common an accessibility barrier is or whether this presentation improves learning.

## How it works

The circuit prepares a GHZ state, applies the selected phase to each qubit, rotates into the measurement basis, and measures. Twelve phase points produce parity counts. A frequency-blind binomial fit estimates frequency, contrast, phase, and offset; it reports intervals and diagnostics and can mark an estimate inconclusive. The audio maps frequency to a 220-times-frequency carrier in hertz and contrast to digital amplitude, with a short fade at both ends. Text, chart, and sound derive from the same fit object.

For an IonQ simulator run, nine small circuits are packed into disjoint blocks of one 21-qubit circuit, because the platform accepts one circuit and one job per run. A complete sweep is assembled from four phase batches. A single batch is deliberately labeled incomplete and does not claim a fitted frequency or contrast.

## Results

Evidence files: `results/frozen-evidence.json` and `results/fresh-evidence.json`. Every value below is **LOCAL MODEL** evidence from an exact small-state simulation with a calibrated Aria-like noise approximation. It is not Qollab execution or device data.

| Suite | Seeded instances | Informative records | Audio agrees with fitted frequency and contrast | Frequency identified | Evidence label |
| --- | ---: | ---: | ---: | ---: | --- |
| Frozen | 24 | 432 | 432/432 | 432/432 | LOCAL MODEL |
| Fresh | 20 | 360 | 360/360 | 360/360 | LOCAL MODEL |

The audio agreement thresholds were absolute frequency error at most 0.02 and contrast error at most 0.01. Identification required the fitted value to be within 0.25 of the recipe frequency and its interval to lie within half a frequency unit of that value. These counts are records nested within seeded instances; they are not independent cloud runs. Per-cell summaries and intervals are in the JSON evidence files. They describe this model and these samples, not guaranteed future performance. Sampling noise can move a fitted point or interval across a decision bound, especially near a boundary; inconclusive records must remain visible.

**Figure (conceptual flow; alt text):** measured phase and parity counts → frequency/contrast fit with uncertainty → chart, text receipt, and WAV. Alt text: “One measured result object feeds three equivalent presentations; audio carries the fitted frequency and contrast.” The live chart is produced by `figures.py` during a run; the durable result files currently provide tables and machine-readable evidence rather than a static chart image.

**RECORDED (Qollab IonQ simulator):** [[CLOUD: date, noise model, shot count, complete sweep outcome, and any failed or inconclusive records]]. Cloud values are pending and are not inferred from local simulations.

## Run it yourself

### Built-in simulator

Open the project in Qollab, select the built-in simulator, leave the default `shots=256` and other settings unchanged, then press **Run**. The default run analyzes three small GHZ circuits and displays the live ideal chart, text output, and WAV/text downloads when the platform supplies its download function. Expected default runtime: [[CLOUD: measured built-in default runtime in seconds]]. Do not select a credits-based QPU for this walkthrough.

### IonQ simulator slots

For a cloud simulator run, choose an available IonQ simulator in Qollab and use the fixed settings shown by the slot selector. Each slot submits one packed circuit and one job; the complete frozen or fresh sweep requires its four preregistered phase batches. One partial batch is not a complete fit. Paste each console `RECORD_JSON` line into `recorded_ionq.py` as described in that file, preserving the original record. Cloud results remain marked RECORDED with date, model, and shots. Results: [[CLOUD: final Qollab IonQ simulator result and provenance]].

### Local reproduction

From the project directory, use a Python environment with Qiskit 2.x, NumPy, SciPy, and Matplotlib installed:

```powershell
python experiments/run.py --quick
python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json
python experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json
```

The full commands generate local simulation evidence and can take longer; they do not submit cloud jobs. Each run writes JSON evidence, text receipts, and WAV files under `results/`. To inspect the live Qollab integration, run `main.py` through Qollab rather than invoking it as a standalone script.

## What is new

The contribution is a compact educational presentation that keeps a measured fit and its uncertainty available in chart, semantic text, and sound, plus a samples-only WAV round-trip measurement. It is an engineering and accessibility exploration, not a new quantum algorithm. Prior quantum sonification is acknowledged above; no claim is made that a complete novelty search proves this approach unique.

## Limits

- No quantum speedup, learner benefit, usability study, or general claim about accessibility prevalence is shown.
- Local noise is an approximation, not an IonQ simulator measurement or physical device model.
- The saved numerical evidence does not establish real browser screen-reader, keyboard, audio playback, or download behavior. Check these in Qollab.
- Frequency alone is not an entanglement witness: product states can show harmonics. Contrast is not a unique estimate of physical noise or GHZ fidelity.
- The comparison is a digital transfer check against the same fitted values exposed by an equal-information table/chart/text path; it does not show that sound is more accurate or useful than text.
- The fit intervals are model-based and their empirical coverage here is descriptive, not a calibration guarantee. Negative or inconclusive outcomes should be retained.
- Cloud confirmation is pending: [[CLOUD: measured results and limitations from the completed Qollab IonQ simulator runs]].

## Judging criteria

- **Novelty and creativity:** makes one measured quantum result available through synchronized visual, textual, and sound encodings; related quantum sonification exists, so the claim is a focused presentation contribution.
- **Technical execution:** combines Qiskit circuits, packed cloud batches, binomial fitting, uncertainty reporting, and sample-only WAV decoding. The local evidence is explicitly bounded to the calibrated noise approximation.
- **Impact potential:** offers an inspectable path for exploring phase fringes when audio or screen-reader workflows are useful. Real user impact remains unmeasured.
- **Documentation quality:** includes reproduction commands, source evidence files, accessible text alternatives, provenance distinctions, and explicit limitations.

## Accessibility

The semantic text receipt is the primary nonvisual route and includes values, units, intervals, fit diagnostics, and inconclusive flags. The chart has labeled axes and corresponding phase/parity values in the receipt. Audio is optional, never autoplayed, and can be stopped; begin at a comfortable low volume. Keep keyboard focus visible and controls keyboard-operable in the Qollab page. Screen-reader announcements should identify pending, error, and completed states. Provide captions or a transcript for spoken demo narration. Browser and assistive-technology behavior still requires direct acceptance review; this documentation does not claim that such review has occurred.

## Disclosure

- **AI tools:** AgentMesh routing used OpenCode free models and OpenAI Codex models; Claude Code is listed as a possible reserve in the shared project instructions. Actual per-task use should be recorded in the provenance log. No AI-generated result is treated as experimental evidence.
- **Code written in the hackathon window:** the Eyes-Free Python modules, evidence harness, and project-specific text were created during the authorized build window. No implementation from the unrelated “JS audio probe (test)” was reused; that probe only checked platform capabilities before the window.
- **Shared packing helper:** `circuit_pack.py` is the project’s phase-major disjoint-wire packing and count-marginalization helper, written during the build window and shared with the related hackathon entries. Eyes-Free-specific circuit, fitting, audio, receipt, and experiment code is described above.
- **Libraries and licences:** Qiskit 2.x (Apache-2.0), NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), Matplotlib (PSF-based licence), and Python standard library. No qiskit-aer is used. See each library’s distribution for full licence text.
- **Platform materials:** Qollab runtime documentation and hackathon rules informed the integration; no Qollab project template code is claimed as reused.

**Theme:** Quantum Unlocked  
**Repository:** https://github.com/sauravdasmg/Qollab  
**Demo video:** [[VIDEO LINK]]  
**Licence:** MIT (see `LICENSE`).  
This effort is supported by Qollab & IonQ.
