"""Bounded ideal demo and single-job injected IonQ capture; no import-time run."""
import json
import platform
import time
import qiskit
from cases import make_demo, analyze_counts
from circuit_pack import demo_blocks, pack_circuits, unpack_counts, normalize_counts, digest, circuit_hash, circuit_description
from receipt import load_records, utc_now, emit_record, MODELS
from figures import present, parity_interval, ASSUMPTIONS
from campaign import build_slot


def _effective_model(active):
    options = getattr(active, 'options', None)
    model = options.get('noise_model') if isinstance(options, dict) else getattr(options, 'noise_model', None)
    if isinstance(model, dict):
        model = model.get('model') or model.get('name')
    if model not in MODELS:
        raise ValueError('actual effective IonQ noise_model must be aria-1, forte-1 or forte-enterprise-1')
    return model


def main(case: int=0, shots: int=200, challenge: str="sealed", assume_trusted_measurements: bool=False, slot: str=""):
    run_started = time.perf_counter()
    if type(slot) is not str: raise ValueError("slot must be a string")
    campaign_row = None
    if type(case) is not int or case not in range(4):
        raise ValueError('case must be a frozen ID 0..3')
    if type(shots) is not int or not 1 <= shots <= 10000:
        raise ValueError('shots must be an integer 1..10000')
    if challenge not in ('sealed', 'anchor', 'audited16'):
        raise ValueError('challenge must be sealed, anchor or audited16')
    if type(assume_trusted_measurements) is not bool:
        raise ValueError('trust flag must be bool')
    print('Opening courtroom docket: exact anchor/reference mode.', flush=True)
    records, statuses = load_records()
    for status in statuses:
        print(status, flush=True)
    if slot:
        active_name = getattr(globals().get('backend'), 'name', '')
        if callable(active_name): active_name = active_name()
        circuits, manifest, campaign_row = build_slot(slot, include_z=not str(active_name).startswith('ionq'))
        case = manifest['case_id']
        challenge = 'campaign'
    else:
        circuits, manifest = make_demo(case, recipe={'audited16': challenge == 'audited16'})
    manifest['shared_helpers'] = ['circuit_pack.py', 'receipt.py']
    blocks = circuits if campaign_row else demo_blocks(circuits, manifest)
    packed, layout = pack_circuits(blocks, max_qubits=32 if campaign_row and not manifest["dropped_Z_exhibits"] else 25)
    active = globals().get('backend')
    if active is None:
        from qiskit.providers.basic_provider import BasicSimulator
        active = BasicSimulator()
    name = getattr(active, 'name', '')
    if callable(name):
        name = name()
    ionq = isinstance(name, str) and name.startswith('ionq')
    if ionq and name != 'ionq_simulator':
        raise ValueError('only the injected IonQ simulator is supported')
    if campaign_row and ionq:
        setter = getattr(active, 'set_options', None)
        if callable(setter): setter(noise_model='aria-1')
    effective = _effective_model(active) if ionq else None
    if campaign_row and shots != 200:
        raise ValueError('preregistered campaign slots require exactly 200 shots')
    if campaign_row and ionq and effective != 'aria-1':
        raise ValueError('campaign slots require the injected aria-1 noise model')
    if ionq and challenge == 'audited16':
        raise ValueError('Readiness gap: 16-wire cloud fallback requires saved Z references and the C27 smoke audit; neither is staged. Use the 24-wire anchor.')
    started = utc_now()
    assumptions = list(manifest['source_assumptions']) + [ASSUMPTIONS,
        'Packed blocks share one execution, not independent generated instances.',
        ('Preregistered campaign slot ' + slot if campaign_row else 'Anchor demonstration is separate from the recorded campaign; see loaded record status and deviations.')]
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
    if campaign_row:
        record.update(slot=slot, prep_noise=manifest['prep_noise'], prep_noise_per_wire_p=manifest['prep_noise_per_wire_p'])
    print('Running ' + ('one packed IonQ circuit' if ionq else str(len(blocks)) + ' tiny built-in circuits in one list job') + '.', flush=True)
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
        print('Analyzing cached counts; no further backend requests.', flush=True)
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
            emit_record(record)
        print('Terminal execution error: ' + str(exc) + '; no automatic resubmission.', flush=True)
        raise
    if ionq:
        emit_record(record)
    if campaign_row:
        campaign_record = {'slot':slot, 'suite':campaign_row['suite'], 'case_id':campaign_row['case_id'], 'stratum':campaign_row['stratum'], 'manifest_hash':campaign_row['manifest_hash'], 'shots':shots, 'noise_model':effective or 'ideal', 'prep_noise':manifest['prep_noise'], 'prep_noise_per_wire_p':manifest['prep_noise_per_wire_p'], 'max_qubits':packed.num_qubits}
        print('Campaign verdict: ' + str(analysis.get('simultaneous_witness',{}).get('receipt','inconclusive')) + ' (conditional on trusted ideal rotations/readout).', flush=True)
        print('RECORD_JSON ' + json.dumps(campaign_record, sort_keys=True), flush=True)
    source = ('Live Qollab IonQ simulator | ' + effective + ' | UTC ' + record['utc_end']) if ionq else 'Live built-in ideal'
    present(marginals, analysis, source, shots, assume_trusted_measurements)
    for saved in ([] if campaign_row else records):
        if saved['error']:
            continue
        saved_manifest = saved['settings'].get('manifest')
        if not saved_manifest:
            print('Recorded entry lacks core manifest; cannot derive project summary.', flush=True)
            continue
        derived = unpack_counts(saved['raw_counts'], saved['layout'])
        saved_trust = saved['settings'].get('assume_trusted_measurements', False)
        summary = analyze_counts(derived, saved_manifest, trusted=saved_trust)
        present(derived, summary, 'Recorded Qollab IonQ | ' + saved['backend'] + ' | ' + saved['noise_model'] + ' | UTC ' + saved['utc_end'], saved['shots'], saved_trust)
    elapsed = time.perf_counter() - run_started
    print('Run runtime: {:.2f} s ({}; includes analysis and displayed exhibits).'.format(
        elapsed, 'LIVE Qollab IonQ' if ionq else 'LIVE built-in simulator'), flush=True)
    return {'manifest': manifest, 'layout': layout, 'marginals': marginals, 'analysis': analysis, 'record': record if ionq else None, 'runtime_seconds': elapsed}
