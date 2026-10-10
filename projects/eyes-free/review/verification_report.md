VERDICT: FAIL

# Final independent claim verification

Reviewed 2026-10-10 UTC, during the authorized build window. This reviewer authored none of the implementation or submission documentation. Only this report was edited. No full experiments, noise sweeps, new cloud jobs, or many-seed simulations were run. The current numerical totals and all six recorded cloud fits reproduce, but eight claim, integration, reproduction, or disclosure failures prevent PASS.

## Scope and checks

Read README.md, PROJECT_PAGE.md, all nine top-level Python modules, HELPER_SPEC.md, LICENSE, requirements.txt, experiments/PLAN.md including both amendments, the experiment/decoder/summary/cloud-fit implementation, evidence_summary.json, recorded_ionq.py, the full frozen/fresh JSON evidence, saved development/G1 and cloud evidence, all ten Qollab HTML exports, and both earlier review reports. Read the supplied official rules including AMA, website rules, binding organizer answers, and the Eyes-Free entries in the global provenance log. Local results and earlier reviews are evidence to audit, not substituted for this review's checks.

Commands were run from the submission directory. The environment's bare `python` is Python 3.14 without pytest. The requested checker worked under it; execution/tests used `../../.venv/Scripts/python.exe`, the repository's documented environment. Bytecode writing was disabled for execution checks; pytest's cache provider was disabled to avoid changing the existing cache.

| Check | Observed result | Assessment |
| --- | --- | --- |
| `python ../../tools/build_window.py` | Build phase; deadline and feature freeze still ahead | OK |
| `python ../../tools/check_submission.py .` | All automated blockers pass except the absent PASS verifier report; six manual items remain | OK for checker scope, excluding this report and human items as requested |
| `../../.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` | **60 passed in 7.90 s** | OK; does not catch F1 or prove real browser downloads |
| `../../.venv/Scripts/python.exe ../../tools/qollab_local.py run . --backend ideal` | Exit 0; main called; runtime contract verified; targeted repeat reports **0.79 s** inside the runner | Execution OK; functional failures F1/F2 appear in stdout |
| Saved-evidence arithmetic | Recomputed all 792 local record success decisions from fit/decoder values; inspected every width/noise cell | OK |
| Bounded local replay | One saved nominal-noise width-4 record per suite, refitted and decoded from its WAV bytes | Exact agreement with saved fit and decoder outputs |
| Recorded cloud replay | Independently extracted each block with integer shifts/masks, computed even/odd counts, refitted all six series | Exact agreement with shipped cloud fit values |
| Top-level-only runtime audit | Nine Python files use only top-level project modules and bundled libraries; no filesystem data reads; `wave.open` receives BytesIO | OK; no dependency on results/, review/, experiments/, or parent-directory data during main |
| Shipped evidence availability | Top-level recorded_ionq.py contains all nine raw cloud records; evidence_summary.json contains local statistics and all six cloud fits including counts/intervals | Saved compact evidence is present; F1/F3/F6 remain |

The checker reported 19 shipped files under its enumeration; direct immediate-file enumeration found 15 top-level files. Every actual top-level file is below 2 MB (largest: recorded_ionq.py, 217,922 bytes; evidence_summary.json, 190,833 bytes). The larger full local JSON files remain local under results/, which is appropriate for upload size but must be distinguished from the compact shipped summary.

The local runner's Matplotlib Agg warning is expected in headless emulation and is not a Qollab chart failure. The real built-in export contains plot output and three fitted series at 256 shots per phase. No logged-out/browser/assistive-technology acceptance was performed in this review.

## Blocking failures: exact text, evidence, and required correction

### F1 — The documented recorded-data workflow rejects every bundled record

README.md:66 says: **“Paste each console `RECORD_JSON` line into `recorded_ionq.py` as described in that file, preserving the original record.”** PROJECT_PAGE.md:63 gives the same paste workflow. README.md:39 and PROJECT_PAGE.md:41 identify that file as the original count records.

The actual slot producer, main.py:79–80, emits:

