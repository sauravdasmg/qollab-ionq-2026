# The Noise Tax: when does noise erase a quantum strategy's margin?

**Run it (judges):** built-in simulator, default settings (512 shots, aria-1), press **Run**, about 1 s; check the live W and N scores, recorded anchors, and modeled curves.

**Summary.** The Noise Tax compares two specific quantum-game recipes with their stated references while increasing a calibrated local noise model. Both modeled margins cross zero across 24 paired instances; RECORDED Qollab IonQ simulator slots T01-T08 show W +0.002 to +0.011 and N -0.035 to -0.022. Local crossings are not device thresholds.

**Preregistered N acceptance conditions were NOT met:** frozen aria-1 N interval width 0.325 > 0.30, and frozen vs fresh aria-1 N crossover difference 0.116 > 0.10 (fresh comparison pass = false). The W crossover result and the N direction are reported; N's precision/agreement is a negative result. These two preregistered gates are reported as failed; no tolerance or seed was changed.

The published Qollab entry is the JS page: `web/index.html`, `web/main.js`, `web/main.css`, and `web/tax_bridge.py` are flattened to the top level, built by the repository's `tools/package_project.py noise-tax --web` into `uploads/noise-tax-web.zip`, alongside `main.py` which stays a Python fallback. From the repository root, run `python tools/package_project.py noise-tax --web`. Upload the ZIP contents as a JS project; publication and logged-out browser acceptance are human checks.

**Problem.** Ideal quantum strategies can have an advantage over a chosen reference, but a noisy implementation may change that margin. This demo makes the comparison and assumptions visible. The double-trine and published hedging recipes are adapted from the retired same-team entries, as disclosed below.

**How it works.** The live Qiskit program prepares a double-trine discrimination game and a two-test hedging game, samples W's joint arm only against the analytic ideal one-way reference and both N arms on the injected backend; it prints word error, failure rates, and fixed-prize loss. W physical one-way circuits run only in cloud slots. Its precomputed curves use a shared calibrated IonQ-like approximation over noise scales 0 to 2 in steps of 0.025. Sign rule: positive favors joint for W and the published hedge for N; negative favors the ideal one-way reference and the attained product, respectively. Frozen and fresh local runs each use 24 seeded instances.

**Results — LOCAL MODEL (not device data).**

**Preregistered N acceptance conditions were NOT met:** frozen aria-1 N interval width 0.325 > 0.30, and frozen vs fresh aria-1 N crossover difference 0.116 > 0.10 (fresh comparison pass = false). The W crossover result and the N direction are reported; N's precision/agreement is a negative result. These two preregistered gates are reported as failed; no tolerance or seed was changed. W roots are deterministic for the stated model; ranges are calibration sensitivity, not confidence intervals. N intervals are 97.5% paired-instance bootstrap simultaneous-band intervals.

Both LOCAL MODEL suites ship in `nt_curves.py`; top-level `recorded_local.py` contains `LOCAL` (frozen receipt) and `FRESH` (compact fresh receipt), with machine, simulator, versions, UTC times, settings, and manifest identifiers. The full repository receipts are `results/frozen.json` and `results/fresh.json`.

| Model | W frozen / fresh s* | W calibration sensitivity | N frozen s* [interval] | N fresh s* [interval] |
|---|---:|---:|---:|---:|
| aria-1 | 1.309 / 1.309 | 1.206–1.431 | 0.411 [0.250, 0.575] | 0.295 [0.150, 0.450] |
| forte-1 | 1.141 / 1.141 | 1.062–1.233 | 0.339 [0.200, 0.475] | 0.243 [0.125, 0.375] |
| forte-enterprise-1 | 0.684 / 0.684 | 0.655–0.716 | 0.200 [0.100, 0.300] | 0.144 [0.050, 0.225] |


