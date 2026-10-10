"""Quick audit of retained evidence labels and immutable export identity."""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recorded_ionq import EXPORT_INDEX, RECORDED
from receipt import load_records


def test_campaign_status_tracks_supplied_records_and_legacy_deviation():
    records, statuses = load_records()
    assert len(records) == 25
    assert 'Recorded campaign: 24/24 retained slots supplied.' in statuses
    assert any('Legacy preparation-noise deviation: C02, C03, C04, C05, C06, C07' in s for s in statuses)
    assert not any('not yet supplied' in s for s in statuses)
    assert any('draw-level counts' in s for s in statuses)
    _, empty_status = load_records('')
    assert any('Recorded campaign: 0/24' in s and 'Missing: C02' in s for s in empty_status)


def test_archive_mapping_matches_each_original_export():
    archived = [json.loads(line) for line in RECORDED.splitlines() if line.strip()]
    indexed = {(entry['job_id'], entry['utc_end']): entry for entry in EXPORT_INDEX}
    assert len(archived) == len(indexed) == 31
    decoder = json.JSONDecoder()
    for record in archived:
        entry = indexed[(record['job_id'], record['utc_end'])]
        path = ROOT / entry['source_file']
        assert record['source_file'] == entry['source_file']
        assert record['original_source_file'] == 'results/exports/qollab-console.txt'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
        text = html.unescape(re.sub(r'<[^>]+>', '', path.read_text(encoding='utf-8')))
        exported = []
        for match in re.finditer('RECORD_JSON', text):
            try:
                original, _ = decoder.raw_decode(text[match.end():].lstrip(': '))
            except json.JSONDecodeError:
                continue
            if original.get('job_id') == record['job_id'] and original.get('utc_end') == record['utc_end']:
                exported.append(original)
        assert len(exported) == 1
        for key in ('raw_counts', 'settings', 'layout', 'marginals', 'uncertainty',
                    'recipe_hash', 'circuit_hash', 'layout_hash', 'shots', 'noise_model'):
            assert exported[0][key] == record[key]
