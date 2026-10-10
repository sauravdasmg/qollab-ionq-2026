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
    assert data["evidence_label"].startswith("LOCAL MODEL")
    for rel, expected in data["source_files_sha256"].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert actual == expected
    for suite in ("frozen", "fresh"):
        original = json.loads((ROOT / "results" / (suite + "-evidence.json")).read_text(encoding="utf-8"))
        compact = data["suites"][suite]
        assert compact["summary"] == original["summary"]
        assert compact["seed_summary"] == original["seed_summary"]
        assert compact["record_count"] == len(original["records"])
