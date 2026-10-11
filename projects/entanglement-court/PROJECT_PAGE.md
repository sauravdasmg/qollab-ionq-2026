# Entanglement Court

Entanglement Court turns a subtle quantum question into a courtroom challenge: can measurements distinguish entanglement when two preparations look identical in the computational basis?

**Result:** local-model graph certification was 0.50/0.50 in ideal simulation and 0.42/0.43 in the Aria-like model; RECORDED Qollab IonQ Aria 1 results certified 12/12 easy cases and abstained on all 12 near-threshold cases (200 shots, 2026-10-10). The product and biseparable controls had zero false certificates in the local campaign summary.

**Run it (judges): Built-in simulator, default settings, press Run, about 8 s on Qollab (7.93 s measured on the Qollab built-in simulator, Python version, 2026-10-11 UTC; 3.49-3.79 s on the local runner); then inspect the matched Z histograms and conditional witness receipt.**

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
| IonQ simulator subset | RECORDED | 2026-10-10; IonQ Aria 1 (`aria-1`), 200 shots per block; 12/12 easy certified and 0/12 near-threshold certified (C02-C25). |

Here, ideal disables only the approximate device channel and retains deliberate preparation phase noise; Aria-like means nominal scale 1.

**Local evidence retention limitation:** frozen/fresh/development files retain per-case aggregate counters, probability references, seeds and metadata; the harness discarded sampled draw-level counts and retained no separately hashed replay transcript. Published fractions can be independently summed from saved counters, but original draws cannot be reconstructed from retained observations in a quick audit. Full local commands generate a new replay, not an audit of retained raw draws. This explicitly departs from the original raw-count retention plan; no full independent rerun or complete raw-result reproduction is claimed here.

## Cloud evidence (RECORDED, Qollab IonQ simulator)

On 2026-10-10, slots C02-C25 ran on the Qollab IonQ Aria 1 simulator (`aria-1`), with 200 shots per block. The campaign included frozen easy cases (C02-C07), frozen near-threshold cases (C08-C13), fresh easy cases (C14-C19), and fresh near-threshold cases (C20-C25). A separate 100-shot C01 smoke run on 2026-10-09 is retained but excluded from campaign totals. These packed jobs measured the two witness color settings for target and product impostor; all current cloud slots (C08-C25, including fresh easy C14-C19) omitted the two Z histogram blocks and use the exact uniform-Z result as a mathematical reference.

| Cloud evidence | Slots | Outcome |
|---|---|---|
| Frozen easy | C02-C07 | 6/6 certified; F_lower 0.75-0.86. These ran before the ancilla preparation-noise channel was added; retained with the documented easy-case deviation (per-wire p < 0.015). |
| Fresh easy | C14-C19 | 6/6 certified; F_lower 0.67-0.75. |
| Frozen near-threshold, corrected | C08-C13 | 0/6 certified; all inconclusive (appropriate abstention); F_lower 0.11-0.18. |
| Fresh near-threshold | C20-C25 | 0/6 certified; all inconclusive (appropriate abstention); F_lower 0.07-0.25. |
| **Campaign total** | **C02-C25** | **12/12 easy cases certified; 0/12 near-threshold cases certified.** |

**Exact circuit reproduction:** Slot runs need the Python version of this project (`main.py` as the entry point; `uploads/entanglement-court.zip` in the repository); the published web page runs the default demo only. current code reproduces the saved recipes/circuit hashes for C08-C25: select **IonQ Aria 1**, set **Slot=C08** through **C25**, and **Shots=200**. New finite-shot counts will vary. C02-C07 are retained **LEGACY, preparation noise omitted** observations from the pre-WP-C-14 code, not executions of the current noisy factory. To reconstruct those historical circuits, use repository commit `3a0b99071655a50567990b84a9958596f94f3c29` (the version before WP-C-14), upload that revision's top-level Entanglement Court files in a separate project, select **IonQ Aria 1**, **Slot=C02** through **C07**, **Shots=200**, and keep other parameters at their defaults. Selecting C02-C07 in current code executes the corrected noisy recipe and does not reproduce the historical circuit. Reanalysis of archived raw counts uses the shipped `recorded_ionq.py` without rerunning any job.

**C01 is a smoke run, not an accepted Slot value:** select **IonQ Aria 1**, leave **Slot blank**, set **Case=0**, **Challenge=sealed** (default anchor mode), **Shots=100**, and keep the trust flag at its default false. It remains excluded from campaign totals.

Complete receipts ship at top level in `recorded_ionq.py`; its `EXPORT_INDEX` maps every archived job ID and UTC end to its actual HTML export and SHA-256. Original exported source pointers are preserved separately as historical annotations. The immutable HTML console exports under `results/exports/` are **repository-only** archives, not Qollab upload files. The built-in demo reanalyzes the complete shipped receipts as RECORDED evidence.

Deviation and superseded runs: C02-C07 omitted the declared per-wire preparation phase-flip channel; they are retained only as easy results, with p < 0.015 and the deviation labeled in each receipt. The first C08-C13 runs (13:37-13:42 UTC) also omitted this channel and are superseded; they remain in the exports and receipt archive labeled superseded, and are excluded from the near-threshold outcome above. Corrected C08-C13 reruns at 15:05-15:08 UTC used the ancilla phase-flip channel. C14-C25 also used that channel. In corrected runs, independent per-wire phase flips are implemented by measured ancillas that are marginalized; the added RY/CZ gates themselves incur simulator noise. All cloud witness claims remain conditional on trusted measurement rotations and readout; systematic measurement error is not bounded here.

