# Disposition of the final verification findings

`verification_report.md` is the independent round-2 report (VERDICT: FAIL), kept unedited. Round 2 found F1-F9 of
round 1 resolved (F2 resolved as disclosure: the preregistered N precision and frozen/fresh agreement gates are reported
as failed) and one new finding, fixed by the orchestrator (Claude Code) without a third independent review:

- R2-1 (archival receipts said to be indexed in `evidence_summary.json` and exported in this folder): text now says
  `evidence_summary.json` indexes only T01-T08 and gives the retired projects' export paths.
- Later: web import crash on Qollab fixed (bridge no longer imports `noise_channel`); legacy game names replaced;
  layout fixes; slot runs documented as needing the Python version.
Tests after the fixes: 103 passed. Details: repository `research/logs/provenance.jsonl` (2026-10-10/11).
