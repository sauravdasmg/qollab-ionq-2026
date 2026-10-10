import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eyes_bridge


def test_catalog_and_wav():
    records = eyes_bridge.fringe_catalog()
    assert {r["n"] for r in records} == {1, 2, 4}
    assert all(r["source"] == "LOCAL MODEL" for r in records)
    wav = eyes_bridge.make_wav(2, 0.5)
    assert wav[:4] == b"RIFF" and len(wav) > 1000


def test_actual_recorded_cloud_fits_are_js_catalog_records():
    records = eyes_bridge.recorded_fringe()
    assert len(records) == 6
    assert {r["source"] for r in records} == {"RECORDED"}
    assert {r["suite"] for r in records} == {"frozen", "fresh"}
    for r in records:
        assert r["informative"] and abs(r["frequency"] - r["n"]) < .03
        assert r["frequency_ci"][0] <= r["frequency"] <= r["frequency_ci"][1]
        assert len(r["source_files"]) == 4 and r["shots_per_phase"] == 1000
        assert r["source"] in eyes_bridge.receipt_text(r)
