"""Thin Python adapter for Entanglement Court web frontend. Called via .callPromising()."""
import json
import platform
import qiskit
from cases import make_demo, analyze_counts
from circuit_pack import demo_blocks, pack_circuits, unpack_counts, normalize_counts, digest, circuit_hash, circuit_description
from receipt import load_records, utc_now, MODELS
from figures import parity_interval, ASSUMPTIONS


def _effective_model(active):
    options = getattr(active, 'options', None)
    model = options.get('noise_model') if isinstance(options, dict) else getattr(options, 'noise_model', None)
    if isinstance(model, dict):
        model = model.get('model') or model.get('name')
    if model not in MODELS:
        raise ValueError('actual effective IonQ noise_model must be aria-1, forte-1 or forte-enterprise-1')
    return model


def run_demo(backend, case=0, shots=200, challenge="sealed", assume_trusted_measurements=False):
    """Run the entanglement court demo and return JSON-serializable results."""
    if not isinstance(case, int) or case not in range(4):
        raise ValueError('case must be a frozen ID 0..3')
    if not isinstance(shots, int) or not 1 <= shots <= 10000:
        raise ValueError('shots must be an integer 1..10000')
    if challenge not in ('sealed', 'anchor', 'audited16'):
        raise ValueError('challenge must be sealed, anchor or audited16')
    if not isinstance(assume_trusted_measurements, bool):
        raise ValueError('trust flag must be bool')

    records, statuses = load_records()
    circuits, manifest = make_demo(case, recipe={'audited16': challenge == 'audited16'})
    manifest['shared_helpers'] = ['circuit_pack.py', 'receipt.py']
    blocks = demo_blocks(circuits, manifest)
    packed, layout = pack_circuits(blocks)

    active = backend
    name = getattr(active, 'name', '')
    if callable(name):
        name = name()
    ionq = isinstance(name, str) and name.startswith('ionq')
    if ionq and name != 'ionq_simulator':
        raise ValueError('only the injected IonQ simulator is supported')
    effective = _effective_model(active) if ionq else None
    if ionq and challenge == 'audited16':
        raise ValueError('Readiness gap: 16-wire cloud fallback requires saved Z references and the C27 smoke audit; neither is staged. Use the 24-wire anchor.')

    started = utc_now()
    assumptions = list(manifest['source_assumptions']) + [ASSUMPTIONS,
        'Packed blocks share one execution, not independent generated instances.',
        'Anchor demonstration is not the prescribed campaign; cloud budget/controls pending.']

    record = dict(schema_version='1.0.0', source='Qollab IonQ simulator run', operator_environment=platform.platform(),
                  backend=name, noise_model=effective, shots=shots, settings={'manifest': manifest, 'challenge': challenge,
                  'packed_circuit': circuit_description(packed),
                  'backend_options': {'noise_model': effective}, 'execution': {'shots': shots},
                  'assume_trusted_measurements': assume_trusted_measurements}, qiskit_version=qiskit.__version__,
                  utc_start=started, utc_end=started, case_id=str(case), construction_seed=manifest['seed'],
                  recipe_hash=digest(manifest), circuit_hash=circuit_hash(packed), layout_hash=digest(layout), layout=layout,
                  raw_counts={}, marginals={}, uncertainty={}, assumptions=assumptions, job_id=None,
                  source_file='results/exports/qollab-console.txt', receipt_path='recorded_ionq.py',
                  result_path='recorded_ionq.py', error=None)

    try:
        job = active.run(packed if ionq else blocks, shots=shots)
        if ionq:
            job_id = getattr(job, 'job_id', None)
            record['job_id'] = str(job_id() if callable(job_id) else job_id) if job_id is not None else None
        result = job.result()
        cached = result.get_counts()
        if ionq:
            raw = dict(cached)
            record['noise_model'] = _effective_model(active)
            record['settings']['backend_options']['noise_model'] = record['noise_model']
            marginals = unpack_counts(raw, layout)
            if sum(raw.values()) != shots:
                raise ValueError('returned IonQ shot total differs from requested shots')
            record['raw_counts'], record['marginals'] = raw, marginals
            record['settings']['raw_counts_hash'] = digest(raw)
        else:
            if isinstance(cached, dict):
                cached = [cached]
            if len(cached) != len(blocks):
                raise ValueError('built-in block result count mismatch')
            marginals = {b.name: normalize_counts(hist, b.num_clbits) for b, hist in zip(blocks, cached)}
            if any(sum(hist.values()) != shots for hist in marginals.values()):
                raise ValueError('built-in shot count mismatch')
        analysis = analyze_counts(marginals, manifest, trusted=assume_trusted_measurements)
        analysis['parity_intervals_95'] = {
            block: [{'generator': row['generator'], 'shots': row['shots'],
                     'estimate': row['estimate'],
                     'interval': list(parity_interval(row['successes'], row['shots'])),
                     'units': 'dimensionless signed parity', 'scope': 'individual two-sided interval'}
                    for row in rows] for block, rows in analysis['blocks'].items()}
        record['uncertainty'] = analysis
        record['utc_end'] = utc_now()
    except Exception as exc:
        if ionq:
            record.update(utc_end=utc_now(), error=str(exc), raw_counts={}, marginals={})
        raise

    if ionq:
        from receipt import emit_record
        emit_record(record)

    source = ('Live Qollab IonQ simulator | ' + effective + ' | UTC ' + record['utc_end']) if ionq else 'Live built-in ideal'

    # Prepare JSON-serializable result
    result_data = {
        'manifest': manifest,
        'layout': layout,
        'marginals': marginals,
        # Explicit rows preserve leading-zero outcomes across Python/JS bridges.
        # Missing Z blocks in audited16 are unavailable, never fabricated zeros.
        'distributions': {
            name: [{'outcome': format(i, '04b'),
                    'probability': hist.get(format(i, '04b'), 0) / sum(hist.values())}
                   for i in range(16)]
            for name, hist in marginals.items() if name.endswith('_Z')
        },
        'analysis': analysis,
        'record': record if ionq else None,
        'source': source,
        'shots': shots,
        'trusted': assume_trusted_measurements,
        'statuses': statuses
    }

    return result_data


