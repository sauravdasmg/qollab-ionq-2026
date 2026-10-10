"""Two Whispers Make a Word - runtime entry and shared-helper disclosure.

Shared helpers live in their own files: circuit_pack.py and receipt.py implement
circuit packing, count normalization, backend dispatch and evidence receipts.
Written during Oct 9-11, 2026, with exact UTC provenance and source/license
attribution; used by Two Whispers Make a Word, Never Lose Twice and
Entanglement Court only where the shipped manifest lists the helper.
Project-specific physics, decoding, inference and presentation are described
on each project page.

Qollab calls main() itself after running the module. This module never invokes
main() at import time or under __main__.
"""

import importlib
import numbers

import matplotlib.pyplot as plt

import circuit_pack
import core
import figures
import receipt
import recorded_ionq

EFFECTIVE_MODELS = receipt.EFFECTIVE_MODELS


def _backend():
    backend = globals().get('backend')
    if backend is None:
        from qiskit.providers.basic_provider import BasicSimulator
        return BasicSimulator()
    return backend


def _validate_inputs(case, shots, noise_model):
    if isinstance(case, bool) or not isinstance(case, numbers.Integral) or not 0 <= int(case) <= 28:
        raise ValueError('case must be a frozen integer ID 0..28')
    if isinstance(shots, bool) or not isinstance(shots, numbers.Integral) or int(shots) < 1:
        raise ValueError('shots must be a positive integer')
    if not isinstance(noise_model, str) or noise_model not in EFFECTIVE_MODELS:
        raise ValueError('noise_model must be one of ' + ', '.join(EFFECTIVE_MODELS))


def _load_frozen_recipe():
    """Return a staged development-frozen recipe bundle, or None (untuned)."""
    candidates = (
        ('recipe_bundle', ('RECIPE_BUNDLE', 'RECIPES')),
        ('frozen_recipes', ('RECIPE_BUNDLE', 'RECIPES')),
    )
    for module_name, attributes in candidates:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                continue
            raise
        for attribute in attributes:
            value = getattr(module, attribute, None)
            if isinstance(value, dict):
                return value
        raise ValueError(f'{module_name} must export a frozen recipe dictionary')
    return None


def _recipe_source_note(recipe):
    if recipe is None:
        return ('Frozen synthesis recipe: not staged yet - exact anchor/reference '
                'mode (untuned). No measured extension is claimed before a frozen '
                'recipe and its recorded noisy evidence exist.')
    return 'Frozen synthesis recipe: development-frozen recipes selected.'


def _builtin_branch(backend, circuits, manifest, case, shots, noise_model):
    print('Running: nine small ideal circuits in one built-in list job...', flush=True)
    job = backend.run(circuits, shots=shots)
    print('Waiting: single result fetch...', flush=True)
    result = job.result()
    counts = result.get_counts()
    if not isinstance(counts, list) or len(counts) != len(circuits):
        raise ValueError('built-in list job did not return one histogram per circuit')
    marginals = counts
    if any(sum(m.values()) != shots for m in marginals):
        raise ValueError('built-in marginal total differs from requested shots')
    analysis = core.analyze_counts(marginals, manifest)
    print('Analysed: complete confusion matrices and Wilson intervals.', flush=True)
    return {
        'mode': 'built-in ideal', 'backend': backend.name, 'case': int(case),
        'shots': int(shots), 'noise_model': noise_model, 'noise_used': False,
        'marginals': marginals, 'analysis': analysis,
    }


