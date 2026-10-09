import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.noise import config, depolarize, ideal_probabilities, readout_probabilities
from experiments.run import binomial_interval, load_independent_manifest, run_quick, validate_args, parser, run_suite, run_g1
from cases import make_demo, analyze_counts
from circuit_pack import digest


def test_quick_is_bounded_and_does_not_overwrite_full_evidence(tmp_path):
    quick = tmp_path / "quick-development"
    result = run_quick(quick)
    assert len(result["records"]) == 2
    assert all(row["draws"] == 10 for row in result["records"])
    assert (quick / "quick-c-evidence.json").is_file()
    assert not (quick / "c-evidence.json").exists()
    args = parser().parse_args(["--quick", "--suite", "development"])
    with pytest.raises(ValueError):
        validate_args(args)


def test_import_by_filename_from_other_cwd():
    proc = subprocess.run([sys.executable, str(ROOT / "experiments" / "run.py"), "--help"],
                          cwd=ROOT.parent, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "--independent-manifest" in proc.stdout


def test_fresh_manifest_missing_and_malformed(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        load_independent_manifest(tmp_path / "absent.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        load_independent_manifest(bad)
    with pytest.raises(ValueError, match="requires --independent-manifest"):
        validate_args(parser().parse_args(["--suite", "fresh"]))


def test_exact_probabilities_and_local_channel_are_deterministic():
    state = np.array([1, 0], dtype=complex)
    rho = np.outer(state, state.conj())
    assert ideal_probabilities(state).tolist() == [1.0, 0.0]
    np.testing.assert_allclose(depolarize(rho, 0), rho)
    np.testing.assert_allclose(readout_probabilities(rho, bias=0), [1, 0])
    assert config("aria")["label"] == "local IonQ-like approximation"


def test_paired_baseline_uses_same_counts():
    circuits, manifest = make_demo(0)
    # Deterministic synthetic counts; baseline and simultaneous witness are run from same marginals.
    marginals = {name: {"0000": 25, "1111": 25} for name in manifest["ordered_blocks"]}
    result = analyze_counts(marginals, manifest)
    assert result["two_color_comparator"]["terms"] == result["simultaneous_witness"]["terms"]


def test_interval_boundaries_and_invalid_inputs():
    lo, hi = binomial_interval(0, 10)
    assert lo == 0 and 0 < hi < 1
    lo, hi = binomial_interval(10, 10)
    assert 0 < lo < 1 and hi == 1
    with pytest.raises(ValueError):
        binomial_interval(11, 10)


def test_full_runner_tiny_resume_and_results(tmp_path):
    # Exercise one development case through the suite internals with tiny draw count.
    import experiments.run as harness
    original = harness._case_specs
    try:
        harness._case_specs = lambda suite, manifest_path=None: original("development")[:1]
        result = run_suite("development", draws=2, shots=20, seed=17, output_dir=tmp_path)
        assert result["summary"]["case_count"] == 1
        assert (tmp_path / "development.json").is_file()
        assert (tmp_path / "figures" / "development.png").is_file()
        resumed = run_suite("development", draws=2, shots=20, seed=17, output_dir=tmp_path, resume=True)
        assert resumed["summary"]["complete"]
    finally:
        harness._case_specs = original


def test_gate_small_result_fails_inadequate_coverage_and_writes(tmp_path):
    gate = run_g1({"cases": []}, tmp_path)
    assert gate["overall"] is False
    assert (tmp_path / "g1.json").is_file()


def test_g1_adds_real_200_shot_aria_projection_rows(tmp_path, monkeypatch):
    import experiments.run as harness
    original = harness._case_specs
    monkeypatch.setattr(harness, "_case_specs", lambda suite, manifest_path=None: original("development")[:1])
    result = run_suite("development", draws=5, shots=50, seed=23, output_dir=tmp_path,
                       g1_cloud_projection=True)
    projection = [x for x in result["cases"][0]["noise_results"]
                  if x.get("purpose") == "g1_cloud_projection"]
    assert len(projection) == 1
    assert projection[0]["noise"]["name"] == "aria@1"
    assert projection[0]["shots_per_block"] == 200
    assert projection[0]["draws"] == 5
    gate = run_g1(result, tmp_path)
    assert gate["metrics"]["cloud_projection_mean"] is not None


def test_measured_probabilities_match_main_blocks():
    from qiskit.quantum_info import Statevector
    from circuit_pack import demo_blocks
    from experiments.run import _probabilities
    # All frames and both color bases must match the actual demo circuits.
    for case in range(4):
        circuits, manifest = make_demo(case)
        for block in demo_blocks(circuits, manifest):
            expected = Statevector.from_instruction(block.remove_final_measurements(inplace=False)).probabilities()
            np.testing.assert_allclose(_probabilities(case, block.name), expected, atol=1e-12)
        from experiments.run import _control_probabilities
        np.testing.assert_allclose(_control_probabilities('graph', case, 0., 'aria', 0., 'target_A'),
                                   _probabilities(case, 'target_A'), atol=1e-12)


@pytest.fixture
def ideal_main(monkeypatch):
    import main as demo
    # Avoid saved receipts and presentation while exercising the real main ideal job.
    monkeypatch.setattr(demo, 'load_records', lambda: ([], []))
    monkeypatch.setattr(demo, 'present', lambda *a, **k: None)
    monkeypatch.delattr(demo, 'backend', raising=False)
    return demo.main(case=0, shots=100)


def test_ideal_graph_power_and_product_control_200_draws(monkeypatch, ideal_main):
    import experiments.run as harness
    monkeypatch.setattr(harness, 'NOISE_SCALES', ())
    spec = harness._case_specs('development')[0]
    ideal = harness._draw_record(spec, draws=200, shots=100, base_seed=9137)[0]
    graph = ideal['controls']['graph']['summary']
    assert graph['certification_rate'] >= .99
    reference = ideal_main['analysis']['simultaneous_witness']['F_lower']
    assert abs(graph['mean_F_lower'] - reference) < .05
    product = ideal['controls']['product']
    assert product['certificates'] == product['false_certificates'] == 0
    assert product['summary']['certification_rate'] == 0.
    assert product['inconclusive'] == 200


def test_harness_main_identical_counts_identical_parities(monkeypatch):
    import main as demo
    from experiments.run import _probabilities, _sample_marginals
    _, manifest = make_demo(0)
    probabilities = {kind: {name: _probabilities(0, name, kind)
                            for name in manifest['ordered_blocks']}
                     for kind in ('graph', 'product')}
    marginals = _sample_marginals(probabilities, manifest, 'graph', 100, np.random.default_rng(819))
    harness_analysis = analyze_counts(marginals, manifest)

    class CachedResult:
        def get_counts(self):
            return [marginals[name] for name in manifest['ordered_blocks']]

    class CachedJob:
        def result(self):
            return CachedResult()

    class CachedBackend:
        name = 'fixed-ideal-counts'
        def run(self, blocks, shots):
            assert [b.name for b in blocks] == manifest['ordered_blocks']
            assert shots == 100
            return CachedJob()

    monkeypatch.setattr(demo, 'backend', CachedBackend(), raising=False)
    monkeypatch.setattr(demo, 'load_records', lambda: ([], []))
    monkeypatch.setattr(demo, 'present', lambda *a, **k: None)
    result = demo.main(case=0, shots=100)
    assert result['marginals'] == marginals
    assert result['analysis']['blocks'] == harness_analysis['blocks']
    assert result['analysis']['simultaneous_witness'] == harness_analysis['simultaneous_witness']


def test_default_output_paths_have_no_doubled_results():
    from experiments.run import _output_paths
    assert _output_paths(parser().parse_args([]).output_dir) == (ROOT / 'results', ROOT / 'figures')
    assert _output_paths('results') == (ROOT / 'results', ROOT / 'figures')