```python
record = {"slot":slot,"suite":spec["suite"],"manifest_hash":spec["manifest_hash"],
          "shots":shots,"effective_noise_model":effective,"counts":counts,"manifest":manifest}
```

But receipt.py:18–19 requires:

```python
if record.get("schema") != SCHEMA or record.get("noise_model") != "aria-1":
    raise ValueError("unknown schema or effective noise model")
```

Further validation requires label, UTC, qubits, phase frame, and counts/manifest digests that the slot producer does not emit. The raw objects at recorded_ionq.py:3–11 are the slot schema, not the older receipt schema. All nine match the original exports exactly after the existing source_file annotation; the problem is ingestion, not falsified counts.

Direct `parse_records(RECORDED)` returns zero records and nine `unknown schema or effective noise model` errors. The default run prints:

```text
line 2: unknown schema or effective noise model
...
line 10: unknown schema or effective noise model
missing recorded Qollab IonQ evidence
Validated recorded packs: 0; these are not independent cloud instances.
Missing/duplicate recorded frozen sweep; no complete fit.
Missing/duplicate recorded fresh sweep; no complete fit.
```

Thus the shipped runtime never reaches either recorded sweep's fit. Exit 0 is insufficient to validate the documented replay. Align the producer, parser, and main assembly with the authentic slot schema, preserving raw counts and acquisition provenance. Add a regression that parses the actual bundled file and obtains the two complete sweeps. Merely renaming effective_noise_model will not fix the missing metadata/phase-frame fields. The existing tests validate the old phase_frame route and slot submission separately, without joining the slot output to the parser.

### F2 — The demonstrated Qollab run has no audio download despite the headline instruction

README.md:7 says: **“then check the parity chart, text receipt, and WAV download.”** PROJECT_PAGE.md:11 says: **“then inspect the parity chart, text receipt, and WAV download.”** README.md:14 describes **“downloadable WAV audio.”**

The actual built-in Qollab export `results/exports/saurav-eyes-free-entanglement-output-completed-2026-10-10T14-39-04.532Z.html`:1 contains the exact console message:

```text
Audio download unavailable: sendFile not injected; fallback needs operator verification.
```

The current default local run emits the same message. main.py:140 is `sender = globals().get("sendFile")`; lines 141–146 provide a download only if that function is callable, otherwise print the unavailable message. The shipped top-level set has no browser audio interface or alternative download implementation. The test injects a mock sender, so its success does not contradict the failed real Qollab export.

The conditional caveats at README.md:62,92 and PROJECT_PAGE.md:61 are useful but do not establish the headline feature. `results/g1.json` and the shipped summary also retain `js_bridge_and_audio_fallback` false and overall FAIL. Implement and verify a working Qollab audio/download path, or clearly limit the submission's claims to the functioning features and disclose that the intended audio delivery remains unmet. A generic pending human acceptance item cannot turn an observed missing core feature into PASS.

### F3 — Global provenance labels misclassify cloud results as local-only

README.md:28 says: **“Every value below is **LOCAL MODEL** evidence from an exact small-state simulation with a calibrated Aria-like noise approximation. It is not Qollab execution or device data.”** Immediately below, lines 30–39 present the RECORDED cloud table. This is contradictory provenance, not a punctuation issue.

evidence_summary.json:2 says:

```json
"evidence_label": "LOCAL MODEL (calibrated IonQ-like approximation, not device)"
```

Its line 6385 says:

```json
"scope": "Saved local simulation evidence only; Qollab IonQ simulator records are in recorded_ionq.py."
```

Yet its `cloud_fit` section begins at line 3395 and line 3396 correctly labels cloud RECORD_JSON counts. README.md:45 and PROJECT_PAGE.md:5 likewise describe the entire file as a **“compact LOCAL MODEL summary”**, without acknowledging its recorded cloud section. Scope the local-only statements to the local suites and give the mixed evidence file an accurate overall description; retain the correct per-section labels.

### F4 — The default circuit count is wrong

README.md:62 states: **“The default run analyzes three small GHZ circuits”**.

eyes_core.py:47 is:

