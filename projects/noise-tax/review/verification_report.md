VERDICT: FAIL

# Final independent claim verification — The Noise Tax

Reviewed 2026-10-10 UTC against the working-folder contents and the supplied official-rule compilation. This reviewer wrote none of the implementation or submission documentation. Only this report is an intentional deliverable. No full experiment, parameter sweep, new seeded evidence campaign, or remote job was run. The checks below distinguish reproducible numbers from unmet scientific gates and inaccurate presentation claims.

The numerical tables reproduce. The default Python run succeeds and the test suite passes with a permitted temporary directory. PASS is nevertheless blocked by F1–F9 below. In particular, the primary N precision and fresh-agreement requirements remain unmet; overlapping intervals do not satisfy the separate agreement tolerance.

## Checks performed and scope

- Read README.md, PROJECT_PAGE.md, main.py, all scientific core modules, channel/calibration code, crossover analysis, packing and receipt/parser code, cloud_slots.py, reuse_sources.json, experiments/PLAN.md including both amendments, experiment/reproduction code, nt_curves.py, recorded_local.py, recorded_ionq.py, evidence_summary.json, both earlier review reports, independent manifests, and the parent merged plan and official hackathon rules.
- Parsed the complete frozen/fresh result files (111,221,890 and 111,206,061 bytes), not just their summaries. Recomputed every mean advantage from saved outcome probabilities, every tabulated crossing by linear interpolation, all W sensitivity roots from saved edge curves, and all six N intervals from a separate vectorized implementation of the prescribed bootstrap over saved curves. This is quick reanalysis of existing evidence, not a new simulation campaign.
- Decoded T01–T08 directly from raw packed bitstrings and layout offsets, independently of the project metric functions. Compared all eight embedded raw receipts to JSON extracted from their original HTML exports; every receipt was identical. Checked all indexed dates, models, shots, slot settings, job IDs and source labels against evidence_summary.json.
- Read all nine HTML exports: eight cloud slots and the built-in default export ending `16-21-42.122Z.html`. Visually inspected frozen-curves.png and frozen-anchors.png and checked their plotting implementation.
- Read project-related provenance entries, including the merge decision, G1 HOLD, frozen/fresh evidence, cloud campaign, parser repair and final documentation. The relevant dated events are inside the authorized window. This is an artifact audit, not independent authentication of the remote service or a logged-out publication check.

## Required quick checks

Commands use `../../.venv/Scripts/python.exe` from the submission folder.

| Check | Reproduced result | Status |
|---|---|---|
| `../../tools/check_submission.py .` | All automated blockers pass except the then-missing PASS verifier report. Six human-only checks remain. The checker reports 27 files because its inventory includes `web/*` flattened at publication. | OK for the requested exclusion of this report and human-only items |
| Checker noise-model recommendation | Reports an unguarded setting; inspection shows `main()` uses `cloud = name == 'ionq_simulator'`, and `run_slot()` rejects other backend names before setting options. | OK; static-check false positive |
| `../../tools/qollab_local.py run . --backend ideal` | Exit 0; 0.7 seconds; `calls_main: true`, `contract_verified: true`; five small blocks, 512 shots/block; 14 validated receipts and zero receipt issues. | OK |
| `python -m pytest tests -q -p no:cacheprovider` | Initial execution: 66 passed, 12 setup errors from Windows denying access to the shared pytest temporary directory. These were fixture/environment errors. | Resolved below |
| Same tests with `--basetemp .verify-final-tmp --tb=short` | 78 passed, four expected noninteractive Matplotlib warnings, 3.86 seconds. | OK |
| Frozen and fresh verifier-manifest validation | Both accepted by current `validate_independent_manifest`; owner, independent specifications, counts, seeds, digests and immutable settings checked. | OK |
| Scientific implementation provenance | Current scientific modules match the recorded hashes. Loader/presentation changes are covered by the WP-NT-09 amendment; the pinned scientific-function AST digest still matches. | OK |
| Calibration snapshot | Top-level snapshot bytes exactly equal the parent calibration JSON. | OK |

