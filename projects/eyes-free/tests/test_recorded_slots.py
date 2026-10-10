import copy
import json
import pytest
from recorded_ionq import RECORDED
from receipt import parse_records
from main import recorded_estimates


def test_actual_shipped_slot_records_form_both_sweeps():
    originals = [json.loads(line.removeprefix("RECORD_JSON ")) for line in RECORDED.splitlines() if line.strip()]
    records, errors = parse_records(RECORDED)
    assert not errors and len(records) == 9
    assert {r["slot"] for r in records} == {"E%02d" % n for n in range(1, 10)}
    for raw, validated in zip(originals, records):
        for key in raw:
            assert validated[key] == raw[key]
        assert validated["utc"].startswith("2026-10-10T")
    sweeps, _, errors = recorded_estimates()
    assert not errors and set(sweeps) == {"frozen", "fresh"}
    for estimates in sweeps.values():
        assert len(estimates) == 3
        for width, estimate in zip((1, 2, 4), estimates):
            assert len(estimate["phases_rad"]) == 12
            assert estimate["informative"]
            assert abs(estimate["frequency"] - width) < .03


@pytest.mark.parametrize("field,value", [("shots", 999), ("suite", "fresh"),
    ("manifest_hash", "invalid"), ("effective_noise_model", "ideal")])
def test_actual_slot_rejects_changed_acquisition_contract(field, value):
    raw = json.loads(RECORDED.splitlines()[2])
    raw[field] = value
    records, errors = parse_records("RECORD_JSON " + json.dumps(raw))
    assert not records and errors


def test_actual_slot_rejects_changed_phase_or_totals():
    raw = json.loads(RECORDED.splitlines()[2])
    changed = copy.deepcopy(raw)
    changed["manifest"][0]["phase_rad"] += .1
    assert not parse_records(json.dumps(changed))[0]
    changed = copy.deepcopy(raw)
    first = next(iter(changed["counts"]))
    changed["counts"][first] += 1
    assert not parse_records(json.dumps(changed))[0]
