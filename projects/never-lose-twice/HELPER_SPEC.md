# Shared Helper Specification: `circuit_pack.py` and `receipt.py`

This document defines the interface and operational contracts for `circuit_pack.py` and `receipt.py`. It is an internal implementation specification for this submission folder (`never-lose-twice`), authored anew under work package WP-S-01.

## Required Disclosure Note

> Shared helpers live in their own files: circuit_pack.py and receipt.py implement circuit packing, count normalization, backend dispatch and evidence receipts. Written during Oct 9-11, 2026, with exact UTC provenance and source/license attribution; used by Two Whispers Make a Word, Never Lose Twice and Entanglement Court only where the shipped manifest lists the helper. Project-specific physics, decoding, inference and presentation are described on each project page.

---

## 1. Specification: `pack_circuits`

### Signature
`pack_circuits(circuits, max_qubits=25) -> (packed_circuit, layout)`

### Contracts & Validation
- **Input Validation**:
  - Rejects empty input sequence of circuits.
  - Rejects circuits containing nonterminal measurements (measurements must only occur at the end of circuit execution).
  - Rejects dynamic circuits, conditional operations (`c_if`), resets mid-circuit, and unsupported classical wiring.
  - Validates total required qubits across all input circuits: if `sum(qc.num_qubits for qc in circuits) > max_qubits` (default 25), rejects execution with an explicit width cap error.
  - No cross-block gates are permitted; each sub-circuit is placed on disjoint quantum and classical register slices.
- **Layout Structure**:
  - `layout` is an ordered list or structured record containing:
    - `name`: block name or sub-circuit identifier.
    - `qubit_offset` and `qubit_width`: starting index and width on the packed quantum register.
    - `clbit_offset` and `clbit_width`: starting index and width on the packed classical register.
    - `local_qubit_to_cbit_map`: explicit mapping from local sub-circuit qubits to local classical bits.
    - `manifest_hash`: deterministic hash of the constituent circuit definition/instructions.
- **Packed Circuit Assembly**:
  - Combines sub-circuits onto a single `QuantumCircuit` with disjoint wire allocations.
  - Measurements are placed at the end into the designated classical offsets.
  - Packed blocks are not independent generated instances; they run synchronously in one circuit execution.

---

## 2. Specification: `unpack_counts`

### Signature
`unpack_counts(raw_counts, layout) -> dict[str, dict[str, int]]` or ordered block histograms.

### Contracts & Bitstring Decoding
- **Bit Order Handling**:
  - Qiskit displays the highest classical bit index on the left (big-endian bitstring display: c[N-1] ... c[1] c[0]).
  - Unpacking must decode via explicit classical offsets (`clbit_offset`, `clbit_width`) and register slices, NEVER by visually guessed string slicing or naive substrings.
- **Count Normalization**:
  - Normalizes raw binary keys, stripping internal spaces (e.g. `'01 10'` -> `'0110'`) and handling hex or leading zeros uniformly.
  - Rejects invalid bit keys (characters other than `'0'` and `'1'`).
  - Rejects negative counts, non-integer count values, and integer overflows.
  - Conserves total shot count: every shot is preserved. Each marginal histogram total must strictly equal the total shots of `raw_counts`.

---

## 3. Runtime Dispatch & Backend Ownership

- **Execution Separation**:
  - Built-in live execution (`BasicSimulator` / local default) uses standard circuit execution (or lists of small circuits).
  - IonQ branch requires packing onto disjoint wires <= 25 qubits.
  - Execution uses exactly one job: exactly one `backend.run(...)`, exactly one `job.result()`, and cached `result.get_counts()`.
  - Never call `job.get_counts()`, never perform result polling loops, never submit a second job, never pass an unpacked circuit list to IonQ, and never trigger automatic retries.
- **Ownership**:
  - Backend instantiation and job execution ownership remain strictly in `main.py` / caller.
  - `receipt.py` serializes, formats, and analyzes cached result objects; it never refetches or calls network backends.