Default execution imports its project data from top-level Python modules; it does not require results/, experiments/, review/, or an external project data file. Qiskit, NumPy, SciPy and Matplotlib are declared; no Aer, BackendSamplerV2, input prompt, credentials, or double invocation is needed. Cloud branches submit one packed circuit and fetch `job.result()` once. These checks do not establish that the separate web presentation has been flattened and published (F7).

`noise_channel.py:16–23` intentionally uses the parent calibration JSON when available and the top-level snapshot otherwise; it is a local-analysis module, not imported by the default main. `_reuse.py` identifies itself as a one-time import tool and contains repository reads/writes; it is not imported by main and should remain excluded from an actual runtime upload. Neither is evidence of a failed default run.

## Claims table: local numbers

Sources for every row are `nt_curves.CURVES['suites'][suite]['analysis'][game][model]`, the matching complete `results/{suite}.json`, and the independent probability/curve reanalysis. All retained fields of nt_curves match the full analysis; the compact module deliberately omits some full-analysis fields. Its SHA-256 references match both complete result files.

| Claim | Source in submission docs | Reproduced value | OK/FAIL |
|---|---|---|---|
| Two comparisons, three equally likely W labels, two four-qubit N arms | README 11, 23; PROJECT_PAGE 9 | Three joint W circuits of 2 qubits; two N circuits of 4 qubits. W's ideal reference is analytic in the default run. | OK, except “samples both arms” ambiguity/error F9 |
| Defaults 512 shots, aria-1, about 1 second | README 7, 74; PROJECT_PAGE 3 | Signature agrees; local default 0.7 s. Existing Qollab built-in export also shows 512 shots/block. Wall time is machine/runtime dependent. | OK as approximate local runtime |
| 24 frozen and 24 fresh instances, scales 0–2 by 0.025 | README 5, 25, 44; PROJECT_PAGE 5, 9 | Each game/model/suite has 24 cases and 81 points; frozen/fresh construction seeds are disjoint. 96 distinct specifications total, reused across the three model choices. | OK |
| Fixed-prize coefficient 0.02 | README 25 | Independently decoded loss is `P(FF) + 0.02*(2 - mean_passes)`; all outcomes retained. | OK |
| W aria-1 frozen/fresh 1.309; sensitivity 1.206–1.431 | README 33; PROJECT_PAGE 15 | 1.3090210649612195 / 1.3090210649612200; sensitivity 1.2062439116792891–1.4309278492650925 (fresh agrees to roundoff). | OK |
| W forte-1 frozen/fresh 1.141; sensitivity 1.062–1.233 | README 34; PROJECT_PAGE 16 | 1.1411212795684418 / 1.1411212795684418; sensitivity 1.062191127350596–1.2327217550388907. | OK |
| W forte-enterprise-1 frozen/fresh 0.684; sensitivity 0.655–0.716 | README 35; PROJECT_PAGE 17 | 0.6837939139632098 / 0.6837939139632088; sensitivity 0.6546402762877587–0.7156633135689505. | OK |
| N aria-1 frozen 0.411 [0.250,0.575], fresh 0.295 [0.150,0.450] | README 36; PROJECT_PAGE 15 | 0.4110549014142178 [0.25,0.575]; 0.29525964619400413 [0.15,0.45]. | OK numbers; gate FAIL F2 |
| N forte-1 frozen 0.339 [0.200,0.475], fresh 0.243 [0.125,0.375] | README 37; PROJECT_PAGE 16 | 0.3387383220152828 [0.2,0.475]; 0.2432722629836531 [0.125,0.375]. | OK |
| N forte-enterprise-1 frozen 0.200 [0.100,0.300], fresh 0.144 [0.050,0.225] | README 38; PROJECT_PAGE 17 | 0.20012138608834365 [0.1,0.3]; 0.14369513780285453 [0.05,0.225]. | OK |
| N 97.5% whole-instance simultaneous bootstrap bands | README 29; PROJECT_PAGE 11 | Reanalysis used PCG64 seed 2026104402, 4,000 whole-curve draws, maximum absolute deviation and higher 0.975 quantile. All six intervals match; radius discrepancies <=1.4e-17. Nominal bootstrap coverage is an assumption, not empirically certified coverage. | OK |
| Frozen/fresh N intervals overlap in each model | README 29 | All three overlap. Aria root difference is nevertheless 0.11579525522021367 > 0.10. | OK literal overlap; omitted failure F2 |
| W is deterministic, sensitivity is not a sampling CI | README 29, 104; PROJECT_PAGE 11, 59 | Maximum within-suite W curve differences <=8.9e-16; deterministic roots and +/-0.001 two-qubit-rate sensitivity are correctly distinguished. | OK |
| Both mean margins cross zero | README 5; PROJECT_PAGE 5 | Exactly one positive-to-negative interior crossing in each of 12 game/model/suite curves. Saved-probability reanalysis agrees with stored means within 4.2e-17. | OK; does not imply every individual N case crosses |
| No speedup, device threshold, universal classical superiority, noisy-global-product optimum or noise reduction | README 102–107; PROJECT_PAGE 59 | Those stronger claims are expressly excluded and are not needed to interpret the tables. | OK |

