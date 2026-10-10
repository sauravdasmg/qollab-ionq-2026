import json
import sys
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
    for campaign in data["campaigns"]:
        source = json.loads((ROOT / campaign["source"]).read_text(encoding="utf-8"))
        assert campaign["sha256"] == data["sources"][[s["path"] for s in data["sources"]].index(campaign["source"])]["sha256"]
        assert len(campaign["cases"]) == len(source["cases"])
        first = campaign["cases"][0]
        original = source["cases"][0]
        assert first["manifest_sha256"] == original["manifest_hash"]
        assert first["configurations"][0]["draws"] == original["noise_results"][0]["draws"]
    gate = json.loads((ROOT / "results/g1.json").read_text(encoding="utf-8"))
    assert data["gate_decisions"]["result"] == gate
