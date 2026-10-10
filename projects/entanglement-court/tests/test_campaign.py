import json
from campaign import SLOTS, build_slot, verify_manifests
from circuit_pack import pack_circuits

def test_campaign_slots_manifest_and_width():
    assert verify_manifests()
    assert [row["slot"] for row in SLOTS] == [f"C{i:02d}" for i in range(2, 26)]
    for row in SLOTS:
        circuits, manifest, metadata = build_slot(row["slot"])
        packed, layout = pack_circuits(circuits)
        assert packed.num_qubits <= 25
        assert metadata["manifest_hash"] == row["manifest_hash"]
        assert manifest["case_id"] == row["case_id"]

