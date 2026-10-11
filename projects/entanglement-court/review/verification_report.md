VERDICT: FAIL

Independent final claim verification, 2026-10-10 UTC. The reviewer authored none of the submission implementation or documentation. This review replaces the earlier verification report and changes no implementation, documentation, or saved evidence. Two blocking findings remain: the development figure and its captions mix shot budgets (F1), and the shipped summary calls an uncalibrated approximation calibrated (F2). The headline frozen/fresh and cloud certification numbers reproduce.

## Scope and method

Read README.md, PROJECT_PAGE.md, main.py, all top-level physics/helper modules, campaign.py, recorded_ionq.py, evidence_summary.json, experiments/PLAN.md including both amendments, the local harness/noise/summary generator, full frozen/fresh/development result files, supporting result/check files, all 33 HTML exports, prior independent reviews and manifests, the previous verification report, the official hackathon rules/AMA/binding answers, and 70 matching project provenance entries. Inspected all three PNGs and the companion web accessibility provisions. Reviewed the historical campaign factory at the exact documented git commit. The verifier used the verify-claims procedure with the user's explicit quick-check restriction: no full campaigns, fresh random-stream experiments, noise sweeps, or new cloud jobs were run.

Checks independently decoded archived counts, inverted binomial tails, recomputed aggregate fractions, compared every compact counter/statistic with its full source, checked source/export hashes and circuit identities, and performed small deterministic four-qubit mathematical checks. Summing retained local counters is not reproducing the discarded raw draws. This report is neither a formal scientific superiority approval nor final browser/publication acceptance.

The build-window tool reports build phase. Matching provenance spans 2026-10-09T23:19:27Z through 2026-10-10T16:11:48Z, consistent with the supplied opening receipt. Important entries are provenance.jsonl lines 28 (development gate), 34 (C01), 105 (local campaign summary), 123 (historical HOLD), 166 (omitted cloud preparation noise), 178 (corrected runs), and 180 (campaign completion with deviation). These logs support recorded in-window activity; they cannot establish exhaustive authorship history. No parent process log or STATE.md was edited because this task authorizes only this report.

## Executed checks

Commands used the documented repository interpreter `../../.venv/Scripts/python.exe` from the submission folder, with bytecode writing disabled. No scientific source file was edited.

| Check | Reproduced result | Status |
|---|---|---|
| `python ../../tools/check_submission.py .` | All substantive automated blockers pass. Exit 1 solely because the existing verifier report does not say PASS. Six human-only steps remain. | OK under the task's report/human exclusions; this report remains FAIL for F1/F2. |
| `python ../../tools/qollab_local.py run . --backend ideal` | Exit 0; contract_verified=true; default 200 shots; one list job with six small circuits; main elapsed 3.09 s, runner elapsed 5.04 s. | OK |
| Same default in an isolated copy of only the 17 top-level files | Exit 0; contract_verified=true; main elapsed 2.91 s, runner elapsed 3.49 s; one live exhibit plus 25 retained recorded exhibits. | OK |
| Isolated top-level package with `--param slot=C08`, built-in ideal | Exit 0; main elapsed 0.20 s, runner elapsed 0.76 s. No review/results/experiments/web/figures directories were present. | OK |
| `python -m pytest tests -q -p no:cacheprovider` | 47 passed, seven setup errors caused by denied access to the environment's default `C:/Users/<user>/AppData/Local/Temp/pytest-of-<user>`. | Environment issue, resolved in the next check. |
| `python -m pytest tests -q -p no:cacheprovider --basetemp=review/.verification-final-temp --tb=short` | **54 passed in 22.73 s**, exit 0. | OK |
| Archived receipt integrity | 31 full receipts match original exported JSON and the 31-entry EXPORT_INDEX; all export SHA-256s match. Loader accepts 25 records, excludes six superseded near-threshold records, and reports zero malformed records. | OK |
| Current cloud circuit identity | C08-C25: 18/18 recipe and circuit hashes match. C02-C07: current hashes differ, as explicitly documented. | OK |
| Historical recipe reconstruction | C02-C07 at commit `3a0b99071655a50567990b84a9958596f94f3c29`: 6/6 recipe and packed-circuit hashes match retained recordings. | OK |

