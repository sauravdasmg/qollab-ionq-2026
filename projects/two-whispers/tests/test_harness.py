import json
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from experiments import noise
from experiments.run import gate_decisions, paired_bootstrap, parser, wilson


def test_noise_channels_and_exact_statevector_crosscheck():
    zero = np.array([1, 0], complex)
    rho = np.outer(zero, zero.conj())
    assert np.allclose(noise.depolarize(rho, 0), rho)
    assert np.allclose(noise.depolarize(rho, 1), np.diag([1/3, 2/3]))
    probs = noise.probabilities_from_statevector(zero, 1)
    assert probs == {'0': 1.0, '1': 0.0}
    assert noise.readout_probabilities(probs, .1) == pytest.approx({'0': .9, '1': .1})


def test_noise_rejects_large_or_invalid_state():
    with pytest.raises(ValueError):
        noise.depolarize(np.eye(16)/16, .1)
    with pytest.raises(ValueError):
        noise.effective_config('aria', 99)


def test_statistics_boundary_and_small_sample_behavior():
    assert wilson(10, 10)[0] < 1
    with pytest.raises(ValueError):
        wilson(2, 1)
    result = gate_decisions({'seq_minus_joint': [.02, .021, .022],
                             'relative_textbook_margin': [.01, .011, .012]})
    assert result['h1_pass'] and result['h2_pass']
    assert not gate_decisions({'seq_minus_joint': [0, 0, 0],
                               'relative_textbook_margin': [0, 0, 0]})['gate_pass']
    assert paired_bootstrap([.1, .2, .3], seed=1, replicates=100) == paired_bootstrap([.1, .2, .3], seed=1, replicates=100)


def test_cli_help_and_fresh_argument_validation_from_filename(tmp_path):
    help_run = subprocess.run([sys.executable, os.path.join(ROOT, 'experiments', 'run.py'), '--help'],
                              cwd=tmp_path, text=True, capture_output=True, check=True)
    assert '--independent-manifest' in help_run.stdout
    bad = subprocess.run([sys.executable, os.path.join(ROOT, 'experiments', 'run.py'), '--suite', 'fresh'],
                         cwd=tmp_path, text=True, capture_output=True)
    assert bad.returncode != 0 and '--independent-manifest' in bad.stderr


def test_quick_creates_only_quick_named_result(tmp_path):
    out = tmp_path / 'quick-output'
    cmd = [sys.executable, os.path.join(ROOT, 'experiments', 'run.py'), '--quick',
           '--output-dir', str(out), '--draws', '2']
    run = subprocess.run(cmd, cwd=tmp_path, text=True, capture_output=True, timeout=40)
    assert run.returncode == 0, run.stderr
    saved = list(out.glob('quick-*.json'))
    assert len(saved) == 1
    data = json.loads(saved[0].read_text(encoding='utf-8'))
    assert len(data['rows']) == 4
    assert all(row['draws_per_circuit'] <= 2 for row in data['rows'])
    assert data['science_verdict'] is None
    assert not list(out.glob('development.json'))


def test_quick_rejects_conflicting_modes():
    from experiments.run import main
    with pytest.raises(SystemExit):
        main(['--quick', '--suite', 'fresh'])
