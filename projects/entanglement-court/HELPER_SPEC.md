# HELPER_SPEC.md: Shared Helper Specification

This document specifies the internal architecture, interface contracts, data schemas, validation rules, and testing requirements for shared helper modules (`circuit_pack.py` and `receipt.py`) within `entanglement-court`.

Each admitted project writes its own implementation from scratch during the build window. Helpers share interface specifications but code must never be copied across projects or transplanted from templates/rehearsals.

---

## Verbatim Disclosure Note

> Shared helpers live in their own files: circuit_pack.py and receipt.py implement circuit packing, count normalization, backend dispatch and evidence receipts. Written during Oct 9-11, 2026, with exact UTC provenance and source/license attribution; used by Two Whispers Make a Word, Never Lose Twice and Entanglement Court only where the shipped manifest lists the helper. Project-specific physics, decoding, inference and presentation are described on each project page.

---

## 1. Module Overview and Ownership Boundaries

- **`circuit_pack.py`**:
  - Implements disjoint circuit packing onto a single quantum register (width $\le 25$ qubits).
  - Implements deterministic count unpacking and marginal histogram reconstruction.
  - Contains classical bit offset resolution, bit-order normalization, and validation logic.
  - Pure transformation logic; contains no direct backend execution or network calls.

- **`receipt.py`**:
  - Validates and parses recorded IonQ runs pasted into `recorded_ionq.py`.
  - Serializes runtime receipts and produces standardized `RECORD_JSON` structured evidence records.
  - Analyzes cached execution artifacts without refetching from backends.
  - Formats verification data, hashes, metadata, and uncertainty intervals.

- **`main.py` / Runtime Ownership**:
  - Owns backend instantiation, backend options configuration, job submission, and result caching.
  - Dispatches execution paths cleanly between local built-in simulation and IonQ single-circuit execution.
  - Holds execution objects; hands cached `result.get_counts()` data to helper modules.

---

## 2. Interface Specification: `circuit_pack.py`

### 2.1 `pack_circuits(circuits, max_qubits=25)`

Packs an ordered collection of independent, disjoint quantum circuits into a single aggregate `QuantumCircuit`.

- **Parameters**:
  - `circuits` (`Sequence[QuantumCircuit]`): List or sequence of independent circuits to pack.
  - `max_qubits` (`int`, default `25`): Maximum permissible total qubit width for the packed circuit.
- **Returns**: `(packed_circuit, layout)`:
  - `packed_circuit` (`QuantumCircuit`): Combined circuit containing all input blocks allocated onto non-overlapping wire subsets.
  - `layout` (`dict` or `list` of metadata records): Precise placement layout detailing block allocation.
- **Validation Rules & Error Handling**:
  - Rejects empty input sequence (`circuits` must not be empty).
  - Rejects circuits exceeding the total qubit width limit: $\sum 	ext{width}_i \le 	ext{max\_qubits}$ (default 25).
  - Rejects nonterminal measurements: all measurements must be terminal (at the end of circuit execution).
  - Rejects dynamic circuits, conditional operations (`c_if`), classical branch controls, or unsupported classical wiring.
  - Rejects cross-block gates: each block must remain strictly independent on its assigned disjoint wires.
- **Layout Structure**:
  For each sub-circuit block, the layout record includes:
  - `block_name` (`str`): Identifier or original circuit label.
  - `qubit_offset` (`int`): Starting physical index on the packed quantum register.
  - `qubit_width` (`int`): Number of qubits occupied by the block.
  - `clbit_offset` (`int`): Starting physical index on the packed classical register.
  - `clbit_width` (`int`): Number of classical bits allocated to the block.
  - `qubit_to_clbit_map` (`dict[int, int]`): Local block qubit-to-cbit measurement mapping.
  - `manifest_hash` (`str`): Deterministic SHA-256 digest of the block's operation sequence.

### 2.2 `unpack_counts(raw_counts, layout)`

Deconstructs raw packed counts into ordered per-block marginal count dictionaries.

- **Parameters**:
  - `raw_counts` (`dict[str, int]`): Output counts from `result.get_counts()` of the packed circuit.
  - `layout` (`dict` or `list`): Placement layout produced by `pack_circuits`.
- **Bit-Ordering & Decoding Semantics**:
  - Qiskit bitstring formatting convention: **highest classical bit index is printed on the leftmost side** ($c_{N-1} c_{N-2} \dots c_1 c_0$).
  - String slicing must be derived explicitly via classical offsets:
    For classical bit index $k$, the character position from the left in a string of length $N$ is index $(N - 1 - k)$.
  - Visually guessed substrings or naive index slicing without explicit classical bit offsets are strictly forbidden.
- **Normalization & Validation**:
  - Strip spaces, validate binary alphabet (`[0, 1]`), and pad leading zeros to match the total packed classical register width.
  - Reject non-integer counts, negative counts, or invalid characters.
  - Shot preservation guarantee: Every individual shot is accounted for.
  - For every block, the sum of marginal counts strictly equals the total packed counts:
    $$\sum_{k} 	ext{block\_counts}[k] = \sum_{j} 	ext{raw\_counts}[j] = 	ext{total\_shots}$$

---

## 3. Runtime Dispatch & Backend Execution Contract

- **Built-in Backend Dispatch**:
  - Executes individual small circuits as a list without packing.
  - Runs in $< 40$ seconds with flushed progress.
  - Bypasses packing overhead while sharing identical downstream analysis and unpacking data structures.
  - Gracefully handles backends that reject `set_options`.