The isolated copy was automatically removed. Pytest created only temporary fixtures. Automatic approval review rejected cleanup of `review/.verification-final-temp` with **"blocked by policy"**; those fixtures remain, are not submission evidence, and were not used to modify the project. The isolated local runs emitted the expected Agg noninteractive-display warning; they are not browser visual acceptance tests.

## Claims table

R = README.md; P = PROJECT_PAGE.md. Line numbers refer to the reviewed versions identified by SHA-256 below. Repeated headline/table claims are grouped. JSON paths identify data in the one-line top-level evidence_summary.json. Counts are recomputed from retained data, not copied from narrative summaries. Dates, slot IDs, revision IDs, software versions and command budgets are also checked; they are not treated as experimental effect sizes.

| Claim | Source | Reproduced value / evidence | OK/FAIL |
|---|---|---|---|
| Four-qubit connected graph paired with separable equatorial product preparation | R4,18; P3,11,15 | graphs.py and cases.py implement connected bipartite four-wire templates and product preparations. Independent checks cover all four default cases. | OK |
| Exactly uniform ideal Z distributions, exact total variation zero | R18; P15 | Exact diagonal-phase argument gives 1/16 per outcome. Statevector maximum paired TV 1.11e-16 and uniform discrepancy 6.94e-17 are roundoff. Finite-shot histograms are not claimed identical. | OK |
| Two witness coloring bases/settings | R10,18; P15 | A/B generator maps jointly cover four stabilizers; additional Z exhibit is a control. Current cloud Z reference is explicitly mathematical. | OK |
| Biseparable threshold 1/2; strict certification above it | R18; P15 | Largest squared Schmidt coefficient over all seven bipartitions is 0.5000000000000001 for each supported graph. Generator-projector lower-bound operator is positive up to -2.64e-16 roundoff; witness.py uses strict F_lower > .5. | OK |
| Simultaneous per-round guarantee with measurement assumptions | R20,106; P17,95 | alpha=.05 divided over two preparations and four generators gives .00625 each; CP tail inversion residual 5.90e-17 at representative 200-shot counts. Union bound needs no independence between generators, but needs valid marginal IID-shot models and trusted/bounded measurement bias. No campaign-wide guarantee is claimed. | OK |
| 24 frozen + 20 fresh local instances | R26; P23 and figure captions | Full source and compact summary contain 24 and 20 cases; all manifests, manifest hashes and sampling seeds match independently staged files. Four graph templates recur; these are parameter instances, not distinct graph isomorphism classes. | OK |
| Ideal graph certification .50/.50 | R5,26; P5,23 | 12,000/24,000 and 10,000/20,000 retained graph certificates at 100 shots/block. | OK |
| Nominal Aria-like graph certification .42/.43 | R5,26,31; P5,23,28 | 10,016/24,000=.4173333333 and 8,554/20,000=.4277000000, rounded to two decimals; scale 1. | OK |
| Zero product/biseparable false certificates | R27; P5,24 | Each control: 0/528,000 frozen and 0/440,000 fresh saved rounds across configurations. Finite observations, not zero population risk. | OK |
| Comparator ties, no stronger-baseline victory | R28,102,106; P25,91,95 | witness.py:26 calls simultaneous_witness directly; all 2,904 frozen/fresh configuration/control rows have equal certificate counts. Counts/alpha/budget are shared. | OK |
| Ideal retains deliberate preparation noise; nominal Aria scale 1 | R31; P28 | experiments/run.py:174 applies manifest phase flips before the optional approximate device channel. | OK |
| Missing local raw draws disclosed; no complete independent rerun claimed | R33; P30; PLAN46 | experiments/run.py:368 discards counts; sources retain aggregates/probabilities/seeds. Dated amendment expressly supersedes retention claims. This review verifies arithmetic only for the original local campaigns. | OK, scoped limitation |
| Cloud 12/12 easy certified, 0/12 near-threshold certified | R5,29,45; P5,26,42 | Independent raw parity decoding and CP calculation: 12 easy bounds >.5, all 12 corrected near bounds <=.5. Six easy receipts are expressly legacy deviations. | OK as descriptive tally |
| Frozen easy C02-C07: 6/6, F_lower .75-.86 | R41; P38 | Minimum .746063679961, maximum .857248102210; correctly rounded. | OK |
| Fresh easy C14-C19: 6/6, F_lower .67-.75 | R42; P39 | Minimum .667093542653, maximum .746807080310. | OK |
| Corrected frozen near C08-C13: 0/6, F_lower .11-.18 | R43; P40 | Minimum .108288492822, maximum .176504543153. | OK |
| Fresh near C20-C25: 0/6, F_lower .07-.25 | R44; P41 | Minimum .067758859007, maximum .246972961125. | OK |
| Cloud simulator/date/shots/slot provenance | R29,37; P26,34 | All 24 retained campaign records: ionq_simulator, aria-1, 200 raw shots, UTC 2026-10-10, corresponding slot/case; export metadata matches. All block marginal totals equal 200. | OK |
| Separate C01, 100 shots on 2026-10-09 | R37,49; P34,46 | Archived smoke has 100 raw shots, case 0, seed 2026100100, aria-1, UTC end 23:58:48.524; independently recomputed target F_lower=.744565381423. Excluded from campaign tally. | OK |
| Easy legacy preparation p < .015 was omitted | R41,47,53; P38,44,50 | Declared p range .001090316970-.014952533337; historical circuits omit channel. Loader/archive status and docs label deviation. | OK |
| First C08-C13 superseded, 13:37-13:42 UTC; corrected runs 15:05-15:08 UTC | R53; P50 | Exact export UTC endpoints fall within these minute ranges. Six old near records remain archived but are filtered from retained counts. | OK |
| Corrected C08-C25 use channel, four blocks/eight ancillas/24 wires, omit two Z blocks | R37,53,83,111; P34,50,72; PLAN42 | Factory and recorded layouts agree: four witness blocks, 16 data wires plus eight measured ancillas; only data bits enter parities. Independent phase flips on Z-measured wires may be omitted without changing measured distribution. Added gates incur device noise as disclosed. | OK |
| Default anchor and historical jobs: six four-wire blocks | R83,111; P72 | Six blocks, total 24 wires. Built-in executes the list of components; IonQ executes one packed circuit. Built-in campaign list aggregate is 32 wires, never submitted as a 32-wire IonQ job. | OK |
| Exact current recipe reproduction C08-C25 at Shots=200 | R47; P44 | 18/18 circuit and recipe hashes match deterministic current build; new counts need not match. | OK |
| Historical C02-C07 reproduction via named commit | R47; P44 | Historical factory plus helper manifest yields 6/6 matching circuit/recipe hashes. Missing review directory is emulated by disabling only optional repository comparison; circuit construction is unchanged. | OK |
| C01 blank slot/Case=0/Challenge=sealed/Shots=100 | R49; P46 | Matches anchor factory and recorded settings; C01 correctly is not a valid campaign slot. | OK |
| Complete shipped cloud receipts and accurate EXPORT_INDEX | R51; P48 | Top-level recorded_ionq.py includes 31 full count receipts and hashes; all 31 job-ID/UTC-end export matches are exact. Historical original_source_file is separated from corrected source_file. | OK |
| Compact local statistics, original UTC/platform/versions/settings and source hashes | R57; P83 | All three campaigns match full sources field by field. Original UTC values: frozen 00:56:56.483497, fresh 01:26:08.339217 on Oct 10; development Oct 9 23:43:18.176191. Windows 11, Python 3.14.6, Qiskit 2.5.2, NumPy 2.5.3, SciPy 1.18.1. Summary generated Oct 10 16:09:34.534965 UTC. | OK |
| Saved-data evidence label claims calibration | evidence_summary.json:1 $.evidence_label; experiments/make_summary.py:88 | Label says calibrated; harness uses preliminary hardcoded rates and a different aggregate channel, without a matching calibration record. | **FAIL F2** |
| Frozen/fresh figures: 100 shots, 24/20 cases, ideal versus Aria scale 1 | R59-65; P52-58 | Saved rows uniquely select the correct 100-shot settings; visible chart bars agree with saved rates. Easy cases certify, near cases abstain. | OK |
| Development figure: four cases, 100 shots, all ideal/Aria fractions 1.0 | R67,69; P60,62; figures/development.png title/bars | At 100 shots Aria fractions are .974/.969/.956/.966, mean .96625. All-one Aria values belong to separate **200-shot** development projection rows. | **FAIL F1** |
| Three static charts, separate interactive web companion | R72-73; P65-66 | Three PNGs are static plots; web source files exist separately. Page documents flattened upload names. Final upload/render is a human step. | OK except F1's development values |
| Approximately 4 s, historical local range 3.49-3.79 s on Oct 10 | R6,79; P7,70 | Range comes from the previous independent report: 3.49 s source-folder run and 3.79 s isolated run. Preserved here as historical reviewer observations, not shipped experiment data or browser timings. Current independent runs gave 5.04 s repository and 3.49 s isolated runner elapsed; main elapsed 3.09/2.91 s. Approximate, explicitly local, not a guaranteed bound. | OK with provenance qualification |
| Local commands use frozen/fresh manifests and 1,000 draws | R90-98; P77-87 | CLI accepts --suite, --independent-manifest, --draws 1000 and --output-dir; sources record 1,000 draws. Full commands intentionally not executed by this worker. | OK instructions, not a new reproduction claim |
| doi:10.1038/s41534-024-00810-3 contextual finite-copy witness citation | R14; P11 | Publisher identifies "Valid and efficient entanglement verification with finite copies of a quantum state," npj Quantum Information 10, 14 (2024). No new theorem is attributed to this project. | OK |
| Qiskit 2.x; library names/licenses; helper dates Oct 9-11, 2026 | R121; P110 | Declared bundled libraries and shared-helper notes are present; local/receipt Qiskit version 2.5.2 agrees. Dates describe the build window, not evidence of work performed after this review. | OK |

