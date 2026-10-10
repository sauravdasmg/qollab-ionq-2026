VERDICT: FAIL

# Round-2 final independent claim verification: The Noise Tax

Reviewed 2026-10-10 against the working tree at commit 9d5d9de. The reviewer wrote none of the code or docs. Only this file was written. No full experiment was run. The only experiment-harness calls were the documented `--validate-only --draws 1` smoke checks, with output sent to a scratch directory outside the project.

Round 1 found F1-F9. Eight are resolved (F2 is resolved as honest disclosure of a failed gate). One new, small, blocking documentation mismatch remains (R2-1). It is a two-line fix.

## Quick checks

| Check | Result | Status |
|---|---|---|
| `python -m pytest tests web -q` | 103 passed, 4 expected non-interactive Matplotlib warnings, 7.1 s | OK |
| `python ../../tools/check_submission.py .` | All BLOCKERs pass except "Verifier report says PASS" (this report). The recommended-only "unguarded noise_model" item is a static false positive: main.py:42 guards it with `cloud = name == 'ionq_simulator'`. Six human-only MANUAL items remain. 27 shipped files, none over 2 MB. | OK |
| `qollab_local.py run . --backend ideal --shots 512` | Exit 0. 14 receipts validated, 0 issues. Prints LIVE, RECORDED and LOCAL MODEL lines. | OK |
| `run.py --suite frozen\|fresh --independent-manifest review/manifests/<suite>.json --draws 1 --validate-only` (as in README:107-108) | Both exit 0 with "manifest validated; bounded smoke complete; no inference evidence". The documented commands now run as written. | OK |
| `nt_curves.py` against `results/frozen.json` and `results/fresh.json` | `source_sha256` matches both files. All analysis arrays equal the full results (0 differences). Only the `gate.decision` label differs (see style note S1). | OK |

## Round-1 findings: disposition

| # | Round-1 finding | Current evidence | Status |
|---|---|---|---|
| F1 | Sign rule reversed | README:15 and :29 and PROJECT_PAGE:13 say "positive favors joint for W and the published hedge for N; negative favors the ideal one-way reference and the attained product, respectively." web/index.html:5 says the same. "First-named" appears nowhere. Headings read "published hedge vs attained product" throughout. | RESOLVED |
| F2 | N gates failed, undisclosed | README:7 and :33 and PROJECT_PAGE:7 and :17 say: "Preregistered N acceptance conditions were NOT met: frozen aria-1 N interval width 0.325 > 0.30, and frozen vs fresh aria-1 N crossover difference 0.116 > 0.10 (fresh comparison pass = false)... no tolerance or seed was changed." README:35 adds "overlap does not satisfy the separate 0.10 agreement tolerance". web/index.html:4 shows the same text at the top of the page and adds "This is not a G2/G3 pass". Recomputed: frozen aria-1 N CI [0.25, 0.575], width 0.325; fresh-vs-frozen difference 0.11579525522; `recorded_local.FRESH['fresh_comparison']['N']['pass']` is False and the tolerance is 0.1. `nt_curves.py` gate decisions now read "LOCAL_CONDITIONS_ONLY; N precision and frozen/fresh agreement gates not met". All N and W numbers, seeds and tolerances equal the frozen/fresh result files. Nothing in shipped text implies a G2/G3 pass. Whether to submit is a human decision. | RESOLVED (as disclosure) |
| F3 | Reproduction commands broken | README:104-112 and PROJECT_PAGE:73-83 use one working directory. Each suite has its own manifest. The new-or-`--resume` output policy is stated. The make_curves/summary.json caveat is explained. The commands were verified, including `--resume` and `--validate-only`. | RESOLVED |
| F4 | Fresh run metadata missing | `recorded_local.FRESH` (top level) has machine "Saurav", simulator "exact NumPy small-block density evolution", qiskit 2.5.2 / numpy 2.5.3 / python 3.14.6, start/end UTC, settings, manifest and configuration hashes and instance ids. README:37 and PROJECT_PAGE:19 point to it. | RESOLVED |
| F5 | Reuse disclosure | The "project-specific" overclaim is gone. README:23 and :146 and PROJECT_PAGE:11 and :93 credit the retired Two Whispers / Never Lose Twice code and name the adapted files. The "see REUSE_MANIFEST.md" references are removed from `reuse_sources.json`. The `circuit_pack.py` header now matches the docs. | RESOLVED |
| F6 | Figure descriptions wrong | README:48 and :50 and PROJECT_PAGE:29 now say solid/dashed/dotted identify Aria/Forte/Forte Enterprise, and that anchors appear only in frozen-anchors.png. I viewed the PNGs and they match, including N hatch bands 0.25-0.575 (frozen) and 0.15-0.45 (fresh). The anchors figure shows six archival receipts and is labelled so. README links use `results/figures/`, which resolves in the repository. PROJECT_PAGE:27 tells the human to upload the three PNGs as top-level assets. | RESOLVED (PNG upload is a human step, see S3) |
| F7 | Interactive/accessibility claims | README:11 and PROJECT_PAGE:9 state that the published entry is the JS page flattened by `tools/package_project.py noise-tax --web`. The existing `uploads/noise-tax-web.zip` contains index.html, main.js, main.css, tax_bridge.py and main.py. README:140 and PROJECT_PAGE:91 describe the accessibility features as source-level and name browser acceptance as a human check. web/index.html has labels, a table per chart and `aria-live` regions. | RESOLVED |
| F8 | Six archival runs unlabelled | A new "Archival anchors" section (README:77-90, PROJECT_PAGE:56-69) gives origin, date (00:15-00:38 UTC, 2026-10-10), model, shots, signed value and case=0, and says "NOT reproducible via T slots". Recomputed from `recorded_ionq.py`: W +0.0113/+0.0017/-0.0177 (1000 shots); N -0.0209 (4000), -0.0211 and -0.0377 (1000). All match. But see R2-1 for a mismatch in the same section. | RESOLVED, except R2-1 |
| F9 | Default W samples only one arm | README:27 and PROJECT_PAGE:13 now say the default run samples the W joint arm only against the analytic ideal one-way reference, N samples both arms, and W one-way circuits run only in cloud slots. This matches main.py:49. | RESOLVED |