def load_recorded():
    """Load recorded IonQ runs from recorded_ionq.py."""
    records, statuses = load_records()
    return {'records': records, 'statuses': statuses}


def get_case_metadata(case=0):
    """Get metadata for a case without running circuits."""
    if not isinstance(case, int) or case not in range(4):
        raise ValueError('case must be a frozen ID 0..3')
    from cases import SEEDS, ANGLES, FRAMES
    from graphs import edges, validate_connected_bipartite
    g = edges(case)
    validate_connected_bipartite(g)
    centers = validate_connected_bipartite(g)
    return {
        'case_id': case,
        'seed': SEEDS[case],
        'edges': [list(x) for x in g],
        'frame_radians': list(FRAMES[case]),
        'product_angles_radians': list(ANGLES[case]),
        'color_partitions': [list(c) for c in centers],
        'exact_Z_uniform': True,
        'exact_tv_distance': 0.0
    }


def get_circuit_text(case=0, challenge="sealed", block_name=None):
    """Get circuit as text for a specific block or all blocks."""
    circuits, manifest = make_demo(case, recipe={'audited16': challenge == 'audited16'})
    blocks = demo_blocks(circuits, manifest)
    if block_name:
        aliases = {'sealed': ('target_Z', 'impostor_Z'),
                   'Z': ('target_Z', 'impostor_Z'),
                   'A': ('target_A', 'impostor_A'),
                   'B': ('target_B', 'impostor_B'),
                   'stamp': ('target_A', 'target_B'),
                   'receipt': ('target_A', 'target_B')}
        names = aliases.get(block_name, (block_name,))
        available = {b.name: b for b in blocks}
        reference = ''
        if any(name.endswith('_Z') and name not in available for name in names):
            # audited16 omits Z measurements; show the actual reference circuit
            # with an explicit disclosure rather than an unrelated A/B circuit.
            z_circuits, z_manifest = make_demo(case)
            available.update({b.name: b for b in demo_blocks(z_circuits, z_manifest)})
            reference = 'Z reference circuits only; not measured in the audited16 run.\n\n'
        if any(name not in available for name in names):
            return 'Circuit unavailable for this view. Choose Exhibit Z, A, B or the receipt.'
        return reference + '\n\n'.join(name + '\n' + str(available[name]) for name in names)
    return '\n\n'.join(str(b) for b in blocks)


def get_measurement_meaning():
    """Return the one-line meaning for the side panel."""
    return "Matching Z statistics can hide different correlations in other bases."