- **Simulator Options & Noise**:
  - Options must be guarded: `if backend.name == "ionq_simulator": ...`
  - Record the actual effective `noise_model` from options or explicit dialog settings.
  - Never label simulator noise as "as selected in Qollab".
  - Gracefully handle cases where the built-in simulator refuses `set_options` yet proceeds with execution.

---

## 4. Specification: `receipt.py` and Evidence Serialization

### Recorded Parser & Validation
- Top-level `recorded_ionq.py` stores evidence in `RECORDED = """..."""` as an initially empty raw triple-quoted string.
- Operators paste JSON lines into `RECORDED`.
- Parser parses line-by-line, accepting bare JSON or `RECORD_JSON: { ... }` prefixes, skipping blank lines.
- Reports missing or malformed data honestly and rejects tampering; never invents evidence.
- No shipped data in subfolders. Original console exports stay in local-only `results/exports/`, referenced by `source_file`.
- Distinguishes clearly between:
  1. Live built-in ideal reference
  2. Mathematical reference
  3. Recorded Qollab IonQ evidence
  4. Local noise approximation
  No local simulation can masquerade as Qollab evidence.

### `RECORD_JSON` Schema
Every record must contain the following required fields:
- `schema_version`: schema identifier version string (e.g. `"1.0.0"`).
- `source`: `"Qollab IonQ simulator run"`.
- `environment`: operator machine, browser, or environment details.
- `backend`: backend name string (e.g. `"ionq_simulator"`).
- `noise_model`: effective noise model name / parameters.
- `shots`: integer total shots.
- `settings`: dictionary of runtime options/settings.
- `qiskit_version`: version string of Qiskit environment.
- `utc_start`: ISO-8601 UTC timestamp of execution start.
- `utc_end`: ISO-8601 UTC timestamp of execution completion.
- `case_id`: identifier of the experiment case / problem instance.
- `parameters`: construction seeds and instance parameters.
- `hashes`: dictionary containing recipe hash, circuit hash, and layout hash.
- `layout`: serialized block layout definition.
- `raw_counts`: complete packed counts dictionary.
- `marginals`: unpacked per-block marginal counts.
- `uncertainties`: statistical uncertainty, finite-shot intervals, and explicit assumptions.
- `job_id`: remote job identifier if available.
- `source_file`: path to the export in `results/exports/`.
- `receipt_path`: destination receipt file path.
- `result_path`: destination result summary path.
- On failure: retain charged attempt ID and explicit error reason. Remote sampler seeds are acknowledged as non-reproducible.

---

## 5. Required Unit Tests

Test suite (`tests/`) must verify the following properties deterministically without external network calls:
1. **Unequal-width asymmetric states**: Packing sub-circuits with differing qubit counts and asymmetric state preparations.
2. **Non-identity cbit mapping**: Circuits where physical qubit indices do not match classical bit indices 1-to-1.
3. **Spaced and short binary keys**: Parsing raw Qiskit count keys containing spaces, varied bitstring lengths, and leading zeros.
4. **Shot total preservation**: Verifying sum of counts in every marginal equals the packed total.
5. **Invalid data rejection**: Validating rejection of negative counts, float counts, invalid bit characters, and malformed structures.
6. **Width cap enforcement**: Rejection when cumulative qubit count exceeds `max_qubits` (25).
7. **Terminal-only measurement enforcement**: Rejection of circuits with intermediate measurements or dynamic branching.
8. **One job / one fetch contract**: Verifying with mock backends that exactly one `backend.run()` and one `job.result()` occur without polling or retries.
9. **Built-in options tolerance**: Verifying backend runs when backend refuses `set_options`.
10. **Malformed and empty record handling**: Verifying `receipt.py` parser behavior on empty string, comments, and invalid JSON.
11. **Finite-shot intervals & reproducibility**: Statistical interval calculation and deterministic reproducibility from saved counts.
