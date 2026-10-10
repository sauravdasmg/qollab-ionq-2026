"""Paste original RECORD_JSON console lines here; empty means no cloud evidence."""
RECORDED = r""""""

# Status applies to original exports; preserve their raw counts unchanged.
LEGACY_PREP_NOISE_STATUS = {
    **{f"C{i:02d}": "prep-noise omitted (superseded)" for i in range(8, 14)},
    **{f"C{i:02d}": "prep-noise omitted (easy; small documented deviation)" for i in range(2, 8)},
}