![Frozen local-model curves. Alt text: W and N panels each show three frozen curves; solid, dashed, and dotted identify Aria, Forte, and Forte Enterprise. W shaded ranges are calibration sensitivity; N shows the Aria bootstrap band and crossover interval. No cloud anchors appear here.](https://raw.githubusercontent.com/sauravdasmg/qollab-ionq-2026/main/projects/noise-tax/results/figures/frozen-curves.png)

![Fresh local-model curves. Alt text: Three fresh curves use solid/dashed/dotted for Aria/Forte/Forte Enterprise; W shading shows calibration sensitivity and N the Aria bootstrap band and crossover interval.](https://raw.githubusercontent.com/sauravdasmg/qollab-ionq-2026/main/projects/noise-tax/results/figures/fresh-curves.png)

![Archival recorded anchors. Alt text: Six earlier case-0 W/N receipts on Aria, Forte, and Forte Enterprise are shown with cloud sampling bounds beside frozen local s=1 predictions; these are not T-slot receipts or a cloud noise sweep.](https://raw.githubusercontent.com/sauravdasmg/qollab-ionq-2026/main/projects/noise-tax/results/figures/frozen-anchors.png)

**RECORDED** Qollab IonQ simulator slots T01-T08 (2026-10-10 UTC) show W signed advantages from +0.002 to +0.011 and N advantages from -0.035 to -0.022. They are discrete anchors, not a cloud crossover; per-slot outcomes and reproduction settings follow below.

## Cloud evidence (RECORDED, Qollab IonQ simulator)

On 2026-10-10 UTC, slots T01-T08 ran the W double-trine suite (T01, T03, T05, T07) and N hedging suite (T02, T04, T06, T08). W used 1,000 shots per label; N used 4,000 shots per arm. The recorded noise models and signed outcomes are:

| Slot | Suite / comparison | Noise model | Shots | Signed outcome |
|---|---|---|---:|---:|
| T01 | W: joint vs ideal one-way | aria-2 | 1,000 per label | +0.005 |
| T02 | N: published hedge vs attained product | aria-2 | 4,000 per arm | -0.030 |
| T03 | W: joint vs ideal one-way | aria-1 | 1,000 per label | +0.002 |
| T04 | N: published hedge vs attained product | aria-1 | 4,000 per arm | -0.022 |
| T05 | W: joint vs ideal one-way | forte-1 | 1,000 per label | +0.005 |
| T06 | N: published hedge vs attained product | forte-1 | 4,000 per arm | -0.035 |
| T07 | W: joint vs ideal one-way (fixed fresh corroboration) | aria-1 | 1,000 per label | +0.011 |
| T08 | N: published hedge vs attained product (fixed fresh corroboration) | aria-1 | 4,000 per arm | -0.022 |

Slot runs need the Python version of this project (`main.py` as the entry point; `uploads/noise-tax.zip` in the repository); the published web page runs the default demo only. Positive W favors the joint measurement over the ideal one-way reference. Negative N means the attained product strategy has lower fixed-prize loss than the published hedge. These are discrete simulator anchors, not a cloud noise sweep or threshold. Reproduce each run by selecting **IonQ Aria 1**, setting **Slot=Txx** and **Shots=1000** for W or **Shots=4000** for N, then running the project; the slot selects the recorded noise model shown above (including Forte 1 on T05/T06). All raw `RECORD_JSON` lines for these eight valid runs are in [`recorded_ionq.py`](https://github.com/sauravdasmg/qollab-ionq-2026/blob/main/projects/noise-tax/recorded_ionq.py), with the compact index and outcomes in [`evidence_summary.json`](https://github.com/sauravdasmg/qollab-ionq-2026/blob/main/projects/noise-tax/evidence_summary.json); both files are included in this project. Original Qollab console exports are retained under `results/exports/`.

**Deviations and superseded runs:** the campaign provenance and evidence summary report no Noise Tax cloud deviations or superseded runs. T07/T08 are fixed-seed fresh corroboration and are additional runs, not replacements. No Entanglement Court preparation-noise deviation applies to this project.

## Archival anchors

The six earlier receipts were produced on 2026-10-10 00:15-00:38 UTC by the retired Two Whispers / Never Lose Twice programs with the original **case=0** setting and the models/budgets below. Their packed circuits include extra recipe arms. They are kept as recorded and are **NOT reproducible via T slots**. Historical reruns require the original retired `projects/two-whispers/main.py` or `projects/never-lose-twice/main.py`, case=0, and the matching model/shots, including their original packing recipes; the merged entry does not recreate them.

| Original program / comparison | Noise model | Shots | Signed outcome |
|---|---|---:|---:|
| Two Whispers W: joint vs ideal one-way | aria-1 | 1,000 | +0.0113 |
| Two Whispers W: joint vs ideal one-way | forte-1 | 1,000 | +0.0017 |
| Two Whispers W: joint vs ideal one-way | forte-enterprise-1 | 1,000 | -0.0177 |
| Never Lose Twice N: published hedge vs attained product | aria-1 | 4,000 | -0.0209 |
| Never Lose Twice N: published hedge vs attained product | forte-1 | 1,000 | -0.0211 |
| Never Lose Twice N: published hedge vs attained product | forte-enterprise-1 | 1,000 | -0.0377 |

These six raw receipts are stored in top-level `recorded_ionq.py` (`evidence_summary.json` indexes only T01-T08); the original exported consoles are retained in the repository under `projects/two-whispers/results/exports/` (W02-W04) and `projects/never-lose-twice/results/exports/` (N02-N04), the paths recorded in `recorded_ionq.SOURCE_FILES`. `frozen-anchors.png` shows these six archival observations beside local s=1 predictions, not T01-T08. The default display includes all 14 stored receipts, with the eight T-slot campaign receipts separate from this archive.

Finite-shot estimates can cross a bound by sampling chance; interpret each estimate with its uncertainty interval. **LIVE** built-in results are the judge-facing run; **RECORDED** denotes the named Qollab IonQ simulator runs; **LOCAL MODEL** denotes the calibrated approximation.

**How to run (and replicate).** On Qollab, select the built-in simulator, keep defaults, and press Run. On the IonQ simulator, use a slot defined in `cloud_slots.py`; the slot receipt records its noise model and shots. From one working directory, the project folder `D:\Quantum Projects\Qollab\projects\noise-tax`, with repository dependencies installed:

```powershell
..\..\.venv\Scripts\python.exe experiments\run.py --suite frozen --independent-manifest review\manifests\frozen.json --draws 4000 --output-dir replication-frozen-01
..\..\.venv\Scripts\python.exe experiments\run.py --suite fresh --independent-manifest review\manifests\fresh.json --draws 4000 --output-dir replication-fresh-01
..\..\.venv\Scripts\python.exe ..\..\tools\qollab_local.py run . --backend ideal --shots 512
```

The output directories must be new and empty; choose new names for subsequent runs, or deliberately use `--resume` for an existing matching run. Full runs take several minutes each. To check either manifest without a full experiment, append `--validate-only --draws 1` and use another new output directory; this is a bounded smoke check, not inference evidence. The fresh harness compares against the shipped `results/frozen.json`, even with a separate output directory.

`experiments/make_curves.py` reads `results/summary.json`; it does not rebuild the summary from new full result files. Running it alone regenerates the shipped summary's curves, potentially stale for a new campaign. A new summary must be assembled and verified from both full suites before regenerating new evidence. The shipped summary can be regenerated with `../../.venv/Scripts/python.exe experiments/make_curves.py`.

**What is new.** One inspectable demo presents two different quantum comparisons, their modeled crossings, instance uncertainty, calibration sensitivity, and discrete measured anchors together. It does not claim new ideal strategies or new noise physics.

**Limits.** No speedup or noise reduction is shown. The local model approximates IonQ noise and cannot certify device thresholds. W compares the joint recipe with an ideal one-way sequential reference, not all LOCC or separable measurements. N compares the fixed published hedge with an attained product recipe at one fixed prize, not a globally optimal noisy product strategy. The W root is deterministic in the model with calibration sensitivity; N has bootstrap intervals. Cloud anchors do not make a cloud sweep. Negative margins mean the named comparator wins; neither comparison says classical computation beats quantum computation generally.

**Judging criteria.** Novelty and creativity: an interactive cross-game view of modeled noise thresholds. Technical execution: Qiskit circuits, shared approximate channel, seeded suites and receipts. Impact potential: a clear way to inspect how noise changes specific quantum-game margins. Documentation quality: definitions, commands, figures with alt text, accessibility and scope limits.

**Accessibility.** The web source provides native range/select/button controls, associated labels, visible focus styles, chart data tables, circuit text, and a polite live status region. These source features support keyboard and screen-reader access; browser/screen-reader acceptance is a human check on the published page. No audio is required. The demo video should include captions or subtitles.

**Disclosure.** AI tools: AgentMesh routing (including OpenCode free models), OpenAI Codex models, and Claude Code. The demo-video voiceover is AI-generated with Microsoft neural text-to-speech (voice en-US-AndrewNeural, via the open-source edge-tts tool). `circuit_pack.py` is a packing helper written during the hackathon build window (Oct 9-11, 2026). It packs several small circuits onto disjoint qubits of one circuit for Qollab's one-job-per-run IonQ interface and splits the measured counts back per block. Each of our entries (Entanglement Court, The Noise Tax, Eyes-Free) ships its own version of this helper with the same purpose; the files differ in detail. `whispers_core.py`, `hedging_core.py`, `hedging_strategies.py`, and `product_bounds.py` were adapted in-window from the retired Two Whispers / Never Lose Twice build-window code (same author/team, Oct 9-10 UTC). The shared noise channel, crossover analysis, cloud slots, and UI are new in the merged entry. `reuse_sources.json` records the source hashes, import timestamps, and the reused synthesis, noise-analysis, receipt, calibration, and emulator references. Libraries: Qiskit (Apache-2.0), NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), Matplotlib (Matplotlib license), and Python standard library (PSF License). Qollab docs and templates were consulted; platform runtime patterns are disclosed here. MIT licence: see [LICENSE](https://github.com/sauravdasmg/qollab-ionq-2026/blob/main/projects/noise-tax/LICENSE).

**Theme:** Quantum Unlocked.

**Attribution:** This effort is supported by Qollab & IonQ.

**Repository:** https://github.com/sauravdasmg/qollab-ionq-2026  
**Video:** https://youtu.be/-vbi4atEZaM
