"""Receipts, recorded-evidence loading and shared-helper disclosure.

Shared helpers live in their own files: circuit_pack.py and receipt.py implement
circuit packing, count normalization, backend dispatch and evidence receipts.
Written during Oct 9-11, 2026, with exact UTC provenance and source/license
attribution; used by Two Whispers Make a Word, Never Lose Twice and
Entanglement Court only where the shipped manifest lists the helper.
Project-specific physics, decoding, inference and presentation are described
on each project page.
"""

import hashlib
import json
import numbers
import re
from datetime import datetime, timezone

import qiskit

import circuit_pack

SCHEMA_VERSION = '1.0'
VALID_SOURCE = 'Qollab IonQ simulator run'
EFFECTIVE_MODELS = ('aria-1', 'forte-1', 'forte-enterprise-1')
WINDOW_START = datetime(2026, 10, 9, 23, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 10, 11, 23, 0, tzinfo=timezone.utc)
_HEX64 = re.compile(r'[0-9a-f]{64}')


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha256_hex(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def hash_block(block):
    return sha256_hex(block)


def hash_layout(layout):
    return sha256_hex([dict(entry) for entry in layout])


def hash_recipe(recipe):
    if recipe is None:
        return hashlib.sha256(b'null').hexdigest()
    return sha256_hex(recipe)


def hash_circuits(circuits):
    summary = []
    for circuit in circuits:
        summary.append({
            'name': circuit.name,
            'qubits': circuit.num_qubits,
            'clbits': circuit.num_clbits,
            'global_phase': float(circuit.global_phase),
            'operations': [
                {'name': inst.operation.name,
                 'qubits': [circuit.find_bit(q).index for q in inst.qubits],
                 'clbits': [circuit.find_bit(c).index for c in inst.clbits],
                 'parameters': [float(p) for p in inst.operation.params]}
                for inst in circuit.data],
        })
    return sha256_hex(summary)


def job_identifier(job):
    value = getattr(job, 'job_id', None)
    try:
        value = value() if callable(value) else value
    except Exception:
        return None
    return value if isinstance(value, str) and value else None


def annotate_layout(layout, blocks):
    if len(layout) != len(blocks):
        raise ValueError('layout and manifest block counts differ')
    annotated = []
    for entry, block in zip(layout, blocks):
        item = dict(entry)
        item['manifest_hash'] = hash_block(block)
        annotated.append(item)
    return annotated


def _now_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def build_record(*, case_id, parameters, construction_seed, shots, noise_model,
                 packed_counts, marginals, layout, hashes, uncertainty, assumptions,
                 settings=None, qiskit_version=None, job_id=None, environment=None,
                 source_file='results/exports/ionq_console_export.txt',
                 result_path='results/qollab_ionq_counts.json',
                 receipt_path='results/receipts/ionq_case.jsonl',
                 started_utc=None, ended_utc=None, backend_name='ionq_simulator',
                 backend_provider='qiskit_ionq', status='success'):
    return {
        'schema_version': SCHEMA_VERSION,
        'source': VALID_SOURCE,
        'environment': environment if environment is not None else {'operator': 'unspecified'},
        'backend': {'name': backend_name, 'provider': backend_provider},
        'noise_model': noise_model,
        'shots': int(shots),
        'settings': settings if settings is not None else {},
        'qiskit_version': qiskit_version or qiskit.__version__,
        'timestamps': {
            'started_utc': started_utc or _now_utc(),
            'ended_utc': ended_utc or _now_utc(),
        },
        'case_id': int(case_id),
        'construction_seed': None if construction_seed is None else int(construction_seed),
        'parameters': parameters,
        'hashes': dict(hashes),
        'layout': [dict(entry) for entry in layout],
        'counts': {
            'packed': {str(k): int(v) for k, v in packed_counts.items()},
            'marginals': [dict(m) for m in marginals],
        },
        'uncertainty': uncertainty,
        'assumptions': list(assumptions),
        'job': {'job_id': job_id, 'available': job_id is not None},
        'paths': {
            'source_file': source_file,
            'receipt': receipt_path,
            'result': result_path,
        },
        'status': status,
    }


def format_record(record):
    return 'RECORD_JSON ' + _json(record)
def _parse_utc(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be a string')
    text = value.strip()
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError('timestamp must include a UTC offset or Z')
    return parsed.astimezone(timezone.utc)


def validate_record(record):
    """Return a list of validation errors; empty means the record is valid."""
    errors = []

    def err(message):
        errors.append(message)

    if not isinstance(record, dict):
        return ['record must be a JSON object']
    try:
        _json(record)
    except (TypeError, ValueError):
        return ['record must contain finite JSON values']
    if record.get('schema_version') != SCHEMA_VERSION:
        err(f"unsupported schema_version {record.get('schema_version')!r}")
    if record.get('source') != VALID_SOURCE:
        err('source must be "Qollab IonQ simulator run"')
    status = record.get('status', 'success')
    if status not in ('success', 'failure'):
        err('status must be success or failure')
    environment = record.get('environment')
    if not isinstance(environment, dict) or not environment or not any(
            key in environment for key in ('machine', 'operator')):
        err('environment must name the machine or operator')
    backend = record.get('backend')
    if not isinstance(backend, dict) or backend.get('name') != 'ionq_simulator':
        err('backend.name must be ionq_simulator')
    if record.get('noise_model') not in EFFECTIVE_MODELS:
        err('noise_model must be one of ' + ', '.join(EFFECTIVE_MODELS))
    shots = record.get('shots')
    if isinstance(shots, bool) or not isinstance(shots, numbers.Integral) or shots < 1:
        err('shots must be a positive integer')
    if not isinstance(record.get('settings'), dict):
        err('settings must be an object')
    version = record.get('qiskit_version')
    if not isinstance(version, str) or not re.match(r'^\d+\.\d+\.\d+', version):
        err('qiskit_version must be a version string')
    timestamps = record.get('timestamps')
    if not isinstance(timestamps, dict):
        err('timestamps must be an object')
    else:
        start = end = None
        try:
            start = _parse_utc(timestamps.get('started_utc'))
        except (ValueError, TypeError) as exc:
            err(f'started_utc: {exc}')
        try:
            end = _parse_utc(timestamps.get('ended_utc'))
        except (ValueError, TypeError) as exc:
            err(f'ended_utc: {exc}')
        if start is not None and end is not None:
            if end < start:
                err('ended_utc precedes started_utc')
            if not WINDOW_START <= start <= WINDOW_END:
                err('started_utc outside the Oct 9-11 2026 build window')
            if not WINDOW_START <= end <= WINDOW_END:
                err('ended_utc outside the Oct 9-11 2026 build window')
    case_id = record.get('case_id')
    if isinstance(case_id, bool) or not isinstance(case_id, numbers.Integral) or not 0 <= case_id <= 28:
        err('case_id must be a frozen integer 0..28')
    seed = record.get('construction_seed')
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, numbers.Integral)):
        err('construction_seed must be an integer or null')
    if not isinstance(record.get('parameters'), dict):
        err('parameters must be an object')
    paths = record.get('paths')
    if not isinstance(paths, dict) or not all(
            isinstance(paths.get(k), str) and paths.get(k)
            for k in ('source_file', 'receipt', 'result')):
        err('paths must name source_file, receipt and result literal strings')
    elif (not paths['source_file'].startswith('results/exports/')
          or '..' in paths['source_file'].split('/')
          or '\\' in paths['source_file']):
        err('source_file must point inside local-only results/exports/')
    job = record.get('job')
    if not isinstance(job, dict) or 'job_id' not in job:
        err('job must record a job_id (null when unavailable)')
    elif job.get('job_id') is not None and not isinstance(job.get('job_id'), str):
        err('job_id must be a string or null')
    elif not isinstance(job.get('available'), bool) or job['available'] != (job['job_id'] is not None):
        err('job.available must match job_id availability')

    if status == 'failure':
        if not isinstance(record.get('attempt_id'), str) or not record.get('attempt_id'):
            err('failure records must retain a charged attempt_id')
        if not isinstance(record.get('error'), str) or not record.get('error'):
            err('failure records must record the error')
        if record.get('counts'):
            err('failure records must not carry successful counts')
        return errors

    hashes = record.get('hashes')
    if not isinstance(hashes, dict):
        err('hashes must be an object')
    else:
        for field in ('recipe', 'circuit', 'layout', 'manifest'):
            value = hashes.get(field)
            if not isinstance(value, str) or not _HEX64.fullmatch(value):
                err(f'hashes.{field} must be a 64-character hex digest')
    layout = record.get('layout')
    try:
        circuit_pack.validate_layout(layout)
    except (ValueError, TypeError) as exc:
        err(f'layout invalid: {exc}')
        layout = None
    if isinstance(hashes, dict) and layout is not None:
        if any(not isinstance(entry.get('manifest_hash'), str)
               or not _HEX64.fullmatch(entry['manifest_hash']) for entry in layout):
            err('each layout block must carry a manifest hash')
        try:
            expected = hash_layout(layout)
        except (TypeError, ValueError) as exc:
            err(f'layout cannot be hashed: {exc}')
        else:
            if hashes.get('layout') != expected:
                err('hashes.layout does not match the stored layout')
    manifest = record.get('manifest')
    if manifest is not None:
        if not isinstance(manifest, dict):
            err('manifest must be an object')
        else:
            try:
                if not isinstance(hashes, dict) or hashes.get('manifest') != sha256_hex(manifest):
                    err('manifest hash does not match stored manifest')
                blocks = manifest['ordered_blocks']
                if layout is None or len(blocks) != len(layout):
                    err('manifest blocks differ from layout')
                elif any(hash_block(block) != entry.get('manifest_hash')
                         for block, entry in zip(blocks, layout)):
                    err('block manifest hashes differ from layout')
                if isinstance(hashes, dict) and hashes.get('recipe') != hash_recipe(manifest.get('recipe')):
                    err('recipe hash does not match stored recipe')
            except (KeyError, TypeError, ValueError) as exc:
                err(f'manifest invalid: {exc}')
    counts = record.get('counts')
    if not isinstance(counts, dict) or not isinstance(counts.get('packed'), dict) \
            or not isinstance(counts.get('marginals'), list):
        err('counts must provide a packed object and ordered marginals list')
    elif layout is not None:
        packed = counts['packed']
        marginals = counts['marginals']
        if len(marginals) != len(layout):
            err('marginal count does not match the layout block count')
        total = 0
        bad_count = False
        for value in packed.values():
            if isinstance(value, bool) or not isinstance(value, numbers.Integral) or value < 0:
                bad_count = True
            else:
                total += int(value)
        if bad_count:
            err('packed counts must be nonnegative integers')
        elif total != shots:
            err('packed count total does not equal shots')
        try:
            fresh = circuit_pack.unpack_counts(packed, layout)
        except (ValueError, TypeError) as exc:
            err(f'packed counts cannot be unpacked: {exc}')
        else:
            if fresh != marginals:
                err('stored marginals differ from fresh unpacking of the packed counts')
            for marginal in marginals:
                if not isinstance(marginal, dict) or any(
                        isinstance(v, bool) or not isinstance(v, numbers.Integral) or v < 0
                        for v in marginal.values()):
                    err('marginal counts must be objects of nonnegative integers')
    uncertainty = record.get('uncertainty')
    if not isinstance(uncertainty, dict) or not isinstance(uncertainty.get('method'), str):
        err('uncertainty must state a method')
    else:
        confidence = uncertainty.get('confidence')
        if isinstance(confidence, bool) or not isinstance(confidence, numbers.Real) \
                or not 0 < confidence < 1:
            err('uncertainty must state a confidence level in (0,1)')
    assumptions = record.get('assumptions')
    if not isinstance(assumptions, list) or not assumptions \
            or not all(isinstance(item, str) for item in assumptions):
        err('assumptions must be a nonempty list of strings')
    return errors


