# Eyes-Free Entanglement

Explore a measured GHZ parity fringe as a chart, a screen-reader-ready receipt, and optional sound. Pitch encodes fitted frequency; digital amplitude encodes contrast.

**Key local result:** in the LOCAL MODEL frozen suite, audio preserved the fitted frequency and contrast within the stated tolerances for 432/432 records; in the fresh suite, 360/360. These are calibrated IonQ-like simulations, not cloud or device results.

**Run it (judges):** open the published JS page, select the built-in simulator, keep defaults and press **Run**. Choose a fringe and press **Play**; inspect the parity chart, fitted numbers in text and table, and full fit details. Web Audio and speech were verified on Qollab in an unrelated capability probe on 2026-10-05. WAV download requires `sendFile`; the observed Python fallback had no download bridge. About one second is a local Python emulation timing, not browser loading time.

**RECORDED (Qollab IonQ simulator, 2026-10-10, aria-1, 1,000 shots per phase):** frozen and fresh sweeps recovered frequencies near 1, 2, and 4 in all six fits.  
Theme: **Quantum Unlocked** · [Repository](https://github.com/sauravdasmg/Qollab) · [Video]([[VIDEO LINK]])

## Summary

Eyes-Free teaches phase-dependent parity measurements with a compact GHZ example. The JS page shows the same fitted frequency and contrast in text and table, with intervals, provenance and diagnostics in full fit details. Its chart shows measured phase/parity without fit intervals. Optional sound encodes only frequency and contrast of the selected informative series; speech reads its summary. Illustrative LOCAL MODEL references are explicitly labeled and are not measured fits. The sound is generated from measured data; it is not acoustic emission from qubits. No sound starts automatically.

## The problem

Charts alone can make it harder to inspect exact values, uncertainty, or inconclusive results in a nonvisual workflow. This project builds an accessible result presentation for one quantum experiment, without claiming the barrier is universal or that learning improves. Related quantum sonification work includes arXiv:2504.04624 and arXiv:2203.07879.

## How it works

Prepare GHZ states with widths 1, 2, and 4; apply a shared phase; measure parity at twelve phase points; fit frequency and contrast without giving the fitting procedure the width label. The fit also retains phase, offset, intervals, and diagnostics. The sound uses a 220-times-frequency carrier and an amplitude proportional to contrast, with fades at the clip edges. A table/transcript, plot, and audio use the same fit data.

IonQ simulator mode packs nine small circuits into disjoint blocks of a 21-qubit circuit. Each cloud job covers three phase points; four batches are needed for a full sweep. Partial data are labeled pending rather than shown as a fitted answer.

## Cloud evidence (RECORDED, Qollab IonQ simulator)

On 2026-10-10, slots E02-E05 ran the frozen suite and E06-E09 ran the fresh suite on IonQ Aria 1 (effective noise model `aria-1`), at 1,000 shots per phase point. Each four-slot suite combined to 12 phase points for each GHZ width. E01 was a 100-shot smoke run and is not part of either fit. The fitted cloud outcomes (frequency; contrast) were:

| Suite | Slots | Width 1 | Width 2 | Width 4 |
| --- | --- | --- | --- | --- |
| Frozen | E02-E05 | 0.992; 1.000 | 1.999; 0.989 | 3.998; 0.951 |
| Fresh | E06-E09 | 0.997; 0.991 | 1.997; 0.986 | 4.005; 0.955 |

To reproduce a recorded batch, select **IonQ Aria 1**, set **Slot=E02** (or the listed slot) and **Shots=1,000**, then run; repeat the four slots in the suite to reconstruct its sweep. The original count records are in `recorded_ionq.py`; the fitted counts, intervals, and analysis are in `results/cloud_fit.json` and the compact evidence index is `evidence_summary.json`. The original Qollab console exports are retained in `results/exports/`.

Deviation: the initial combined-fit analysis sliced packed counts incorrectly. The cloud records themselves are valid; the indexing was corrected before the reported fit was produced. E01 is smoke-only and excluded. No cloud slot was superseded.


## Evidence files in this project

`evidence_summary.json` is a compact mixed evidence index of LOCAL MODEL suites and RECORDED cloud fits; `recorded_ionq.py` contains the recorded Qollab IonQ simulator runs. Regenerate the summary from the full files in `results/` with `python experiments/make_summary.py`.


### Local evidence (LOCAL MODEL)

All numbers in this table are **LOCAL MODEL** results from saved evidence JSON; they are not live Qollab measurements. Full details, cell breakdowns, and uncertainty summaries are in `results/frozen-evidence.json` and `results/fresh-evidence.json`.

| Local suite | Seeded instances | Records | Digital audio fidelity | Frequency identified |
| --- | ---: | ---: | ---: | ---: |
| Frozen | 24 | 432 | 432/432 | 432/432 |
| Fresh | 20 | 360 | 360/360 | 360/360 |

Audio fidelity means frequency error no greater than 0.02 and contrast error no greater than 0.01 against the values used to generate the audio. Frequency identification uses a 0.25 error bound plus an interval criterion; per-cell definitions and counts are in the evidence files. Records within a suite share seeded simulation settings and are not independent cloud trials. Sampling noise may shift estimates or confidence bounds across a threshold; inconclusive results remain results and are not silently removed.

**Figure / alt text:** Data-flow figure: phase/parity counts → fitted result and uncertainty → chart, receipt, WAV. Alt text: “The three outputs are generated from one measured fit, with audio encoding frequency and contrast.” The JS page and `figures.py` fallback chart show phase/parity without fit intervals; the evidence files contain data tables rather than a saved standalone figure.



## How to run (and replicate)

**Built-in JS page:** use the run instructions above. The Python `main.py` fallback defaults to 36 circuits at 256 shots each, forming three fitted width series (9,216 circuit shots). It shows a parity chart and full text; WAV download requires `sendFile`, which was unavailable in the observed fallback run. Local Python emulation takes about 1 s; browser timing is unmeasured.

**IonQ simulator:** choose an IonQ noise-model simulator, select a fixed slot, and run one slot per Qollab Run. Preserve the printed record and enter each `RECORD_JSON` line in the top-level `recorded_ionq.py`. Four phase batches make one complete sweep; do not interpret an incomplete batch as a frequency estimate. Recorded facts will be labeled with acquisition date, effective noise model, and shots: 2026-10-10, aria-1, 1,000 shots per phase point; see the recorded suite table above.

**Local reproduction** (local simulation only, from the repository project directory; `experiments/` and `review/manifests/` are not in the flattened upload). Use a new output directory on each rerun; use `--resume` only to continue a matching existing run. Add `--draws 1` to a full command for a bounded check, not full evidence:

```powershell
python experiments/run.py --quick --output-dir results/reproduce-quick
python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --output-dir results/reproduce-frozen
python experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json --output-dir results/reproduce-fresh
```

### Replicate and extend

To replicate the local evidence, run `python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --output-dir results/reproduce-frozen` (use the separate fresh command above for the fresh suite). To extend it, add more GHZ widths or another sonification mapping in `sonify.py`, keeping the text/table alternative for every sound.

## What is new

This entry joins an uncertainty-aware measured fringe with a parity chart, full text/table fit details, and a frequency/contrast sound mapping, including a WAV round-trip check that decodes from samples alone. It is an educational presentation and measurement exercise, not a new quantum algorithm. Prior sonification examples are acknowledged; uniqueness is not claimed as established.

## Limits

No speedup, learner benefit, human usability result, physical device claim, or validated noise estimate is shown. The local IonQ-like noise model is an approximation. A product-state fringe can contain harmonics, so frequency alone does not prove entanglement; contrast is not GHZ fidelity. The comparator exposes full fitted information in structured text/table; the chart shows phase/parity without fit intervals. Audio is checked for digital fidelity, not for being better than text or perceptually equivalent to it. Confidence-interval coverage is descriptive and may be sensitive to model mismatch and sampling. The local simulation is not cloud confirmation.

## Judging criteria summary

- **Novelty and creativity:** links measured phase data to optional sound while keeping uncertainty and a complete text path; adjacent sonification prior art exists.
- **Technical execution:** Qiskit GHZ measurements, one-circuit cloud packing, constrained binomial fit, structured receipts, and a samples-only audio decoder.
- **Impact potential:** could make this example easier to explore in audio and screen-reader workflows; impact on learners has not been measured.
- **Documentation quality:** evidence files, commands, data labels, figure alternative text, and scope limits support inspection and reproduction.

## Accessibility

Use keyboard-operable controls with visible focus, readable contrast, semantic headings and tables, and screen-reader announcements for pending, error, and completed states. Keep audio user-triggered and provide Stop plus a text equivalent. Chart axes are labeled; the receipt lists the underlying phase/parity values. Demo narration should have captions or a transcript. Actual browser and assistive-technology behavior remains to be confirmed.

## Disclosure

AI assistance is routed through AgentMesh using OpenCode free models and OpenAI Codex models; Claude Code is named as a reserve in project instructions. Consult the provenance log for task-specific records. Project-specific Python implementation, experiment harness, and copy were created within the build window. The unrelated pre-window “JS audio probe (test)” was only a platform capability check; its code and text were not reused.

`circuit_pack.py` packs phase-major circuits into disjoint wires and marginalizes little-endian counts. It was written during the hackathon build window and is used by Entanglement Court, The Noise Tax and Eyes-Free. GHZ phase recipes, frequency-blind fitting, browser audio/speech, receipts, UI, and evidence/decoder protocol are specific to Eyes-Free. Libraries: Qiskit 2.x (Apache-2.0), NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), Matplotlib (PSF-based licence), and Python standard library. No Aer. Qollab runtime documentation and hackathon rules were consulted; no Qollab template code is claimed as reused.

