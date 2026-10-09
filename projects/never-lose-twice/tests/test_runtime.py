"""tests/test_runtime.py: WP-N-02 runtime, packing, receipt and presentation checks.

All tests are deterministic and offline: they use tiny instrumented backend/job doubles, real tiny
BasicSimulator runs and in-memory synthetic record fixtures (marked TEST ONLY, never written to disk and
never shipped as evidence). No test submits a cloud job or touches the network.
"""
from __future__ import annotations

import hashlib
import json

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

import core
import receipt
import circuit_pack
import figures
import main as main_mod
import recorded_ionq

SHOTS = 200


def _sample_counts(circuit, shots, seed):
    probs = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False)).probabilities()
    rng = np.random.default_rng(seed)
    draws = rng.choice(2 ** circuit.num_qubits, size=shots, p=probs)
    counts = {}
    for draw in draws:
        key = format(int(draw), f"0{circuit.num_qubits}b")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _fake_counts(circuits, shots=SHOTS, seed=100):
    return [_sample_counts(circuits[index], shots, seed + index) for index in range(len(circuits))]


def _circuit_hash(circuits):
    digest = hashlib.sha256()
    for circuit in circuits:
        digest.update(circuit_pack.circuit_digest(circuit).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _synthetic_record(case=0, shots=SHOTS, noise_model="aria-1", seed=11):
    circuits, manifest = core.make_demo(case)
    packed, layout = circuit_pack.pack_circuits(circuits)
    raw_counts = _sample_counts(packed, shots, seed)
    marginals = circuit_pack.unpack_counts(raw_counts, layout)
    analysis = core.analyze_counts(marginals, manifest, lambda_value=0.02)
    hashes = {"recipe": manifest["recipe_hash"], "circuit": _circuit_hash(circuits),
              "layout": hashlib.sha256(json.dumps(layout, sort_keys=True).encode()).hexdigest()}
    return receipt.assemble_record(
        manifest=manifest, layout=layout, raw_counts=raw_counts, marginals=marginals,
        analysis=analysis, lambda_star=0.02, prize="frozen", shots=shots,
        backend_name="ionq_simulator", noise_model=noise_model,
        settings={"fixture": "TEST ONLY synthetic record; never shipped as evidence"},
        job_id="fixture-synthetic", qiskit_version="2.5.2",
        utc_start="2026-10-10T12:00:00Z", utc_end="2026-10-10T12:00:05Z",
        environment="pytest (TEST ONLY)", hashes=hashes, source_file="results/exports/none.txt",
        receipt_path="results/none.json", result_path="results/none.json")


# --------------------------------------------------------------------------- job/backend doubles
class _CountsResult:
    def __init__(self, counts):
        self._counts = counts
        self.get_counts_calls = 0
        self.job_id = "fake-result"

    def get_counts(self):
        self.get_counts_calls += 1
        if self.get_counts_calls > 1:
            raise AssertionError("result.get_counts() fetched more than once")
        return self._counts


class _CountsJob:
    def __init__(self, counts, job_id="fake-job"):
        self._counts = counts
        self.job_id = job_id
        self.result_calls = 0

    def result(self, *args, **kwargs):
        self.result_calls += 1
        if self.result_calls > 1:
            raise AssertionError("job.result() fetched more than once")
        return _CountsResult(self._counts)


class _BuiltinDouble:
    """Strict built-in double: accepts LIST jobs, has NO set_options, counts every access."""

    name = "basic_simulator"

    def __init__(self, counts_list):
        self._counts = list(counts_list)
        self.run_calls = 0
        self.last_target = None
        self.last_shots = None

    def run(self, circuits, shots=1024, **kwargs):
        self.run_calls += 1
        if self.run_calls > 1:
            raise AssertionError("built-in backend run called more than once")
        if not isinstance(circuits, (list, tuple)):
            raise AssertionError("built-in double expects a list job")
        if len(circuits) != len(self._counts):
            raise AssertionError("built-in double got an unexpected circuit count")
        self.last_target = circuits
        self.last_shots = shots
        return _CountsJob(self._counts, "fake-builtin-job")


class _IonQDouble:
    """Strict IonQ double: rejects lists, seconds jobs and second result fetches; has set_options."""

    name = "ionq_simulator"

    def __init__(self, counts):
        self._counts = counts
        self.run_calls = 0
        self.set_options_calls = []
        self.options = {"noise_model": "aria-1"}

    def set_options(self, **fields):
        self.set_options_calls.append(fields)
        self.options.update(fields)

    def run(self, circuits, shots=1024, **kwargs):
        self.run_calls += 1
        if self.run_calls > 1:
            raise AssertionError("second IonQ job")
        if isinstance(circuits, (list, tuple)):
            raise AssertionError("IonQ rejects circuit lists; circuits must be packed")
        return _CountsJob(self._counts, "fake-ionq-job")


# --------------------------------------------------------------------------- import without side effects
def test_import_creates_no_job():
    assert callable(main_mod.main)
    assert "backend" not in vars(main_mod)


def _set_backend(monkeypatch, backend):
    monkeypatch.setitem(main_mod.__dict__, "backend", backend)


def test_records_present_flag_missing():
    records, issues = receipt.load_records()
    assert records == [] and issues == []
    assert receipt.record_status(records) == "No recorded IonQ runs yet"


# --------------------------------------------------------------------------- built-in main branch
def test_builtin_double_strict_contract(capsys, monkeypatch):
    circuits, _ = core.make_demo()
    counts_list = _fake_counts(circuits, SHOTS)
    backend = _BuiltinDouble(counts_list)
    assert not hasattr(backend, "set_options")
    _set_backend(monkeypatch, backend)
    monkeypatch.setattr(main_mod.plt, "show", lambda *a, **k: None)
    main_mod.main(case=0, shots=SHOTS, prize="frozen")
    out = capsys.readouterr().out
    assert backend.run_calls == 1
    assert backend.last_shots == SHOTS
    assert "live built-in ideal" in out
    assert "No recorded IonQ runs yet" in out
    assert "frozen lambda*: 0.02000" in out
    assert "RECORD_JSON" not in out
    for block in ("attained_product", "published_hedge", "optimized_joint", "product_control"):
        assert block in out
    assert "never means zero risk" in out


def test_builtin_ignores_noise_model_and_validation(capsys, monkeypatch):
    circuits, _ = core.make_demo()
    backend = _BuiltinDouble(_fake_counts(circuits, 64, 50))
    assert not hasattr(backend, "set_options")
    _set_backend(monkeypatch, backend)
    monkeypatch.setattr(main_mod.plt, "show", lambda *a, **k: None)
    main_mod.main(case=0, shots=64, noise_model="forte-1", prize="tail")
    out = capsys.readouterr().out
    assert "ignored on the built-in backend" in out


def test_real_tiny_basic_simulator_builtin_branch(capsys, monkeypatch):
    from qiskit.providers.basic_provider import BasicSimulator

    _set_backend(monkeypatch, BasicSimulator())
    monkeypatch.setattr(main_mod.plt, "show", lambda *a, **k: None)
    main_mod.main(case=0, shots=64, prize="frozen")
    out = capsys.readouterr().out
    assert "live built-in ideal" in out
    assert "SOURCE:" in out
    for block in ("attained_product", "published_hedge", "optimized_joint", "product_control"):
        assert block in out


def test_main_requires_injected_backend(monkeypatch):
    monkeypatch.delattr(main_mod, "backend", raising=False)
    with pytest.raises(RuntimeError):
        main_mod.main()


def test_main_validates_inputs(capsys, monkeypatch):
    _set_backend(monkeypatch, _BuiltinDouble(_fake_counts(core.make_demo()[0], 8, 0)))
    for kwargs in ({"case": 9}, {"case": True}, {"shots": 0}, {"shots": -3},
                   {"noise_model": "warp-9"}, {"prize": "jackpot"}):
        with pytest.raises(ValueError):
            main_mod.main(**kwargs)


# --------------------------------------------------------------------------- IonQ main branch
def test_ionq_double_strict_contract(capsys, monkeypatch):
    circuits, _ = core.make_demo()
    packed, _ = circuit_pack.pack_circuits(circuits)
    packed_counts = _sample_counts(packed, SHOTS, 200)
    backend = _IonQDouble(packed_counts)
    _set_backend(monkeypatch, backend)
    monkeypatch.setattr(main_mod.plt, "show", lambda *a, **k: None)
    main_mod.main(case=0, shots=SHOTS, noise_model="aria-1", prize="frozen")
    out = capsys.readouterr().out
    assert backend.run_calls == 1
    assert backend.set_options_calls == [{"noise_model": "aria-1"}]
    records_lines = [line for line in out.splitlines() if line.startswith("RECORD_JSON")]
    assert len(records_lines) == 1
    payload = json.loads(records_lines[0][len("RECORD_JSON"):])
    assert "RECORD_JSON" in out and "copy the RECORD_JSON line above" in out
    assert receipt.validate_record(payload) == []
    assert payload["backend"] == "ionq_simulator"
    assert payload["noise_model"] == "aria-1"
    assert payload["shots"] == SHOTS
    assert payload["case_id"] == 0
    assert sum(payload["raw_counts"].values()) == SHOTS
    for block, histogram in payload["marginals"].items():
        assert sum(histogram.values()) == SHOTS
    assert set(payload["marginals"]) == set(core.make_demo()[1]["ordered_blocks"])
    assert "Fixed-prize decision" not in out
    assert "Readiness gap: no recorded Qollab IonQ runs yet" in out


# --------------------------------------------------------------------------- circuit packing
def test_pack_asymmetric_unequal_widths_and_cbit_map():
    c1 = QuantumCircuit(2, 2, name="c1")
    c1.x(0)
    c1.measure(0, 1)
    c1.measure(1, 0)
    c2 = QuantumCircuit(3, 3, name="c2")
    c2.x(2)
    c2.measure(0, 2)
    c2.measure(1, 1)
    c2.measure(2, 0)
    packed, layout = circuit_pack.pack_circuits([c1, c2], max_qubits=25)
    assert packed.num_qubits == 5 and packed.num_clbits == 5
    assert layout[0]["name"] == "c1" and layout[0]["qubit_offset"] == 0 and layout[0]["qubit_width"] == 2
    assert layout[0]["clbit_offset"] == 0 and layout[0]["clbit_width"] == 2
    assert layout[1]["name"] == "c2" and layout[1]["qubit_offset"] == 2 and layout[1]["qubit_width"] == 3
    assert layout[1]["clbit_offset"] == 2 and layout[1]["clbit_width"] == 3
    assert layout[0]["local_qubit_to_cbit_map"] == [[0, 1], [1, 0]]
    assert layout[1]["local_qubit_to_cbit_map"] == [[0, 2], [1, 1], [2, 0]]
    assert all(len(entry["manifest_hash"]) == 64 for entry in layout)
    marginals = circuit_pack.unpack_counts({"10110": 7}, layout)
    assert marginals == {"c1": {"10": 7}, "c2": {"101": 7}}
    raw = {"00000": 3, "10110": 4, "11111": 5}
    marginals2 = circuit_pack.unpack_counts(raw, layout)
    for histogram in marginals2.values():
        assert sum(histogram.values()) == 12


def test_pack_terminal_measurement_passes_full_core():
    circuits, manifest = core.make_demo()
    packed, layout = circuit_pack.pack_circuits(circuits, max_qubits=25)
    assert packed.num_qubits == 16
    assert [entry["name"] for entry in layout] == list(manifest["ordered_blocks"])
    assert [entry["qubit_offset"] for entry in layout] == [0, 4, 8, 12]
    for entry in layout:
        assert entry["local_qubit_to_cbit_map"] == [[0, 0], [1, 1], [2, 2], [3, 3]]


def test_pack_validation():
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([])
    single = QuantumCircuit(1, 1)
    single.measure(0, 0)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits(single)
    mid = QuantumCircuit(4, 4)
    mid.measure(0, 0)
    mid.x(3)
    mid.measure(range(1, 4), range(1, 4))
    with pytest.raises(ValueError, match="terminal"):
        circuit_pack.pack_circuits([mid])
    reset = QuantumCircuit(2, 2)
    reset.reset(0)
    reset.measure(range(2), range(2))
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([reset])
    cond = QuantumCircuit(2, 2)
    cond.h(0)
    cond.measure(0, 0)
    with cond.if_test((cond.clbits[0], 1)):
        cond.x(0)
    cond.measure(1, 1)
    with pytest.raises(ValueError):
        circuit_pack.pack_circuits([cond])
    with pytest.raises(ValueError, match="exceeds max_qubits"):
        circuit_pack.pack_circuits([QuantumCircuit(14, 14), QuantumCircuit(15, 15)], max_qubits=25)


def test_unpack_normalization_and_invalid_keys():
    layout = [{"name": "b", "clbit_offset": 0, "clbit_width": 4}]
    marginals = circuit_pack.unpack_counts({"01 10": 5, "0x3": 2, "111": 1}, layout)
    assert marginals == {"b": {"0110": 5, "0011": 2, "0111": 1}}
    assert sum(marginals["b"].values()) == 8
    for bad in ({"0100": -1}, {"0100": 1.5}, {"0100": True}, {"9": 1}, {"010101": 1}, {}):
        with pytest.raises(ValueError):
            circuit_pack.unpack_counts(bad, layout)


# --------------------------------------------------------------------------- receipts
def test_receipt_parser_empty_and_malformed():
    records, issues = receipt.parse_records("")
    assert records == [] and issues == []
    assert receipt.record_status(records) == "No recorded IonQ runs yet"
    records, issues = receipt.parse_records("# comment\n\nRECORD_JSON {this is not json\n")
    assert records == [] and len(issues) == 1
    assert "invalid JSON" in issues[0]["reason"]
    records, issues = receipt.parse_records('{"schema_version": "9.9.9"}\n')
    assert records == [] and issues[0]["reason"].startswith("missing required field")


def test_receipt_valid_synthetic_fixture_test_only():
    record = _synthetic_record()
    assert receipt.validate_record(record) == []
    records, issues = receipt.parse_records("RECORD_JSON " + json.dumps(record, sort_keys=True))
    assert len(records) == 1 and issues == []
    assert receipt.record_status(records) == "Recorded IonQ runs: 1"
    assertion = receipt.analyze_record(records[0], lambda_value=0.02)
    assert len(assertion["results"]) == 4
    assert receipt.effective_model_label(records[0]) == "aria-1"
    assert records[0]["environment"].startswith("pytest (TEST ONLY)")


def test_receipt_rejects_tampering():
    record = _synthetic_record()
    tampered = dict(record)
    tampered["source"] = "local noise approximation"
    assert receipt.validate_record(tampered)
    tampered2 = dict(record)
    tampered2["utc_start"] = "2026-09-01T00:00:00Z"
    assert receipt.validate_record(tampered2)
    tampered3 = dict(record)
    tampered3["shots"] = 999991
    assert receipt.validate_record(tampered3)
    tampered4 = dict(record)
    tampered4["raw_counts"]["0000000000000000"] = -3
    assert receipt.validate_record(tampered4)
    tampered5 = dict(record)
    tampered5["hashes"]["circuit"] = "not-a-hash"
    assert receipt.validate_record(tampered5)


def test_main_before_and_after_records_exist(capsys, monkeypatch):
    circuits, _ = core.make_demo()
    counts_list = _fake_counts(circuits, 128, 300)
    _set_backend(monkeypatch, _BuiltinDouble(counts_list))
    monkeypatch.setattr(main_mod.plt, "show", lambda *a, **k: None)
    monkeypatch.setattr(recorded_ionq, "RECORDED", r"""""")
    main_mod.main(case=0, shots=128, prize="frozen")
    before = capsys.readouterr().out
    assert "No recorded IonQ runs yet" in before
    assert "RECORD_JSON" not in before
    fixture = "RECORD_JSON " + json.dumps(_synthetic_record(shots=128), sort_keys=True)
    monkeypatch.setattr(recorded_ionq, "RECORDED", "# TEST ONLY fixture (not shipped evidence)\n" + fixture + "\n")
    _set_backend(monkeypatch, _BuiltinDouble(counts_list))
    main_mod.main(case=0, shots=128, prize="frozen")
    after = capsys.readouterr().out
    assert "Recorded IonQ runs: 1" in after
    assert "Fixed-prize decision at frozen lambda*=" in after
    assert "Readiness gap: no recorded Qollab IonQ runs yet" not in after


# --------------------------------------------------------------------------- presentation & finite shots
def test_figure_and_report_labels():
    circuits, manifest = core.make_demo()
    shots = 300
    counts_list = _fake_counts(circuits, shots, 700)
    marginals = {name: counts_list[index] for index, name in enumerate(manifest["ordered_blocks"])}
    analysis = core.analyze_counts(marginals, manifest, lambda_value=0.02)
    report = figures.plain_report(
        analysis["results"], source_label="live built-in ideal (fake)", shots=shots,
        lambda_star=0.02, prize_label="frozen", winner_label="optimized_joint", lambda_value=0.02,
        p_bound=0.8535533905932737, product_tail=0.021446609406726218,
        record_status="No recorded IonQ runs yet")
    assert "live built-in ideal (fake)" in report
    assert "shots: 300" in report
    assert "lambda*: 0.02000" in report
    assert "Assumptions:" in report
    assert "95% CI" in report
    assert "Units:" in report
    board = figures.build_trial_board(
        analysis["results"], source_label="live built-in ideal (fake)", shots=shots,
        lambda_star=0.02, prize_label="frozen", winner_label="optimized_joint", lambda_value=0.02,
        record_status="No recorded IonQ runs yet", p_bound=0.8535533905932737,
        product_tail=0.021446609406726218)
    text = figures.figure_text(board)
    assert "SOURCE" in text and "source" in text.lower()
    assert "shots" in text.lower()
    assert "Intervals" in text
    assert "Units" in text
    assert "never zero" in text.lower() or "never promised zero" in text.lower()
    assert "optimized_joint" in text
    import matplotlib.pyplot as plt

    plt.close(board)


def test_finite_shot_zero_ff_upper_bound():
    _, manifest = core.make_demo()
    analysis = core.analyze_counts({name: {"0000": 1024} for name in manifest["ordered_blocks"]},
                                   manifest, lambda_value=0.02)
    entry = analysis["results"][0]
    assert entry["double_failure_upper_if_zero"] == pytest.approx(1 - 0.05 ** (1 / 1024))
    report = figures.plain_report(analysis["results"], source_label="x", shots=1024,
                                  lambda_star=0.02, prize_label="frozen",
                                  winner_label="attained_product", lambda_value=0.02)
    assert "never means zero risk" in report
    assert "95% CI" in report