def parse_records(text):
    """Parse RECORD_JSON lines or bare JSON lines; blank lines are skipped."""
    if not isinstance(text, str):
        raise TypeError('recorded evidence must be a string')
    records, statuses = [], []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        payload = line
        if line.startswith('RECORD_JSON'):
            payload = line[len('RECORD_JSON'):].strip()
        if not payload:
            statuses.append({'line': number, 'ok': False, 'error': 'empty record payload'})
            continue
        try:
            record = json.loads(payload)
        except (ValueError, TypeError) as exc:
            statuses.append({'line': number, 'ok': False, 'error': f'malformed JSON: {exc}'})
            continue
        try:
            errors = validate_record(record)
        except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
            errors = [f'malformed record structure: {exc}']
        if errors:
            statuses.append({'line': number, 'ok': False, 'error': '; '.join(errors)})
            continue
        records.append(record)
        statuses.append({'line': number, 'ok': True, 'error': None})
    return records, statuses


def recap(records):
    if not records:
        return ['No recorded IonQ runs yet']
    lines = []
    for record in records:
        stamp = record['timestamps']
        lines.append(
            f"Recorded {record.get('status', 'success').upper()} "
            f"case={record['case_id']} backend={record['backend']['name']} "
            f"noise_model={record['noise_model']} shots={record['shots']} "
            f"{stamp['started_utc']}..{stamp['ended_utc']} "
            f"source_file={record['paths']['source_file']}")
    return lines


def campaign_status(records):
    """Budget and explicit-case readiness; never infer a control from an anchor."""
    success = [r for r in records if r.get('status', 'success') == 'success']
    lines = []
    for campaign, model, shots in (
            ('W01', 'aria-1', 100), ('W02', 'aria-1', 1000),
            ('W03', 'forte-1', 1000), ('W04', 'forte-enterprise-1', 1000)):
        def matches(record):
            manifest = record.get('manifest') or {}
            if record['noise_model'] != model or record['shots'] != shots:
                return False
            if campaign == 'W01':
                return (record['case_id'] in manifest.get('smoke_control_ids', [])
                        and manifest.get('case_role') == 'asymmetric-control')
            return record['case_id'] == 0 and manifest.get('case_role') == 'anchor'
        ready = any(matches(r) for r in success)
        lines.append(f'Campaign {campaign}: ' + ('Recorded' if ready else 'readiness gap')
                     + f' ({model}, {shots} shots, '
                     + ('explicit asymmetric control' if campaign == 'W01' else 'standard-frame anchor') + ')')
    return lines
