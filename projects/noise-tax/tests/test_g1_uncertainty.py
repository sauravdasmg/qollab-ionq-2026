"""G1 reporting: deterministic W, calibrated edges, N precision, cloud shots."""
import numpy as np
import pytest
import crossover
import noise_channel as channel
import whispers_core as w
import recorded_ionq
from recorded_parser import summarize_record, binomial_interval
from experiments.run import build_manifest, calibration_sensitivity


def test_w_frame_invariance_and_reporting():
    grid = [0., 1., 2.]
    curves = []
    for seed in (2026104500, 2026104501):
        circuits, manifest = w.make_demo(w.make_instance(seed))
        compiled = [channel.compile_circuit(c) for c in circuits]
        curves.append([w.analyze_probabilities(
            [channel.probabilities(c, channel.configuration(scale=s)) for c in compiled],
            manifest)['advantage'] for s in grid])
    result = crossover.deterministic(grid, curves)
    assert result['reporting'] == 'DETERMINISTIC'
    assert result['max_frame_curve_difference'] < 1e-12
    assert result['point']['status'] == 'resolved'
    assert result['inversion']['numerical_grid_bracket'] == [1., 2.]
    for name in ('confidence', 'ci_width', 'draws', 'lower_band', 'bootstrap_status_counts'):
        assert name not in result
    assert 'confidence_interval' not in result['inversion']
    with pytest.raises(ValueError, match='invariance'):
        crossover.deterministic(grid, [curves[0], np.array(curves[0])+.001])


@pytest.mark.parametrize('model', channel.MODELS)
def test_calibration_sensitivity_recomputes_edge_curves(model):
    spec = w.make_instance(2026104500)
    grid = [0., 1., 2.]
    result = calibration_sensitivity(spec, grid, model)
    fitted = channel.configuration(model)
    assert result['uncertainty_source'] == 'CALIBRATION SENSITIVITY'
    assert result['status'] == 'resolved'
    assert result['s_star_range'][0] < result['s_star_range'][1]
    circuits, manifest = w.make_demo(spec)
    compiled = [channel.compile_circuit(c, model) for c in circuits]
    for edge, shift in zip(result['edges'], (-.001, .001)):
        assert edge['r_2q'] == fitted['r_2q']+shift
        assert edge['r_1q'] == fitted['r_1q']
        probs = [channel.probabilities(c, channel.configuration(model, 1., calibration_shift=shift))
                 for c in compiled]
        assert edge['mean_advantage'][1] == pytest.approx(w.analyze_probabilities(probs, manifest)['advantage'])
    with pytest.raises(ValueError):
        channel.configuration(model, calibration_shift=.002)


def test_g1_fine_grid_and_unchanged_seeds():
    cfg = build_manifest('development', gate='g1')['configuration']
    assert cfg['grid'] == [k/40 for k in range(81)]
    assert [s['seed'] for s in cfg['instances']['W']] == list(range(2026104500, 2026104524))
    assert [s['seed'] for s in cfg['instances']['N']] == list(range(2026104600, 2026104624))
    assert cfg['fixed_prize'] == .02


def test_n_keeps_bootstrap_and_precision_failure():
    grid = np.arange(81)/40
    result = crossover.analyze(grid, [.5-grid, 1.5-grid], draws=40)
    assert result['inversion']['confidence_interval'] is not None
    assert result['ci_width'] > .30
    assert not result['precision_target_met']
    assert result['bootstrap_status_counts']


def test_cloud_binomial_intervals_cover_each_recorded_point():
    assert binomial_interval(0, 10)[0] == 0.
    assert binomial_interval(10, 10)[1] == 1.
    records, _ = recorded_ionq.parse_records()
    for record in records:
        for anchor in summarize_record(record):
            uncertainty = anchor['cloud_sampling']
            assert uncertainty['uncertainty_source'] == 'CLOUD SAMPLING'
            assert uncertainty['advantage_interval'][0] <= anchor['advantage'] <= uncertainty['advantage_interval'][1]
            assert len(uncertainty['components']) == (3 if anchor['game'] == 'W' else 8)
            for row in uncertainty['components']:
                assert row['binomial_interval'] == binomial_interval(row['count'], row['shots'])