![Static LOCAL MODEL chart from saved frozen aggregates at 100 shots/block: 24 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.](https://raw.githubusercontent.com/sauravdasmg/qollab-ionq-2026/main/projects/entanglement-court/figures/frozen.png)

*Alt text: Static LOCAL MODEL chart from saved frozen aggregates at 100 shots/block: 24 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.*

![Static LOCAL MODEL chart from saved fresh aggregates at 100 shots/block: 20 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.](https://raw.githubusercontent.com/sauravdasmg/qollab-ionq-2026/main/projects/entanglement-court/figures/fresh.png)

*Alt text: Static LOCAL MODEL chart from saved fresh aggregates at 100 shots/block: 20 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.*

![Static LOCAL MODEL chart from saved development aggregates at 100 shots/block: four development cases, ideal device channel (all 1.000) versus Aria-like scale 1 (0.974, 0.969, 0.956, 0.966; mean 0.966), 1,000 draws per case. This is a bar chart, not an interactive web screenshot.](https://raw.githubusercontent.com/sauravdasmg/qollab-ionq-2026/main/projects/entanglement-court/figures/development.png)

*Alt text: Static LOCAL MODEL chart from saved development aggregates at 100 shots/block: four development cases, ideal device channel (all 1.000) versus Aria-like scale 1 (0.974, 0.969, 0.956, 0.966; mean 0.966), 1,000 draws per case. This is a bar chart, not an interactive web screenshot.*


These three figures are static LOCAL charts. The companion interactive courtroom is implemented separately in `web/index.html`, `web/main.js`, `web/main.css` and `web/court_bridge.py`; its Z/parity/witness panels are not depicted in these PNGs. Short axis suffixes map to full case IDs in the repository results.


## How to run (and replicate)

**Judging run:** select Qollab's Built-in simulator, keep the default form settings, and press Run. Check the paired Z exhibits and whether the finite-shot witness receipt is conditional or inconclusive. The measured built-in default runtime is about 8 s on Qollab (7.93 s measured on the Qollab built-in simulator, Python version, 2026-10-11 UTC; 3.49-3.79 s on the local runner).

**IonQ simulator:** follow the version-specific instructions above. Current cloud slots use four witness blocks with ancillas (24 wires); default anchor and legacy jobs use six four-wire blocks.

**Local reproduction commands** (commands only; their output is not asserted here):

```powershell
..\..\.venv\Scripts\python.exe experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --draws 1000 --output-dir results/frozen-reproduction
..\..\.venv\Scripts\python.exe experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json --draws 1000 --output-dir results/fresh-reproduction
```

The local IonQ-like noise model is an approximation and is not hardware or Qollab cloud evidence.

**Evidence files in this project:** `evidence_summary.json` contains compact LOCAL MODEL statistics, original run UTC/platform/software versions, summary-generation provenance and source SHA-256s; `recorded_ionq.py` holds the Qollab IonQ runs. Full local results are repository-only evidence, not top-level Qollab uploads. Regenerate the summary in the repository with `python experiments/make_summary.py`.

### Replicate and extend

To replicate the local evidence, run `python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json` (and `--suite fresh` with `fresh.json`) from the repository. To extend it, add new graph/product preparations in `cases.py` or new witness terms in `witness.py`, then add matching independent manifests.

## What is new

The original educational contribution is a preregistered adversarial exhibit: a connected graph-state preparation and a known separable preparation share the same ideal Z distribution, then face a stabilizer challenge and finite-copy receipt. The witness mathematics is established; no speedup or stronger-baseline advantage is claimed.

## Limits

This project does not show a quantum speedup. It does not show that its witness beats a stronger baseline: the comparator calls the same witness implementation twice on shared counts. Local noise results are approximate, and cloud conclusions depend on trusted measurement assumptions. Near-threshold cases can be inconclusive. Zero observed control failures in a finite sample is not a zero-risk guarantee; per-round error control is not campaign-wide control.

## Judging criteria

- **Novelty and creativity:** turns matched preparations and witness assumptions into an adversarial courtroom interaction; novelty is in the teaching artifact and case set, not the witness theorem.
- **Technical execution:** count-based stabilizer measurements, finite-sample bounds, and packed execution for the IonQ one-circuit job limit.
- **Impact potential:** helps learners understand why observed distributions and uncertainty assumptions matter in entanglement claims.
- **Documentation quality:** supplies run steps, labeled evidence, figures with alt text, reproduction commands, disclosures, and explicit limits.

## Accessibility

The web interface is keyboard-operable and uses text and symbols alongside high-contrast color. Exhibit data and status are available as text for screen readers. Audio is not needed for interaction; captions should accompany any video narration.

## Disclosure and submission details

AI tools: AgentMesh routing to OpenCode free models, OpenAI Codex models, and Claude Code. The demo-video voiceover is AI-generated with Microsoft neural text-to-speech (voice en-US-AndrewNeural, via the open-source edge-tts tool). Shared helper code in `circuit_pack.py` and `receipt.py` was written during Oct 9–11, 2026: it packs several small circuits onto disjoint qubits of one circuit for Qollab's one-job-per-run IonQ interface, splits the counts back per block and writes evidence receipts. Each of our entries (Entanglement Court, The Noise Tax, Eyes-Free) ships its own version of these helpers with the same purpose; the files differ in detail; the project-specific physics and presentation are distinct. Libraries: Qiskit 2.x (Apache-2.0), NumPy and SciPy (BSD-3-Clause), Matplotlib (PSF-based license). Qollab runtime documentation and hackathon rules informed the implementation; no Qollab starter template or outside project code is represented as original work.

**Theme tag:** Quantum Unlocked  
**License:** MIT ([LICENSE](LICENSE))

This effort is supported by Qollab & IonQ.

**Repository:** https://github.com/sauravdasmg/qollab-ionq-2026  
**Video:** https://youtu.be/dVbXgx0EbbE
