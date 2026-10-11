VERDICT: FAIL

# Round-2 FINAL independent claim verification: Eyes-Free Entanglement

Reviewed 2026-10-10 UTC. The reviewer wrote none of the code or docs. Only this file was edited. No full experiments, noise sweeps or cloud jobs were run. Python was `D:\Quantum Projects\Qollab\.venv\Scripts\python.exe`, with bytecode writing and the pytest cache disabled.

The numbers and the code now hold up. All round-1 code/evidence findings are resolved, and all six recorded cloud fits reproduce. Four documentation findings remain (N1-N4). Each is a text-only fix with no code change. They are claims that do not match the current published page, or labels and disclosures that are inaccurate. By the project's own rule these block PASS.

## 1. Commands run

| Check | Result |
|---|---|
| `python -m pytest tests web -q` | 74 passed in 11.2 s |
| `python ../../tools/check_submission.py .` | One blocker, "Verifier report says PASS", which is this report. All other blockers pass. Six MANUAL human-only items remain. 19 shipped files, all under 2 MB. |
| `python ../../tools/qollab_local.py run . --backend ideal` | Succeeded. It printed 3 live series, then "Validated RECORDED packs: 9", then six RECORDED transcripts. There is no "missing recorded evidence" line. |
| `main.recorded_estimates()` | 9 records, 0 errors, 6 informative fits. They equal `evidence_summary.json` cloud_fit to under 1e-9 on frequency and contrast. |
| Independent refit | Integer shift/mask marginalization of `recorded_ionq.RECORDED`, then a plain unweighted least-squares fit. Every block has 1,000 shots. Results are in the table below and agree with the shipped binomial fits to within about 0.01. |
| `experiments/run.py --help` and the guard code | `--output-dir` is accepted. A new directory passes the preflight (run.py:208-211). |
| Shipped-set audit | The only file read is `wave.open(BytesIO)`. There are no other file reads, and the modules import only top-level modules. `uploads/eyes-free-web.zip` holds the same bytes as the project for every file except `evidence_summary.json` (see Section 5). |

Independent refit versus shipped binomial fit (frequency; contrast):

| Series | Independent LS refit | Shipped fit |
|---|---|---|
| frozen n1 | 0.990; 0.999 | 0.9922; 1.0000 |
| frozen n2 | 2.000; 0.988 | 1.9986; 0.9890 |
| frozen n4 | 3.998; 0.9506 | 3.9977; 0.9506 |
| fresh n1 | 0.993; 0.990 | 0.9970; 0.9909 |
| fresh n2 | 2.002; 0.980 | 1.9974; 0.9864 |
| fresh n4 | 4.003; 0.955 | 4.0052; 0.9546 |

The human-accepted frozen n=4 values (3.9977, interval [3.975, 4.025]; contrast 0.9506, interval [0.8335, 1]) equal the shipped fit exactly.

## 2. Round-1 findings: status

