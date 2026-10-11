# Entanglement Court

Entanglement Court is a small interactive courtroom for testing graph-state entanglement evidence.
It pairs an entangled graph state with a separable product state that has the same ideal Z-basis distribution.
**Result:** local-model graph certification was 0.50/0.50 in ideal simulation and 0.42/0.43 in the Aria-like model; RECORDED Qollab IonQ Aria 1 results certified 12/12 easy cases and abstained on all 12 near-threshold cases (200 shots, 2026-10-10).
**Run it (judges): built-in simulator, default settings, press Run, about 8 s on Qollab (7.93 s measured on the Qollab built-in simulator, Python version, 2026-10-11 UTC; 3.49-3.79 s on the local runner); then check the matched Z exhibits and the conditional witness receipt.**

## Summary

The demo shows why matching computational-basis histograms cannot by themselves reveal entanglement. A judge can inspect both preparations, challenge the evidence with two measurement settings, and see a finite-sample lower bound and its assumptions. The project is an educational evidence game and coverage study; it is not a new entanglement theorem.

## The problem

Graph-state stabilizer witnesses can certify genuine multipartite entanglement, but a point estimate can overstate what finite measurements support. The exhibit makes this limitation visible by pairing a graph state and a separable equatorial product preparation with the same ideal Z distribution. The planned context cites finite-copy witness work, doi:10.1038/s41534-024-00810-3.

## How it works

The live run prepares a four-qubit connected graph state and a separable product state. Both have exactly uniform ideal Z probabilities, so their theoretical total-variation distance is zero. The program measures Z for the matching exhibit and measures graph stabilizers in two coloring bases. It computes parity counts, confidence bounds, and a conservative fidelity lower bound. The graph-state biseparable threshold is 1/2; the receipt certifies only when the lower bound is strictly above it.

The simultaneous bound allocates error probability across generator parities and reports a per-round guarantee under its measurement assumptions. A finite sample can cross a theoretical bound by chance; confidence intervals make sampling uncertainty visible. “Inconclusive” does not mean separable.

## Results

| Evidence | Label | Result |
|---|---|---|
| Frozen and fresh local campaign, 24 + 20 cases | LOCAL MODEL | Graph certification fraction: 0.50 / 0.50 in ideal simulation; 0.42 / 0.43 in the aria-like approximation. |
| Product and biseparable controls | LOCAL MODEL | Zero false certificates reported in the provenance summary. |
| Comparator | LOCAL MODEL | Two-color comparator and simultaneous generator witness are implementation-identical and tie; this is not a stronger-baseline win. |
| Qollab IonQ simulator subset | RECORDED | 2026-10-10; IonQ Aria 1 (`aria-1`), 200 shots per block; 12/12 easy cases certified and 0/12 near-threshold cases certified (C02-C25; see cloud table below). |

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

The local noise model approximates IonQ-like errors and is not a device result.

**Evidence files in this project:** `evidence_summary.json` contains compact LOCAL MODEL statistics, original run UTC/platform/software versions, summary-generation provenance and source SHA-256s; `recorded_ionq.py` holds the Qollab IonQ runs. Full local results are repository-only evidence, not top-level Qollab uploads. Regenerate the summary in the repository with `python experiments/make_summary.py`.

![Static LOCAL MODEL chart from saved frozen aggregates at 100 shots/block: 24 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.](figures/frozen.png)

*Alt text: Static LOCAL MODEL chart from saved frozen aggregates at 100 shots/block: 24 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.*

![Static LOCAL MODEL chart from saved fresh aggregates at 100 shots/block: 20 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.](figures/fresh.png)

*Alt text: Static LOCAL MODEL chart from saved fresh aggregates at 100 shots/block: 20 cases, ideal device channel versus Aria-like scale 1; easy cases certify more often than near-threshold cases. Deliberate preparation noise remains in both series.*

![Static LOCAL MODEL chart from saved development aggregates at 100 shots/block: four development cases, ideal device channel (all 1.000) versus Aria-like scale 1 (0.974, 0.969, 0.956, 0.966; mean 0.966), 1,000 draws per case. This is a bar chart, not an interactive web screenshot.](figures/development.png)

*Alt text: Static LOCAL MODEL chart from saved development aggregates at 100 shots/block: four development cases, ideal device channel (all 1.000) versus Aria-like scale 1 (0.974, 0.969, 0.956, 0.966; mean 0.966), 1,000 draws per case. This is a bar chart, not an interactive web screenshot.*