def _ionq_branch(backend, circuits, manifest, case, shots, noise_model, started):
    print('IonQ mode: packing nine blocks on 21 disjoint wires (<= 25 qubits)...',
          flush=True)
    packed, layout = circuit_pack.pack_circuits(circuits, max_qubits=25)
    offsets = [entry['qubit_offset'] for entry in layout]
    if offsets != manifest['packed_offsets']:
        raise ValueError('packed offsets disagree with the manifested offsets')
    annotated = receipt.annotate_layout(layout, manifest['ordered_blocks'])
    if backend.name == 'ionq_simulator':
        backend.set_options(noise_model=noise_model)
    options = getattr(backend, 'options', None)
    effective = (options.get('noise_model', noise_model) if isinstance(options, dict)
                 else getattr(options, 'noise_model', noise_model))
    if effective not in EFFECTIVE_MODELS:
        raise ValueError('backend reports an unsupported effective noise model')
    noise_model = effective
    print(f'Running: one packed circuit, {shots} shots, noise model {noise_model}...',
          flush=True)
    job = None
    try:
        job = backend.run(packed, shots=shots)
        print('Waiting: single result fetch...', flush=True)
        result = job.result()
        raw = result.get_counts()
        marginals = circuit_pack.unpack_counts(raw, annotated)
        if sum(raw.values()) != shots:
            raise ValueError('packed count total differs from requested shots')
        analysis = core.analyze_counts(marginals, manifest)
    except Exception as exc:
        job_id = receipt.job_identifier(job)
        failure = {
            'schema_version': receipt.SCHEMA_VERSION, 'source': receipt.VALID_SOURCE,
            'status': 'failure', 'attempt_id': job_id or 'unavailable',
            'error': str(exc), 'backend': {'name': backend.name},
            'noise_model': noise_model, 'shots': int(shots), 'case_id': int(case),
            'timestamps': {'started_utc': started, 'ended_utc': receipt._now_utc()},
            'job': {'job_id': job_id, 'available': job_id is not None},
            'environment': {'operator': 'Qollab console'},
            'settings': {'noise_model': noise_model, 'shots': int(shots)},
            'qiskit_version': receipt.qiskit.__version__,
            'parameters': manifest['parameters'],
            'construction_seed': manifest['parameters'].get('seed'),
            'paths': {'source_file': 'results/exports/ionq_console_export.txt',
                      'receipt': 'results/receipts/ionq_case.jsonl',
                      'result': 'results/qollab_ionq_counts.json'},
        }
        print(receipt.format_record(failure), flush=True)
        raise
    ended = receipt._now_utc()
    hashes = {
        'recipe': receipt.hash_recipe(manifest.get('recipe')),
        'circuit': receipt.hash_circuits(circuits),
        'layout': receipt.hash_layout(annotated),
        'manifest': receipt.sha256_hex(manifest),
    }
    uncertainty = {
        'method': 'pointwise Wilson cells; Bonferroni row intervals for mean success',
        'confidence': 0.95,
        'success_interval_95': {
            family: analysis[family]['success_interval_95'] for family in core.FAMILIES},
    }
    assumptions = list(analysis['assumptions'].values())
    assumptions.append(manifest['source_assumptions'])
    assumptions.append(manifest['comparison_scope'])
    record = receipt.build_record(
        case_id=int(case), parameters=manifest['parameters'],
        construction_seed=manifest['parameters'].get('seed'),
        shots=shots, noise_model=noise_model, packed_counts=raw,
        marginals=marginals, layout=annotated, hashes=hashes,
        uncertainty=uncertainty, assumptions=assumptions,
        settings={'noise_model': noise_model, 'backend': backend.name,
                  'shots': shots, 'case': int(case),
                  'recipe_identity': manifest.get('recipe_identity')},
        job_id=receipt.job_identifier(job),
        started_utc=started, ended_utc=ended,
        environment={'operator': 'Qollab console export, pasted into recorded_ionq.py '
                     'by the submission operator'})
    record['manifest'] = manifest
    print(receipt.format_record(record), flush=True)
    return {
        'mode': 'recorded Qollab IonQ', 'backend': backend.name, 'case': int(case),
        'shots': int(shots), 'noise_model': noise_model, 'noise_used': True,
        'packed': packed, 'layout': annotated, 'marginals': marginals,
        'analysis': analysis, 'record': record,
    }


def _print_confusion(analysis):
    for family in core.FAMILIES:
        entry = analysis[family]
        print(f'\nFamily: {family}', flush=True)
        print('  confusion matrix (rows sent label, columns decoded distribution):',
              flush=True)
        for k, row in enumerate(entry['confusion_matrix']):
            cells = ' '.join(f'{p:.4f}' if p is not None else '   -  '
                             for p in row)
            print(f'    sent{k}: {cells}', flush=True)
            intervals = ' '.join(f'[{lo:.4f},{hi:.4f}]' for lo, hi
                                 in entry['confusion_intervals_95'][k])
            print(f'      95% cell intervals: {intervals}', flush=True)
        success = entry['success_probability']
        interval = entry['success_interval_95']
        if success is None:
            print('  success: no counts (zero shots) - null estimate', flush=True)
        else:
            print(f'  success probability {success:.6f}  '
                  f'word error {1 - success:.6f}  '
                  f'95% interval [{interval[0]:.4f}, {interval[1]:.4f}]', flush=True)
        per_label = entry['per_label_error']
        per_intervals = entry['per_label_error_intervals_95']
        print('  per-label error: ' + ', '.join(
            f'label{k} {e:.4f}' if e is not None else f'label{k} n/a'
            for k, e in enumerate(per_label)), flush=True)
        print('  per-label error 95%: ' + ', '.join(
            f'label{k} [{lo:.4f}, {hi:.4f}]' if per_label[k] is not None else f'label{k} n/a'
            for k, (lo, hi) in enumerate(per_intervals)), flush=True)
        print('  unused terminal outcomes (counts; all decoded to fixed label 0): '
              + ', '.join(str(value) for value in entry['unused_outcome_counts']),
              flush=True)
        print('  assignment: ' + entry['unused_outcome_assignment'], flush=True)
        print('  packing note: ' + analysis['assumptions']['packing'], flush=True)