| ID | Round-1 problem | Current evidence | Status |
|---|---|---|---|
| F1 | Parser rejected every bundled record | `main.recorded_estimates()` returns 9 records, 0 errors and both sweeps. `receipt.normalize_slot_record` exists (receipt.py:35). `tests/test_recorded_slots.py` parses the real `RECORDED`. The stale comment is replaced by recorded_ionq.py:1: "Nine original Qollab IonQ slot records. Preserve raw RECORD_JSON ...". | RESOLVED |
| F2 | WAV download missing in the observed run | README:7 "WAV download requires `sendFile`; the observed Python fallback run did not receive it." README:14 "WAV export is conditional on `sendFile`." main.js:180 hides the button unless `sendFile` is a function. main.js:97-141 plays audio in the browser. Provenance line 282 (human, 2026-10-10): the page ran, audio played for all fringe types, and the chart drew. The claim is now limited to what works. | RESOLVED |
| F3 | Cloud results labeled local-only | README:28 now reads "Evidence has two separate sources: RECORDED ... and LOCAL MODEL ...". evidence_summary.json `evidence_label` is "Mixed evidence: LOCAL MODEL suites and RECORDED Qollab IonQ simulator cloud fits". Its `scope` field separates the two. README:45 and PROJECT_PAGE:42 call it a "compact mixed evidence index". | RESOLVED |
| F4 | "three circuits" | README:62 and PROJECT_PAGE:62 say "36 ... circuits ... three fitted width series (256 shots each; 9,216 circuit shots)". This matches eyes_core.py:47 and main.py:16. | RESOLVED |
| F5 | Sound and chart did not carry full information | README:4 "Sound encodes the fitted fringe frequency as pitch and contrast as digital amplitude." README:125 "Playback encodes selected frequency and contrast, not uncertainty or fit status". Text and table carry the intervals. README:86 and PROJECT_PAGE:14 describe the three outputs as different channels. The code agrees: sonify uses only f and C, and main.js:129-131 does the same. The residual doc problem about the chart is N1. | RESOLVED, but see N1 |
| F6 | No acquisition metadata in the summary | `provenance` has generated_utc, machine "Saurav", platform, Python 3.14.6, Qiskit 2.5.2 and NumPy 2.5.3. Each suite's provenance has software_versions (numpy 2.5.3, scipy 1.18.1, qiskit 2.5.2), simulator, noise_settings and settings. It also has `acquisition` with date_utc 2026-10-10 and a stated date_basis. The original host and Python version are honestly marked "not captured". Top-level config has shots_per_phase 1000 and noise_scales [0, 0.5, 0.75, 1, 1.5, 2], no longer null. | RESOLVED |
| F7 | Shared-helper note unfinished | The note now names projects (README:113, PROJECT_PAGE:101, HELPER_SPEC:8, circuit_pack.py:3). The named projects are wrong; see N4. | PARTIAL (N4) |
| F8 | Local reproduction commands blocked by the existing-evidence guard | README:73-75 and PROJECT_PAGE:69-71 now carry `--output-dir results/reproduce-*`. README:78 says to use a new directory per rerun and that `experiments/` and `review/manifests/` are repository files, not in the upload. | RESOLVED |

## 3. Blocking findings (all text-only fixes)

### N1. Docs say the chart has no intervals, but the page chart now draws error bars and a fitted curve

This is stale text. The current page has pointwise error bars and a fitted curve.

Docs text:
- README.md:54: "The JS chart shows measured parity without fit intervals; `figures.py` supplies the Python fallback chart ... also without intervals".
- README.md:94: "the parity chart omits fit intervals".
- PROJECT_PAGE.md:14: "Its chart shows measured phase/parity without fit intervals."
- PROJECT_PAGE.md:56: "The JS page and `figures.py` fallback chart show phase/parity without fit intervals".
- PROJECT_PAGE.md:84: "the chart shows phase/parity without fit intervals".

The code:
- web/main.js:84-91 draws a pointwise Wilson 95% interval bar for every phase point.
- web/main.js:78-83 draws the fitted offset + cosine + sine curve.
- web/main.js:97-99 gives the chart note: "Points show pointwise 95% Wilson intervals; purple curve is the fitted offset + cosine + sine model. Fit parameter intervals are in the results table."
- web/index.html:14 adds a table with Phase, Parity, Shots and "95% parity interval" columns.

Required fix. In each of those five places, replace the "without fit intervals" wording with text like this: "For RECORDED and LIVE series the JS chart draws measured parity with pointwise 95% Wilson intervals and the fitted offset + cosine + sine curve, with a matching data table. LOCAL MODEL reference entries draw analytic points and curve with no sampling error bars. The fit-parameter intervals for frequency and contrast are shown in the results table, the text and Full fit details, not on the chart. The `figures.py` fallback chart shows no intervals."

Also update the README:54 and PROJECT_PAGE:56 alt text so it does not imply the chart has no uncertainty display.

### N2. The page's "LOCAL MODEL" rows are an invented decay law, not the LOCAL MODEL evidence, and the docs do not say so

web/eyes_bridge.py:16-27 builds the catalog with `contrast = exp(-0.025 * scale * n)` and `frequency = n` for noise scales 0, 0.5, 1 and 2. The page shows these rows with the source label "LOCAL MODEL", a "Noise scale" column, and zero-width intervals.

