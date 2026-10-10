VERDICT: FAIL

Independent final review, 2026-10-10 UTC. Reviewer did not author the implementation or submission documentation. Only this report was edited. Full experiments, sweeps, and new cloud jobs were not run; this review uses saved evidence, independent count decoding, deterministic mathematical checks, existing tests, and short built-in runs. The task's quick-check restriction supersedes the broader verify-claims skill's full fresh-seed rerun procedure.

The principal numerical results reproduce: LOCAL MODEL ideal certification is 0.50/0.50, nominal Aria-like certification is 0.417333/0.427700, and the retained RECORDED cloud observations are 12/12 easy certificates and 0/12 near-threshold certificates. The runtime and tests work. FAIL is for the exact reproduction, evidence-labeling, documentation, and evidence-retention findings below; it does not mean the reproduced certification totals are incorrect.

## Scope and checks actually performed

Read README.md, PROJECT_PAGE.md, main.py, all top-level core/helper modules, recorded_ionq.py, evidence_summary.json, experiments/PLAN.md including its amendment, the local harness/noise/summary generator, saved frozen/fresh/development results and gate/status files, all 33 HTML console exports, both earlier independent reviews and their manifests, the supplied official rules/answers, and 67 matching project provenance entries. Inspected all three referenced PNG figures. Examined the companion web bridge and source inventory for the accessibility/deployment distinction.

`python ../../tools/build_window.py` reported the build phase. The supplied opening receipt is consistent with the project provenance. The first matching log entry is 2026-10-09T23:19:27Z; the reviewed campaign-completion entry is 2026-10-10T15:50:16Z. No pre-window implementation is established by the reviewed log. Logs are evidence of recorded activity, not an independent exhaustive attestation of authorship.

The bare `python` executable is `C:/Program Files/Python314/python.exe` and lacks pytest and Qiskit. Scientific commands were therefore run with the documented repository interpreter `../../.venv/Scripts/python.exe`; that environment issue is not a project failure. Tests generated temporary fixtures under review/.verification-tmp-20261010-1604. Automatic approval review rejected cleanup with “blocked by policy,” including an explicit-path cleanup attempt after verifying the target was inside this workspace. Those fixtures remain; they are test artifacts, not submission evidence. The isolated-package temporary copy was automatically removed by its temporary-directory context.

| Check | Actual result | Assessment |
|---|---|---|
| `python ../../tools/check_submission.py .` | All substantive automated blockers PASS; its sole failing blocker is the absent/not-PASS verification report. Six human-only steps remain. | OK under the task's exclusions; this FAIL report must not be changed to bypass the checker. |
| Repository Python, `../../tools/qollab_local.py run . --backend ideal` | Exit 0; default 200 shots; six small circuits; 3.49 s reported by runner. | OK runtime; see F1 for the published timing claim. |
| Isolated copy containing only the 17 existing top-level files, same default command | Exit 0; 3.79 s; one LIVE exhibit plus 25 RECORDED exhibits. | OK: no results/, review/, experiments/, web/, or figures/ directory needed for this Python run. |
| Same isolated copy, built-in `--param slot=C08` | Exit 0; 0.84 s. | OK: embedded campaign manifests suffice without local review files. |
| Repository Python, `-m pytest tests -q -p no:cacheprovider --basetemp=review/.verification-tmp-20261010-1604 --tb=short` | 51 passed, 5 warnings, 35.86 s. | OK. Default pytest temp directory first produced seven fixture permission errors; using a new writable temp directory resolved all seven. |
| Warnings | Matplotlib reports more than 20 open figures; Agg reports noninteractive display in the isolated slot check. | Non-blocking resource/display warnings; no runtime error. |
| Cloud archive | 31 full receipts matched 31 exported full JSON records; 25 retained by loader; six superseded near-threshold runs excluded; zero malformed records. | OK. |
| Current cloud circuit identity | C08-C25: 18/18 circuit and recipe hashes match their retained recordings. C02-C07: 0/6 match. | FAIL for generic legacy reproduction instructions, F2. |

The checker counts 21 potential shipped files because it additionally counts four web assets intended to be flattened at publishing. The requested Python top-level set has 17 files. Both inventories are below 100 files and every included file is below 2 MB: recorded_ionq.py is 656,119 bytes and evidence_summary.json is 1,476,126 bytes. The checker reports zero job-call sites because the runtime uses `active.run`, which its simple matcher misses. Manual inspection and dispatch tests establish one run, one `job.result()`, and one cached result's `get_counts()` per actual execution path; no remote circuit list, automatic retry, or second job is used.