For an explicit endpoint check, Aria W goes from +0.03839181889881236 to -0.0195050206201174; frozen N goes from +0.009017572620242198 to -0.032268509877639; fresh N goes from +0.006462691112714878 to -0.0345461534122232. These are LOCAL MODEL means, not observed cloud thresholds.

## Claims table: recorded cloud numbers

All dates below are 2026-10-10 UTC. The eight records, their slot configurations, models and shots agree with `cloud_slots.py`, `recorded_ionq.py`, `evidence_summary.json` and the eight corresponding HTML exports. Outcome values in evidence_summary are rounded to four decimals; documentation values are correctly rounded to three decimals.

| Claim | Source | Independently reproduced value | OK/FAIL |
|---|---|---|---|
| T01 W aria-2, 1,000/label, +0.005 | README 56; PROJECT_PAGE 31 | Success counts 955, 932, 928; mean success minus `(1/2+sqrt(3)/4)` = +0.005320631441114054. | OK |
| T02 N aria-2, 4,000/arm, -0.030 | README 57; PROJECT_PAGE 32 | Product/hedge FF counts 97/158; pass totals 6795/3870; losses 0.030275/0.060150; difference -0.029875. | OK |
| T03 W aria-1, 1,000/label, +0.002 | README 58; PROJECT_PAGE 33 | Success counts 941, 927, 938; +0.0023206314411140516. | OK |
| T04 N aria-1, 4,000/arm, -0.022 | README 59; PROJECT_PAGE 34 | FF 82/110; passes 6841/3914; losses 0.026295/0.047930; difference -0.021635. | OK |
| T05 W forte-1, 1,000/label, +0.005 | README 60; PROJECT_PAGE 35 | Success counts 950, 932, 931; +0.00465396477444735. | OK |
| T06 N forte-1, 4,000/arm, -0.035 | README 61; PROJECT_PAGE 36 | FF 81/163; passes 6838/3870; losses 0.026060/0.061400; difference -0.035340. | OK |
| T07 W aria-1 fixed fresh, 1,000/label, +0.011 | README 62; PROJECT_PAGE 37 | Success counts 950, 941, 940; +0.010653964774447355; seed 2026104100. | OK |
| T08 N aria-1 fixed fresh, 4,000/arm, -0.022 | README 63; PROJECT_PAGE 38 | FF 87/115; passes 6921/3915; losses 0.027145/0.049175; difference -0.022030; seed 2026104300. | OK |
| Eight slots; W range +0.002 to +0.011, N -0.035 to -0.022 | README 5, 48, 52; PROJECT_PAGE 5, 23, 27 | Four W and four N records; exact extrema +0.0023206314/+0.0106539648 and -0.03534/-0.021635. | OK |
| Slot determines model and budget; choose free IonQ simulator | README 66, 78; PROJECT_PAGE 41, 47 | Slot configuration overrides the normal noise-model and shots settings: W 1,000; N 4,000; Aria-2/Aria-1/Forte-1 as documented. No exact repeat of random counts is promised. | OK |
| No reported T-campaign cloud deviations or superseded runs | README 68; PROJECT_PAGE 43 | No contrary campaign entry found; all eight receipts are distinct and valid. Earlier LOCAL MODEL amendments and six legacy anchors are separate issues. | OK for the explicitly cloud-scoped statement |
| Cloud signs are observed anchors, not a fitted cloud crossover | README 66; PROJECT_PAGE 41, 45 | All four W propagated 95% intervals include zero; all four T-slot N intervals lie below zero. Docs do not claim statistically certified W superiority. | OK |
| Saved cloud data shipped at top level | README 66; PROJECT_PAGE 41 | Full raw packed counts are in recorded_ionq.py (164,124 bytes), not merely links to excluded results folders; evidence_summary.json is also top-level. | OK |

