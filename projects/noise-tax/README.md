# The Noise Tax

Two familiar quantum strategies meet a calibrated, local IonQ-like noise model: when does their measured advantage cross zero?

LOCAL MODEL: across 24 paired instances, both comparisons cross as modeled noise rises; RECORDED Qollab IonQ simulator slots T01-T08 show W +0.002 to +0.011 and N -0.035 to -0.022.

**Preregistered N acceptance conditions were NOT met:** frozen aria-1 N interval width 0.325 > 0.30, and frozen vs fresh aria-1 N crossover difference 0.116 > 0.10 (fresh comparison pass = false). The W crossover result and the N direction are reported; N's precision/agreement is a negative result. These two preregistered gates are reported as failed; no tolerance or seed was changed.

**Run it (judges):** choose the built-in simulator; leave defaults (512 shots, aria-1); press **Run** (about 1 s); then check the two live score summaries, recorded IonQ anchors, and noise curves.

The published Qollab entry is the JS page: `web/index.html`, `web/main.js`, `web/main.css`, and `web/tax_bridge.py` are flattened to the top level, built by the repository's `tools/package_project.py noise-tax --web` into `uploads/noise-tax-web.zip`, alongside `main.py` which stays a Python fallback. From the repository root, run `python tools/package_project.py noise-tax --web`. Upload the ZIP contents as a JS project; publication and logged-out browser acceptance are human checks.

## Summary

The Noise Tax is a compact benchmark and interactive explanation of modeled noise thresholds for two specific comparisons: a joint measurement against an ideal one-way reference on the double-trine game, and a published hedging strategy against an attained product strategy on a fixed prize. Sign rule: positive favors joint for W and the published hedge for N; negative favors the ideal one-way reference and the attained product, respectively.

Results distinguish **LIVE** built-in runs, **RECORDED** Qollab IonQ simulator runs, and **LOCAL MODEL** results from a calibrated IonQ-like approximation. A local-model crossing is conditional on that model; it is not an IonQ device threshold.

## The problem

Quantum strategies can outperform a selected reference in an idealized setting, while noise changes their measured outcomes. We ask how the signed margin changes as a specified local noise scale increases, and show how that answer depends on the model. The comparisons are deliberately narrow: the one-way ideal reference is not every separable or LOCC measurement, and the product strategy is itself quantum.

The double-trine and published hedging recipes are adapted from the retired same-team entries; attribution and reused material are disclosed below and in `reuse_sources.json`.

## How it works

The default W run samples the joint arm only against the analytic ideal one-way reference; N samples both arms. W physical one-way circuits run only in cloud slots. The live entry prepares small Qiskit circuits for three equiprobable double-trine labels and for two four-qubit hedging arms, runs them on the injected backend, and prints estimated errors, failure rates, and fixed-prize loss. It displays stored local sweeps beside the live run and historical cloud measurements. Cloud data are separate anchor observations; cloud noise scale is not adjustable and no cloud crossover is fitted.

For the local study, the same calibrated channel semantics are applied across the games after compilation. The W metric is ideal one-way word error minus joint-measurement word error. The N metric is product loss minus hedge loss, where loss is double-failure probability plus 0.02 times the expected number of unused passes. Sign rule: positive favors joint for W and the published hedge for N; negative favors the ideal one-way reference and the attained product, respectively. Frozen and fresh sets each use 24 seeded instances and a grid from 0 to 2 in steps of 0.025.

## Results

**Preregistered N acceptance conditions were NOT met:** frozen aria-1 N interval width 0.325 > 0.30, and frozen vs fresh aria-1 N crossover difference 0.116 > 0.10 (fresh comparison pass = false). The W crossover result and the N direction are reported; N's precision/agreement is a negative result. These two preregistered gates are reported as failed; no tolerance or seed was changed.

All table values below are **LOCAL MODEL** (calibrated IonQ-like approximation; not device data). W has a deterministic root for this model and a calibration-sensitivity range, not a sampling confidence interval. N uses a 97.5% paired-instance bootstrap simultaneous-band interval. The frozen and fresh N intervals overlap for each model; overlap does not satisfy the separate 0.10 agreement tolerance.

Both LOCAL MODEL suites ship in `nt_curves.py`; top-level `recorded_local.py` contains `LOCAL` (frozen receipt) and `FRESH` (compact fresh receipt), with machine, simulator, versions, UTC times, settings, and manifest identifiers. The full repository receipts are `results/frozen.json` and `results/fresh.json`.

