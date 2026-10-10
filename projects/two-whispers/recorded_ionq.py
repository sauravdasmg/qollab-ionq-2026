"""Recorded Qollab IonQ console exports, one RECORD_JSON line per line.

Initially empty. The human pastes each console RECORD_JSON line into this raw
string in Qollab's code editor; receipt.py parses and validates every line and
never invents evidence. No shipped data lives in subfolders; original console
exports stay local-only under results/exports/ and each record's source_file
points there.
"""
RECORDED = r""""""