```python
return [circuit(n, p + phase_frame) for n in WIDTHS for p in PHASES]
```

WIDTHS has 3 elements and PHASES has 12, so the default submits **36 circuits**, producing **three fitted series**, with 256 shots per circuit: 9,216 physical circuit shots in the local list job. main.py:15–17 also explicitly requires 36 count dictionaries. Correct “three ... circuits” to three width series / 36 circuits. This is a numeric execution-budget discrepancy.

### F5 — Sound and chart do not carry the full information claimed

PROJECT_PAGE.md:18 states: **“It makes the same fitted frequency, contrast, uncertainty, and fit status available visually, in structured text, and as a sound mapping.”** README.md:86 claims **“a measured fit and its uncertainty available in chart, semantic text, and sound”**. README.md:54 calls the outputs **“three equivalent presentations”**.

sonify.py:13 reads only frequency and contrast, and line 21 emits:

```python
return 0.5*c*np.sin(2*np.pi*CARRIER*f*t)*envelope
```

There is no uncertainty or fit-status encoding in the waveform. main.py:136–139 selects informative fits and exports only `informative[0]`; it does not export one sound for each plotted width. figures.py:10–12 plots measured phase/parity with frequency, contrast, and flag in the legend, but no interval/error-bar display. The text transcript does retain the complete fit and its intervals. A two-number digital round trip does not validate equivalence of these channels.

State precisely that optional sound encodes frequency and contrast of the selected informative series, while text carries the full uncertainty/provenance/diagnostics; specify the chart's actual information. Alternatively implement and validate the fuller representations. No additional quantum superiority or user benefit claim was found.

### F6 — The shipped local evidence lacks required acquisition metadata

The binding rule at `../../docs/hackathon-rules.md`:186–187 is: **“Local-simulation result files may ship as project files and be plotted during the run; label each with machine, simulator, Qiskit version, settings and date.”**

README.md:45 and PROJECT_PAGE.md:5 identify **“`evidence_summary.json` ... [as] the compact LOCAL MODEL summary of the saved local results”**. The shipped summary has no machine, software-version, or result-acquisition-date metadata. This was checked recursively over its keys. Manifest hashes and numeric sampling seeds are not run dates or software versions. Its top-level config even has the exact entries `"shots_per_phase": null` (line 66), `"noise_scales": null` (line 68), and `"grid": null` (line 69), although the suite-specific configuration correctly retains shots=1000, six scales, phases, and fit settings.

The local full evidence files contain Qiskit 2.5.2, NumPy 2.5.3, and SciPy 1.18.1, but the summary generator drops those versions. The full files are neither top-level nor below the upload limit. Add truthful machine, simulation implementation, exact software versions, settings, and acquisition date metadata to the shipped summary using the existing evidence/provenance. Do not substitute this review's date for the original run date. Repair the redundant null config keys or remove them with clear documentation.

Cloud provenance is separately sufficient to establish the documented day/model/shots/slots from source filenames, model fields, counts, and export records. It must still be made consumable under F1.

### F7 — The mandatory shared-helper disclosure is unfinished

The binding rule at `../../docs/hackathon-rules.md`:184–185 requires the same helper note in each project stating **“what it does, when written, which projects use it”** and identifying project-specific work.

README.md:113 states that the helper was **“written during the build window and shared with the related hackathon entries.”** PROJECT_PAGE.md:100 similarly says **“created during the window and shared with related entries.”** Neither names the actual consuming projects. The helper's own circuit_pack.py:1 contains only **“Phase-major disjoint-wire packs and little-endian marginalization.”** HELPER_SPEC.md:8–9 expressly says:

```text
Canonical shared participant/filename disclosure is pending orchestrator finalization; this file
must not serve as a substitute for the identical final disclosure across entries.
```

Finalize an accurate identical helper note with the specific project names and creation timing. If the file is actually project-specific rather than reused, correct the reuse claim instead. The present audit does not invent cross-project reuse or independently certify other entries' notes. The broad AI/library/probe disclosures are present; this specific required shared-code note remains incomplete.

### F8 — Documented local reproduction commands stop in the evidence-bearing checkout