## Remaining blocking finding

### R2-1: Two claims about the six archival receipts do not trace to shipped files

- README.md:90 and PROJECT_PAGE.md:69 say: "These six raw receipts are stored in top-level `recorded_ionq.py`, indexed in `evidence_summary.json`; the original exported consoles are retained in repository `results/exports/`."
- `evidence_summary.json` indexes only the eight T01-T08 runs. It has no archival entries. A search for "archiv" returns 0 hits, and the keys are project, source, date_utc, campaign_slots, export_files, runs, outcomes, interpretation and deviations.
- This project's `results/exports/` holds only the nine Noise Tax exports (eight T slots plus the default run). The six archival console exports are in `projects/two-whispers/results/exports/` (W02, W03, W04) and `projects/never-lose-twice/results/exports/` (N02, N03, N04). `recorded_ionq.SOURCE_FILES` records exactly those paths.

Exact fix, either one:
- Edit README:90 and PROJECT_PAGE:69 to read "stored in top-level `recorded_ionq.py` (provenance paths in `recorded_ionq.SOURCE_FILES`); the original console exports are in the retired projects' `results/exports/` (`two-whispers` W02-W04, `never-lose-twice` N02-N04)." Delete "indexed in `evidence_summary.json`".
- Or add the six archival records to `evidence_summary.json` and keep the sentence, correcting the `results/exports/` location.

## Claims table (recomputed; all prior numbers re-checked)