These three figures are static LOCAL charts. The companion interactive courtroom is implemented separately in `web/index.html`, `web/main.js`, `web/main.css` and `web/court_bridge.py`; its Z/parity/witness panels are not depicted in these PNGs. Short axis suffixes map to full case IDs in the repository results.
Repository image links retain `figures/` paths. For publication, upload the three PNGs under flattened top-level names `frozen.png`, `fresh.png`, `development.png` and use the matching paths in PROJECT_PAGE.md, or replace them with the asset-upload URLs returned by Qollab. Verify the rendered images before publishing.

## How to run (and replicate)

### Built-in simulator

Open the project in Qollab, select **Built-in simulator**, leave the form at its defaults, and press **Run**. Review the paired Z histograms, the two stabilizer exhibits, and the receipt's trusted-measurement condition. The built-in default run took 7.93 s on Qollab (Python version, 2026-10-11 UTC) and 3.49-3.79 s on the local runner (2026-10-10); main.py prints the elapsed time at the end of each run.

### IonQ simulator slots

Use the version-specific cloud reproduction instructions above. Current C08-C25 use four witness blocks with ancillas, totaling 24 wires; the default anchor and legacy C02-C07 jobs use six four-wire blocks.

### Local reproduction

From this folder, use the repository Python environment:

```powershell
..\..\.venv\Scripts\python.exe experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --draws 1000 --output-dir results/frozen-reproduction
..\..\.venv\Scripts\python.exe experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json --draws 1000 --output-dir results/fresh-reproduction
```

These commands describe how to reproduce local campaigns; they are not claims that those commands were run for this page. The local IonQ-like simulation is an approximation, not a Qollab cloud receipt.

### Replicate and extend

To replicate the local evidence, run `python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json` (and `--suite fresh` with `fresh.json`) from the repository. To extend it, add new graph/product preparations in `cases.py` or new witness terms in `witness.py`, then add matching independent manifests.

## What is new

The contribution is the adversarial matched-preparation exhibit, its frozen case sets, and an accessible evidence receipt that names its assumptions. Graph-state witnesses and finite-sample confidence methods are established techniques. This work does not claim a new theorem, speedup, or superiority to a stronger witness.

## Limits

The comparator calls the same witness implementation twice on shared counts, so results tie by construction. The local noise model is approximate. A successful cloud receipt is conditional on trusted measurement rotations and readout; systematic measurement error is otherwise unbounded. The local campaign's results do not establish hardware performance. Near-threshold cases can be inconclusive. Zero observed false certificates in finite controls is not proof of a zero population risk, and these per-round intervals do not create a campaign-wide guarantee.

## Judging-criteria summary

- **Novelty and creativity:** an adversarial courtroom pairs preparations that look identical in Z and invites a measurement challenge; the witness itself is established.
- **Technical execution:** six four-wire blocks are packed for the default anchor and legacy jobs; current cloud slots pack four witness blocks with ancillas (24 wires) into one IonQ circuit; evidence is computed from counts and confidence bounds.
- **Impact potential:** the demo teaches the difference between matching samples and entanglement evidence, including when evidence is insufficient.
- **Documentation quality:** run instructions, saved figures, result labels, assumptions, reproduction commands, and limitations are provided.

## Accessibility

The companion web interface supports keyboard operation, uses high-contrast colors with text labels and symbols so color is not the only cue, and exposes exhibits and status as readable text for screen readers. No audio is required; any demo-video narration should include captions.

## Disclosure

AI tools used during the build window: AgentMesh routing to OpenCode free models, OpenAI Codex models, and Claude Code. The demo-video voiceover is AI-generated with Microsoft neural text-to-speech (voice en-US-AndrewNeural, via the open-source edge-tts tool). Shared helper code in `circuit_pack.py` and `receipt.py` was written during Oct 9–11, 2026: it packs several small circuits onto disjoint qubits of one circuit for Qollab's one-job-per-run IonQ interface, splits the counts back per block and writes evidence receipts. Each of our entries (Entanglement Court, The Noise Tax, Eyes-Free) ships its own version of these helpers with the same purpose; the files differ in detail. Project-specific preparation, witness, decoding, and presentation code is described above. Dependencies are Qiskit 2.x (Apache-2.0), NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), and Matplotlib (PSF-based license); see their upstream license files. No extra Qollab template or third-party project code is claimed as reused. The Qollab runtime documentation and hackathon rules were consulted.

**Theme:** Quantum Unlocked

**License:** MIT; see [LICENSE](LICENSE).

This effort is supported by Qollab & IonQ.

**Repository:** https://github.com/sauravdasmg/Qollab  
**Demo video:** https://youtu.be/dVbXgx0EbbE