README.md:74–75 lists:

```powershell
python experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json
python experiments/run.py --suite fresh --independent-manifest review/manifests/fresh.json
```

PROJECT_PAGE.md:69–70 lists the same commands; README.md:82 and PROJECT_PAGE.md:75 repeat the frozen command. experiments/run.py:208–209 deliberately protects existing evidence:

```python
if destination.exists() and not args.quick and not args.resume:
    raise ValueError("full evidence already exists; preserve it before a separate orchestrator run")
```

Both documented configurations were checked only through this preflight, before any simulation. Both immediately raise that exact ValueError because the full saved files exist. Preserve the guard and document `--output-dir` pointing to a new directory for each rerun, plus the fact that experiments/ and review/manifests/ come from the repository rather than the top-level Qollab upload. Do not instruct users to overwrite or delete the authentic evidence. Recorded cloud slot settings themselves are correct; their replay problem is F1.

## Claims table

Repeated numerical claims are grouped with both source locations. “OK” on a number does not override a related presentation or runtime FAIL above.

| Claim | Source | Reproduced value / evidence | OK/FAIL |
| --- | --- | --- | --- |
| Frozen audio fidelity 432/432 | README:5,49; PROJECT_PAGE:9,50; summary suites.frozen | 432 records; all 432 informative; all 432 independently recomputed decoder errors meet both limits | OK |
| Fresh audio fidelity 360/360 | README:5,50; PROJECT_PAGE:9,51; summary suites.fresh | 360 records; all 360 informative; all 360 meet both limits | OK |
| 24 frozen, 20 fresh seeded instances | README:49–50; PROJECT_PAGE:50–51 | 24 distinct frozen seeds and 20 distinct fresh seeds; disjoint; 18 records per seed | OK |
| 432/432 and 360/360 identified frequencies | README:49–52; PROJECT_PAGE:50–53 | Recomputed nearest width, absolute error <=0.25, and interval containment within width +/-0.5; 432 and 360 pass | OK |
| Audio tolerances 0.02 frequency, 0.01 contrast | README:52; PROJECT_PAGE:53; PLAN:17–18 | Frozen max errors 2.9028807801978473e-08 and 7.044340941675387e-07; fresh 2.945757504591029e-08 and 4.140304343813739e-07 | OK |
| Identification tolerance 0.25 and half-unit interval criterion | README:52; PROJECT_PAGE:53; experiments/run.py:254–256 | Largest recipe-frequency error 0.02200198132318798 frozen, 0.02186073980319203 fresh; interval criteria also pass for every record | OK |
| GHZ widths 1, 2, 4; width 1 reference | README:8,14,56; PROJECT_PAGE:13,26 | eyes_core.WIDTHS=(1,2,4); no frequency-only entanglement certification claim | OK |
| Twelve phase points per series | README:22,32,56; PROJECT_PAGE:26,34 | Twelve sorted phases per width in each suite; frozen step pi/6, fresh shift pi/24 | OK |
| Carrier 220 times fitted frequency | README:22; PROJECT_PAGE:26 | sonify.CARRIER=220; waveform formula matches; samples-only replay exactly matches saved decoder | OK |
| Nine blocks, 21 qubits, three phase points, four batches | README:24; PROJECT_PAGE:28 | Three phases times widths (1+2+4)=21 wires; 9 blocks; four batches provide 12 phases. E01 is the documented smoke exception | OK |
| One cloud circuit/job per run | README:24,66; PROJECT_PAGE:28,63 | One packed circuit at shared backend.run call, one result fetch/get_counts; no cloud loop | OK |
| Default analyzes three circuits | README:62 | 36 actual circuits, three fitted series | FAIL F4 |
| Default shots=256 | README:62; PROJECT_PAGE:61 | main signature; actual built-in export has 256 shots at each of 12 phases for each width | OK |
| “about 1 s” default runtime | README:7,62; PROJECT_PAGE:11,61 | Current local runner reports 0.79 s; plausible local estimate, not an independently timed browser guarantee. No end-to-end browser timing is in the saved export | OK as approximate estimate only; identify timing environment on publication |
| Acquisition 2026-10-10, aria-1, 1,000 shots/phase | README:8,32,56,66; PROJECT_PAGE:13,34,63 | E02–E09 source filenames are that UTC day; effective_noise_model aria-1; every packed count total is 1,000, so every marginal phase has 1,000 observations | OK |
| Frozen E02–E05; fresh E06–E09 | README:32,36–39; PROJECT_PAGE:34,38–41 | Four unique slots per suite, frames and independent manifest hashes agree with cloud_slots.py and manifests | OK |
| E01 smoke, 100 shots, excluded from fits | README:32,41; PROJECT_PAGE:34,43 | One 19-bit result 1010011000011110101 occurring 100 times; four expected asymmetric marginals; excluded from both fits | OK |
| Frozen width 1: frequency 0.992; contrast 1.000 | README:36; PROJECT_PAGE:38 | 0.9922171041710965; 0.9999999899999998 | OK |
| Frozen width 2: 1.999; 0.989 | README:36; PROJECT_PAGE:38 | 1.9985706741889826; 0.9889584761288279 | OK |
| Frozen width 4: 3.998; 0.951 | README:36; PROJECT_PAGE:38 | 3.997744296141045; 0.9505559387221133 | OK |
| Fresh width 1: 0.997; 0.991 | README:37; PROJECT_PAGE:39 | 0.9970041964892508; 0.9908850668475474 | OK |
| Fresh width 2: 1.997; 0.986 | README:37; PROJECT_PAGE:39 | 1.9974143966450224; 0.9863568871107461 | OK |
| Fresh width 4: 4.005; 0.955 | README:37; PROJECT_PAGE:39 | 4.0051720328305835; 0.954602163394363 | OK |
| All six cloud fits near 1,2,4 | README:8,56; PROJECT_PAGE:13 | Six informative fits; all recipe frequencies within their intervals. Exact replay differences from summary: zero | OK |
| RECORDED/LOCAL MODEL separation | README:28,45; PROJECT_PAGE:5; summary root labels | Correct table-level cloud labels but contradictory encompassing local-only labels | FAIL F3 |
| Same full information in three equivalent presentations | README:54,86; PROJECT_PAGE:18 | Audio only encodes f/C, first informative series; chart does not display intervals | FAIL F5 |
| Live Qollab WAV download | README:7,14; PROJECT_PAGE:11 | Saved actual Qollab export reports sendFile unavailable | FAIL F2 |
| Recorded results paste/replay | README:39,66; PROJECT_PAGE:41,63 | Authentic saved objects present, but zero accepted by main's parser | FAIL F1 |
| Reproduce local results using supplied commands | README:74–75,82; PROJECT_PAGE:69–70,75 | Both commands fail existing-evidence preflight | FAIL F8 |
| Local evidence includes required provenance metadata | Shipped evidence_summary.json; organizer rule:186–187 | No acquisition date, machine, or software-version metadata | FAIL F6 |
| No superseded cloud slot; corrected indexing disclosed | README:41; PROJECT_PAGE:43; WP-E-09 | Nine unique authentic slots, no duplicate replacements in exports; bit-slice repair is documented and independently verified | OK |
| Equal-information baseline; no superiority/speedup/user-study claim | README:88–96; PROJECT_PAGE:83 | Same fit/counts, baseline and audio both 12,000 shots/series; zero resampling; comparator retains full information; no measured improvement over text asserted | OK subject to F5 |
| Intervals descriptive, not guaranteed coverage | README:95; PROJECT_PAGE:83 | Frozen physical-frequency coverage 429/432; projection 431/432; contrast 432/432. Fresh all three 360/360. Boundary/mismatch misses retained | OK |
| Prior sonification arXiv:2504.04624 and arXiv:2203.07879 | README:18; PROJECT_PAGE:22 | Both retrieved from arXiv and relevant to quantum sound/sonification; no unsearched uniqueness claim made | OK |
| Qiskit 2.x and disclosed library licences | README:70,114; PROJECT_PAGE:100; requirements.txt | Environment Qiskit 2.5.2; NumPy/SciPy BSD family, Qiskit Apache-2.0, Matplotlib PSF-derived licence; shipped code has no Aer dependency | OK |
| Shared helper disclosure complete | README:113; PROJECT_PAGE:100; HELPER_SPEC:8–9 | Purpose/window and Eyes-Free-specific work stated, but exact consuming projects/final common note absent | FAIL F7 |