- **IonQ Execution Branch**:
  - Disjoint packing: All sub-experiments packed into exactly one circuit on $\le 25$ qubits.
  - Single execution guarantee: Exactly **one job**, exactly **one `backend.run()`**, and exactly **one `job.result()`**.
  - No result polling loops, no second job submissions, no circuit lists to remote backends, and no automatic retries.
  - Guard noise configuration:
    ```python
    if backend.name == "ionq_simulator":
        # configure explicit noise options
    ```
  - Record the actual effective `noise_model` directly from options or the explicit dialog setting; never label it "as selected in Qollab".
  - Result caching: Immediately capture `result.get_counts()` into memory. Never call `job.get_counts()`.

---

## 4. Specification: `receipt.py` & Record Serialization

### 4.1 Parser & Storage Interface (`recorded_ionq.py`)

- `recorded_ionq.py` exposes top-level string `RECORDED = """..."""` (initially empty).
- Human operators paste JSON objects into `RECORDED` (one `RECORD_JSON` object per line or raw JSON block).
- `receipt.py` parser requirements:
  - Supports prefixed lines or bare JSON objects.
  - Skips empty or whitespace-only lines.
  - Validates all schema requirements; fails gracefully and reports malformed or missing fields without throwing unhandled exceptions.
  - Strictly honest: never synthesizes, hallucinates, or invents missing empirical evidence.
  - Distinguishes clearly between live built-in ideal, mathematical reference, recorded Qollab IonQ, and local noise approximation.
  - Local simulations must never masquerade as Qollab evidence.

### 4.2 `RECORD_JSON` Schema

Each serialized record is a valid JSON object containing:

1. `schema_version` (`str`): Semantic version of receipt schema (e.g., `"1.0.0"`).
2. `source` (`str`): Must be `"Qollab IonQ simulator run"`.
3. `operator_environment` (`str`): Operator platform, browser, or machine environment.
4. `backend` (`str`): Backend name (e.g., `"ionq_simulator"`).
5. `noise_model` (`str` or `dict`): Effective noise configuration applied during run.
6. `shots` (`int`): Total shots executed.
7. `settings` (`dict`): Execution options and backend configuration.
8. `qiskit_version` (`str`): Running Qiskit package version (e.g., `"2.5.2"`).
9. `utc_start` (`str`): ISO-8601 UTC timestamp of execution start.
10. `utc_end` (`str`): ISO-8601 UTC timestamp of execution completion.
11. `case_id` (`str`): Experiment or test-case identifier.
12. `construction_seed` (`int` or `None`): Parameters or seed used to build circuits. Note: remote sampler seeds are not reproducible.
13. `recipe_hash` (`str`): Hash of experiment recipe / parameter definition.
14. `circuit_hash` (`str`): Hash of packed circuit instruction representation.
15. `layout_hash` (`str`): Hash of placement layout table.
16. `layout` (`list[dict]`): Full layout mapping block positions and bit offsets.
17. `raw_counts` (`dict[str, int]`): Unmodified raw counts returned by the backend.
18. `marginals` (`dict[str, dict[str, int]]`): Unpacked per-block marginal histograms.
19. `uncertainty` (`dict`): Finite-shot statistical uncertainty intervals (e.g., binomial/multinomial Wilson intervals).
20. `assumptions` (`list[str]`): Stated theoretical assumptions.
21. `job_id` (`str` or `None`): Remote job execution ID if available.
22. `source_file` (`str`): Local export path in `results/exports/` pointing to the original export file.
23. `receipt_path` (`str`): Relative path to serialized receipt artifact.
24. `result_path` (`str`): Relative path to processed results artifact.
25. `error` (`str` or `None`): Error message and charged attempt ID if failure occurred.

---

## 5. Required Unit and Property Tests

The test suite in `tests/` must verify helper behavior deterministically:

1. **Unequal-width Asymmetric States**:
   - Pack blocks of varying qubit widths (e.g., 1-qubit, 2-qubit, 5-qubit circuits). Verify non-interference and correct subregister mapping.
2. **Nonidentity Classical Bit Mapping**:
   - Verify correct unpacking when local circuits measure qubit $q_i 	o c_{\pi(i)}$ where $\pi$ is a permutation or nonidentity mapping.
3. **Spaced and Short Binary Keys**:
   - Validate handling of counts formatted with whitespace (e.g., `'01 10'`), omitted leading zeros, or varying string lengths.
4. **Conservation of Totals**:
   - Verify marginal shot totals for each block match the total packed count shot sum.
5. **Invalid Data Rejection**:
   - Reject negative counts, floating-point shot counts, invalid characters, or corrupted bitstrings.
6. **Width Cap Enforcement**:
   - Pack requests totaling $> 25$ qubits must raise a clear exception before backend dispatch.
7. **Terminal-only Measurement Enforcement**:
   - Reject circuits containing mid-circuit measurements or reset operations followed by gates.
8. **One Job / One Fetch Assertion**:
   - Instrumented test doubles must assert that IonQ dispatch invokes `backend.run()` exactly once and `job.result()` exactly once.
9. **Built-in Backend `set_options` Robustness**:
   - Verify built-in dispatch succeeds without failure even if backend raises an error or rejects `set_options`.
10. **Malformed and Empty Record Handling**:
    - Verify `receipt.py` parser handles empty `RECORDED`, truncated JSON, missing required fields, or corrupt syntax with honest error reporting.
11. **Finite-shot Intervals & Reproducibility**:
    - Validate confidence interval calculations from saved counts and deterministic offline re-computation.
12. **Independence Constraint Disclosure**:
    - Explicitly test and document that packed blocks sharing a single circuit execution are not independent generated instances across runs.
