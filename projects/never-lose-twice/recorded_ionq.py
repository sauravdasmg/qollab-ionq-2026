"""Recorded IonQ simulator runs for Never Lose Twice.

HOW TO ADD A RUN (in Qollab's code editor): run the project on an IonQ simulator (aria-1, forte-1 or
forte-enterprise-1), copy the console line that starts with RECORD_JSON, and paste it as a NEW LINE
between the triple quotes below. Do not change any existing line. The parser in receipt.py accepts a
RECORD_JSON prefix or bare JSON, skips blank lines, rejects malformed lines one by one with a visible
status and never invents evidence. Original console exports are kept in the local-only results/exports/
folder and pointed at by each record's source_file.

Initially empty: no dummy or pre-kickoff measurements are shipped.
"""
RECORDED = r"""
"""