| Comparison | Model | Frozen crossing s* | Fresh crossing s* | Uncertainty / interpretation |
|---|---|---:|---:|---|
| W joint vs ideal one-way | aria-1 | 1.309 | 1.309 | deterministic; calibration sensitivity 1.206–1.431 |
| W joint vs ideal one-way | forte-1 | 1.141 | 1.141 | deterministic; calibration sensitivity 1.062–1.233 |
| W joint vs ideal one-way | forte-enterprise-1 | 0.684 | 0.684 | deterministic; calibration sensitivity 0.655–0.716 |
| N published hedge vs attained product | aria-1 | 0.411 | 0.295 | frozen CI 0.250–0.575; fresh CI 0.150–0.450 |
| N published hedge vs attained product | forte-1 | 0.339 | 0.243 | frozen CI 0.200–0.475; fresh CI 0.125–0.375 |
| N published hedge vs attained product | forte-enterprise-1 | 0.200 | 0.144 | frozen CI 0.100–0.300; fresh CI 0.050–0.225 |

**LOCAL MODEL figures.** Each curves PNG shows only its named suite. Solid/dashed/dotted identify Aria/Forte/Forte Enterprise. W shading is calibration sensitivity; N shows the Aria bootstrap band and crossover interval. Anchors appear only in the separate frozen-anchors.png, which shows the six earlier archival receipts.

![Frozen local-model curves. Alt text: W and N panels each show three frozen curves; solid, dashed, and dotted identify Aria, Forte, and Forte Enterprise. W shaded ranges are calibration sensitivity; N shows the Aria bootstrap band and crossover interval. No cloud anchors appear here.](results/figures/frozen-curves.png)

![Fresh local-model curves. Alt text: W and N panels show the independent fresh 24-instance set; solid, dashed, and dotted identify Aria, Forte, and Forte Enterprise. W is deterministic with calibration sensitivity; N shows the Aria bootstrap band and crossover interval.](results/figures/fresh-curves.png)

![Archival recorded anchors. Alt text: Six earlier case-0 W/N receipts on Aria, Forte, and Forte Enterprise are shown with cloud sampling bounds beside frozen local s=1 predictions; these are not T-slot receipts or a cloud noise sweep.](results/figures/frozen-anchors.png)

**RECORDED** Qollab IonQ simulator slots T01-T08 (2026-10-10 UTC) show W signed advantages from +0.002 to +0.011 and N advantages from -0.035 to -0.022. They are discrete anchors, not a cloud crossover; the per-slot outcomes and reproduction settings follow below.

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

Positive W favors the joint measurement over the ideal one-way reference. Negative N means the attained product strategy has lower fixed-prize loss than the published hedge. These are discrete simulator anchors, not a cloud noise sweep or threshold. Reproduce each run by selecting **IonQ Aria 1**, setting **Slot=Txx** and **Shots=1000** for W or **Shots=4000** for N, then running the project; the slot selects the recorded noise model shown above (including Forte 1 on T05/T06). All raw `RECORD_JSON` lines for these eight valid runs are in [`recorded_ionq.py`](recorded_ionq.py), with the compact index and outcomes in [`evidence_summary.json`](evidence_summary.json); both files are included in this project. Original Qollab console exports are retained under `results/exports/`.

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

## How to run (and replicate)

### Built-in simulator

On Qollab, select the built-in simulator and press Run with the default form values (512 shots, aria-1). The run prints live estimates and labels results as LIVE; stored curves and anchors are separate LOCAL MODEL and RECORDED evidence. The page's main program generates small circuits and evaluates both games in one run.

### IonQ simulator slots

Choose an available slot through the `slot` parameter only when running the project on the Qollab IonQ simulator; the run records the selected noise model, shot count and receipt. Available slot names and budgets are defined in `cloud_slots.py`. IonQ results are useful as measured anchors; they add no judging points and do not create a tunable cloud noise sweep. Do not select a real QPU.

### Local reproduction

From one working directory, the project folder `D:\Quantum Projects\Qollab\projects\noise-tax`, with repository dependencies installed:

```powershell
..\..\.venv\Scripts\python.exe experiments\run.py --suite frozen --independent-manifest review\manifests\frozen.json --draws 4000 --output-dir replication-frozen-01
..\..\.venv\Scripts\python.exe experiments\run.py --suite fresh --independent-manifest review\manifests\fresh.json --draws 4000 --output-dir replication-fresh-01
..\..\.venv\Scripts\python.exe ..\..\tools\qollab_local.py run . --backend ideal --shots 512
```

