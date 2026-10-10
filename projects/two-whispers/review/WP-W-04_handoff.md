# WP-W-04 harness repair and synthesis handoff

Completed root-cause repairs: reversed global/local density indexing and Pauli placement; noisy sequential substituted for the ideal H1 ceiling; stale infidelities, wrong gate basis, independent leg channels, noisy rz and missing infidelity conversion; source rotations unrecognized after decomposition; missing physical development objective and incorrect textbook phase/relabel search freedom.

Density evolution now uses Qiskit qargs. Source preparation is separated by a receiver_start barrier in the same circuits consumed by main.py and the harness. Both compilers therefore preserve this boundary. Local calibration remains an approximation and cloud confirmation is outstanding. H1 remains conditional on ideal sources when source noise is included; the noisy sequential estimate is separately retained. H2 keeps its 0.9 factor and cannot pass without completed equal-budget synthesis.

Synthesis provides a development-only exact physical objective, common recipe selection across orientations, 128 candidates per family by default, full ideal outcome/unitarity checks to 1e-10, budget-matched textbook standard/compiler variants without equivalence search, an untuned reference, exclusive recipe/search exports, hashes and source/receiver/CPU/wall accounting. Tests exercised budget 2 on case 1 only. Full selection was deliberately not run.

Checks: 58 tests passed (8 expected noninteractive plotting warnings). The specified five-draw development G1 smoke completed with 192 small-block regime rows, under results/quick-g1-smoke/development.json. This smoke is not science evidence; no completed synthesis selection exists yet, and its H2 and combined gate cannot pass. Prior campaign files were not replaced.

Orchestrator full-search command:

```
python synthesis.py --budget 128 --cases 1 2 3 4 5 6 7 8 --output-dir results/development-selection-w04
```

Then use the exported recipe.json with experiments/run.py --recipe, in a new evidence directory. Full search, full evidence, independent verification, and Qollab cloud confirmation remain outstanding.

Shared parent process-log/STATE/provenance files are outside this worker's writable scope; this local handoff and provenance entry are for the orchestrator to incorporate.
