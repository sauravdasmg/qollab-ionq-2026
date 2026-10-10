# Eyes-Free Python implementation handoff

Created anew after the admitted window-open receipt. No rehearsal/probe implementation reused.
Owned outputs are the Python core, WAV fallback, bounded evidence CLI and focused tests.
No interactive UI or science PASS is supplied. This effort is supported by Qollab & IonQ.

Qiskit 2.x, NumPy, SciPy, Matplotlib and standard-library dependencies only.
`circuit_pack.py` packs phase-major circuits into disjoint wires and marginalizes little-endian counts. It was written during the hackathon build window and is used by Entanglement Court, The Noise Tax and Eyes-Free.
GHZ phase recipes, frequency-blind fitting, browser audio/speech, receipts, UI, and evidence/decoder protocol are specific to Eyes-Free.
The orchestration work order describes an earlier generic JS audio probe; none is copied here.

Protocol: GHZ widths 1,2,4; 12 phases; H analysis before terminal Z measurements;
Qiskit little-endian classical wires. Exact reference controls include incoherent GHZ and
products: product harmonics prevent interpreting frequency as entanglement certification.
Fit accepts phases/counts only, never a width answer. Profile grid 0.025, refined local minima,
free cosine/sine, constrained offset (1e-8 interior numerical guard), binomial likelihood, family alpha 0.05/6, lowest-frequency
tie selection, all disconnected accepted components retained. Low signal, boundaries,
wide/disconnected intervals and optimizer failure are inconclusive. Contrast interval uses a
union of joint (including frequency) Wald radii over accepted profile grid points, with
grid-Bonferroni adjustment and LR null test; these are asymptotic intervals whose empirical
coverage must be independently checked, especially at physical boundaries. No bootstrap is run.

Audio encodes the measured estimate: 220*f Hz, 0.5*C peak, 2 seconds, mono 48 kHz PCM,
50 ms linear fades, no normalization. Decode sees only WAV samples and public constants.
Text preserves the identical full-precision fit including units, intervals, residuals and flags.
There is no learner/usability, acoustic-emission, noise-recovery or entanglement-certification claim.
Only informative estimates are offered by the main fallback. Verify actual sendFile signature
and downloads on Qollab before acceptance; the Python download is unavailable without sendFile; the published JS page uses browser Web Audio/speech.

Built-in main default: one list job of 36 circuits. IonQ: one disjoint 21-wire circuit, one run,
one result, cached get_counts, fixed guarded aria-1 option verified from backend options.
Historical phase_frame interface (current slots are in cloud_slots.py):
Use phase_frame=k*pi/2 for frozen and k*pi/2+pi/24 for fresh, k=0..3; 1000 shots.
E01 smoke uses phase_frame=-1, shots=100, 19 wires and asymmetric X controls.
The historical export used phase_frame=2*pi. Current E10 is the acceptance slot at frame=0; E11/E12 are reserved retries. None is included in the embedded E02-E09 sweep fits.
Retries are human-controlled exact failed retries only. No automatic job retry or polling.

Nine actual slot RECORD_JSON objects are bundled in top-level recorded_ionq.RECORDED.
Preserve original consoles under local-only results/exports/ and set source_file to the actual original console filename.
For authentic slots, suite/shot budget/independent manifest hash and exact packed manifest are validated against cloud_slots.py. Effective model and count totals are checked. UTC is retained if present or derived from the original timestamped export filename; descriptive counts/manifest digests are derived without changing the raw data. The older receipt schema remains supported. Four unique
phase triples are required for each recorded sweep; duplicate/missing packs do not produce fits.
Two cloud sweeps are not 44 independent cloud instances. Mathematical references, live ideal,
recorded cloud and local noise approximations retain separate labels.
