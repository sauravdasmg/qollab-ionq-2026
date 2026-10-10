"""Validate legacy W/N and merged records without rewriting original receipts."""
import json
import numbers
from datetime import datetime
from circuit_pack import unpack_counts
import whispers_core as w
import hedging_core as n

def normalized_layout(record):
    layout = []
    for entry in record['layout']:
        if 'classical_offset' in entry:
            layout.append(entry)
        else:
            layout.append({'block_name': entry['name'], 'qubit_offset': entry['qubit_offset'],
                           'qubit_width': entry['qubit_width'], 'classical_offset': entry['clbit_offset'],
                           'classical_width': entry['clbit_width'],
                           'qubit_to_cbit_map': dict(entry['local_qubit_to_cbit_map']),
                           'manifest_hash': entry.get('manifest_hash')})
    return layout

def record_marginals(record):
    raw = (record.get('counts') or {}).get('packed')
    if raw is None:
        raw = record.get('raw_counts', record.get('raw_packed_counts'))
    if not isinstance(raw, dict) or not raw:
        raise ValueError('raw packed counts required')
    if any(isinstance(v, bool) or not isinstance(v, numbers.Integral) or v < 0 for v in raw.values()):
        raise ValueError('nonnegative integer raw counts required')
    if sum(raw.values()) != record['shots']:
        raise ValueError('raw count total differs from shots')
    layout = normalized_layout(record)
    fresh = unpack_counts(raw, layout)
    stored = (record.get('counts') or {}).get('marginals', record.get('marginals'))
    if isinstance(stored, dict):
        stored = [stored[b['block_name']] for b in layout]
    if stored is None or len(stored) != len(fresh):
        raise ValueError('missing stored marginal counts')
    # Empty zero bins may be stored or omitted, but all populated bins must match.
    for a, b in zip(fresh, stored):
        if any(isinstance(v, bool) or not isinstance(v, numbers.Integral) or v < 0 for v in b.values()):
            raise ValueError('invalid stored marginal')
        if {k:v for k,v in a.items() if v} != {k:v for k,v in b.items() if v}:
            raise ValueError('stored marginal disagrees with raw packed counts')
    return fresh

def parse_records(text):
    records, statuses, seen = [], [], set()
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line.removeprefix('RECORD_JSON').strip())
            if not isinstance(r, dict) or r.get('schema_version') not in ('1.0', '1.0.0', 'noise-tax-1'):
                raise ValueError('unsupported receipt schema')
            if r.get('source') != 'Qollab IonQ simulator run':
                raise ValueError('receipt source is not Qollab IonQ simulator')
            if r.get('noise_model') not in ('aria-1', 'aria-2', 'forte-1', 'forte-enterprise-1'):
                raise ValueError('unknown discrete noise model')
            backend = r.get('backend')
            if (backend.get('name') if isinstance(backend, dict) else backend) != 'ionq_simulator':
                raise ValueError('backend is not ionq_simulator')
            if isinstance(r.get('shots'), bool) or not isinstance(r.get('shots'), int) or r['shots'] <= 0:
                raise ValueError('positive integer shots required')
            timestamps = r.get('timestamps', {})
            start = timestamps.get('started_utc', r.get('utc_start'))
            end = timestamps.get('ended_utc', r.get('utc_end'))
            a = datetime.fromisoformat(start.replace('Z', '+00:00'))
            b = datetime.fromisoformat(end.replace('Z', '+00:00'))
            if a.tzinfo is None or b.tzinfo is None or a > b:
                raise ValueError('invalid receipt times')
            record_marginals(r)
            identity = (r['noise_model'], start, end, r.get('case_id'),
                        (r.get('hashes') or {}).get('circuit'))
            if identity in seen:
                statuses.append({'line': number, 'ok': False, 'duplicate': True, 'error': 'duplicate receipt identity'})
                continue
            seen.add(identity)
            records.append(r); statuses.append({'line': number, 'ok': True, 'error': None})
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            statuses.append({'line': number, 'ok': False, 'error': str(exc)})
    return records, statuses

def summarize_record(r):
    marginals = record_marginals(r)
    manifest = r['manifest']
    common = {'model': r['noise_model'], 'shots': r['shots'],
              'source_file': r.get('source_file', r.get('paths', {}).get('source_file')),
              'case_id': r.get('case_id'), 'label': 'RECORDED IonQ simulator'}
    if r.get('project') == 'The Noise Tax' or r.get('schema_version') == 'noise-tax-1':
        wm, nm = manifest['W'], manifest['N']
        wa = w.analyze_counts(marginals[:3], wm)
        na = n.analyze_probabilities(marginals[3:], nm)
        return [dict(common, game='W', advantage=wa['advantage'], word_error=wa['joint']['word_error']),
                dict(common, game='N', advantage=na['advantage'], metrics=na)]
    blocks = manifest['ordered_blocks']
    if isinstance(blocks[0], dict):
        # Historical textbook arm is the fixed reference; don't choose synthesis
        # arm based on its observed counts. Preserve all raw original arms.
        indices = [j for j, b in enumerate(blocks) if b['family'] == 'textbook']
        copied = []
        for j in indices:
            b = dict(blocks[j], arm='joint')
            copied.append(b)
        wa = w.analyze_counts([marginals[j] for j in indices], {'ordered_blocks': copied})
        return [dict(common, game='W', advantage=wa['advantage'],
                     word_error=wa['joint']['word_error'], arm='textbook',
                     reference='analytic noiseless one-way bound')]
    indices = [blocks.index(name) for name in n.BLOCKS]
    selected = dict(manifest, ordered_blocks=list(n.BLOCKS),
                    decoding_maps=[manifest['decoding_maps'][j] for j in indices])
    na = n.analyze_probabilities([marginals[j] for j in indices], selected)
    return [dict(common, game='N', advantage=na['advantage'], metrics=na,
                 reference='attained product recipe, fixed prize 0.02')]