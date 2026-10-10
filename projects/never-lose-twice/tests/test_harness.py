"""Tiny deterministic checks only. Never submits jobs or runs a full campaign."""
import copy
import json
import math
import runpy
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments import noise, run
from core import make_demo
from product_bounds import acceptance_functional
from circuit_pack import pack_circuits


@pytest.fixture
def tmp_path():
    # Windows sandbox cannot traverse the global pytest temp tree. Keep these
    # disposable fixtures inside this worker's writable results directory.
    root = (ROOT/"results").resolve()
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="quick-n-tests-", dir=root) as folder:
        path = Path(folder).resolve()
        assert path.parent == root
        yield path


def test_filename_import_and_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(ROOT)])
    module = runpy.run_path(str(ROOT/"experiments/run.py"), run_name="harness_import_test")
    assert str(ROOT) in sys.path
    with pytest.raises(SystemExit) as exc:
        module["main"](["--help"])
    assert exc.value.code == 0
    assert "orchestrator-only" in capsys.readouterr().out


def test_noise_exact_repeatable_and_zero_rate():
    qc = QuantumCircuit(2, 2)
    qc.ry(.31, 0); qc.cx(0, 1); qc.rz(.27, 1); qc.measure([0, 1], [0, 1])
    reference = Statevector.from_instruction(qc.remove_final_measurements(inplace=False)).probabilities()
    assert noise.probabilities(qc, ideal=True) == pytest.approx(reference)
    assert noise.probabilities(qc, noise.configuration(scale=0)) == pytest.approx(reference)
    p = noise.probabilities(qc, noise.configuration())
    assert np.min(p) >= 0 and p.sum() == pytest.approx(1)
    assert noise.histogram(p, 25, 99) == noise.histogram(p, 25, 99)


def test_pauli_probability_and_measurement_order():
    qc = QuantumCircuit(1, 1); qc.x(0); qc.measure(0, 0)
    cfg = dict(noise.configuration(), one_qubit=.3)
    assert noise.probabilities(qc, cfg) == pytest.approx([.2, .8])
    swapped = QuantumCircuit(2, 2); swapped.x(0); swapped.measure([0, 1], [1, 0])
    assert noise.probabilities(swapped, ideal=True) == pytest.approx([0, 0, 1, 0])
    with pytest.raises(ValueError, match="four"):
        noise.probabilities(QuantumCircuit(5))
    bad = QuantumCircuit(1, 1); bad.measure(0, 0); bad.x(0)
    with pytest.raises(ValueError, match="terminal"):
        noise.probabilities(bad)


def test_noisy_tester_matches_shared_product_probability():
    circuits, manifest = make_demo(1)
    for cfg in (noise.configuration(scale=0), noise.configuration(readout=.005)):
        rho, effect = noise.product_tester(circuits[0], cfg)
        w = acceptance_functional(rho, effect)
        ident = np.array([1, 0, 0, 1])
        p = float(np.trace(w@np.outer(ident, ident)).real)
        probs = {n: noise.probabilities(c, cfg) for n, c in zip(manifest["ordered_blocks"], circuits)}
        result = run.metrics(probs, manifest)["attained_product"]
        assert result["f"] == pytest.approx((1-p)**2, abs=1e-11)
        assert result["m"] == pytest.approx(2*p, abs=1e-11)
        assert np.trace(rho).real == pytest.approx(1)
        assert np.linalg.eigvalsh(effect).min() >= -1e-12


def test_one_tiny_noisy_certificate_bounds_attained_product():
    # One anchor SDP is a focused math check, never a frozen/fresh campaign.
    case = run.cases("quick", 3)[0]
    regime = {"id": "aria-s1", "config": noise.configuration()}
    circuits, manifest = run.build_case(case, {}, regime)
    cert = run.certify(circuits, manifest, regime)
    assert cert["status"] == "CERTIFIED"
    assert cert["certificate"]["gap"] <= 1e-4
    p = noise.probabilities(circuits[0], regime["config"])
    reduced = dict(manifest, ordered_blocks=["attained_product"], decoding_maps=manifest["decoding_maps"][:1])
    attained = run.metrics({"attained_product": p}, reduced)["attained_product"]
    assert cert["bound"]["double_failure_lower_bound"] <= attained["f"]+1e-10


def test_configuration_labels_hash_validation_and_source_shift():
    cfg = noise.configuration("forte", .75, readout=.005, source_imbalance=.01)
    assert "approximation" in cfg["origin"] and cfg["readout"] == .005
    assert cfg["hash"] == noise.digest({k: v for k, v in cfg.items() if k != "hash"})
    for kw in ({"readout": .7}, {"scale": float("nan")}, {"two_factor": -1}):
        with pytest.raises(ValueError):
            noise.configuration(**kw)
    case = run.cases("quick", 1)[0]
    cs, m = run.build_case(case, {}, {"id": "sensitivity", "config": cfg})
    assert m["parameters"]["alpha"] == pytest.approx(math.pi/4+.01)
    with pytest.raises(ValueError, match="apply source"):
        noise.probabilities(cs[0], cfg)


@pytest.mark.parametrize("argv", [
    ["--quick", "--suite", "development"], ["--quick", "--resume"],
    ["--quick", "--draws", "3"], ["--quick", "--replicates", "200"],
    ["--suite", "development", "--draws", "1"], ["--quick", "--gate", "g1"],
    ["--suite", "frozen"], ["--suite", "fresh"], ["--quick", "--seed", "-1"],
])
def test_quick_and_full_bounds(argv):
    with pytest.raises(ValueError):
        run.validate_args(run.parser().parse_args(argv))