For reference, T01–T08 N uncertainty bounds from the shipped conservative Clopper–Pearson/Bonferroni propagation are T02 [-0.0472352,-0.0124273], T04 [-0.0370600,-0.00614689], T06 [-0.0522386,-0.0183358], T08 [-0.0377781,-0.00621815]. Shared packed shots do not require independent arms for that union-bound construction. W success indicators are weighted equally over the three labels.

## Blocking findings (exact source text)

### F1 — Sign explanation reverses the loss/error comparison

README.md:25 states: **“A positive sign favors the first-named recipe in each definition.”** The same paragraph defines W as ideal one-way error minus joint error and N as product loss minus hedge loss. Positive therefore favors the *second* term's strategy in those definitions: joint and hedge, respectively. PROJECT_PAGE.md:9 states **“Positive signed advantage favors the first-named strategy.”**, while its N table at line 32 labels the comparison **“N: product vs published hedge”**. That would tell a reader a positive N margin favors product, which is backwards.

The later negative-N explanation at README:66 / PROJECT_PAGE:41 is correct but does not repair the contradiction. Replace the sign rule explicitly with “positive favors joint for W and published hedge for N; negative favors ideal one-way and attained product, respectively.” Keep comparison headings consistent.

### F2 — Primary scientific gates fail and are not disclosed in the result narrative

experiments/PLAN.md:73 requires **“finite CI width <=0.30”**; line 75 requires estimates **“resolve and agree within absolute 0.10 and their combined interval bounds;”**. The later amendment at line 127 expressly preserves **“<=0.30 remains explicit and a failure stays a failure.”**

Frozen Aria N width is 0.575 - 0.25 = **0.325**, above 0.30. Frozen/fresh Aria N root difference is **0.11579525522021367**, above 0.10; `results/fresh.json.fresh_comparison.N.pass` is false. Fresh width is mathematically 0.300; its stored false precision flag comes from floating-point 0.30000000000000004 and should not be treated as an additional substantive precision miss. The frozen width and root-difference misses remain real.

README.md:29 only reports **“The frozen and fresh N intervals overlap for each model.”** The summaries (README:5 / PROJECT_PAGE:5) present successful crossings without explaining the unmet acceptance conditions. `nt_curves.py:3477` and `:1699` contain **`'decision': 'PASS_LOCAL_CONDITIONS',`**, alongside false precision flags. The harness only includes precision in that decision when `--gate g2` is supplied and never folds fresh comparison failure into the decision. These generic flags are not G2/G3 passes.

The parent plan explicitly makes failed primary gates a HOLD/drop decision unless the human revises scope. No such subsequent scope amendment was found in the reviewed project provenance. Preserve the negative result, disclose both misses, and have the orchestrator resolve the scientific admission/scope decision; do not reinterpret overlap as a pass or silently retune the seeds/tolerances.