**Theme tag:** Quantum Unlocked  
**MIT licence:** included as `LICENSE`  
**Repository:** https://github.com/sauravdasmg/Qollab  
**Demo video:** [[VIDEO LINK]]  
This effort is supported by Qollab & IonQ.

### Publication and provenance

Publish `web/index.html`, `web/main.js`, `web/main.css` and `web/eyes_bridge.py` flattened to the Qollab top level, together with their top-level Python dependencies and compact evidence files. Keep `main.py` as the documented Python fallback. The JS page fits both embedded RECORDED cloud sweeps; LOCAL MODEL catalog entries are illustrative references, not new acquisitions. Playback encodes selected frequency and contrast, not uncertainty or fit status; text/table retain those details. WAV download works only where `sendFile` is supplied, otherwise the page explicitly reports it unavailable.

The summary reports its UTC generation date, machine/platform and Python/Qiskit/NumPy versions separately from original local acquisition metadata. Original evidence retains Qiskit/NumPy/SciPy versions and all settings. Its original host identifier, Python version and precise acquisition clock were not captured; source-file last-modified timestamps supply a labeled date basis, not invented acquisition timestamps. Historical G1 FAIL and independent/cloud-false flags describe the earlier local generation stage and remain unchanged. Recorded cloud fits are later evidence; no new independent PASS is asserted by this repair.