## Claims table

R denotes README.md; P denotes PROJECT_PAGE.md. References use the reviewed files' line numbers. JSON paths refer to the named saved file; evidence_summary.json occupies one physical line. Rounded decimals below are evaluated as rounded descriptive values, not exact inequalities. Repeated headline/table claims are grouped with all their source locations.

| Claim | Source | Reproduced value / evidence | OK/FAIL |
|---|---|---|---|
| Four-qubit connected graph and product preparation | R18; P15 | graphs.py has four connected bipartite four-wire templates; cases.make_demo builds graph/product preparations and inverse local frames. | OK |
| Uniform ideal Z distributions; total variation zero | R4,18; P3,11,15 | Independent statevector checks on all four demo cases: max TV 1.53e-16; max discrepancy from 1/16 is 6.94e-17. Diagonal phase flips preserve these probabilities. Zero is the exact mathematical value, not an assertion that finite sampled histograms match exactly. | OK |
| Two coloring bases / settings | R10,18; P15 | A/B partition covers all four graph generators; same counts are used in the comparison. | OK |
| Biseparable threshold 1/2, certificate strictly above it | R18; P15 | Independent Schmidt checks across all nontrivial cuts give maximum squared coefficient 0.5000000000000001; minimum eigenvalue of projector minus generator lower-bound operator is -2.64e-16. witness.py uses strict `f>.5`. | OK |
| Simultaneous per-round guarantee with trusted measurement assumptions | R20,45,94; P17,42,83 | alpha .05 is allocated .00625 per generator across two preparations; union bound needs no cross-generator independence, but binomial marginals require IID fixed-probability shots. No campaign-wide guarantee or bound on unmodeled measurement error is claimed. | OK |
| 24 frozen + 20 fresh local cases | R26; P23 and reproduction commands | 24 and 20 distinct manifest IDs; 1,000 draws/configuration/control, 100 shots/block, 22 configurations/case. The fresh manifest is independently staged. These are parameterized instances, not 44 graph isomorphism classes. | OK |
| Ideal graph certification 0.50 / 0.50 | R5,26; P5,23 | Frozen 12,000/24,000 = .5; fresh 10,000/20,000 = .5. `campaigns[0/1].cases[].configurations[noise.name=ideal].controls.graph.certificates`. | OK |
| Aria-like graph certification 0.42 / 0.43 | R5,26; P5,23 | Nominal `aria@1`: frozen 10,016/24,000 = .4173333333; fresh 8,554/20,000 = .4277. Correct rounding. | OK |
| Zero local product/biseparable false certificates | R27; P5,24 | Each control: frozen 0/528,000, fresh 0/440,000 across all 22 configurations. The docs correctly avoid equating zero observed failures with zero population risk. | OK |
| Comparator is implementation-identical and ties | R28,90,94; P25,79,83 | All 2,904 frozen/fresh case/configuration/control rows have equal certificate counts and zero paired difference; witness.py:26 directly calls simultaneous_witness. | OK in public docs; conflicting PLAN wording is F7. |
| Local reproduction uses 1,000 draws and supplied manifests | R78-79,86; P65-66,75 | CLI accepts these arguments; saved config.draws is 1000 and both independent manifests exist in the repository. Commands are explicitly repository commands, not Qollab runtime imports. Full commands not rerun in this bounded review. | OK as instructions |
| Cloud date 2026-10-10, Aria 1 / aria-1, 200 shots/block, C02-C25 | R5,29,33,43,71; P5,26,30,40,60 | Retained 24 campaign receipts: backend ionq_simulator, model aria-1, all raw totals 200, UTC dates 2026-10-10; slot-to-manifest mapping matches the declared subset. | OK |
| C01 smoke: 2026-10-09, 100 shots, excluded | R33,43,71; P30,40,60 | C01 UTC end 23:58:48.524Z; 100 packed shots; case 0/seed 2026100100; excluded from both 12-case denominators. | OK numerically; missing C01 run instructions are F2. |
| Frozen easy C02-C07: 6/6, F_lower .75-.86 | R37; P34 | 6/6; exact extrema .746063679961 and .857248102210. | OK, rounded; applies to the explicitly deviating clean preparations. |
| Fresh easy C14-C19: 6/6, F_lower .67-.75 | R38; P35 | 6/6; extrema .667093542653 and .746807080310. | OK |
| Corrected frozen near C08-C13: 0/6, .11-.18 | R39; P36 | 0/6; extrema .108288492821 and .176504543153. | OK |
| Fresh near C20-C25: 0/6, .07-.25 | R40; P37 | 0/6; extrema .067758859007 and .246972961125. | OK |
| Combined easy 12/12 and near 0/12 | R5,29,41; P5,26,38 | Sum of the four groups above; all 12 near outcomes are inconclusive. Independently computed cloud impostor witnesses: 0/24 certified, largest F_lower -1.192197911773. | OK as labeled observations; not an undeviated preregistration pass. |
| Omitted easy preparation probability p < .015 | R37,45; P34,42 | C02-C07 declared p range .001090316970-.014952533337. Archived circuits omit ancillas/phase flips; deviation exists in all six evidence labels and loader warnings. | OK disclosure |
| First C08-C13 at 13:37-13:42 UTC superseded; corrected reruns at 15:05-15:08 UTC | R45; P42 | Six original records retained with SUPERSEDED status; loader excludes them. Corrected end times 15:05:25.365-15:08:04.087Z; original export times agree with stated rounded minute range. | OK |
| C14-C25 use measured ancilla phase-flip channel | R45; P42 | Recorded circuit descriptions contain the stated RY/CZ ancillas; current circuit hashes match; exact preparation-channel tests pass for all 24 slots. Marginal parities ignore ancilla bits. | OK |
| Saved cloud evidence is included at top level | R43,49; P40,71 | recorded_ionq.py contains complete raw counts, manifests, layouts, circuit descriptions, timestamps, shots and models; no external file is required to recompute cloud bounds. | OK; source-pointer/package descriptions need correction, F3. |
| Compact LOCAL MODEL evidence and source hashes | R49; P71 | Summary equals its generator's output (test); SHA-256 agrees with frozen/fresh/development and gate source files. Local summary metadata required by the rules was dropped. | Numeric trace OK; metadata FAIL F3 |
| About 1 s measured built-in default | R6; P7,58 | Current measured runner times 3.49 s and 3.79 s. No saved 1-second measurement was found in the inspected result files or built-in exports. | FAIL F1 |
| All recorded slots reproducible by Slot=Cxx / Shots | R43,71; P40,60 | C08-C25 match; C02-C07 build different recipes/circuits; C01 is rejected as a slot. | FAIL F2 |
| Development PNG is a live courtroom/interactive exhibit | R59,61; P52,54 | Actually a static LOCAL development certification bar chart at 100 shots, with four bars at 1.0. | FAIL F4 |
| Six measurement blocks for IonQ execution | R99; experiments/PLAN.md:36 | Six for default anchor and original legacy jobs; four for all current cloud campaign slots, including fresh easy, with 24 total wires. | FAIL F6 |
| Scientific context doi:10.1038/s41534-024-00810-3 | R14; P11 | Publisher identifies finite-copy entanglement verification as the subject; citation is relevant context, not a claim of implementing that paper's exact method. | OK |
| Qiskit 2.x and build-window dates Oct 9-11, 2026 | R109; P98 | Runtime/recorded Qiskit 2.5.2; local metadata and project provenance are within the stated window. Helpers contain the disclosure note. | OK |
| No speedup / stronger-witness superiority / hardware claim | R47,90,94; P69,79,83 | Public claims are scoped to educational evidence and simulator observations, with approximate local models and conditional cloud inference. | OK |