### F3 — Local reproduction instructions do not run as written

README.md:82 says **“From the parent Qollab repository”**, but lines 85–87 give:

```text
..\..\.venv\Scripts\python.exe experiments\run.py --suite frozen
..\..\.venv\Scripts\python.exe experiments\run.py --suite fresh
..\..\.venv\Scripts\python.exe tools\qollab_local.py run projects\noise-tax --backend ideal --shots 512
```

These mix project-relative interpreter/experiment paths with repository-relative tool paths. PROJECT_PAGE.md:47 says **“Local reproduction from the repository root:”**, but lines 50–51 use `experiments\run.py` instead of `projects\noise-tax\experiments\run.py`.

Even when run from the project with the correct interpreter, the first experiment command immediately fails with the exact error from experiments/run.py:315: **`ValueError: frozen/fresh evaluation requires a verifier-owned --independent-manifest`**. I reproduced that early error without running an experiment. README:94 / PROJECT_PAGE:55 show a frozen manifest then merely **“(and `--suite fresh`)”**; changing just the suite retains the wrong frozen manifest. Existing checkpoints also require `--resume` or a clean output directory.

Provide complete commands with one explicit working directory, the correct frozen/fresh manifest for each suite, and a deliberate resume/clean-output policy. Also explain that `make_curves.py` reads results/summary.json: it does not rebuild that summary from newly generated full results, so the current advertised sequence can regenerate stale curves.

### F4 — Fresh LOCAL MODEL bundle lacks required run metadata

PROJECT_PAGE.md:9 states **“Frozen and fresh local runs each use 24 seeded instances.”** README.md:44 labels the figure **“the independent fresh 24-instance set”**. The fresh numbers are shipped in nt_curves.py, but that suite contains only `analysis`, `gate`, `grid`, and `source_sha256`. `recorded_local.LOCAL['suite']` is only `frozen`; it supplies no fresh receipt.

The binding official-answer section requires local results to **“label each with machine, simulator, Qiskit version, settings and date.”** Fresh metadata exists only in excluded results/fresh.json: machine Saurav, exact NumPy small-block density evolution, Qiskit 2.5.2 / NumPy 2.5.3 / Python 3.14.6, 2026-10-10T03:49:37.041758+00:00 through 03:50:24.565050+00:00, plus manifest/settings. A content hash alone does not provide those fields to a top-level-only upload. Ship a compact fresh receipt/metadata record and point the docs to both local evidence modules.

### F5 — Reuse disclosure is incomplete and conflicts with the project-specific claim

README.md:124 says **“This project's game logic, noise analysis, UI, and results are project-specific. Other reused or adapted material, if any, is identified in `reuse_sources.json`.”** PROJECT_PAGE.md:65 similarly says **“Game logic, analysis, UI, and results are specific to this entry.”** Yet reuse_sources.json records direct in-window adaptation/copying of Two Whispers core.py into whispers_core.py and Never Lose Twice core.py, strategies.py and product_bounds.py into this entry's game modules.

Six entries in reuse_sources.json at lines 40, 46, 52, 58, 64 and 70 use the exact destination **`"adapted algorithm/reference; see REUSE_MANIFEST.md"`**. REUSE_MANIFEST.md is absent. The earlier independent G1 review already identified that missing disclosure. The timestamps and hashes do provide useful traceability; this is not an allegation of undisclosed pre-window building. The unresolved issue is the inaccurate exclusivity implication and missing adaptation/reference explanation.

Explicitly credit the retired W/N entries and reused theoretical/analysis material, distinguish the new merged contribution, and replace broken disclosure references with actual shipped explanations. Keep the shared-helper note consistent: the page lists Court/Eyes-Free/Noise Tax, whereas the helper's own opening note still lists the retired W/N names and Court.

### F6 — Figure descriptions identify the wrong curves and unavailable uploaded assets

