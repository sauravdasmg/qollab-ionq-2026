import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.make_summary import LIMIT, write_summary


def test_summary_is_compact_and_matches_sources(tmp_path):
    output = write_summary(tmp_path / "evidence_summary.json")
    data = json.loads(output.read_text(encoding="utf-8"))
    assert output.stat().st_size < LIMIT
    expected = {"frozen", "fresh", "development"}
    assert {campaign["suite"] for campaign in data["campaigns"]} == expected
    provenance = data["provenance"]
    assert datetime.fromisoformat(provenance["generated_utc"]).utcoffset().total_seconds() == 0
    for key in ("platform", "python", "qiskit", "numpy", "scipy"):
        assert provenance[key]
    assert provenance["generator_sha256"] == hashlib.sha256((ROOT / provenance["generator"]).read_bytes()).hexdigest()
    for campaign in data["campaigns"]:
        source = json.loads((ROOT / campaign["source"]).read_text(encoding="utf-8"))
        assert campaign["created_utc"] == source["created_utc"]
        assert campaign["versions"] == source["versions"]
        assert campaign["simulator"]
        assert "discarded" in campaign["retention"]
        assert campaign["sha256"] == hashlib.sha256((ROOT / campaign["source"]).read_bytes()).hexdigest()
        assert campaign["sha256"] == data["sources"][[s["path"] for s in data["sources"]].index(campaign["source"])]["sha256"]
        assert len(campaign["cases"]) == len(source["cases"])
        first = campaign["cases"][0]
        original = source["cases"][0]
        assert first["manifest_sha256"] == original["manifest_hash"]
        assert first["configurations"][0]["draws"] == original["noise_results"][0]["draws"]
    gate = json.loads((ROOT / "results/g1.json").read_text(encoding="utf-8"))
    assert data["gate_decisions"]["result"] == gate


def test_shipped_summary_matches_saved_sources():
    from experiments.make_summary import build_summary
    shipped = json.loads((ROOT / "evidence_summary.json").read_text(encoding="utf-8"))
    assert shipped == build_summary(generated_utc=shipped["provenance"]["generated_utc"])