The two cited papers were checked directly: [arXiv:2504.04624, Notes on Quantum Soundscapes and Music](https://arxiv.org/abs/2504.04624) and [arXiv:2203.07879, Superconducting qubits as musical synthesizers for live performance](https://arxiv.org/abs/2203.07879). This confirms citation relevance, not an exhaustive novelty search.

## Evidence, baseline, and protocol audit

For each suite the complete Cartesian record coverage is present: 3 widths times 6 scales (0, 0.5, 0.75, 1, 1.5, 2) times 24 or 20 seeds. Every one of the 18 cells has its full denominator, all informative, all audio-success and identification decisions passing the declared thresholds. There are no dropped abstentions in these files. Cells are correlated within a seed; the docs correctly avoid calling them independent cloud trials. Seed-level audio/inference flags are 24/24 and 20/20. The gate is a digital information-preservation criterion, not a gain over the exact text baseline.

The main fitter receives phases and counts only. Width enters later scoring, not fit_counts. Mathematical controls demonstrate GHZ parity cos(n*phase), product parity cos(phase)^n, and zero incoherent parity. The pure local noise code uses rz/sx/x/rxx compilation, noiseless rz, single-qubit depolarization 2*r1 and two-qubit depolarization 4*r2/3, with r1=0.0005, r2=0.009 and readout=0. These remain an approximation to IonQ noise, as documented; cloud agreement does not calibrate or uniquely identify the physical noise.

The amended manifest contract is implemented and tested for both suites; file-byte hashes match cloud_slots.py and summary. Exact noisy probability vectors, KL-projection targets, residuals, and empirical coverage are present in the full evidence. The earlier manifest/truth/coverage defects in early_math.md have been repaired. Its warning that fresh seed values had already been sampled before that early review still limits any claim of outcome-unseen holdout status. Current README/page use “fresh” without asserting untouched/blind outcomes, so no additional failure is assigned.

All six source hashes in evidence_summary.json match the current source bytes, including both manifests, full local files, g1.json and cloud_fit.json. Summary record counts and suite/seed statistics exactly match full evidence. For saved nominal-noise width-4 records with seeds 2026100500 and 20261011500, refitting counts gave zero difference in f/C; decoding existing WAVs gave zero difference from saved decoder outputs and their SHA-256 hashes matched. These are bounded replay checks, not fresh full-suite independent reproduction.

Cloud marginalization was independently recomputed as `((int(bitstring, 2) >> offset) & ((1 << width) - 1)).bit_count() % 2`; this avoids relying on the repaired substring routine. For both suites the frequency intervals are [0.975,1.025], [1.975,2.025], and [3.975,4.025]. Contrast intervals are frozen [0.8912654901716573,1], [0.8743782571519161,1], [0.8335105972300244,1]; fresh [0.8416779541940168,1], [0.8775061858318477,1], [0.8465580785235766,1]. All agree with the shipped summary. The correct numerical analysis does not repair main's incompatible parser.

There are no crossover, certification-count, quantum advantage, or hardware superiority claims to verify for this entry. Frequency alone is explicitly not an entanglement witness; contrast is explicitly not GHZ fidelity.

## Submission requirements and provenance

| Requirement | Evidence / limitation | Result |
| --- | --- | --- |
| MIT licence | LICENSE:1–21, copyright 2026 Saurav Das; README:120; PROJECT_PAGE:103 | Present |
| Exact attribution | `This effort is supported by Qollab & IonQ.` in README:10,121 and PROJECT_PAGE:106 | Present |
| AI, libraries, templates, prior work | README:109–115 and PROJECT_PAGE:96–100 name AgentMesh/OpenCode/OpenAI, reserve Claude, libraries, platform materials, and the pre-window probe with no code reuse asserted | Present at broad disclosure level; task-specific model attribution is not fully established by the available hook log |
| In-window/shared helper reuse | Purpose and window disclosed; exact project list/final common note missing | FAIL F7 |
| Theme | Quantum Unlocked in both docs | Present; platform tag remains human step |
| Accessibility notes | Text path, labels, optional audio, keyboard/focus/captions, direct-acceptance caveat | Present; F2/F5 affect delivered claims; actual AT behavior untested |
| Four judging criteria | Both docs explicitly cover novelty, technical execution, impact, documentation | Present |
| Repo link | https://github.com/sauravdasmg/Qollab in both docs | Present; public/logged-out repository access is not asserted as tested |
| Video | `[[VIDEO LINK]]` remains | Allowed human step in this work order |
| Build window | Phase check and supplied receipt; project-specific provenance entries occur after kickoff | Consistent with in-window work; no contrary pre-window implementation event found |
| Qollab default | Real built-in export and local ideal execution succeed | Execution present; parser/download behavior still fails |
| Cloud confirmation | E01–E09 authentic saved Qollab simulator records and six correct replayed fits | Numerical confirmation present, not hardware evidence or a repaired live replay |
| Logged-out acceptance/publication | No direct logged-out run established here | Human-only outstanding item |

Relevant provenance log entries: line 73 admits Eyes-Free after another entry's technical-claim kill at 00:42:31 UTC; lines 80–88 record Eyes-Free implementation/testing in the open window; line 124 records the early HOLD at 03:30:59; lines 129–130 record repaired checks and frozen/fresh runs; lines 138–139 record slot/upload work; line 168 records E01–E09 completion at 14:47:25; line 176 records the repaired cloud analysis and correct rounded fits at 14:59:15. Hooks often identify agent as “main” and do not establish a complete per-task model ledger. They support timing, not a fabricated precise AI attribution. No global process/state/provenance file was modified because the work order authorizes only this report.

## STYLE (non-blocking)

- README:56 repeats “RECORDED (Qollab IonQ simulator)” and ends with a doubled period; line 96 has another doubled period.
- README:66 and PROJECT_PAGE:63 refer to the cloud table “below” although it is above.
- PROJECT_PAGE's consecutive Results/Cloud evidence headings and large leading Evidence files section could be clearer without changing any claim.
- recorded_ionq.py:1 still says “No evidence is bundled.” despite nine embedded objects. Remove this stale comment when repairing F1; it is not evidence that the records are absent.
- HELPER_SPEC.md contains older slot-interface details (including the historical E10 phase-frame description); distinguish historical implementation notes from the current slot ledger when finalizing it.
- The summary retains historical G1 FAIL/independent-pass-false flags and raw evidence's cloud_confirmation=false. Do not silently relabel these as new passes. Explain their generation stage and add later independent status only after actual corrections/verification.
- The approximate one-second runtime currently matches local emulation; state the measurement environment and avoid implying a measured end-to-end browser loading guarantee.

## Snapshot and disposition

| File | SHA-256 at review |
| --- | --- |
| README.md | d76f398df2efa8aed0e9b58d161bc847be4ea4aa0af1f95807c6d36bbd1b9847 |
| PROJECT_PAGE.md | 220da874ee33992e1081cec361b81845b798e98d9af7df6d8d54a70fa6c0ebfd |
| main.py | eb598669c181befc791426534d4062fcfd65b0527f37bf16c59dfd678a090eef |
| recorded_ionq.py | 41acb96e9dbf4bee0997b91c82c39f2829f4eb90e9bfbed52cd723e4cf38de38 |
| evidence_summary.json | e89f4d627562f33835f5436b30e11864837c241b5833bcb0b39cb3e180261cf0 |

Required for a subsequent PASS: resolve F1–F8, rerun focused parser/download/contract checks and this claims audit against the final shipped files. Existing scientific counts do not need replacement merely to address these failures. Full independent experiments, browser acceptance, publication, and video were not performed or claimed by this quick verification.