The README uses "LOCAL MODEL" for the calibrated Aria-like simulation suites. Those suites give different values. The mean fitted contrast in `results/frozen-evidence.json`:

| Width | At 1x noise, saved suite | At 1x noise, catalog formula | At 2x noise, saved suite | At 2x noise, catalog formula |
|---|---|---|---|---|
| n=1 | 0.9995 | 0.9753 | 0.9991 | 0.9512 |
| n=2 | 0.9858 | 0.9512 | 0.9709 | 0.9048 |
| n=4 | 0.9591 | 0.9048 | 0.9174 | 0.8187 |

A reader who sees "LOCAL MODEL, noise scale 1, n=4, contrast 0.905" will reasonably take it to be the evidence in the README table, and it contradicts that evidence. The bridge status string says "analytic reference ...". README:125 and PROJECT_PAGE:111 say only that these entries are "illustrative references, not new acquisitions". Neither says what the numbers are.

Required fix. In README ("Publication and provenance" paragraph) and PROJECT_PAGE (same section), state: "The page's LOCAL MODEL catalog rows are a stylised analytic reference (frequency = n, contrast = exp(-0.025 x noise-scale x n), no sampling). They are not outputs of the calibrated noise simulation and do not match the saved 432/360-record suites (for example, the mean fitted contrast of the saved frozen suite at 1x noise and n=4 is 0.959, not 0.905)."

The alternative fix is to rename the page's source label for those rows, for example "ANALYTIC REFERENCE". That means changing `source` in `fringe_catalog()` and the matching `"LOCAL MODEL"` string checks in web/main.js (lines 13, 97) and web/test_bridge.py. It needs a rebuild and a re-test, so the text fix is cheaper.

### N3. The documented recorded-batch reproduction cannot be done on the published JS page, and the page's one IonQ action is undocumented

README.md:39 and PROJECT_PAGE.md:35 say: "select IonQ Aria 1, set Slot=E02 ... and Shots=1,000, then run". README.md:66 and PROJECT_PAGE.md:64 say to "use the fixed settings shown by the slot selector" and to paste each `RECORD_JSON` line into `recorded_ionq.py`.

The published artifact is the flattened `--web` set. `tools/package_project.py:26` says "index.html + main.js at top level take precedence; main.py stays (bridges may import it)". The slot/shots/phase_frame parameters live only in `main.py:49`. The JS page never calls `main()`. Its only IonQ action is the button "Run one packed IonQ sample". That button calls `ionq_sample(backend, 128)` in web/eyes_bridge.py:66, which uses `pack(0.0)`, 128 shots, no slot, and returns a partial parity sample with no fit. The docs never mention this button.

The docs therefore tell a reader to do something the published page cannot do. This breaks the requirement that the docs state how to reproduce the recorded results.

Required fix. In README ("IonQ simulator slots" and the line-39 paragraph) and PROJECT_PAGE (lines 35 and 64), state:
- Slot runs E01-E09 were made with the Python `main.py` project variant (upload `uploads/eyes-free.zip`, not the `--web` build). Use its parameters `slot=E02..E09` and `shots=1000`. That is what produced the `RECORD_JSON` lines.
- The published JS page does not expose slots. It only replays the embedded recorded sweeps.
- The page offers one optional button, "Run one packed IonQ sample". It submits one 21-qubit packed circuit at 128 shots, yields a partial parity value only, and does not reproduce any recorded slot.

### N4. Shared-helper note names projects whose code Eyes-Free does not share

The note appears at README.md:113, PROJECT_PAGE.md:101, HELPER_SPEC.md:8 and circuit_pack.py:3. It says `circuit_pack.py` "is used by Entanglement Court, The Noise Tax and Eyes-Free."

