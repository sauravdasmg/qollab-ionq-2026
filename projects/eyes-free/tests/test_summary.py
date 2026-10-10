import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_summary_matches_sources_and_size():
    subprocess.run([sys.executable, str(ROOT / "experiments" / "make_summary.py")], check=True)
    path = ROOT / "evidence_summary.json"
    assert path.stat().st_size < int(1.5 * 1024 * 1024)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "LOCAL MODEL" in data["evidence_label"] and "RECORDED" in data["evidence_label"]
    for rel, expected in data["source_files_sha256"].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert actual == expected
    for suite in ("frozen", "fresh"):
        original = json.loads((ROOT / "results" / (suite + "-evidence.json")).read_text(encoding="utf-8"))
        compact = data["suites"][suite]
        assert compact["summary"] == original["summary"]
        assert compact["seed_summary"] == original["seed_summary"]
        assert compact["record_count"] == len(original["records"])


def test_summary_provenance_preserves_acquisition_and_generation():
    from datetime import datetime, timezone
    import platform
    import numpy as np
    import qiskit
    from experiments.make_summary import build_summary
    before = datetime.now(timezone.utc)
    data = build_summary()
    p = data["provenance"]
    generated = datetime.fromisoformat(p["generated_utc"].replace("Z", "+00:00"))
    assert before <= generated <= datetime.now(timezone.utc)
    assert p["machine"] == platform.node() and p["platform"] == platform.platform()
    assert p["python"] == platform.python_version()
    assert p["qiskit"] == qiskit.__version__ and p["numpy"] == np.__version__
    assert data["config"]["shots_per_phase"] == 1000
    assert data["config"]["noise_scales"] == [0, .5, .75, 1, 1.5, 2]
    assert data["config"]["grid"]["grid_step"] == .025
    for suite in ("frozen", "fresh"):
        path = ROOT / "results" / (suite + "-evidence.json")
        original = json.loads(path.read_text(encoding="utf-8"))
        saved = data["suites"][suite]["provenance"]
        assert saved["software_versions"] == original["versions"]
        assert saved["settings"] == original["configuration"]
        assert saved["acquisition"]["date_utc"] == datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date().isoformat()
        assert "not an embedded acquisition" in saved["acquisition"]["date_basis"]
        assert "not captured" in saved["acquisition"]["machine"]
        assert data["suites"][suite]["gate"]["cloud_confirmation"] is False
    assert "earlier local acquisition stage" in data["historical_status_note"]