The cited paper was checked against the [publisher's page](https://www.nature.com/articles/s41534-024-00810-3), “Valid and efficient entanglement verification with finite copies of a quantum state,” doi:10.1038/s41534-024-00810-3. No fitted frequency, contrast, or crossover claim appears in this entry; those example checks are not applicable.

## Blocking findings with exact quotations

### F1 — Unbacked current default-runtime number

R6: **“about 1 s”**. P7 repeats **“about 1 s”**; P58 says **“The measured built-in default runtime is about 1 s.”**

The current default also renders 25 saved records, producing 26 figures. The local runner measures 3.49 s in the source folder and 3.79 s from an isolated top-level package. The historical built-in HTML verifies successful execution but contains no measured duration supporting 1 s. These are local timings, not a new Qollab browser measurement. Correct the claim to an honestly attributed current measurement/estimate, or include the saved browser timing and date for the version being described. The run remains comfortably within the practical demo budget.

### F2 — Generic instructions do not reproduce the retained legacy recipes

R43 and P40: **“Reproduce a recorded slot in Qollab by selecting **IonQ Aria 1**, setting **Slot=Cxx** to the listed slot ID, and setting **Shots=200** (C01 used 100 shots).”**

R71/P60 similarly direct campaign slots C02-C25 through the current slot factory. For C02-C07, current build_slot adds preparation noise and omits the two Z blocks; all six current recipe and packed-circuit hashes differ from the retained historical runs. The prior omission is disclosed, which is good, but no executable legacy setting or reconstruction instructions are provided. The instructions should explicitly distinguish reanalyzing archived raw counts, rerunning the corrected case, and reconstructing the historical deviating circuit.

For the smoke case, `build_slot('C01')` raises `ValueError: slot must be C02 through C25` at campaign.py:31. Specify the smoke's actual settings (blank Slot, Case=0, default anchor/sealed mode, Shots=100, Aria 1) rather than implying C01 is an accepted slot. C08-C25 already reproduce the saved circuit and recipe hashes; no new cloud run is needed to fix these instructions. New finite-shot counts are not expected to be bit-for-bit identical.

### F3 — Shipped local metadata and package/source descriptions are incomplete or false

Official rules, ../../docs/hackathon-rules.md:186-187: **“Local-simulation result files may ship as project files and be plotted during the run; label each with machine, simulator, Qiskit version, settings and date.”**

The only shipped local result file, evidence_summary.json:1, has campaign keys `cases`, `config`, `sha256`, `source`, `suite`, and `summary`. It does not retain `created_utc` or `versions` (machine/platform, Python, Qiskit, NumPy, SciPy). experiments/make_summary.py:18-28 selects this reduced schema. The missing fields exist in repository-only results: frozen timestamp 2026-10-10T00:56:56.483497Z, fresh 2026-10-10T01:26:08.339217Z, platform Windows-11-10.0.26300-SP0, Qiskit 2.5.2, Python 3.14.6, NumPy 2.5.3, SciPy 1.18.1. Carry these labels into the compact shipped evidence.

evidence_summary.json:1, `description`, also states **“Compact statistics derived from included frozen, fresh, and development local results; full result files remain included.”** The same string is generated at experiments/make_summary.py:69. Full frozen/fresh files are not in the top-level shipment and are 7,427,951 / 6,175,587 bytes, above the per-file upload limit. Call them repository evidence, not included Qollab files. The compact summary itself is adequate to trace the published local aggregate numbers; uploading oversized full files is not the remedy.

R43/P40 say **“The immutable console exports are in `results/exports/`”** and R71 says **“raw exports and complete receipts are included in this project.”** These paths exist in the repository but cannot exist in the defined top-level Qollab shipment. All 31 recorded receipts retain the literal source pointer **`"source_file": "results/exports/qollab-console.txt"`** (recorded_ionq.py:3-33); that file does not exist even in the repository. Actual exports can be matched by job ID and UTC, and their contents match, so this is not fabricated evidence. Supply an accurate export mapping and distinguish repository archives from the complete, top-level saved receipts. Complete receipts already satisfy the cloud saved-result inclusion requirement.

### F4 — Figure provenance and accessible descriptions are wrong

R59: **`![Live built-in courtroom exhibit.](figures/development.png)`**.

R61: **“Alt text: Development exhibit showing matched Z histograms, stabilizer parity intervals, and a conditional witness lower bound.”**

P52: **`![Interactive exhibit.](figures/development.png)`**.

P54: **“Alt text: A sample courtroom display with paired Z histograms, parity intervals, and a witness-bound panel.”**

Visual inspection shows a static bar plot titled **“development local evidence | 100 shots”**, y-axis “Graph certification fraction,” case IDs 0-3, all four bars at 1.0. It contains none of the described histograms, parity intervals or witness panels and is LOCAL MODEL evidence, not a LIVE screenshot. Correct the image/caption/alt text, or replace it with the actual exhibit. This changes scientific provenance and screen-reader meaning; it is not merely style.

All six document image references also use figures/ subpaths, absent from the specified top-level Qollab package. Keep repository-relative images for GitHub if desired, but supply working project-page image assets/URLs and instructions for their publication. The frozen/fresh figures are real local charts and qualitatively match the retained ideal data.

### F5 — Current live output falsely reports that supplied campaign receipts are absent

receipt.py:111 unconditionally appends **“Readiness gap: prescribed cloud campaign and matched saved recipes are not yet supplied.”**

figures.py:29 unconditionally prints **“Readiness gap: near-threshold and extension campaign receipts are not yet supplied; this is exact anchor/reference mode.”**

Both messages appeared in the successfully reproduced default run, including alongside corrected recorded near-threshold exhibits. There are now 24 retained campaign receipts, all validated by the loader. Replace unconditional historical assertions with status derived from the actual records and their deviations. Preserve genuine gaps (legacy reproduction / evidence retention) distinctly. LIVE, RECORDED, and mathematical-reference headings otherwise separate the sources correctly; superseded recordings are excluded.

### F6 — Block-count claim and executable-plan amendment are stale

R99: **“six measurement blocks are run together for the IonQ simulator's one-circuit-per-job constraint”**.

experiments/PLAN.md:36: **“Each slot is one six-block, 24-qubit packed circuit on IonQ aria-1 at 200 shots; built-in checking executes the six component circuits as one list.”** The same line says campaign.py **“verifies each embedded manifest against `review/manifests/frozen.json` or `fresh.json` before building.”**

Every current cloud slot builds four blocks and 24 wires; two Z blocks are dropped to accommodate eight ancillas. This includes C14-C19 easy runs, not only the near-threshold runs discussed in the docs. Built-in campaign execution retains six component circuits whose aggregate width is 32; they are executed separately in a list, so this does not violate the built-in per-circuit limit. The default demonstration and legacy C02-C07 really do use six four-wire blocks. Scope the six-block claim to those paths and append an accurate dated amendment for the current factory. External manifest comparison is optional locally; isolated Qollab execution checks embedded hashes and does not read review/ files.

### F7 — Unsupported strongest-baseline claim survives in the plan

experiments/PLAN.md:9: **“The strongest equal-budget baseline is the predeclared two-color witness using the same marginal counts and shots as the simultaneous witness.”**

witness.py:26 is **`def two_color_witness(parities,alpha=.05,trusted=False):return simultaneous_witness(parities,alpha,trusted=trusted)`**.

This is one implementation called twice, with identical counts and budget; nothing establishes that it is the strongest available equal-budget witness. The public README/page correctly disclaim superiority, but the reviewed plan still makes the stronger statement identified in review/evidence_review.md:35 and :66. Amend that statement while preserving its historical status. No new baseline is necessary for the currently scoped educational claim, provided the project consistently calls this an implementation-identical comparator.

### F8 — The earlier local raw-draw retention finding remains unresolved

experiments/PLAN.md:31 promises **“raw counts/probabilities”** and **“per-instance paired outcomes”** among saved evidence. review/evidence_review.md:69 explicitly requested **“Preserve draw-level outcomes/counts or a separately hashed replay record”**.

experiments/run.py:353 executes **`rec["counts"].append(marginals)`**, but :368 then executes **`rec.pop("counts")`** before saving. The full frozen/fresh files and their case checkpoints contain probability references, seeds, and aggregate counters, but not the sampled per-draw counts or a separately hashed draw transcript. The source hashes are unchanged from the earlier independent review, which expressly did not reproduce the full campaigns.

Thus the published local fractions can be independently summed from saved counters (and were), but cannot be independently reconstructed from retained sampled observations in a quick audit. Resolve this evidence-protocol deviation explicitly: preserve/reconstruct an appropriately hashed replay artifact through the orchestrator, or amend the evidence-retention claim and describe the aggregates-only limitation without calling it complete raw-result reproduction. This review did not start a full rerun or silently waive the earlier finding.

## Cloud recomputation and audit trail

The independent decoder used each raw bit string's integer value, each layout's classical offset, and the manifest generator masks. For each generator it counted even parity successes, calculated the one-sided Clopper-Pearson bound with alpha=.00625, then used `F_lower = sum(p_lower for four generators) - 3`. This avoided using the saved witness value as an input. Every retained campaign bound agrees within 1e-12. The same procedure separately checked product-impostor bounds.

| Slots | Recomputed target F_lower, in slot order |
|---|---|
| C02-C07 | .746063679961, .777348056569, .857248102210, .792012080948, .842335082899, .811738661062 |
| C08-C13 corrected | .164908022394, .108288492821, .176504543153, .164729964662, .164277515699, .159746468377 |
| C14-C19 | .746807080310, .667093542653, .695833739459, .725153155793, .739616017400, .687064756473 |
| C20-C25 | .246972961125, .067758859007, .243643051943, .164277515699, .182097339086, .147931321983 |

The HTML exports are one-line files. HTML text decoding yielded the original RECORD_JSON values. For all 31 receipt/export pairs, job ID plus UTC end identifies the run, and raw counts, settings, layout, uncertainty, noise model, shots, start/end, and circuit/recipe/layout hashes agree exactly. Campaign labels added to recorded_ionq.py are clearly archival annotations. All raw shot totals and recomputed marginals agree with the records. The six superseded near-threshold runs and separate C01 smoke remain available but do not enter campaign totals.

The numeric planned easy thresholds (>=4/6 frozen, >=4/6 fresh, >=8/12 total) are exceeded by the retained observations, and no cloud product impostor certifies. However, frozen easy C02-C07 did not execute the prescribed noisy recipes. Provenance line 180 says **“Preregistered >=8/12 easy met.”** That should be read only as numerical outcome arithmetic with its adjacent disclosed deviation, not a clean protocol-adherence pass. This review does not silently accept the six deviating runs as exact prescribed noisy executions. The public docs appropriately disclose their status; any formal science-gate approval needs explicit disposition of this deviation.

## Local evidence, baseline, and robustness

The complete frozen/fresh result hashes equal those reviewed previously and those shipped in the compact summary. The summary-generation test validates the entire compact output against the saved sources, including negative control results. Each local suite has 22 configurations (ideal plus three approximate models at seven scales), 1,000 draws/configuration/control, and 100 shots/block. The local evidence includes 24 frozen and 20 independently generated fresh parameter instances. It is not a claim that all those instances are independently generated graph topologies.

| Model, nominal scale | Frozen all cases | Fresh all cases |
|---|---:|---:|
| Ideal | .500000 | .500000 |
| Aria-like | .417333 | .427700 |
| Forte-like | .149250 | .155050 |
| Forte Enterprise-like | .002583 | .002550 |

Aria-like all-case certification over scales .5, .75, 1, 1.25, 1.5, 1.75, 2 is respectively:

- Frozen: .494042, .471083, .417333, .337292, .246458, .156750, .090625.
- Fresh: .495050, .474900, .427700, .341850, .247150, .157400, .086600.

These are recomputations of saved counters, not a new sweep. There is substantial degradation with stronger modeled noise; the headline Aria-like number is nominal scale 1, not a robust floor across the sweep. “Ideal” retains the manifest's deliberate preparation phase noise and disables only the additional approximate device channel. This explains all easy ideal draws certifying and near-threshold ideal draws abstaining. The true graph fidelity and the conservative population-generator witness are different quantities.

The equal-budget comparison reuses exactly the same counts/alpha and is identical by implementation, so equality carries no superiority inference. Exact statevector truth is used for reference/coverage auditing, not to feed a favorable empirical witness. The local channel is an aggregate density-channel approximation; it does not reconstruct IonQ compiler noise, ancilla-gate noise or unknown measurement bias. The docs correctly restrict cloud inferences to trusted rotations/readout and do not claim a calibration or hardware result from the local rates.

Earlier mathematical HOLD findings about omitted local phase flips, manifest-specific truth, two-preparation coverage, and negative bias inputs are repaired in current code and tested. Missing cloud receipts from the earlier review are now supplied. The prior draw-retention finding remains F8. Existing reports are historical reviews, not current PASS reports. No new full independent random-stream campaign has been commissioned or claimed by this quick review.

## Submission musts and runtime contract

| Requirement | Evidence / status |
|---|---|
| MIT license | LICENSE contains standard MIT grant and 2026 Saurav Das copyright. OK. |
| Exact attribution | R115 and P103: “This effort is supported by Qollab & IonQ.” OK. |
| AI and outside-tool disclosure | R109/P98 name AgentMesh, OpenCode free models, OpenAI Codex, Claude Code; libraries/licenses and template/reuse statements present. OK for disclosed scope. |
| Shared helpers and in-window reuse note | circuit_pack.py:1 and receipt.py:1 carry the same helper note; R109/P98 describe shared use, dates and project-specific work. No concealed pre-window reuse is established by reviewed records. OK. |
| Libraries / Qollab API | Qiskit 2.x, NumPy, SciPy, Matplotlib are declared bundled dependencies. No qiskit-aer, BackendSamplerV2, provider keys, input(), future imports, or UTF-8 BOM in top-level source. OK. |
| Injected backend / one job / one circuit | Active injected backend used; IonQ gets one packed circuit, one submission and one result fetch; built-in gets small circuit list. Tests and manual inspection pass. |
| File reads | Default uses top-level recorded_ionq import. Optional repository-manifest comparison is guarded by existence; isolated slot run succeeds without it. No required runtime read outside shipped set. OK. |
| Theme | Quantum Unlocked stated at R111/P100. Setting the live theme tag remains human-only. |
| Judging-criteria summary | All four criteria covered at R96-101 and P85-90; F6 corrects one execution detail. |
| Accessibility notes | Present at R103-105/P92-94; companion source has text-oriented/keyboard UI provisions. Actual browser/screen-reader acceptance not independently exercised here; wrong image meaning is F4. |
| Repository link | https://github.com/sauravdasmg/Qollab present at R117/P105. Public availability and final uploaded revision remain human-only checks. |
| Video | [[VIDEO LINK]] remains at R118/P106, explicitly permitted by this task; human step. |
| Publication / logged-out run | Not performed by this reviewer. Historical Qollab exports demonstrate executions, not a logged-out final-package acceptance run. Human step. |

The top-level Python project is a run-form/console/plot demo. The companion interactive web files remain under web/ locally, and the checker counts them as prospective flattened assets. No claim is made here that the final deployed JavaScript project or screen-reader behavior was browser-tested. Final upload selection and project-page asset paths should be checked with the actual published package.

## STYLE (non-blocking)

- The frozen/fresh PNG x-axis case IDs overlap heavily. Short labels or a separate data table would improve readability; plotted values are consistent with ideal saved counters.
- experiments/PLAN.md:34-36 contains literal question marks in place of punctuation/range separators. Meaning remains recoverable from IDs and source data.
- R67 says the runtime “will be updated” while the page currently states a measured value; remove this leftover editorial promise when resolving F1.
- R94/P83 say the comparator is the same witness “measured [in] two ways.” Counts are actually shared between two calls to the same implementation. Earlier explicit identity disclaimers preserve meaning, but more literal wording would be clearer.
- Close or otherwise manage figures after display: the current default renders 26 and emits a Matplotlib open-figure warning. The run still completes successfully.
- State next to the local rates that “ideal” includes the deliberately noisy preparation, and that Aria-like means scale 1. This would make already-correct scoped numbers easier to interpret.

## Reviewed file identities

| File | SHA-256 |
|---|---|
| README.md | fe709d0ff91de449f2e6ecfdd61b4852396ee78f75693caf131c0e7383cb2f1a |
| PROJECT_PAGE.md | 418f9c8dec1fd2da5cdd24c1a7e9c0aeb2b54337c15384e4f563753968fc672b |
| main.py | 46d4a19af80c9d69764179978986f0b3bffdaf309b37b33ca87b498aa8fc6751 |
| witness.py | 72385da6b7a814054f5cff429de2ca96de2a29668051accc110aa18f2f3f53e9 |
| evidence_summary.json | 91b6f768d09d11a037048ab5b2432896d193ce9641fe19e36e2913267d86e6ac |
| recorded_ionq.py | 9bdc84457d3644c89c63407ea16cb5e436e9b8fce6aa81f29aa8834533b369bb |
| results/frozen.json | 548677ec1476f70f83f4a33112fb2d2a0afd25fcff746821bcf1a06df48400e9 |
| results/fresh.json | f240500074d21aaa0fceb9a4a9c22a2a3dfb2d62d8582bc69bc1daf946f4d2dc |

PASS requires disposition of F1-F8 and rechecking the changed claims/package. Human-only publication/video checks are separately outstanding and were not used to manufacture a scientific failure. No implementation or documentation fix was made by this independent reviewer.
