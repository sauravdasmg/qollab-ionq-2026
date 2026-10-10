import json
import tempfile
import unittest
from pathlib import Path
from experiments.cloud_fit import extract_records, combine, _slot_phase_counts

class CloudFitTest(unittest.TestCase):
    def test_parity_excludes_lower_offset_blocks(self):
        # Odd bit 0 must not contaminate even blocks at offsets 1 and 7.
        record = {"counts": {format(1, "021b"): 1000},
                  "manifest": [{"width": 2, "offset": 1, "phase_rad": 0.0},
                               {"width": 2, "offset": 7, "phase_rad": 1.0}]}
        self.assertEqual(_slot_phase_counts(record, 2),
                         [(0.0, {"0": 1000, "1": 0}),
                          (1.0, {"0": 1000, "1": 0})])

    def test_emulated_frozen_slots_recover_frequencies(self):
        from experiments.check_cloud_slots import emulate_frozen, check
        check(emulate_frozen())

    def test_cloud_smoke_matches_asymmetric_wires(self):
        from circuit_pack import smoke_pack, unpack
        record = next(r for r in extract_records() if r["slot"] == "E01")
        _, manifest = smoke_pack()
        self.assertEqual(record["manifest"], manifest)
        expected = "".join(b["expected"] for b in reversed(manifest))
        self.assertEqual(record["counts"], {expected: 100})
        self.assertEqual(unpack(record["counts"], manifest, 19),
                         [{b["expected"]: 100} for b in manifest])

    def test_real_exports_validate_and_combine(self):
        records = extract_records()
        self.assertEqual(len(records), 9)
        fits = combine(records)["suites"]
        self.assertEqual(set(fits), {"frozen", "fresh"})
        for suite in fits.values():
            for fit in suite["fits"].values():
                self.assertEqual(len(fit["phases_rad"]), 12)
                self.assertEqual(len(fit["frequency_ci"]), 2)
                self.assertEqual(len(fit["contrast_ci"]), 2)

    def test_validation_rejects_bad_slot(self):
        from experiments.cloud_fit import SLOTS
        self.assertEqual(SLOTS["E02"]["suite"], "frozen")

if __name__ == "__main__":
    unittest.main()
