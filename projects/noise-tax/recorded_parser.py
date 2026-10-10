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

def _summarize_record(r):
    marginals = record_marginals(r)
    manifest = r['manifest']
    common = {'model': r['noise_model'], 'shots': r['shots'],
              'source_file': r.get('source_file', r.get('paths', {}).get('source_file')),
              'case_id': r.get('case_id'), 'label': 'RECORDED IonQ simulator'}
    if r.get('project') == 'The Noise Tax' or r.get('schema_version') == 'noise-tax-1':
        common = dict(common, slot=r.get('slot'))
        if set(manifest) == {'W'}:
            # Cloud slot T01/T03/...: one W game, joint and physical one-way blocks interleaved.
            wa = w.analyze_counts(marginals, manifest['W'])
            return [dict(common, game='W', advantage=wa['advantage'], word_error=wa['joint']['word_error'],
                         oneway_word_error=wa['oneway']['word_error'] if 'oneway' in wa else None)]
        if set(manifest) == {'N'}:
            # Cloud slot T02/T04/...: one N game, two arms.
            na = n.analyze_probabilities(marginals, manifest['N'])
            return [dict(common, game='N', advantage=na['advantage'], metrics=na)]
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

def binomial_interval(successes, shots, confidence=.95):
    """Two-sided exact Clopper-Pearson interval for one Bernoulli indicator."""
    from scipy.stats import beta
    if not 0 <= successes <= shots or shots <= 0 or not 0 < confidence < 1:
        raise ValueError('valid binomial counts and confidence required')
    tail = (1-confidence)/2
    return [float(beta.ppf(tail, successes, shots-successes+1)) if successes else 0.,
            float(beta.ppf(1-tail, successes+1, shots-successes)) if successes < shots else 1.]

def summarize_record(r):
    """Attach shot uncertainty to each cloud point; never estimate a cloud s*."""
    summaries = _summarize_record(r)
    marginals = record_marginals(r)
    merged = r.get('project') == 'The Noise Tax' or r.get('schema_version') == 'noise-tax-1'
    for summary in summaries:
        rows = []
        if summary['game'] == 'W':
            blocks = r['manifest']['W']['ordered_blocks'] if merged else r['manifest']['ordered_blocks']
            if not merged:
                indices = [i for i, b in enumerate(blocks) if b['family'] == 'textbook']
            elif 'N' in r['manifest']:
                indices = list(range(3))
            else:
                indices = [i for i, b in enumerate(blocks) if b.get('arm', 'joint') == 'joint']
            bounds = []
            for i in indices:
                b = blocks[i]; dist = marginals[i]; total = sum(dist.values())
                count = sum(v for bits, v in dist.items()
                            if b['decoder'][int(bits.replace(' ', ''), 2)] == b['label'])
                ci = binomial_interval(count, total, 1-.05/len(indices))
                bounds.append(ci)
                rows.append({'label': b['label'], 'event': 'decoded success', 'count': count,
                             'shots': total, 'binomial_interval': binomial_interval(count, total),
                             'simultaneous_interval': ci})
            interval = [sum(b[j] for b in bounds)/len(bounds)-w.P_SEQ for j in (0, 1)]
        else:
            # Each joint outcome is a Bernoulli indicator, although loss is not.
            blocks = list(n.BLOCKS)
            arm_bounds = {}
            for arm in blocks:
                probs = summary['metrics'][arm]['joint_probabilities']
                # Validated marginals have exactly r['shots'] observations per arm.
                bounds = {}
                for event, prob in probs.items():
                    count = int(round(prob*r['shots']))
                    ci = binomial_interval(count, r['shots'], 1-.05/8)
                    bounds[event] = ci
                    rows.append({'arm': arm, 'event': event, 'count': count, 'shots': r['shots'],
                                 'binomial_interval': binomial_interval(count, r['shots']),
                                 'simultaneous_interval': ci})
                weights = {'FF': 1.04, 'FP': .02, 'PF': .02, 'PP': 0.}
                arm_bounds[arm] = [sum(weights[e]*bounds[e][j] for e in weights) for j in (0, 1)]
            product, hedge = arm_bounds['attained_product'], arm_bounds['published_hedge']
            interval = [product[0]-hedge[1], product[1]-hedge[0]]
        summary['cloud_sampling'] = {
            'uncertainty_source': 'CLOUD SAMPLING', 'confidence': .95, 'components': rows,
            'advantage_interval': interval,
            'method': 'Clopper-Pearson binomial components; Bonferroni 95% propagated advantage bounds',
            'limitations': 'pointwise shot sampling only; no cloud s* or model uncertainty'}
    return summaries
