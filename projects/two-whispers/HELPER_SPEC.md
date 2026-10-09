# Shared-helper implementation specification

This internal specification defines an interface, not a shared implementation or project page. Each admitted project's runtime owner writes circuit_pack.py and receipt.py anew inside its submission folder during the Oct 9-11, 2026 build window. Never transplant implementations from another entry, tools, rehearsal, templates or an old Qollab draft. This task creates only HELPER_SPEC.md; backend ownership and project physics remain with their respective authors.

## Circuit packing

`pack_circuits(circuits, max_qubits=25)` returns `(packed_circuit, layout)`. Reject empty input, nonterminal measurements, conditions/control flow, unsupported classical wiring, and summed qubit widths over the cap. Allocate disjoint quantum and classical wires; no cross-block gates are permitted. Reject ambiguous measurement wiring rather than silently changing it. Terminal measurements form the final measurement suffix, with no subsequent quantum operation.

Layout is an ordered list, one entry per input block, containing block name, qubit offset/width, classical offset/width, explicit local qubit-to-cbit map, and manifest hash. Suggested field names are `block_name`, `qubit_offset`, `qubit_width`, `classical_offset`, `classical_width`, `qubit_to_cbit_map`, and `manifest_hash`. The manifest defines deterministic serialization and hashing, including measurement mapping. Preserve input block order and validate nonoverlapping offsets and widths.

`unpack_counts(raw_counts, layout)` returns ordered block histograms in layout order. Normalize binary keys including spaces and leading zeros; short keys are left-padded to the packed classical width. Reject empty or invalid keys, negative/noninteger counts (including booleans), and overflow beyond the declared classical width. Merge equivalent normalized keys by summing counts. Use exact integer arithmetic.

Qiskit displays the highest cbit on the left. Decode each normalized key to an integer and extract local cbit j using `(value >> (classical_offset + j)) & 1`; emit local classical bitstrings with the highest local cbit on the left. Use the explicit qubit-to-cbit map when interpreting outcomes in qubit order. Never use visually guessed substrings. Preserve every shot: each marginal total equals the packed total. Validate layout before decoding.

## Runtime ownership and dispatch

Keep built-in execution of a list of small circuits separate from IonQ single-pack execution. main.py owns backend/job lifecycle; receipt.py serializes and analyzes cached objects and never refetches or submits jobs. Built-in default completes end-to-end in less than 40 seconds with flushed progress and small circuit lists.

IonQ execution uses one packed circuit on disjoint wires, at most 25 qubits: exactly one backend.run, one job, exactly one job.result(), and cached result.get_counts(). Never use job.get_counts(), result polling, a second job, a circuit list, or an automatic retry. Guard noise options with `if backend.name == "ionq_simulator"`; built-in backends need not support set_options. Record the actual effective noise_model from backend options or the explicit dialog setting. Never label it "as selected in Qollab"; unavailable information is reported honestly.

Shipped code uses Qiskit 2.5.2 / 2.x, NumPy, SciPy, Matplotlib and stdlib; additional wheels require pure-Python approval. Backend is injected. No qiskit-aer, providers/API keys, Estimator, BackendSamplerV2, input(), dynamic circuits or postselection. Qollab invokes main() itself: no top-level or __main__ invocation. Use literal artifact paths.

## Receipts and recorded evidence

Top-level recorded_ionq.py stores an initially empty raw triple-quoted string: `RECORDED = r""""""`. Later the human pastes one RECORD_JSON JSON object per line in its Python editor. receipt.py accepts the RECORD_JSON prefix or bare JSON, skips blank lines, validates records, and reports missing/malformed data honestly. It never invents evidence. No shipped data lives in subfolders. Original console exports remain local-only in results/exports/; source_file points there.

receipt.py formats RECORD_JSON and validates these required fields (use a documented versioned schema):

- schema_version; source exactly "Qollab IonQ simulator run"; machine/browser or operator environment; backend; actual effective noise_model; shots; settings; Qiskit version.
- UTC start/end; case ID; construction seed and parameters; recipe/circuit/layout hashes; full layout and its block manifest hashes.
- Raw packed counts; all marginals; uncertainty and assumptions; job ID if available; source_file; receipt and result paths.

Validate field types, UTC timestamp order, supported schema version, hash format/consistency where reconstructable, count validity, shot totals, layout consistency, and equality of stored marginals with fresh unpacking of raw counts. A missing job ID is explicitly represented as unavailable, never invented. Distinguish requested construction seeds from remote sampling: remote sampler seeds are not reproducible. Finite-shot intervals state method, confidence level and assumptions; saved counts suffice to reproduce analysis.

Failure records retain the charged attempt ID and error, with available run metadata and explicit failure status. They must not claim successful counts or fabricate missing success fields. Never automatically retry a charged attempt.

Maintain distinct labels: live built-in ideal, mathematical reference, recorded Qollab IonQ, and local noise approximation. No local simulation can masquerade as Qollab evidence. A helper check is an implementation handoff, not independent science PASS. Packed blocks are not independent generated instances.

## Required quick tests

Use tiny states, deterministic assertions, and instrumented backend/job doubles; no external tools or cloud calls from tests. Required coverage:

- Unequal-width asymmetric states and a nonidentity cbit map, with explicitly expected marginal outcomes.
- Spaced/short binary keys, leading zeros, equivalent normalized keys and conservation of every marginal total.
- Invalid keys, negative/noninteger counts, overflow, invalid layout and width cap.
- Terminal-only measurement rejection, conditions and unsupported classical wiring.
- One job/one fetch, cached counts, and built-in backend that refuses set_options yet works.
- Malformed/empty record handling; finite-shot intervals; reproducibility from saved counts.

Tests use project-root imports even when experiments/run.py is launched by filename. Quick outputs use quick-* names and never overwrite full evidence. Do not run full experiments, sweeps, many seeds or large bootstraps during a quick check or default Run.

## Frozen common disclosure

Store the following verbatim and later reproduce it on each admitted README/page:

> Shared helpers live in their own files: circuit_pack.py and receipt.py implement circuit packing, count normalization, backend dispatch and evidence receipts. Written during Oct 9-11, 2026, with exact UTC provenance and source/license attribution; used by Two Whispers Make a Word, Never Lose Twice and Entanglement Court only where the shipped manifest lists the helper. Project-specific physics, decoding, inference and presentation are described on each project page.

The orchestrator finalizes one common actual-participants/filenames note for all surviving manifests; omit helpers/projects not actually used. Add Eyes-Free only if built and using those names, then regenerate the common note consistently. Exact UTC edit timestamps and source/license information belong in build provenance maintained by the orchestrator. Pre-kickoff generic tests are disclosed as tests with no reused code. Pages, figures, wording and layouts remain project-specific.