| Claim | Source | Reproduced | Status |
|---|---|---|---|
| W crossings frozen = fresh: 1.309 / 1.141 / 0.684 (aria-1 / forte-1 / forte-enterprise-1) | README:41-43, PROJECT_PAGE:23-25 | `nt_curves` 1.30902106 / 1.14112128 / 0.68379391 (frozen and fresh) | OK |
| W calibration sensitivity 1.206-1.431 / 1.062-1.233 / 0.655-0.716 | same | 1.20624-1.43093 / 1.06219-1.23272 / 0.65464-0.71566 | OK |
| N frozen 0.411 [0.250, 0.575], 0.339 [0.200, 0.475], 0.200 [0.100, 0.300] | README:44-46, PROJECT_PAGE:23-25 | 0.41105 [0.25, 0.575], 0.33874 [0.2, 0.475], 0.20012 [0.1, 0.3] | OK |
| N fresh 0.295 [0.150, 0.450], 0.243 [0.125, 0.375], 0.144 [0.050, 0.225] | same | 0.29526 [0.15, 0.45], 0.24327 [0.125, 0.375], 0.14370 [0.05, 0.225] | OK |
| Gate misses: frozen aria-1 N width 0.325 > 0.30; frozen/fresh difference 0.116 > 0.10; fresh comparison pass = false | README:7, :33; PROJECT_PAGE:7, :17; web/index.html:4 | width 0.325; difference 0.11580; `pass` False; tolerance 0.1 | OK |
| 24 frozen and 24 fresh instances; grid 0-2 in steps of 0.025; fixed-prize coefficient 0.02 | README:29 | consistent with the manifests and `nt_curves`; the default run prints "n=24" | OK |
| Cloud T01-T08 signed values +0.005, -0.030, +0.002, -0.022, +0.005, -0.035, +0.011, -0.022 | README:64-71, PROJECT_PAGE:43-50 | +0.0053, -0.0299, +0.0023, -0.0216, +0.0047, -0.0353, +0.0107, -0.0220, from the parsed `recorded_ionq` receipts and `evidence_summary.json` | OK |
| Ranges: W +0.002 to +0.011; N -0.035 to -0.022 | README:5, :56 | W +0.0023 to +0.0107; N -0.0353 to -0.0216 | OK |
| Models, shots, slots and date for T01-T08 | README:62-71 | match `evidence_summary.json` runs and `slot_config`; all on 2026-10-10 UTC | OK |
| Six archival values, dates, shots | README:83-88 | match the parsed receipts | OK |
| Default run shows 14 stored receipts; 0 issues | README:90 | "14 validated historical receipts; 0 receipt issues" | OK |
| "indexed in evidence_summary.json"; consoles "retained in repository results/exports/" | README:90, PROJECT_PAGE:69 | not found (see R2-1) | MISMATCH |
| Local run about 1 s, 512 shots, aria-1 | README:9, PROJECT_PAGE:3 | `qollab_local` ideal run completes in about 1 s | OK |
| No speedup, device-threshold or noise-reduction claims | README:124-129 | none made | OK |
| MIT, attribution line, AI/library disclosure, theme, judging summary, accessibility, repo link | README:131-162, PROJECT_PAGE:89-100 | all present; `[[VIDEO LINK]]` remains (human step) | OK |

## Baseline and scope audit

- W's baseline is the analytic ideal optimal one-way sequential reference. This is stated and scoped as "not all LOCC or separable measurements".
- N's baseline is the attained product strategy under one fixed prize. This is stated as not globally optimal.
- Both are evaluated on the same instances and the same noise scale grid. Cloud anchors use the same shot budget per arm.
- There is no use of the exact answer inside a sampled estimate. The analytic W reference is declared as such.
- The noise model is stated: a calibrated IonQ-like approximation (LOCAL MODEL), distinct from RECORDED simulator runs.
- No W cloud 95% interval excludes zero, and the docs do not claim a statistically certified W advantage.

## STYLE (non-blocking)

- S1: `results/frozen.json` and `results/fresh.json` still carry the raw label `"decision": "PASS_LOCAL_CONDITIONS"` next to `precision_target_met: false`. The shipped `nt_curves.py` and `recorded_local.py` carry the corrected label. Those two files are not shipped top-level, but a one-line README note would remove any ambiguity.
- S2: The web UI still uses the legacy names "Two Whispers" and "Never Lose Twice" as card titles, buttons and aria-labels (web/index.html:37, 47, 61, 71, 107-108; tax_bridge.py:54, 62; main.js:365). The docs call the games W and N. Rename or add a line explaining the mapping.
- S3: `tools/package_project.py` ships only .py, .json, LICENSE, requirements.txt and the web files, not PNGs or markdown. The PNG upload for PROJECT_PAGE images is a human step (PROJECT_PAGE:27). Make sure it happens, or the three images will not render.
- S4: The console prints the 14 receipts without an ARCHIVAL / T-slot label, although README:90 says they are "separate". Also, fresh aria-1 N prints "precision target met=False" because its width is 0.300000000000000044, so the width is effectively exactly 0.30. README names only the frozen width miss, which is the substantive one.
- S5: `reuse_sources.json` lists a destination `calibration_snapshot.json`, but the shipped file is `calibration_snapshot.py`.
- S6: Hidden scratch directories in the project root (`.test-tmp-wp-nt-09`, `.verify-final-tmp`, `.wp-nt-01-pytest*`, `.pytest_cache`) are not shipped. Consider deleting them.

## Disposition

FAIL, on one fixable documentation item (R2-1). After the two-line edit, with F1-F9 otherwise resolved and tests, contract check and default run passing, this should be PASS. The N gate misses are disclosed as failed, with no number, seed or tolerance changed. The submission decision remains the human's.