def test_quick_output_no_full_overwrite(tmp_path, monkeypatch):
    sentinel = tmp_path/"frozen.json"
    sentinel.write_text("sentinel")
    def forbidden(*args, **kwargs):
        raise AssertionError("quick must never enter full search/certificate/power")
    monkeypatch.setattr(run, "development_search", forbidden)
    monkeypatch.setattr(run, "solve_product_tester", forbidden)
    monkeypatch.setattr(run, "projected_power", forbidden)
    result = run.main(["--quick", "--draws", "1", "--output-dir", str(tmp_path)])
    assert result.name.startswith("quick-n-")
    assert sentinel.read_text() == "sentinel"
    doc = json.loads(result.read_text())
    assert doc["science_verdict"].startswith("NONE")
    assert len(doc["instances"]) == 6 and doc["configuration"]["replicates"] == 1
    assert doc["configuration"]["shots"] == 128
    assert doc["selection"] is None and doc["gate_decision"] is None
    for e in doc["instances"]:
        assert {sum(h.values()) for h in e["counts"][0].values()} == {128}
        assert e["resources"]["max_simulated_qubits"] == 4


def fresh_manifest():
    # Schema fixture only; no fresh circuits or simulations executed in tests.
    return {"author": "unit-test fixture, not evidence", "independent": True, "selection_hash": "test",
            "manifests": [dict(instance_id=f"fresh-{i}", generation_seed=s, sampling_seed=8000+i,
                               **run.generated(s)) for i, s in enumerate(run.GENERATION["fresh"])]}


def test_fresh_validation(tmp_path):
    with pytest.raises(ValueError, match="cannot load"):
        run._manifest_from_json(tmp_path/"missing.json")
    path = tmp_path/"fresh.json"
    valid = fresh_manifest()
    path.write_text(json.dumps(valid))
    assert len(run._manifest_from_json(path, "test")["manifests"]) == 24
    for change in (lambda o: o.update(independent=False),
                   lambda o: o["manifests"][0].update(alpha=0),
                   lambda o: o["manifests"][1].update(sampling_seed=8000),
                   lambda o: o.update(selection_hash="other"),
                   lambda o: o["manifests"][0].update(generation_seed=2026103000)):
        bad = copy.deepcopy(valid); change(bad); path.write_text(json.dumps(bad))
        with pytest.raises(ValueError):
            run._manifest_from_json(path, "test")


def test_frozen_cases_use_distinct_seed_range_and_core_interface():
    rows = run.cases("frozen", 9)
    assert len(rows) == 24 and {r["generation_seed"] for r in rows} == set(run.GENERATION["frozen"])
    assert not set(run.GENERATION["frozen"]) & set(run.GENERATION["development"])
    # One circuit construction, no full sweep.
    circuits, manifest = run.build_case(rows[-1], {}, {"id": "ideal", "config": None})
    assert manifest["seed"] == 2026103023
    assert manifest["case_id"] == 0 and len(circuits) == 4


def test_intervals_and_exact_zero_boundary():
    assert run.interval(0, 20, .975, True)[1] == pytest.approx(1-.025**(1/20))
    assert run.interval(20, 20, .975, True)[1] == 1
    assert run.interval(0, 20)[0] == 0
    for k, n, confidence in ((0, 0, .95), (21, 20, .95), (.5, 20, .95), (1, 20, 1)):
        with pytest.raises(ValueError):
            run.interval(k, n, confidence)


def test_packed_resampling_preserves_arm_covariance():
    a = QuantumCircuit(1, 1, name="a"); a.measure(0, 0)
    b = QuantumCircuit(1, 1, name="b"); b.measure(0, 0)
    _, layout = pack_circuits([a, b])
    raw, marginals = run.resample_packed({"00": 5, "11": 5}, layout, 123)
    assert set(raw) <= {"00", "11"}
    assert marginals["a"] == marginals["b"] and sum(raw.values()) == 10


def test_missing_gate_evidence_is_blocked():
    result = run.gate_decision({"H1": .99, "H2": .99}, None, "g1", "selection")
    assert result["status"] == "BLOCKED"
    assert "N02" in result["reasons"][0]
    result = run.gate_decision({"H1": .79, "H2": .99}, None, "g2", "selection")
    assert any("below .8" in r for r in result["reasons"])
    assert any("calibration power" in r for r in result["reasons"])


def test_tiny_inference_is_deterministic_and_rejects_missing_certificate():
    case = run.cases("quick", 19)[0]
    entry = run.evaluate(case, {}, {"id": "ideal", "config": None}, 20, 1, quick=True)
    noisy = copy.deepcopy(entry); noisy["regime"] = "aria-s1"
    # Identical ideal test fixture on both sides: H2 reversal cannot pass.
    a = run.inference([entry, noisy], draws=8, seed=3)
    assert a == run.inference([entry, noisy], draws=8, seed=3)
    assert not a["H2"] and a["n_instances"] == 1
    noisy["certificate"] = {"status": "FAILED"}
    with pytest.raises(ValueError, match="certificates"):
        run.inference([entry, noisy], draws=8)


def test_resume_rejects_changed_inputs_before_evaluation(tmp_path, monkeypatch):
    checkpoint = tmp_path/"development-checkpoint.json"
    checkpoint.write_text(json.dumps({"configuration_hash": "wrong", "instances": []}))
    monkeypatch.setattr(run, "development_search", lambda *a: pytest.fail("must reject before search"))
    with pytest.raises(SystemExit, match="mismatch"):
        run.main(["--suite", "development", "--resume", "--output-dir", str(tmp_path)])
    with pytest.raises(SystemExit, match="existing full evidence"):
        run.main(["--suite", "development", "--output-dir", str(tmp_path)])