def _print_ceiling_and_bounds(analysis, manifest):
    reference = manifest['reference_probabilities']
    print('\nReference ceilings (mathematical identities, ideal product source):',
          flush=True)
    print(f'  joint collective/textbook success {reference["collective"]:.6f} '
          f'(word error {1 - reference["collective"]:.6f})', flush=True)
    print(f'  optimal one-way sequential success {reference["deferred-sequential"]:.6f} '
          f'(word error {1 - reference["deferred-sequential"]:.6f})', flush=True)
    print('  unrestricted classical two-bit labels transmit all three words '
          'perfectly: error 0.0', flush=True)
    print('  Ideal equivalent syntheses tie by construction; synthesis extension '
          'is carried only by recorded noisy H2 evidence.', flush=True)
    for family in core.FAMILIES:
        estimate = analysis[family]['success_probability']
        interval = analysis[family]['success_interval_95']
        ceiling = reference[family]
        if estimate is None:
            continue
        if estimate > ceiling:
            print(f'  {family}: sample success {estimate:.4f} exceeds the ideal '
                  f'ceiling {ceiling:.4f}; finite shots can cross a theoretical '
                  f'bound - the 95% interval [{interval[0]:.4f}, {interval[1]:.4f}] '
                  f'{"contains" if interval[0] <= ceiling <= interval[1] else "does not contain"} '
                  f'{ceiling:.4f}.', flush=True)
    print('  Comparison scope: ' + manifest['comparison_scope'], flush=True)


def _print_recorded_status(records, statuses):
    print('\nRecorded IonQ evidence:', flush=True)
    if not records:
        print('  No recorded IonQ runs yet', flush=True)
    else:
        for line in receipt.recap(records):
            print('  ' + line, flush=True)
        for record in records:
            if record.get('status', 'success') != 'success':
                continue
            manifest = record.get('manifest')
            if manifest is None:
                print('  Recorded analysis readiness gap: full decoding manifest '
                      'is absent; no synthesis payoff is inferred.', flush=True)
                continue
            print('  Recorded Qollab IonQ analysis derived from included raw counts:',
                  flush=True)
            marginals = circuit_pack.unpack_counts(record['counts']['packed'],
                                                    record['layout'])
            try:
                recorded_analysis = core.analyze_counts(marginals, manifest)
                _print_confusion(recorded_analysis)
                optimized = recorded_analysis['collective']
                textbook = recorded_analysis['textbook']
                if optimized['success_probability'] is not None and textbook['success_probability'] is not None:
                    delta = optimized['success_probability'] - textbook['success_probability']
                    print(f'  Recorded synthesis comparison: collective minus textbook '
                          f'success = {delta:+.6f} probability units. Individual 95% '
                          'intervals appear above; packed correlation prevents an '
                          'independence-based significance claim.', flush=True)
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                print(f'  Recorded analysis readiness gap: {exc}', flush=True)
    for line in receipt.campaign_status(records):
        print('  ' + line, flush=True)
    for status in statuses:
        if not status['ok']:
            print(f"  line {status['line']}: rejected ({status['error']})", flush=True)


def _present(manifest, summary, records, statuses, recipe_note):
    analysis = summary['analysis']
    print('\n==== TWO WHISPERS MAKE A WORD - receiver benchmark ====', flush=True)
    print(f"Mode: {summary['mode']} | case {summary['case']} "
          f"({manifest['case_role']}) | shots {summary['shots']} | "
          f"backend {summary['backend']}", flush=True)
    if summary.get('noise_used'):
        print(f'Noise model (actual effective model): {summary["noise_model"]}',
              flush=True)
    else:
        print('Noise selection ignored on the built-in ideal simulator; '
              f'requested noise_model={summary["noise_model"]}.', flush=True)
    print(recipe_note, flush=True)
    print('Shared helpers: circuit_pack.py, receipt.py (written Oct 9-11 2026, '
          'provenance per project page).', flush=True)
    _print_confusion(analysis)
    _print_ceiling_and_bounds(analysis, manifest)
    _print_recorded_status(records, statuses)
    print('\nFigures: confusion matrices and word-error intervals shown below.',
          flush=True)
    figures.render(analysis, manifest, source=summary['mode'],
                   shots=summary['shots'], backend=summary['backend'],
                   noise_model=summary['noise_model'] if summary['noise_used'] else None)
    plt.show()


def main(case: int = 0, shots: int = 1024, noise_model: str = 'aria-1'):
    """Validate, run the chosen receiver and present ideal plus recorded evidence."""
    started = receipt._now_utc()
    print('Two Whispers Make a Word - receiver benchmark', flush=True)
    _validate_inputs(case, shots, noise_model)
    print('Startup: validating frozen case, shot budget and effective noise '
          'model before any job...', flush=True)
    recipe = _load_frozen_recipe()
    circuits, manifest = core.make_demo(case, recipe)
    print(f'Built {len(circuits)} blocks: case {case} ({manifest["case_role"]}), '
          f'21 qubits across nine blocks.', flush=True)
    backend = _backend()
    if backend.name == 'ionq_simulator':
        summary = _ionq_branch(backend, circuits, manifest, case, shots,
                               noise_model, started)
    else:
        summary = _builtin_branch(backend, circuits, manifest, case, shots,
                                  noise_model)
    records, statuses = receipt.parse_records(recorded_ionq.RECORDED)
    _present(manifest, summary, records, statuses, _recipe_source_note(recipe))
    return summary
