# Disposition of the final verification findings

`verification_report.md` is the independent round-2 report (VERDICT: FAIL), kept unedited. The project rule allows two
verification rounds; the remaining findings were fixed by the orchestrator (Claude Code) after round 2, without a
third independent review:

- F1 (development chart mixed 100- and 200-shot rows): chart now filtered by `shots_per_block`; regenerated from saved
  data (Aria scale 1 at 100 shots: 0.974, 0.969, 0.956, 0.966); captions corrected in README and PROJECT_PAGE.
- F2 (evidence label said "calibrated"): label now "IonQ-like noise approximation with preliminary rates; not official
  calibration, not device"; `evidence_summary.json` regenerated.
- Later: runtime claim updated to the measured Qollab value (7.93 s); helper note corrected; web layout fixes.
Tests after the fixes: 179 passed. Details: repository `research/logs/provenance.jsonl` (2026-10-10/11).