README.md:40 says **“frozen solid and fresh dashed curves”**; README:44 says **“Dashed curves show the independent fresh 24-instance set”**. PROJECT_PAGE.md:19 describes **“solid frozen and dashed fresh lines”** in `results/figures/frozen-curves.png`. In the actual PNG, all three curves are frozen; solid/dashed/dotted distinguish Aria/Forte/Forte Enterprise. `figures.py:12` explicitly iterates **`for model, style in zip(colors, ('-', '--', ':')):`**. The combined main() figure uses different suite styling, but that is not the linked PNG.

README.md:42 also says **“and separate anchor marks show recorded cloud observations”** in the frozen-curves image. That image has no cloud anchor marks; those are in the separate frozen-anchors.png. These are meaning-changing legend/alt-text errors, not style preferences. The anchor image shows the six earlier legacy observations, including Forte Enterprise, rather than T01–T08; identify that provenance explicitly (F8).

All markdown figure URLs use excluded `results/figures/` paths. A top-level-only Qollab upload cannot resolve those relative assets. Flatten or otherwise publish the figures with matching links, or replace these references with the actually rendered figures and accurate descriptions.

### F7 — Interactive/accessibility claims are not supplied by the inspected top-level entry

README.md:118 states **“The interactive page supports keyboard operation and shows values and labeled controls alongside plots; contrast uses a light background with high-contrast text.”** PROJECT_PAGE.md:63 states **“Keyboard-operable controls, labeled values, a light high-contrast display, and textual results accompany plots”**. README:111 and PROJECT_PAGE:61 also claim an interactive comparison.

The inspected top-level files contain main.py but no index.html, main.js, main.css or tax_bridge.py. The Python entry prints text and renders a static Matplotlib figure. Interactive assets exist only under web/. The checker assumes these will be flattened during publication, which explains why its general result does not catch this distinction; the user's requested top-level shipped-set audit cannot assume that future packaging step has happened.

Provide an explicit flat interactive shipped artifact and verify that entry, or accurately describe the current Python presentation. Existing web source and Python tests are not proof of keyboard/screen-reader operation of the deployed interface. Publishing, logged-out acceptance and browser accessibility verification remain human/runtime steps.

### F8 — Six displayed legacy cloud runs lack documented reproduction/provenance mapping

README.md:66 / PROJECT_PAGE.md:41 document reproduction of **“these eight valid runs”** through T01–T08. However, main.py:79 executes **`for record in records:`** over all **14** receipts. Six are inherited W/N case-0 runs, and the linked frozen-anchors.png uses those earlier six. They are not invalid, but their identities and reproduction route are absent from both user-facing documents.

The earlier receipts are dated 00:15–00:38 UTC on 2026-10-10. W uses 1,000 shots in Aria-1/Forte-1/Forte Enterprise; N uses 4,000 in Aria-1 and 1,000 in the two Forte models. Their signed values are W +0.0113206314, +0.0016539648, -0.0176793686; N -0.020910, -0.021120, -0.037700. No T slot selects Forte Enterprise, and the old receipts include extra packed recipe arms not reproduced by the current T-slot factory. “Run Txx” therefore cannot reproduce every recorded result shown to the judge.

Label these as inherited archival anchors with date/model/shots/original case and a concrete source/setting/file reproduction route, or restrict the displayed/linked evidence to the documented campaign. Do not relabel them all as 4,000-shot N observations or as T-slot runs. The existing cloud-deviation statement is not itself false; the missing archival explanation is the failure.

### F9 — The default does not sample both W comparison arms

PROJECT_PAGE.md:9 says the live program **“samples both arms on the injected backend”** after describing both games. main.py:49 actually calls **`wc, wm = w.make_demo(); nc, nm = n.make_instance_demo()`**. W's default `include_oneway=False` supplies only the joint arm; its comparison is the analytic ideal one-way reference. N does sample both arms. Physical W one-way circuits are included only in cloud slots using `include_oneway=True`.

