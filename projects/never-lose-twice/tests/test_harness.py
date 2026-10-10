import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments import noise, run
from core import make_demo


def test_noise_exact_and_repeatable():
    qc = QuantumCircuit(1, 1); qc.h(0); qc.measure(0, 0)
    ideal = noise.probabilities(qc, ideal=True)
    assert ideal.tolist() == pytest.approx([.5, .5])
    cfg = noise.configuration("aria")
    assert noise.probabilities(qc, cfg).sum() == pytest.approx(1)
    assert noise.histogram(ideal, 50, 12) == noise.histogram(ideal, 50, 12)


def test_local_noise_channel_matches_ideal_statevector_at_zero_rate():
    qc = QuantumCircuit(2, 2); qc.ry(.31, 0); qc.cx(0, 1); qc.measure([0, 1], [0, 1])
    zero = {"one_qubit": 0., "two_qubit": 0., "readout": 0., "scale": 1.}
    assert noise.probabilities(qc, zero) == pytest.approx(noise.probabilities(qc, ideal=True))


def test_quick_guard_and_filename_import(tmp_path):
    with pytest.raises(SystemExit, match="quick-"):
        run.main(["--quick", "--output-dir", str(tmp_path / "ordinary")])
    out = ROOT / "results" / "quick-harness-test"
    subprocess.run([sys.executable, str(ROOT / "experiments" / "run.py"), "--quick",
                    "--draws", "1", "--output-dir", str(out)], cwd=tmp_path,
                   check=True, capture_output=True, text=True)
    assert (out / "quick-n-dev.json").exists()
    assert not (ROOT / "results" / "quick-n-dev.json").exists()
    result = json.loads((out / "quick-n-dev.json").read_text())
    assert result["science_verdict"].startswith("NONE")


def test_fresh_manifest_required_and_validation(tmp_path):
    with pytest.raises(SystemExit, match="requires --independent-manifest"):
        run.main(["--suite", "fresh"])
    path = ROOT / "results" / "quick-bad-manifest-test.json"; path.write_text(json.dumps({"manifests": [{"case_id": 2}]}))
    with pytest.raises(ValueError, match="requires case_id"):
        run._manifest_from_json(path)


def test_analysis_respects_same_shot_budget_and_zero_ff_boundary():
    circuits, manifest = make_demo(0)
    outcome_probs = noise.probabilities(circuits[0], ideal=True)
    hist = noise.histogram(outcome_probs, 20, 99)
    marginal = {name: hist for name in manifest["ordered_blocks"]}
    result = __import__("core").analyze_counts(marginal, manifest)
    assert {x["shots"] for x in result["results"]} == {20}
    assert run.interval(0, 20, confidence=.95, one_sided=True)[1] == pytest.approx(1-.05**(1/20))


def test_configuration_labeling():
    cfg = noise.configuration("forte", .75, readout=.005, source_imbalance=.1)
    assert "approximation" in cfg["origin"] and cfg["readout"] == .005
    with pytest.raises(ValueError): noise.configuration("aria", readout=.7)
