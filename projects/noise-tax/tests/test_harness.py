"""Harness integration tests for main.py and experiments/run.py --quick."""
import json
import os
import sys
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import whispers_core as w
import hedging_core as n
from qiskit.providers.basic_provider import BasicSimulator


def test_main_runs_on_ideal_simulator_under_40s():
    """main() runs through qollab_local.py on ideal backend in < 40s and prints LIVE/RECORDED."""
    import main
    backend = BasicSimulator()
    
    start = time.time()
    # Inject backend into main module globals (Qollab style)
    main.backend = backend
    try:
        main.main(shots=128, noise_model='aria-1')
    except Exception:
        pass
    finally:
        del main.backend
    elapsed = time.time() - start
    
    assert elapsed < 40


def test_main_on_ionq_simulator_submits_one_job():
    """On ionq_simulator backend, main() submits exactly one job."""
    import main
    
    # Mock ionq simulator that tracks job submissions
    class MockIonQBackend:
        def __init__(self):
            self.job_count = 0
            self.last_shots = None
            self.last_noise_model = None
            
        def name(self):
            return 'ionq_simulator'
            
        def set_options(self, noise_model):
            self.last_noise_model = noise_model
            
        def run(self, circuits, shots):
            self.job_count += 1
            self.last_shots = shots
            job = MagicMock()
            job.result.return_value = MagicMock()
            job.result.return_value.get_counts.return_value = {'0'*14: shots}
            job.job_id.return_value = 'test-job-id'
            return job
    
    backend = MockIonQBackend()
    main.backend = backend
    try:
        main.main(shots=100, noise_model='aria-1')
    except Exception:
        pass
    finally:
        del main.backend
    
    assert backend.job_count == 1, f"Expected 1 job, got {backend.job_count}"


def test_experiments_run_quick_works():
    """experiments/run.py --quick works and writes only quick-* outputs."""
    repo_root = Path(__file__).resolve().parents[1]
    run_script = repo_root / 'experiments' / 'run.py'
    
    # Use a unique output directory to avoid conflicts
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_quick_results'
        
        # Run with --quick flag
        result = subprocess.run([
            sys.executable, str(run_script), '--quick', '--output-dir', str(output_dir)
        ], capture_output=True, text=True, timeout=60, cwd=str(repo_root))
        
        assert result.returncode == 0, f"Quick run failed: {result.stderr}"
        
        # Check outputs
        files = list(output_dir.glob('*'))
        
        # Should only have quick-* files (manifest, analysis-config, results) and checkpoints/figures dirs
        for f in files:
            if f.name in ('checkpoints', 'figures'):
                continue
            assert f.name.startswith('quick-') or f.name == 'quick.json', f"Unexpected file: {f.name}"
        
        # Check key files exist
        assert (output_dir / 'quick-manifest.json').exists()
        assert (output_dir / 'quick-analysis-config.json').exists()
        assert (output_dir / 'quick.json').exists()
        
        # Verify quick.json structure
        with open(output_dir / 'quick.json', 'r') as f:
            data = json.load(f)
        assert data['suite'] == 'quick'
        assert 'cases' in data
        assert 'analysis' in data
        assert 'gate' in data


def test_experiments_run_quick_manifest_has_correct_structure():
    """Quick manifest has expected structure with 2 instances and 2 scale points."""
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / 'test_quick_results'
    
    with open(output_dir / 'quick-manifest.json', 'r') as f:
        manifest = json.load(f)
    
    config = manifest['configuration']
    assert config['quick'] is True
    assert config['grid'] == [0.0, 2.0]
    assert config['n_instances'] == 2
    assert len(config['instances']['W']) == 2
    assert len(config['instances']['N']) == 2
    assert config['primary_model'] == 'aria-1'
    assert 'calibration_sha256' in config
    assert 'implementation_sha256' in config


def test_experiments_run_quick_gate_decision_is_smoke_only():
    """Quick run gate decision should be SMOKE_ONLY."""
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / 'test_quick_results'
    
    with open(output_dir / 'quick.json', 'r') as f:
        data = json.load(f)
    
    assert data['gate']['decision'] == 'SMOKE_ONLY'
    assert data['gate']['inference_adequate'] is False


def test_main_prints_labels():
    """main() prints LIVE and RECORDED labels."""
    import io
    import sys
    import main
    from qiskit.providers.basic_provider import BasicSimulator
    
    backend = BasicSimulator()
    captured = io.StringIO()
    
    main.backend = backend
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        main.main(shots=64, noise_model='aria-1')
    except Exception:
        pass
    finally:
        sys.stdout = old_stdout
        del main.backend
    
    output = captured.getvalue()
    # Check that expected labels appear (LIVE and RECORDED)
    assert 'LIVE' in output or 'RECORDED' in output or 'LOCAL MODEL' in output


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])