Clarify the sentence to distinguish default W joint sampling against the analytic reference from N's two sampled arms and W cloud-slot physical diagnostics. This also aligns the page with its otherwise correctly scoped ideal-source W comparator.

## Other required submission claims

| Claim / requirement | Source | Reproduced result | OK/FAIL |
|---|---|---|---|
| MIT license | LICENSE; README 126, 140; PROJECT_PAGE 65 | Complete MIT text, copyright 2026 Saurav Das. | OK |
| Exact attribution | README 130; PROJECT_PAGE 69 | `This effort is supported by Qollab & IonQ.` | OK |
| AI tools and libraries disclosed | README 122, 126, 128; PROJECT_PAGE 65; requirements.txt | AgentMesh/OpenCode, OpenAI Codex, Claude Code; Qiskit, NumPy, SciPy, Matplotlib, Python standard library and template/platform consultation named. | OK presence; reused material still FAIL F5 |
| Shared helper note | README 124; PROJECT_PAGE 65; circuit_pack.py opening | Purpose and in-window timing stated; names inconsistent across page/helper and other adaptations point to missing file. | FAIL F5 |
| One theme | README 132; PROJECT_PAGE 67 | Quantum Unlocked. Actual platform tag is a human check. | OK presence |
| Four judging criteria | README 109–114; PROJECT_PAGE 61 | All four appear. Interactive execution claim needs F7 repair. | OK presence; claim FAIL F7 |
| Accessibility notes and image alt text | README 42–46, 118; PROJECT_PAGE 19–21, 63 | Present; factual curve descriptions and shipped UI require F6/F7 repair. | FAIL F6/F7 |
| Repository link | README 134; PROJECT_PAGE 71 | https://github.com/sauravdasmg/Qollab present. Public accessibility was not asserted or checked here. | OK presence; public access manual |
| Video | README 136; PROJECT_PAGE 72 | `[[VIDEO LINK]]` remains, expressly allowed by this task. | OK for this audit; human completion pending |
| Top-level recorded cloud saved results | recorded_ionq.py, evidence_summary.json | Eight campaign raw receipts plus six archival receipts; each file below 2 MB. | OK storage; archival reproduction FAIL F8 |
| Top-level local curves and metadata | nt_curves.py, recorded_local.py | Both numerical suites are present; only frozen has full receipt metadata. | FAIL F4 |
| Build-window provenance | Parent provenance JSONL lines 86, 97, 125, 145, 189, 217, 235; reuse timestamps | Merge 01:00 UTC; imports 01:08; revised plan/manifest/evidence and T campaign all Oct 10. No reviewed event establishes a final G2/G3 PASS. | OK timing evidence; scientific gate FAIL F2 |

The existing reviews are not final passes: G1_review.md begins `G1 REVIEW: HOLD`; G2_prep.md begins `MANIFESTS: BLOCKED`. The W deterministic uncertainty amendment and current manifest-loader checks address their respective technical concerns. They do not erase the continuing N gate failures or missing reuse explanation. Full independent new-seed simulation was intentionally not repeated under this task's quick-check restriction; this report independently verifies the saved fresh evidence and arithmetic, not a newly generated campaign.

## STYLE (non-blocking)

- Model-name suffixes and library-license identifiers are identifiers, not performance numbers. Their presence was checked separately from empirical claims.
- The cloud sign/scope explanation is repeated in several sections; it can be shortened after the contradictions are fixed.
- “The project plan does not list citable paper identifiers” is process commentary. A concise attribution to the known recipes would serve readers better once F5 is resolved; do not invent citations.
- `[[VIDEO LINK]]`, actual public repository availability, platform theme selection, final publication, and logged-out/video acceptance remain the expressly excluded human steps. None alone caused this verdict.

## Disposition

FAIL pending resolution of F1–F9. The numerical evidence is internally reproducible; the primary scientific acceptance conditions and the submission's claim/reproduction/packaging descriptions are not all satisfied. No submission code or documentation was repaired by this reviewer.
