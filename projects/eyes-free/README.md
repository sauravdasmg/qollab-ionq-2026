# Eyes-Free Entanglement

Turn measured GHZ parity fringes into a chart, a screen-reader-ready receipt, and optional sound.
Sound encodes the fitted fringe frequency as pitch and contrast as digital amplitude.
LOCAL MODEL: the saved frozen suite preserved both values within the preregistered tolerances in 432/432 records; the fresh suite did so in 360/360.
Those are local calibrated-noise simulations, not live Qollab or device results.
**Run it (judges):** open the published JS page, choose the built-in simulator, keep defaults and press **Run**. Choose a fringe, then press **Play**; inspect its parity chart, fitted numbers in text and table, and full fit details. Browser Web Audio and speech were verified by an unrelated Qollab capability probe on 2026-10-05. WAV download requires `sendFile`; the observed Python fallback run did not receive it. The roughly one-second timing is local Python emulation, not browser loading time.
RECORDED (Qollab IonQ simulator, 2026-10-10, aria-1, 1,000 shots per phase): the frozen and fresh sweeps recovered frequencies near 1, 2, and 4 in all six fits.
Theme: Quantum Unlocked · MIT · [Repository](https://github.com/sauravdasmg/Qollab) · [Demo video]([[VIDEO LINK]])
This effort is supported by Qollab & IonQ.

## Summary

Eyes-Free makes a small quantum phase experiment easier to explore without relying on a plot alone. It prepares GHZ states of widths 1, 2, and 4, measures parity across a phase sweep, fits the fringe frequency and contrast, and presents measured parity in a chart, full fit details in text/table, and the selected informative series's frequency and contrast as optional browser sound. WAV export is conditional on `sendFile`. The audio is a designed encoding of measured data, not sound emitted by a quantum processor. Width 1 is a reference; frequency by itself does not certify entanglement.

## The problem

Quantum outputs are often shown as charts, while important details such as uncertainty, fit quality, and inconclusive status need explicit text. This project explores a practical accessible presentation for one phase-measurement example. Prior sonification work is relevant context: arXiv:2504.04624 and arXiv:2203.07879. The project does not establish how common an accessibility barrier is or whether this presentation improves learning.

## How it works

The circuit prepares a GHZ state, applies the selected phase to each qubit, rotates into the measurement basis, and measures. Twelve phase points produce parity counts. A frequency-blind binomial fit estimates frequency, contrast, phase, and offset; it reports intervals and diagnostics and can mark an estimate inconclusive. The audio maps frequency to a 220-times-frequency carrier in hertz and contrast to digital amplitude, with a short fade at both ends. Text, chart, and sound derive from the same fit object.

For an IonQ simulator run, nine small circuits are packed into disjoint blocks of one 21-qubit circuit, because the platform accepts one circuit and one job per run. A complete sweep is assembled from four phase batches. A single batch is deliberately labeled incomplete and does not claim a fitted frequency or contrast.

## Results

Evidence has two separate sources: **RECORDED** Qollab IonQ simulator counts/fits in the cloud section and **LOCAL MODEL** results from `results/frozen-evidence.json` and `results/fresh-evidence.json` in the local table. The local suites use an exact small-state simulation with an Aria-like noise approximation; they are not cloud or device data.

## Cloud evidence (RECORDED, Qollab IonQ simulator)

On 2026-10-10, slots E02-E05 ran the frozen suite and E06-E09 ran the fresh suite on IonQ Aria 1 (effective noise model `aria-1`), at 1,000 shots per phase point. Each four-slot suite combined to 12 phase points for each GHZ width. E01 was a 100-shot smoke run and is not part of either fit. The fitted cloud outcomes (frequency; contrast) were:

| Suite | Slots | Width 1 | Width 2 | Width 4 |
| --- | --- | --- | --- | --- |
| Frozen | E02-E05 | 0.992; 1.000 | 1.999; 0.989 | 3.998; 0.951 |
| Fresh | E06-E09 | 0.997; 0.991 | 1.997; 0.986 | 4.005; 0.955 |

To reproduce a recorded batch, use the Python variant of this project (the same files with `main.py` as the entry point, `uploads/eyes-free.zip` in the repository): select **IonQ Aria 1**, set **Slot=E02** (or the listed slot) and **Shots=1,000**, then run; repeat the four slots in the suite to reconstruct its sweep. The published JS page does not run slots; its optional **Run one packed IonQ sample** button (shown only on the IonQ simulator, Aria 1 noise model) submits one 128-shot packed job at three phases and reports a whole-register parity sample, not a fitted fringe. The original count records are in `recorded_ionq.py`; the fitted counts, intervals, and analysis are in `results/cloud_fit.json` and the compact evidence index is `evidence_summary.json`. The original Qollab console exports are retained in `results/exports/`.

Deviation: the initial combined-fit analysis sliced packed counts incorrectly. The cloud records themselves are valid; the indexing was corrected before the reported fit was produced. E01 is smoke-only and excluded. No cloud slot was superseded.

### Evidence files in this project

`evidence_summary.json` is a compact mixed evidence index of LOCAL MODEL suites and RECORDED cloud fits; `recorded_ionq.py` contains the recorded Qollab IonQ simulator runs. Regenerate the summary from the full files in `results/` with `python experiments/make_summary.py`.

| Suite | Seeded instances | Informative records | Audio agrees with fitted frequency and contrast | Frequency identified | Evidence label |
| --- | ---: | ---: | ---: | ---: | --- |
| Frozen | 24 | 432 | 432/432 | 432/432 | LOCAL MODEL |
| Fresh | 20 | 360 | 360/360 | 360/360 | LOCAL MODEL |

The audio agreement thresholds were absolute frequency error at most 0.02 and contrast error at most 0.01. Identification required the fitted value to be within 0.25 of the recipe frequency and its interval to lie within half a frequency unit of that value. These counts are records nested within seeded instances; they are not independent cloud runs. Per-cell summaries and intervals are in the JSON evidence files. They describe this model and these samples, not guaranteed future performance. Sampling noise can move a fitted point or interval across a decision bound, especially near a boundary; inconclusive records must remain visible.

**Figure (conceptual flow; alt text):** measured phase and parity counts → frequency/contrast fit with uncertainty → chart, text receipt, and WAV. Alt text: “One measured result object feeds three presentations with different information: chart for phase/parity, text/table for the full fit, sound for frequency/contrast; audio carries the fitted frequency and contrast.” The JS chart shows the measured parity points with pointwise 95% Wilson error bars, the fitted curve and a data table of the same points; fit intervals for frequency and contrast are in the results table. `figures.py` supplies the Python fallback chart with frequency/contrast/status in its legend, without intervals; the durable result files currently provide tables and machine-readable evidence rather than a static chart image.

**RECORDED (Qollab IonQ simulator, 2026-10-10, aria-1, 1,000 shots):** frozen and fresh 12-phase sweeps recovered frequencies near 1, 2, and 4; all six fits completed. 

## How to run (and replicate)

### Published JS page and Python fallback

For the published JS page, use the instructions above. For the Python fallback, open the project in Qollab, select the built-in simulator, leave the default `shots=256` and other settings unchanged, then press **Run**. The Python fallback default submits 36 small GHZ circuits, forming three fitted width series (256 shots each; 9,216 circuit shots) and displays the live ideal chart, text output, and WAV/text downloads when the platform supplies its download function. Measured local Python emulation runtime: about 1 s; browser loading time was not measured. Do not select a credits-based QPU for this walkthrough.

### IonQ simulator slots

For a cloud simulator run, use the Python variant (`main.py` entry point), choose an available IonQ simulator in Qollab and use the fixed settings shown by the slot selector. Each slot submits one packed circuit and one job; the complete frozen or fresh sweep requires its four preregistered phase batches. One partial batch is not a complete fit. Paste each console `RECORD_JSON` line into `recorded_ionq.py` as described in that file, preserving the original record. Cloud results remain marked RECORDED with date, model, and shots. Results: 2026-10-10, aria-1, 1,000 shots per phase point; fits are shown in the cloud evidence table above.

### Local reproduction

From the project directory, use a Python environment with Qiskit 2.x, NumPy, SciPy, and Matplotlib installed:

```powershell
python experiments/run.py --quick --output-dir results/reproduce-quick
python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --output-dir results/reproduce-frozen
python experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json --output-dir results/reproduce-fresh
```

The full commands generate local simulation evidence and can take longer; they do not submit cloud jobs. Each run writes JSON evidence, text receipts, and WAV files in its specified output directory. Use a new directory for each rerun; `--resume` is only for continuing an existing matching run. `experiments/` and `review/manifests/` are repository files, not part of the flattened Qollab upload. Add `--draws 1` to either full command for a bounded command check; partial evidence is not a full reproduction. To inspect the live Qollab integration, run `main.py` through Qollab rather than invoking it as a standalone script.

### Replicate and extend

To replicate the local evidence, run `python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --output-dir results/reproduce-frozen` (use the separate fresh command above for the fresh suite). To extend it, add more GHZ widths or another sonification mapping in `sonify.py`, keeping the text/table alternative for every sound.

## What is new

The contribution is a compact educational presentation that keeps a measured fit and its uncertainty in semantic text/table, with phase/parity in the chart and selected frequency/contrast in sound, plus a samples-only WAV round-trip measurement. It is an engineering and accessibility exploration, not a new quantum algorithm. Prior quantum sonification is acknowledged above; no claim is made that a complete novelty search proves this approach unique.

## Limits

- No quantum speedup, learner benefit, usability study, or general claim about accessibility prevalence is shown.
- Local noise is an approximation, not an IonQ simulator measurement or physical device model.
- The pre-window Qollab capability probe verified Web Audio and speech. Saved numerical evidence does not establish this final page's browser, screen-reader, keyboard or download acceptance. The observed Python fallback reports `sendFile` unavailable; browser playback is the audio path, and WAV export remains conditional.
- Frequency alone is not an entanglement witness: product states can show harmonics. Contrast is not a unique estimate of physical noise or GHZ fidelity.
- The comparison is a digital transfer check against the same fitted values exposed by an equal-information table/text path; the parity chart shows pointwise error bars and the fitted curve, while fit intervals are in the table; it does not show that sound is more accurate or useful than text.
- The fit intervals are model-based and their empirical coverage here is descriptive, not a calibration guarantee. Negative or inconclusive outcomes should be retained.
- Recorded cloud fits are close to the intended frequencies; these are simulator results, not device results or a user study.

## Judging criteria

- **Novelty and creativity:** makes one measured quantum result available through synchronized visual, textual, and sound encodings; related quantum sonification exists, so the claim is a focused presentation contribution.
- **Technical execution:** combines Qiskit circuits, packed cloud batches, binomial fitting, uncertainty reporting, and sample-only WAV decoding. The local evidence is explicitly bounded to the calibrated noise approximation.
- **Impact potential:** offers an inspectable path for exploring phase fringes when audio or screen-reader workflows are useful. Real user impact remains unmeasured.
- **Documentation quality:** includes reproduction commands, source evidence files, accessible text alternatives, provenance distinctions, and explicit limitations.

## Accessibility

The semantic text receipt is the primary nonvisual route and includes values, units, intervals, fit diagnostics, and inconclusive flags. The chart has labeled axes and corresponding phase/parity values in the receipt. Audio is optional, never autoplayed, and can be stopped; begin at a comfortable low volume. Keep keyboard focus visible and controls keyboard-operable in the Qollab page. Screen-reader announcements should identify pending, error, and completed states. Provide captions or a transcript for spoken demo narration. Browser and assistive-technology behavior still requires direct acceptance review; this documentation does not claim that such review has occurred.

## Disclosure

- **AI tools:** AgentMesh routing used OpenCode free models and OpenAI Codex models, and Claude Code (Anthropic) orchestrated the work, fixed defects and ran independent verification; per-task use is recorded in the repository provenance log. The demo-video voiceover is AI-generated with Microsoft neural text-to-speech (voice en-US-AndrewNeural, via the open-source edge-tts tool). No AI-generated result is treated as experimental evidence.
- **Code written in the hackathon window:** the Eyes-Free Python modules, evidence harness, and project-specific text were created during the authorized build window. No implementation from the unrelated “JS audio probe (test)” was reused; that probe only checked platform capabilities before the window.
- **Shared packing helper:** `circuit_pack.py` is a packing helper written during the hackathon build window (Oct 9-11, 2026). It packs several small circuits onto disjoint qubits of one circuit for Qollab's one-job-per-run IonQ interface and splits the measured counts back per block. Each of our entries (Entanglement Court, The Noise Tax, Eyes-Free) ships its own version of this helper with the same purpose; the files differ in detail. Eyes-Free's version is specific to its phase-major GHZ batches. GHZ phase recipes, frequency-blind fitting, browser audio/speech, receipts, UI, and evidence/decoder protocol are specific to Eyes-Free.
- **Libraries and licences:** Qiskit 2.x (Apache-2.0), NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), Matplotlib (PSF-based licence), and Python standard library. No qiskit-aer is used. See each library’s distribution for full licence text.
- **Platform materials:** Qollab runtime documentation and hackathon rules informed the integration; no Qollab project template code is claimed as reused.

