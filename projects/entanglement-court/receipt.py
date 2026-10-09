"""Shared helpers live in their own files: circuit_pack.py and receipt.py implement circuit packing, count normalization, backend dispatch and evidence receipts. Written during Oct 9-11, 2026, with exact UTC provenance and source/license attribution; used by Two Whispers Make a Word, Never Lose Twice and Entanglement Court only where the shipped manifest lists the helper. Project-specific physics, decoding, inference and presentation are described on each project page.

Independent implementation from HELPER_SPEC.md; project MIT license applies.
"""
import json
import re
from datetime import datetime, timezone
from circuit_pack import digest, unpack_counts

MODELS = {'aria-1', 'forte-1', 'forte-enterprise-1'}
START = datetime(2026, 10, 9, 23, tzinfo=timezone.utc)
END = datetime(2026, 10, 11, 23, tzinfo=timezone.utc)
FIELDS = {'schema_version', 'source', 'operator_environment', 'backend', 'noise_model', 'shots',
          'settings', 'qiskit_version', 'utc_start', 'utc_end', 'case_id', 'construction_seed',
          'recipe_hash', 'circuit_hash', 'layout_hash', 'layout', 'raw_counts', 'marginals',
          'uncertainty', 'assumptions', 'job_id', 'source_file', 'receipt_path', 'result_path', 'error'}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def validate_record(record):
    if not isinstance(record, dict) or not FIELDS <= record.keys():
        raise ValueError('missing receipt fields')
    if record['schema_version'] != '1.0.0' or record['source'] != 'Qollab IonQ simulator run' or record['backend'] != 'ionq_simulator':
        raise ValueError('unsupported schema or evidence source/backend')
    if record['noise_model'] not in MODELS:
        raise ValueError('unknown effective noise model')
    times = [datetime.fromisoformat(record[k].replace('Z', '+00:00')) for k in ('utc_start', 'utc_end')]
    if any(t.tzinfo is None or t.utcoffset().total_seconds() != 0 for t in times) or not START <= times[0] <= times[1] <= END:
        raise ValueError('receipt dates must be UTC inside the build window')
    if type(record['shots']) is not int or record['shots'] <= 0:
        raise ValueError('invalid shots')
    for k in ('recipe_hash', 'circuit_hash', 'layout_hash'):
        if not isinstance(record[k], str) or not re.fullmatch('[0-9a-f]{64}', record[k]):
            raise ValueError('invalid ' + k)
    if not isinstance(record['assumptions'], list) or not record['assumptions'] or not all(isinstance(x, str) for x in record['assumptions']):
        raise ValueError('missing measurement assumptions')
    if not isinstance(record['settings'], dict) or not isinstance(record['uncertainty'], dict):
        raise ValueError('invalid settings or uncertainty')
    manifest = record['settings'].get('manifest')
    description = record['settings'].get('packed_circuit')
    if not isinstance(manifest, dict) or digest(manifest) != record['recipe_hash']:
        raise ValueError('missing recipe manifest or recipe hash mismatch')
    if not isinstance(description, dict) or digest(description) != record['circuit_hash']:
        raise ValueError('missing circuit representation or circuit hash mismatch')
    if not record['layout'] or sum(b['qubit_width'] for b in record['layout']) > 25:
        raise ValueError('missing layout or qubit cap exceeded')
    if manifest['ordered_blocks'] != [b['block_name'] for b in record['layout']]:
        raise ValueError('layout order differs from core manifest')
    if str(manifest['case_id']) != record['case_id'] or manifest['seed'] != record['construction_seed']:
        raise ValueError('case or seed differs from manifest')
    for block in record['layout']:
        if not re.fullmatch('[0-9a-f]{64}', block['manifest_hash']):
            raise ValueError('invalid block hash')
    if not re.fullmatch(r'results/exports/[A-Za-z0-9_.-]+', record['source_file']):
        raise ValueError('source_file must identify the preserved local console export')
    if digest(record['layout']) != record['layout_hash']:
        raise ValueError('layout hash mismatch')
    if record['error'] is None:
        marginals = unpack_counts(record['raw_counts'], record['layout'])
        if not record['raw_counts'] or sum(record['raw_counts'].values()) != record['shots']:
            raise ValueError('raw shots mismatch')
        if marginals != record['marginals']:
            raise ValueError('marginals do not derive from raw counts')
        if record['settings'].get('raw_counts_hash') != digest(record['raw_counts']):
            raise ValueError('raw counts hash mismatch')
    else:
        if not isinstance(record['error'], str) or not record['error'] or record['raw_counts'] or record['marginals']:
            raise ValueError('invalid terminal error receipt')
    return record


def load_records(text=None):
    if text is None:
        from recorded_ionq import RECORDED
        text = RECORDED
    valid, status = [], []
    for line_number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith('RECORD_JSON'):
            line = line[len('RECORD_JSON'):].lstrip(': ')
        try:
            record = validate_record(json.loads(line))
            valid.append(record)
            status.append('Recorded: ' + record['backend'] + ', ' + record['noise_model'] + ', ' + str(record['shots']) + ' shots, ' + record['utc_end'] + ('; terminal error' if record['error'] else ''))
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
            status.append('Malformed recorded line ' + str(line_number) + ': ' + str(exc))
    if not valid:
        status.append('No recorded IonQ runs yet')
    status.append('Readiness gap: prescribed cloud campaign and matched saved recipes are not yet supplied.')
    return valid, status


def emit_record(record):
    print('RECORD_JSON ' + json.dumps(record, sort_keys=True, allow_nan=False), flush=True)