The output directories must be new and empty; choose new names for subsequent runs, or deliberately use `--resume` for an existing matching run. Full runs take several minutes each. To check either manifest without a full experiment, append `--validate-only --draws 1` and use another new output directory; this is a bounded smoke check, not inference evidence. The fresh harness compares against the shipped `results/frozen.json`, even with a separate output directory.

`experiments/make_curves.py` reads `results/summary.json`; it does not rebuild the summary from new full result files. Running it alone regenerates the shipped summary's curves, potentially stale for a new campaign. A new summary must be assembled and verified from both full suites before regenerating new evidence. The shipped summary can be regenerated with `../../.venv/Scripts/python.exe experiments/make_curves.py`.

To extend it, add a third game with an analytic reference and explicit advantage definition, or another calibrated noise model.

## What is new

The project puts two different quantum-game comparisons on a shared, inspectable noise-scale view, with frozen and independently seeded fresh curves, uncertainty distinctions, and recorded cloud anchors shown separately. This is a reproducible comparison and teaching tool. It does not claim that the underlying ideal strategies or noise channels are new.

## Limits

- No speedup, practical advantage, or noise reduction is demonstrated.
- The local channel is a calibrated IonQ-like approximation, not the device or a complete remote noise model. Calibration sensitivity is distinct from statistical confidence.
- W's comparator is an ideal optimal one-way sequential reference, not all LOCC or separable measurements. Its deterministic W crossing has calibration sensitivity, not an instance-bootstrap CI.
- N compares a fixed published hedge with the attained product recipe under one fixed prize. It does not certify a globally optimal noisy product strategy.
- The N crossover is deterministic for each computed mean curve; its interval reflects seeded instance uncertainty. The cloud observations are discrete measured anchors, not a cloud threshold.
- Results do not imply that a classical strategy beats quantum computation generally. Negative margins are shown plainly as wins for the named comparator.

## Judging-criteria summary

- **Novelty and creativity:** an interactive comparison of two distinct strategy margins and their modeled crossover behavior, with model mismatch made visible.
- **Technical execution:** Qiskit circuits, a shared approximate channel, seeded result bundles, crossover analysis, and separate recorded run receipts.
- **Impact potential:** helps learners and researchers see why ideal performance and noisy observed performance can differ, while showing the assumptions behind that comparison.
- **Documentation quality:** includes reproduction commands, definitions, plotted results with alt text, accessible interaction notes, and explicit limits.

## Accessibility

The web source provides native range/select/button controls, associated labels, visible focus styles, chart data tables, circuit text, and a polite live status region. These source features support keyboard and screen-reader access; browser/screen-reader acceptance is a human check on the published page. No audio is required. The demo video should include captions or subtitles.

## Disclosure

**AI tools:** AgentMesh routing (including OpenCode free models), OpenAI Codex models, and Claude Code were used during development and documentation. Work was produced during the hackathon window.

**Reused code:** `circuit_pack.py` is the shared packing helper written during this hackathon window and used by Entanglement Court, Eyes-Free, and The Noise Tax. It packs small circuits into one circuit for the Qollab IonQ one-job-per-run interface and splits measured counts back into their original blocks. `whispers_core.py`, `hedging_core.py`, `hedging_strategies.py`, and `product_bounds.py` were adapted in-window from the retired Two Whispers / Never Lose Twice build-window code (same author/team, Oct 9-10 UTC). The shared noise channel, crossover analysis, cloud slots, and UI are new in the merged entry. `reuse_sources.json` records the source hashes, import timestamps, and the reused synthesis, noise-analysis, receipt, calibration, and emulator references.

**Libraries and licences:** Qiskit (Apache-2.0), NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), and Matplotlib (custom Matplotlib license); Python standard library components use the Python Software Foundation License. Dependencies are listed in `requirements.txt`. MIT project licence is included in `LICENSE`.

**Platform references:** Qollab runtime documentation, hackathon rules, and project templates were consulted. The project follows the Qollab injected-backend and circuit-packing interface; no claim of original platform code is made.

**Attribution:** This effort is supported by Qollab & IonQ.

**Theme tag:** Quantum Unlocked.

**Repository:** https://github.com/sauravdasmg/Qollab

**Demo video:** [[VIDEO LINK]]

## Licence

MIT. See [LICENSE](LICENSE).