**Theme:** Quantum Unlocked  
**Repository:** https://github.com/sauravdasmg/Qollab  
**Demo video:** [[VIDEO LINK]]  
**Licence:** MIT (see `LICENSE`).  
This effort is supported by Qollab & IonQ.

### Publication and provenance

Publish `web/index.html`, `web/main.js`, `web/main.css` and `web/eyes_bridge.py` flattened to the Qollab top level, together with their top-level Python dependencies and compact evidence files. Keep `main.py` as the documented Python fallback. The JS page fits both embedded RECORDED cloud sweeps; LOCAL MODEL catalog entries are illustrative references, not new acquisitions. The page's LOCAL MODEL entries are analytic references built from the simple formula parity = exp(-0.025 × scale × n) × cos(n × phase) (scale 0, 0.5, 1, 2); they are not the calibrated LOCAL MODEL suites reported above, and their contrast values differ from those suites. Playback encodes selected frequency and contrast, not uncertainty or fit status; text/table retain those details. WAV download works only where `sendFile` is supplied, otherwise the page explicitly reports it unavailable.

The summary reports its UTC generation date, machine/platform and Python/Qiskit/NumPy versions separately from original local acquisition metadata. Original evidence retains Qiskit/NumPy/SciPy versions and all settings. Its original host identifier, Python version and precise acquisition clock were not captured; source-file last-modified timestamps supply a labeled date basis, not invented acquisition timestamps. Historical G1 FAIL and independent/cloud-false flags describe the earlier local generation stage and remain unchanged. Recorded cloud fits are later evidence; no new independent PASS is asserted by this repair.