The checks:
- Eyes-Free's `circuit_pack.py` is its own file. It imports `eyes_core`, and its API is `pack(phase_frame)`, `unpack` and `smoke_pack`.
- It is not byte-identical to any other project's file. The md5 hashes differ across all five `projects/*/circuit_pack.py`.
- The other files use `pack_circuits` / `unpack_counts`, and no other project imports Eyes-Free's file.
- Entanglement Court's own note (README.md:121, HELPER_SPEC.md:11) says its helper is also used by "Two Whispers Make a Word and Never Lose Twice", not by Eyes-Free.
- The Noise Tax note names the same three projects, but its file is also different.

The hackathon rule at `docs/hackathon-rules.md:184-185` needs the note to say what the helper does, when it was written, and which projects use it. The current statement is inaccurate for this file, and the notes disagree across entries.

Required fix. If code is not shared, replace the sentence with the truth: "`circuit_pack.py` is Eyes-Free's own helper, written in the build window. It packs phase-major circuits onto disjoint wires and marginalizes little-endian counts. It contains no code from other entries; sibling entries have separately written files of the same name." If it is a deliberately common helper, instead use one final identical wording across all entries, with the exact project list, and ship the same file.

## 4. Claims table

All README/PROJECT_PAGE numbers were traced to a shipped file or to `results/`.

| Claim | Source | Reproduced value | Status |
|---|---|---|---|
| Frozen audio fidelity 432/432 | README:5,49; PAGE:5,51 | summary.suites.frozen.record_count 432. Seed-level flags 24/24. | OK |
| Fresh audio fidelity 360/360 | README:5,50; PAGE:5,52 | record_count 360. Seed-level flags 20/20. | OK |
| Frozen/fresh frequency identification 432/432 and 360/360 | README:49-50; PAGE:51-52 | Cell-level `identified` equals the denominator. | OK |
| 24 and 20 seeded instances | README:49-50 | 24 and 20 seed lists in the summary. | OK |
| Thresholds 0.02 (frequency), 0.01 (contrast), 0.25 | README:52 | Unchanged from the round-1 recomputation. Maximum observed errors are far below the limits. | OK |
| Cloud table (frequency; contrast) | README:36-37; PAGE:32-33 | See the refit table in Section 1. All 12 values match to the printed digits. | OK |
| Human-accepted n=4 frozen fit | provenance line 282 | 3.9977 [3.975, 4.025]; 0.9506 [0.8335, 1] equals the shipped fit. | OK |
| Acquisition 2026-10-10, aria-1, 1,000 shots, slots E02-E09; E01 100-shot smoke, excluded | README:8,32; PAGE:28 | `recorded_ionq.py` has 9 objects. Slot, suite, shots and effective noise model all match. | OK |
| Nine blocks, 21 qubits, 3 phases per batch, 4 batches | README:24; PAGE:24 | circuit_pack.pack and cloud_slots.build_slot match. | OK |
| Default run is 36 circuits, 3 series, 256 shots, 9,216 circuit shots | README:62; PAGE:62 | eyes_core.py:47 and main.py:16. | OK |
| About 1 s runtime | README:7,62 | Local emulation only. The docs say so. | OK |
| Chart shows no intervals | README:54,94; PAGE:14,56,84 | The page draws pointwise Wilson 95% intervals and the fitted curve. | MISMATCH (N1) |
| LOCAL MODEL catalog rows on the page | eyes_bridge.py:16-27; README:125 | They use an invented decay law and do not match the saved suites. | MISMATCH (N2) |
| Recorded-batch reproduction by "Slot=E02, Shots=1000" | README:39,66; PAGE:35,64 | Not possible on the published JS page. | UNBACKED on the published artifact (N3) |
| Helper "used by Entanglement Court, The Noise Tax and Eyes-Free" | README:113; PAGE:101 | The files are separate and not identical. | MISMATCH (N4) |
| Sound encodes frequency and contrast only; text carries the intervals | README:4,125; PAGE:3,14,111 | sonify.py and main.js:129-131 agree. | OK |
| WAV only where `sendFile` exists | README:7,14,125 | main.js:146,180 agree. | OK |
| Audio for RECORDED/LIVE/LOCAL MODEL | PAGE:7; index.html | All fringe types play (main.js:117-141). Human acceptance confirms. | OK |
| RECORDED, LIVE and LOCAL MODEL labeling in the result table | main.js:13; eyes_bridge.py | RECORDED comes from the embedded sweeps. LIVE comes from the injected ideal simulator. LOCAL MODEL labeling is questioned in N2. | OK except N2 |
| Local reproduction commands | README:73-75; PAGE:68-71 | `--output-dir` is accepted and the guard is satisfied. | OK |
| Prior sonification arXiv:2504.04624 and arXiv:2203.07879 | README:18; PAGE:18 | Retrieved and relevant in round 1. The docs make no uniqueness claim. | OK |
| No speedup, superiority or learner-benefit claim | README:88-96; PAGE:82-84 | None is made. Frequency alone is explicitly not an entanglement witness. | OK |