The contextual paper citation was verified against the [publisher's article page](https://www.nature.com/articles/s41534-024-00810-3). No unseen paper claim or novelty search is inferred from that check.

## Blocking findings, exact text and necessary disposition

### F1 - Development chart overlays 200-shot evidence onto a 100-shot chart

README.md:67 and PROJECT_PAGE.md:60 state exactly:

> Static LOCAL MODEL chart from saved development aggregates at 100 shots/block: four development cases, ideal device channel versus Aria-like scale 1, all certification fractions equal 1.0. This is a bar chart, not an interactive web screenshot.

The same substantive text is repeated in R69/P62. The PNG title is exactly **"development LOCAL MODEL | 100 shots/block"**, and all eight visible bars reach 1.0.

Independent recomputation from both `evidence_summary.json -> campaigns[suite=development].cases[].configurations[]` and `results/development.json -> cases[].noise_results[]` gives:

| Development case | Ideal, 100 shots | Aria scale 1, 100 shots | Aria scale 1, 200 shots |
|---|---:|---:|---:|
| 0 | 1000/1000 = 1.000 | 974/1000 = .974 | 1000/1000 = 1.000 |
| 1 | 1000/1000 = 1.000 | 969/1000 = .969 | 1000/1000 = 1.000 |
| 2 | 1000/1000 = 1.000 | 956/1000 = .956 | 1000/1000 = 1.000 |
| 3 | 1000/1000 = 1.000 | 966/1000 = .966 | 1000/1000 = 1.000 |
| Mean | 1.000 | **.96625** | 1.000 |

Root cause: experiments/run.py:471-474 selects by noise name alone:

```python
rows = [(i, x["controls"]["graph"]["summary"]["certification_rate"])
        for i, r in enumerate(cases) for x in r["noise_results"] if x["noise"]["name"] == model]
if rows:
    ax.bar([i + shift for i, _ in rows], [v for _, v in rows], width=.4, color=color, label=label)
```

It includes both 100- and 200-shot `aria@1` rows at the same x coordinates. The later 200-shot bars cover the 100-shot bars. The title at line 479 uses `result['config']['shots']` (100). This is a quantitative/budget misrepresentation, not a style issue; frozen and fresh files do not contain this duplicate setting.

Required disposition: filter plotted rows by both noise setting and shot budget, regenerate the development PNG from retained 100-shot data, and correct both documents' alt text/captions. Alternatively show an explicitly labeled separate 200-shot projection series with its own budget. No new experiments are needed. Recheck any chart generator selection by actual per-row shots rather than the suite-level default.

### F2 - Shipped local evidence is labeled calibrated without matching calibration

`evidence_summary.json:1`, key `evidence_label`, says exactly:

> LOCAL MODEL (calibrated IonQ-like approximation, not device)

`experiments/make_summary.py:88` generates the same string. In contrast, experiments/PLAN.md:21 says **"Rates are preliminary approximations, not official calibration"**, and experiments/noise.py:98 states **"Raw gate errors approximate server-compiled noise; not official calibration."**

The executable campaign uses `experiments/noise.py:6-8`: Aria 2q=.007, Forte 2q=.0125, Forte Enterprise 2q=.022. `experiments/run.py:176-179` reads these constants and applies two aggregate independent single-wire depolarizing channels; it does not load a fitted cloud model. The repository's separately calibrated `tools/ionq_noise_params.json` instead records .009/.012/.021 and explicit Oct 3 fitting notes. Those different tool-model calibration records do not calibrate the model that produced the shipped Court evidence. No calibration dataset, fit result, or validation mapping for this exact campaign model is retained in the audited source/evidence.

The broad LOCAL MODEL category is correct, and the README/page correctly call it an approximation. The added word **calibrated** is nevertheless an unsupported evidence-strength claim inside a shipped file, and must agree with those limitations.

Required disposition: remove "calibrated" from the generator and regenerate the compact summary, preserving the original campaign data/settings/hashes and truthful local-model limitation. Alternatively supply and disclose actual calibration evidence for this exact model; changing to different rates would require separate new evidence and must not relabel the existing runs. The first option needs no experiments.

## Independent cloud calculation and retained provenance

For each raw bit string, the independent decoder used integer shifts by the layout's classical offsets and widths, then parity masks from the manifest. All independently reconstructed marginals equal the saved ones and sum to the requested shots. For generator successes k out of N, it calculated `p_lower = beta.ppf(.00625, k, N-k+1)` (zero for k=0), then `F_lower = sum(p_lower) - 3`. Saved witness values were comparisons only, never inputs.

| Slots in order | Independently recomputed target F_lower |
|---|---|
| C02-C07 | .746063679961, .777348056569, .857248102210, .792012080948, .842335082899, .811738661062 |
| C08-C13 corrected | .164908022394, .108288492822, .176504543153, .164729964662, .164277515699, .159746468377 |
| C14-C19 | .746807080310, .667093542653, .695833739459, .725153155793, .739616017400, .687064756473 |
| C20-C25 | .246972961125, .067758859007, .243643051943, .164277515699, .182097339086, .147931321983 |

All target bounds agree with archived values within 1e-12. Independently computed campaign product-impostor bounds range from -1.446939928859 to -1.192197911773; zero impostors certify. Smoke C01's product bound is -1.528585751935. These are conditional witness bounds, not calibrated measurement-error claims.

Thirty-three HTML files comprise 31 full cloud records, one historical built-in run, and one invalid-slot exception export at 13:38:19.886Z. The exception is not a successful receipt or a scientific observation. All 31 archived full records match original raw counts, settings, layouts, uncertainty, shot counts, noise model, UTCs, and circuit/recipe/layout hashes. EXPORT_INDEX accurately identifies every source export and SHA-256. Originals remain repository-only; their complete count receipts are included in the top-level Python file and do not require the HTML files at runtime.

C02-C07 are retained historical easy observations, not clean executions of the preregistered noisy recipe. PLAN44 explicitly says the 12/12 tally is not an undeviated protocol-adherence pass. Thus provenance line 180's "Preregistered >=8/12 easy met" is only outcome arithmetic with an adjacent deviation, not this verifier's formal acceptance of exact protocol execution. The corrected near receipts and six fresh easy receipts do match current circuitry. Superseded near receipts are preserved, labeled, and excluded rather than silently overwritten.

## Local evidence, comparison and robustness

Frozen/fresh each have 22 configurations: ideal plus three model approximations at seven scales; each configuration has 1,000 draws/control and 100 shots/block. Development has an additional 200-shot Aria projection, which causes F1 if not explicitly filtered. Full source hashes and every compact counter/statistic match; all frozen/fresh manifests and sampling seeds agree with the independent manifests.

| Nominal configuration | Frozen graph certificates / rounds | Fresh graph certificates / rounds |
|---|---:|---:|
| Ideal device channel, preparation noise retained | 12000/24000 = .500000 | 10000/20000 = .500000 |
| Aria-like scale 1 | 10016/24000 = .417333 | 8554/20000 = .427700 |
| Forte-like scale 1 | 3582/24000 = .149250 | 3101/20000 = .155050 |
| Forte Enterprise-like scale 1 | 62/24000 = .002583 | 51/20000 = .002550 |

Reaggregating saved Aria rows at scales .5/.75/1/1.25/1.5/1.75/2 gives frozen fractions .494042/.471083/.417333/.337292/.246458/.156750/.090625 and fresh fractions .495050/.474900/.427700/.341850/.247150/.157400/.086600. These are descriptive saved-data calculations, not a rerun. Nominal easy fractions are .834667/.855400; power degrades substantially at stronger approximate noise. The headline .42/.43 is not a uniform robustness floor. The docs make no speedup, hardware advantage, or superiority claim.

Baseline fairness is literal identity: both calls receive the same counts, shots and alpha. This supplies no evidence against a distinct stronger witness. Exact state truth is used for mathematical checks and coverage, not to substitute for measured parity counts. Per-round CP/union-bound validity does not imply every finite empirical cell exceeds .95, independence across all configurations, or a campaign-wide confidence guarantee. All observed control certificates are zero, with finite-data uncertainty. Measurement bias is not bounded by these cloud records.

The dated final plan amendment properly dispositions the prior retention/strongest-baseline issues: raw-count loss is acknowledged and the educational claim is narrowed. It does not create missing raw evidence or a fresh-stream verification. Those limitations remain material and are not silently upgraded by this report.

## Earlier review dispositions

| Earlier finding | Current disposition |
|---|---|
| Original early mathematics HOLD: missing phase channel, incorrect manifest truth, incomplete coverage, invalid bias inputs | Current implementations contain phase flips, manifest-specific references, both-preparation coverage, and nonnegative/finite bias validation; relevant tests pass. |
| Earlier evidence HOLD: cloud C02-C25 absent | Full archive now supplied; corrected/current and legacy evidence are distinguished. Formal exact-protocol pass still not inferred for legacy easy cases. |
| Prior final F1: unsupported one-second runtime | Replaced with attributed approximate local timings. Historical 3.49/3.79 s observations preserved above. |
| Prior final F2: generic legacy/C01 reproduction | Version-specific historical commit and blank-slot C01 instructions added; deterministic hashes checked. |
| Earlier inaccurate archive source pointers | 31 accurate indexed sources/hashes verified; original pointers retained separately. |
| Earlier image meaning/assets issues | Static figures and publication asset instructions are now explicit; **new F1 still blocks the development figure's numerical shot label**. |
| Earlier inaccurate six-block description of current cloud slots | Current docs specify four witness blocks plus ancillas, with default/legacy distinction. |
| Prior final F7: unsupported strongest-baseline phrase | Dated PLAN40 supersedes it and explicitly states implementation identity. Historical preregistration remains intact. |
| Prior final F8: lost sampled local raw counts | Explicitly disclosed in both pages, compact metadata, loader status and PLAN46. Accepted only as scoped aggregate arithmetic, not full raw-result reproduction or scientific superiority. |

## Shipped contract and submission musts

The Python upload set is the 17 top-level files. The checker counts 21 prospective files because it additionally considers four companion web assets that would be flattened at publication. Every included file is below 2 MB; the largest is evidence_summary.json at 1,478,120 bytes, and recorded_ionq.py is 671,396 bytes. Repository-only full frozen/fresh JSON files exceed that limit but are explicitly not uploads; they are not runtime dependencies.

Manual dispatch inspection complements the checker's limited matcher (it reports zero submitting call sites because the variable is named `active`). main.py submits exactly once; IonQ receives a single packed circuit, with one `job.result()` followed by one cached `result.get_counts()`. There are no automatic retries, import-time main calls, QPU/provider credentials, qiskit-aer, BackendSamplerV2, input(), future imports, or BOMs in shipped sources. Campaign model selection is guarded by the validated simulator backend. Default built-in execution works independently of all repository subfolders.

campaign.py:24-25 optionally reads repository manifests when present locally; an isolated shipped package has no such directory and checks embedded manifest hashes instead. This is not a required external read. recorded_ionq.py is imported from the shipped set; export paths are provenance annotations, not runtime file reads. No external result/manifest file is needed by the uploaded default or campaign slot.

| Submission requirement | Evidence / result |
|---|---|
| MIT license | Standard MIT LICENSE with 2026 Saurav Das copyright. OK. |
| Exact attribution | R127/P115: "This effort is supported by Qollab & IonQ." OK. |
| AI/tools/templates disclosure | R121/P110 name AgentMesh, OpenCode free models, OpenAI Codex, Claude Code, consulted rules/docs and template/outside-code scope. OK. |
| Reused in-window helpers and shared note | Both helper docstrings carry the same purpose/date/project-use note; R121/P110 disclose reuse and project-specific physics/presentation. main.py stamps shared_helpers in manifests. OK. |
| Libraries/licenses | Qiskit, NumPy, SciPy, Matplotlib identified with licenses; requirements.txt states bundled dependencies. Runtime/tests use Qiskit 2.5.2. OK. |
| Theme | Quantum Unlocked in R123/P112. Actual live tag remains human-only. |
| Judging-criteria summary | All four criteria covered at R108-113/P97-102. OK. |
| Accessibility | R115-117/P104-106 include keyboard/text/color/audio/caption provisions; companion source has native controls, focus styles, ARIA status/labels and keyboard handlers. Browser/screen-reader acceptance not run here. Development alt text remains F1. |
| Repository | https://github.com/sauravdasmg/qollab-ionq-2026 at R129/P117. Link supplied; public visibility and final published revision remain human checks. |
| Video | [[VIDEO LINK]] at R130/P118 is explicitly permitted for this task. Human step. |
| Recorded reproduction and saved result inclusion | Version-specific settings plus top-level complete cloud records and compact local statistics are present. HTML/full local sources correctly identified as repository archives. OK. |
| Logged-out run, final Qollab publication, page image rendering | Not performed by this worker. Historical exports do not prove final-package logged-out acceptance. Human steps, not manufactured claim failures. |

## STYLE (non-blocking)

- The frozen PNG's abbreviated x-axis labels still crowd together around 03/04 and 17/18. Values are recoverable from source data; improve spacing if desired.
- Runtime documentation could name "runner elapsed" versus main.py's shorter "Run runtime" more explicitly. Both are local timings, and actual elapsed time varies by environment.
- Repository README image links use figures/ while the project page intentionally uses flattened names. The existing upload instructions explain this; publishing must still attach and verify the assets.
- The default displays 26 exhibits. That is verbose but now closes each figure and completes successfully; it is not a contract error.

## Reproduction of the two failures without experiments

Run this read-only snippet with the repository Python from this folder:

```python
import json
from pathlib import Path
summary = json.loads(Path('evidence_summary.json').read_text(encoding='utf-8'))
print(summary['evidence_label'])
dev = next(c for c in summary['campaigns'] if c['suite'] == 'development')
for case in dev['cases']:
    rows = [(r['noise']['name'], r['shots_per_block'],
             r['controls']['graph']['certificates'], r['draws'])
            for r in case['configurations']
            if r['noise']['name'] in ('ideal', 'aria@1')]
    print(case['case_id'], rows)
```

PASS requires correcting F1 and F2 and rechecking the affected figure, captions and regenerated summary. No additional full experiments are required to fix these reporting defects. The passing scientific arithmetic and runtime checks must not be used to change this verdict before those defects are resolved.

## Reviewed identities

| File | SHA-256 |
|---|---|
| README.md | 5d9f52da2c1c0316d67870d7ae7678a88425d7a6610885398087db75a8461071 |
| PROJECT_PAGE.md | 9cbf5760c7ee6f85091722b5c77425fe0603c11832c7fec336e9ed3914d75580 |
| main.py | bda6fd4d1dc6a1fd3ee22ef8ccdba18d796f69037b3cf938f15cfdecc35541e8 |
| recorded_ionq.py | 91f367a381a99f817d722e4ad6d9eae96aff2dfb0b1d02ca9dc987b965dc1c74 |
| evidence_summary.json | 88f9c0d0f63eeacf59276e8b5760a40e2bcef3fd449aeb7b7c567dacd150c6f1 |
| figures/development.png | a07fbd84f5ed1122c05bb0c58e1790b7de0210218c80f6d08bb16522159578c8 |
| results/frozen.json | 548677ec1476f70f83f4a33112fb2d2a0afd25fcff746821bcf1a06df48400e9 |
| results/fresh.json | f240500074d21aaa0fceb9a4a9c22a2a3dfb2d62d8582bc69bc1daf946f4d2dc |
| results/development.json | 051f6a3355c1315b526c50b80638ec6fedd01fa72cfb19fd8f7e3a340bd31be7 |
| experiments/PLAN.md | 5a8852a2cda05908b0a770d2e8d70d1b14cbf6c770f1718de3af3fd90b58e08c |

Report written UTC: 2026-10-10T18:54:20.035869+00:00.
