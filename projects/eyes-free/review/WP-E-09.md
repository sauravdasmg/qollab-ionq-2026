# WP-E-09: cloud fit marginalization repair

Build-window work: 2026-10-10 UTC. No circuits or source cloud exports changed.

Root cause: experiments/cloud_fit.py sliced bits[-offset-width:] for every
nonzero offset. This includes all lower-offset blocks through bit 0, so their
parities multiply into the intended block parity. Qiskit prints bit 0 at the
right. The correct interval is bits[21-offset-width:21-offset]. The existing
circuit_pack.unpack already uses that correct interval.

E02-E05 main() records were captured using tools/qollab_local.py's run_project,
seed 1234, 1000 shots per slot, ionq-aria. The requested unmodified CLI E02 run
was stopped because its default 21-wire noisy statevector was too slow for a
quick check. The four-slot check selects Aer's matrix_product_state method and
one thread, preserving circuits, noise channels, compilation, backend facade,
one-job contract and shot budgets. This is a local approximation of IonQ.
Reproduce: ../../.venv/Scripts/python.exe experiments/check_cloud_slots.py.
Captured RECORD_JSON lines: results/local-cloud-slots.txt; counts and fits:
results/local-cloud-slots.json. All manifest, hash, suite, shot and effective
noise fields agree with corresponding cloud records.

| n | Local old-slice frequency | Local corrected frequency | Corrected contrast |
|---|---:|---:|---:|
| 1 | 0.644249 | 1.003399 | 1.000000 |
| 2 | 0.612123 | 1.988344 | 0.989304 |
| 4 | 0.554951 | 4.000938 | 0.955860 |

E01 cloud counts are exactly {"1010011000011110101": 100}, matching the
19-wire smoke circuit. Marginals are 0101, 1111, 0000, 1010011, each 100 shots.

Existing Qollab records are valid and require no rerun for this bug. Corrected
frequency-blind fits, using unchanged counts and unchanged fitting algorithm:

| Suite | n | Frequency | Frequency CI | Contrast | Contrast CI |
|---|---:|---:|---|---:|---|
| frozen | 1 | 0.9922 | [0.9750, 1.0250] | 1.0000 | [0.8913, 1.0000] |
| frozen | 2 | 1.9986 | [1.9750, 2.0250] | 0.9890 | [0.8744, 1.0000] |
| frozen | 4 | 3.9977 | [3.9750, 4.0250] | 0.9506 | [0.8335, 1.0000] |
| fresh | 1 | 0.9970 | [0.9750, 1.0250] | 0.9909 | [0.8417, 1.0000] |
| fresh | 2 | 1.9974 | [1.9750, 2.0250] | 0.9864 | [0.8775, 1.0000] |
| fresh | 4 | 4.0052 | [3.9750, 4.0250] | 0.9546 | [0.8466, 1.0000] |

Regenerated results/cloud_fit.json and evidence_summary.json with the corrected
fits. cloud_fit.py also synchronizes recorded_ionq.py from the original exports;
no counts are altered. Targeted tests: 5 passed, including four emulated frozen
slots recovering frequencies within 0.05, an asymmetric lower-block parity
regression, and the real E01 smoke result. No full experiment sweep performed.
Global process/provenance logs remain the orchestrator's responsibility because
this worker may write only inside the submission folder.