## 5. Baseline, evidence and shipped-set audit

- **Baseline.** The text/table comparator carries the same fit, so no gain over text is claimed. Baseline and audio paths both use the same 12,000 shots per series (`baseline_shots` and `audio_shots` are both 12000, `resamples` 0). The fit sees only phases and counts, never the width. The saved-evidence gates remain historical G1 FAIL. They are disclosed at README:127.
- **Noise model.** It is stated as local and approximate (r1 = 0.0005, r2 = 0.009, readout 0, basis rz/sx/x/rxx). Cloud agreement is not claimed to calibrate it.
- **Shipped-set integrity.** `uploads/eyes-free-web.zip` (built 14:52) holds the same bytes as the project for every file except `evidence_summary.json`. That file was regenerated later, with the corrected labels and provenance. Rebuild the zip with `python tools/package_project.py eyes-free --web` from the repository root before upload, or it will ship the older summary. The rebuild changes only the data summary; the code files are already identical.
- **Contract.** All BLOCKER checks pass except this report. The six MANUAL items are human-only (publish, logged-out run, video, public repo, theme tag, in-window attestation).

## 6. Submission musts

| Requirement | Evidence | Status |
|---|---|---|
| MIT licence | LICENSE; README:120; PAGE:104 | Present |
| Exact attribution line | README:10,121; PAGE:107 | Present |
| AI, library and prior-work disclosure | README:109-115; PAGE:99-101 | Present (helper note is N4) |
| Theme tag | "Quantum Unlocked" | Present |
| Accessibility notes | README:105-107; PAGE:93-95 | Present |
| Four judging-criteria summaries | README:98-103; PAGE:86-91 | Present |
| Repo link | https://github.com/sauravdasmg/qollab-ionq-2026 | Present (public access not tested) |
| Video | `[[VIDEO LINK]]` remains | Allowed human step |

## 7. STYLE (non-blocking)

- README:92 still says the final page's browser acceptance is unestablished. It could now cite the human acceptance (provenance line 282, 2026-10-10: the page ran, audio played for all fringe types, the chart drew, and the n=4 values matched). It should still say screen-reader and keyboard behavior are untested.
- README:54 and PAGE:56 alt text end with "... WAV". WAV is conditional, so say "optional WAV where `sendFile` exists".
- README:56 duplicates the line-8 RECORDED sentence and ends with a doubled period.
- README:66 and PAGE:64 say the fits are "below" or "above" inconsistently with the layout. PAGE:39-40 has stray blank lines.
- The result-table column "Noise scale" shows "aria-1" for RECORDED rows and 0 for LIVE rows. A column title such as "Noise scale / model" would be clearer.
- `evidence_summary.json` still carries the historical g1 gate with `overall: FAIL` and `js_bridge_and_audio_fallback: false`. This is explained by `historical_status_note` and README:127. Keep that note prominent.
- The Python `main.py` fallback still prints the older "Audio download unavailable" message when `sendFile` is missing. This is fine, but it is not what the JS page shows.

## 8. What is required for PASS

Make the four documentation edits N1-N4 in README.md and PROJECT_PAGE.md. N4 also needs the HELPER_SPEC.md line and the circuit_pack.py docstring. Then rebuild the zip from the repository root. No code change is needed if N2 is fixed by text. Nothing in the numbers needs to change. Browser, logged-out and video steps remain human-only.
