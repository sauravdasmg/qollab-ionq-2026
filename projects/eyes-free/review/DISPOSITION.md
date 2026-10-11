# Disposition of the final verification findings

`verification_report.md` is the independent round-2 report (VERDICT: FAIL), kept unedited. Round 2 found round-1
F1-F6 and F8 resolved and the numbers reproduced; its four documentation findings were fixed by the orchestrator
(Claude Code) without a third independent review:

- N1: chart description now matches the page (pointwise 95% error bars, fitted curve, data table).
- N2: the page's LOCAL MODEL entries are described as analytic references (formula stated), not the calibrated suites.
- N3: slot reproduction needs the Python version; the "Run one packed IonQ sample" button is documented.
- N4: helper note corrected (each entry ships its own `circuit_pack.py`).
Tests after the fixes: 74 passed. Human acceptance on Qollab 2026-10-10. Details: `research/logs/provenance.jsonl`.
