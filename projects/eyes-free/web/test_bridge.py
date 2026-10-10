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
