"""Tiny loader-boundary tests; no full evaluation or bootstrap runs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from experiments import run as harness
from receipt import digest


ROOT = Path(__file__).resolve().parents[1]


def manifest(suite='frozen'):
    return json.loads((ROOT/'review'/'manifests'/(suite+'.json')).read_text(encoding='utf-8'))


def seal(value):
    value['instances_sha256'] = digest(value['configuration']['instances'])
    value['configuration_sha256'] = digest(value['configuration'])
    return value


def arguments(path, output, suite='frozen', validate=True):
    return argparse.Namespace(suite=suite, independent_manifest=str(path),
        output_dir=str(output), quick=False, gate=None, resume=False,
        draws=4000, validate_only=validate)


@pytest.mark.parametrize('suite', ['frozen', 'fresh'])
def test_verifier_owned_suites_accepted(suite):
    value = manifest(suite)
    assert harness.validate_independent_manifest(value, suite) is value['configuration']


def test_suite_mismatch():
    with pytest.raises(ValueError, match='suite mismatch'):
        harness.validate_independent_manifest(manifest(), 'fresh')


@pytest.mark.parametrize('defect', [
    'owner', 'time', 'generator', 'id', 'seed', 'id_mapping', 'count',
    'development', 'legacy_w', 'legacy_n', 'frozen_overlap', 'frame', 'angle',
    'config_digest', 'instance_digest', 'channel', 'implementation', 'grid', 'unplanned_seed'])
def test_schema_rejects(defect):
    value = manifest('fresh')
    cfg = value['configuration']
    specs = cfg['instances']['W']
    ids = value['instance_ids']['W']
    if defect == 'owner': value['owner'] = 'builder'
    elif defect == 'time': value['generated_utc'] = '2026-10-10T03:00:00'
    elif defect == 'generator': value['generator'] = {}
    elif defect == 'id': ids[1]['id'] = ids[0]['id']
    elif defect == 'seed': specs[1]['seed'] = specs[0]['seed']
    elif defect == 'id_mapping': ids[0]['seed'] += 100
    elif defect == 'count': specs.pop()
    elif defect in ('development', 'legacy_w', 'legacy_n', 'frozen_overlap'):
        specs[0]['seed'] = {'development': 2026104500, 'legacy_w': 2026100900,
                            'legacy_n': 2026102900, 'frozen_overlap': 2026104000}[defect]
        ids[0]['seed'] = specs[0]['seed']
    elif defect == 'frame': specs[0]['frame'][0][0][0] = 4.
    elif defect == 'angle': cfg['instances']['N'][0]['alpha'] = np.pi/2
    elif defect == 'channel': cfg['fixed_prize'] = .03
    elif defect == 'implementation': cfg['implementation_sha256']['noise_channel.py'] = '0'*64
    elif defect == 'grid': cfg['grid'] = [0., 2.]
    elif defect == 'unplanned_seed':
        specs[0]['seed'] = 123456
        ids[0]['seed'] = 123456
    seal(value)
    if defect == 'config_digest': value['configuration_sha256'] = '0'*64
    if defect == 'instance_digest': value['instances_sha256'] = '0'*64
    with pytest.raises(ValueError):
        harness.validate_independent_manifest(value, 'fresh')


def test_authoritative_specs_are_not_regenerated(monkeypatch):
    value = manifest()
    value['configuration']['instances']['W'][0]['frame'] = [
        [[1., 0.], [0., 0.]], [[0., 0.], [1., 0.]]]
    value['configuration']['instances']['N'][0]['alpha'] = float(np.pi/4)
    seal(value)
    def forbidden(*args, **kwargs):
        raise AssertionError('builder instance generator called')
    monkeypatch.setattr(harness.w, 'make_instance', forbidden)
    monkeypatch.setattr(harness.n, 'make_instance', forbidden)
    assert harness.validate_independent_manifest(value, 'frozen')['instances'] == value['configuration']['instances']


def test_missing_explicit_path_never_created(tmp_path):
    missing = tmp_path/'missing.json'
    with pytest.raises(FileNotFoundError):
        harness.run(arguments(missing, tmp_path/'output'))
    assert not missing.exists()
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('suite', ['frozen', 'fresh'])
def test_full_evaluation_requires_verifier_file(tmp_path, suite):
    args = arguments('unused', tmp_path/'output', suite, validate=False)
    args.independent_manifest = None
    with pytest.raises(ValueError, match='requires a verifier-owned'):
        harness.run(args)


@pytest.mark.parametrize('suite', ['frozen', 'fresh'])
def test_bounded_smoke_keeps_manifest_and_original_sampling_indices(tmp_path, monkeypatch, suite):
    path = ROOT/'review'/'manifests'/(suite+'.json')
    raw = path.read_bytes()
    value = manifest(suite)
    consumed = []
    def evaluate(game, spec, cfg, model, mi, checkpoint, resume):
        assert cfg['grid'] == [0., 1., 2.]
        assert cfg['_grid_indices'] == [0, 40, 80]
        assert spec in value['configuration']['instances'][game][:2]
        consumed.append((game, spec['seed'], model))
        return {'points': [], 'specification': copy.deepcopy(spec)}
    monkeypatch.setattr(harness, 'evaluate_case', evaluate)
    def forbidden(*args, **kwargs):
        raise AssertionError('smoke attempted inference/figures/controls')
    for name in ('calibration_sensitivity', 'diagnostic_controls', 'plot_results', 'plot_cloud_comparison'):
        monkeypatch.setattr(harness, name, forbidden)
    monkeypatch.setattr(harness.crossover, 'analyze', forbidden)
    monkeypatch.setattr(harness.crossover, 'deterministic', forbidden)
    recorded = ROOT/'recorded_local.py'
    before = recorded.read_bytes() if recorded.exists() else None
    result = harness.run(arguments(path, tmp_path, suite))
    assert len(consumed) == 4*len(harness.channel.MODELS)
    assert result['manifest'] == value
    assert result['manifest']['configuration']['grid'] == [k/40 for k in range(81)]
    assert result['consumed_manifest_sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['gate']['decision'] == 'SMOKE_ONLY'
    assert result['analysis'] == {}
    assert path.read_bytes() == raw
    assert (recorded.read_bytes() if recorded.exists() else None) == before
    assert not (tmp_path/(suite+'.json')).exists()


def test_full_manifest_validated_before_smoke(tmp_path, monkeypatch):
    value = manifest()
    value['configuration']['instances']['W'][23]['frame'][0][0][0] = 8.
    path = tmp_path/'invalid.json'
    path.write_text(json.dumps(seal(value)), encoding='utf-8')
    def forbidden(*args, **kwargs):
        raise AssertionError('evaluation started before complete validation')
    monkeypatch.setattr(harness, 'evaluate_case', forbidden)
    with pytest.raises(ValueError, match='frame'):
        harness.run(arguments(path, tmp_path/'output'))


def test_implementation_compatibility_is_loader_only():
    value = manifest()
    assert value['configuration']['implementation_sha256']['experiments/run.py'] == harness.PRE_REPAIR_LOADER_SHA256
    value['configuration']['implementation_sha256']['experiments/run.py'] = '0'*64
    seal(value)
    with pytest.raises(ValueError, match='implementation mismatch'):
        harness.validate_independent_manifest(value, 'frozen')


@pytest.mark.parametrize('suite', ['frozen', 'fresh'])
def test_full_loader_acceptance_stops_before_numerics(tmp_path, monkeypatch, suite):
    value = manifest(suite)
    def stop(game, spec, cfg, *args):
        assert cfg['grid'] == [k/40 for k in range(81)]
        assert cfg['instances'] == value['configuration']['instances']
        assert spec == value['configuration']['instances']['W'][0]
        raise RuntimeError('loader accepted; stop before evaluation')
    monkeypatch.setattr(harness, 'evaluate_case', stop)
    path = ROOT/'review'/'manifests'/(suite+'.json')
    with pytest.raises(RuntimeError, match='loader accepted'):
        harness.run(arguments(path, tmp_path, suite, validate=False))


def test_smoke_sampling_preserves_original_grid_streams(tmp_path, monkeypatch):
    value = manifest()
    cfg = dict(value['configuration'], _hash=value['configuration_sha256'],
               grid=[0., 1., 2.], _grid_indices=[0, 40, 80])
    seen = []
    original = harness.sampling_seed
    def sample(*args):
        seen.append(args[4])
        return original(*args)
    monkeypatch.setattr(harness, 'sampling_seed', sample)
    monkeypatch.setattr(harness, 'atomic_json', lambda *args: None)
    case = harness.evaluate_case('W', cfg['instances']['W'][0], cfg, 'aria-1',
                                 0, tmp_path/'case.json')
    assert set(seen) == {0, 40, 80}
    assert [p['scale'] for p in case['points']] == [0., 1., 2.]
    for point, index in zip(case['points'], (0, 40, 80)):
        assert point['sampling_seeds'][0] == original(cfg, 'W', cfg['instances']['W'][0]['seed'], 0, index, 0)
