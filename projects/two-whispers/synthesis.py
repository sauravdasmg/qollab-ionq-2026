"""Development-only bounded synthesis and frozen JSON receiver recipes.

Full development: eight frames, seeds 2026100900..2026100907, exactly 128
candidate evaluations per family across development frames. No runtime search.
"""
import hashlib
import json
import math
import numbers
import numpy as np

FAMILIES = ('collective', 'textbook', 'deferred-sequential')
DEVELOPMENT_SEEDS = tuple(range(2026100900, 2026100908))
FULL_BUDGET = 128


def haar_su2(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = (rng.normal(size=(2,2))+1j*rng.normal(size=(2,2)))/math.sqrt(2)
    q,r = np.linalg.qr(z)
    q = q @ np.diag(np.diag(r)/np.abs(np.diag(r)))
    return q/np.sqrt(np.linalg.det(q))


def validate_recipe(recipe):
    if not isinstance(recipe, dict) or not isinstance(recipe.get('parameters', {}), dict):
        raise ValueError('recipe must be an object with parameter object')
    if 'families' in recipe:
        if not isinstance(recipe['families'], dict) or set(recipe['families'])-set(FAMILIES):
            raise ValueError('invalid family bundle')
        for family, member in recipe['families'].items():
            validate_recipe(member)
            if member.get('family', family) != family:
                raise ValueError('recipe family mismatch')
    if recipe.get('family', 'collective') not in FAMILIES:
        raise ValueError('unknown receiver family')
    p = recipe.get('parameters', {})
    if set(p)-{'relabel','row_phase','row_phases','completion_phase','optimization_level','compiler_seed','decomposition'}:
        raise ValueError('unsupported recipe parameter')
    for key, low, high in (('relabel',0,5),('optimization_level',0,1),('compiler_seed',0,2**32-1)):
        value = p.get(key, low)
        if isinstance(value,bool) or not isinstance(value,numbers.Integral) or not low <= value <= high:
            raise ValueError('invalid '+key)
    phases = p.get('row_phases', [p.get('row_phase',0.0)]*4)
    if not isinstance(phases,(list,tuple)) or len(phases) != 4:
        raise ValueError('row_phases needs four real phases')
    for phase in list(phases)+[p.get('completion_phase',0.0)]:
        if isinstance(phase,bool) or not isinstance(phase,numbers.Real) or not math.isfinite(phase):
            raise ValueError('invalid phase')
    if p.get('decomposition','default') not in ('default','standard'):
        raise ValueError('unsupported decomposition')
    try:
        json.dumps(recipe, allow_nan=False)
    except (TypeError,ValueError) as exc:
        raise ValueError('recipe must contain finite JSON values') from exc
    return recipe


def recipe_hash(recipe):
    return hashlib.sha256(json.dumps(recipe,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def bounded_search(objective, *, budget=8, seed=2026100900, family='collective'):
    """Exactly budget calls, maximize objective; candidate zero is untuned.

    Textbook receives standard decomposition, compiler seeds/levels and the same
    fixed measurement, without phase/relabel freedom. The caller compiles/evaluates each
    candidate once using identical noise settings and shot budgets.
    """
    if isinstance(budget,bool) or not isinstance(budget,int) or not 1 <= budget <= FULL_BUDGET:
        raise ValueError('budget must be an integer in 1..128')
    if family not in FAMILIES:
        raise ValueError('unknown family')
    rng = np.random.default_rng(seed)
    tried = []
    for i in range(budget):
        params = {'relabel':int(rng.integers(6)), 'row_phases':rng.uniform(-math.pi,math.pi,4).tolist(),
                  'completion_phase':float(rng.uniform(-math.pi,math.pi)),
                  'optimization_level':1, 'compiler_seed':int(rng.integers(2**31)),
                  'decomposition':'standard' if family == 'textbook' and i%2 else 'default'}
        if family == 'textbook':
            params.update(relabel=0, row_phases=[0.0]*4, completion_phase=0.0)
        if i == 0:
            params.update(relabel=0,row_phases=[0.0]*4,completion_phase=0.0,
                          optimization_level=1,compiler_seed=0,decomposition='default')
        recipe = {'family':family,'parameters':params,'identity':f'{family}-{seed}-{i}'}
        validate_recipe(recipe)
        value = float(objective(recipe))
        if not math.isfinite(value):
            raise ValueError('objective must be finite')
        tried.append({'recipe':recipe,'objective':value})
    return {'best':max(tried,key=lambda c:c['objective']), 'untuned_reference':tried[0],
            'evaluations':len(tried),'candidates':tried,'seed':seed,'family':family,
            'budget':budget,'objective_direction':'maximize'}


def equal_budget_search(objectives, *, budget=FULL_BUDGET, seed=2026100900):
    """One development frame; objectives must share settings and shot budget."""
    if seed not in DEVELOPMENT_SEEDS:
        raise ValueError('equal-budget tuning is restricted to predeclared development seeds')
    if set(objectives) != set(FAMILIES):
        raise ValueError('provide objectives for all three families')
    searches = {f:bounded_search(objectives[f],budget=budget,seed=seed,family=f) for f in FAMILIES}
    bundle = {'identity':f'frozen-{seed}-budget{budget}',
              'families':{f:searches[f]['best']['recipe'] for f in FAMILIES}}
    return {'searches':searches,'recipe':bundle,'settings':{'budget_per_family':budget,'seed':seed},
            'decisive_comparator':'best budget-matched textbook','held_out_tuning':False}


def export_recipe(recipe, path=None):
    validate_recipe(recipe)
    data = json.dumps(recipe,sort_keys=True,separators=(',',':'),allow_nan=False)
    if path is not None:
        with open(path,'w',encoding='utf-8') as stream:
            stream.write(data+'\n')
    return data


def import_recipe(source):
    try:
        if isinstance(source,str) and source.lstrip().startswith('{'):
            data = json.loads(source)
        else:
            with open(source,encoding='utf-8') as stream:
                data = json.load(stream)
        return validate_recipe(data)
    except (OSError,ValueError,TypeError) as exc:
        raise ValueError(f'invalid recipe: {exc}') from exc


def verify_equivalence(case, family, recipe, circuits=None, manifest=None):
    """Check unitaries and every terminal probability after record relabeling."""
    import core
    from qiskit.quantum_info import Statevector
    frame, _ = core._frame_for_case(case)
    if family == 'deferred-sequential':
        first, control, _ = core.sequential_receiver(frame, recipe)
        unitaries = [first, control]
    else:
        unitaries = [core.joint_unitary(frame, recipe)]
    residual = max(float(np.max(np.abs(u.conj().T@u-np.eye(len(u))))) for u in unitaries)
    if residual > 1e-10:
        raise ValueError('candidate unitary residual exceeds 1e-10')
    if circuits is None:
        circuits, manifest = core.make_demo(case, recipe)
    reference, ref_manifest = core.make_demo(case)
    permutation = list(core._permutation(recipe['parameters'])) + [3]
    deviation = 0.0
    for circuit, ref, block in zip(circuits, reference, manifest['ordered_blocks']):
        if block['family'] != family:
            continue
        actual = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False)).probabilities()
        expected = Statevector.from_instruction(ref.remove_final_measurements(inplace=False)).probabilities()
        aligned = np.zeros_like(actual)
        for ix, probability in enumerate(actual):
            if family == 'deferred-sequential':
                m = (ix & 1) + 2*((ix >> 2) & 1)
                original = permutation[m]
                target = (original & 1) + (ix & 2) + 4*(original >> 1)
            else:
                target = permutation[ix]
            aligned[target] = probability
        deviation = max(deviation, float(np.max(np.abs(aligned-expected))),
                        float(abs(actual.sum()-1)))
    if deviation > 1e-10:
        raise ValueError('candidate ideal probabilities differ by more than 1e-10')
    return {'unitary_residual': residual, 'probability_residual': deviation}


def development_search(*, budget=FULL_BUDGET, cases=tuple(range(1, 9)),
                       seed=DEVELOPMENT_SEEDS[0], model='aria', scale=1.0,
                       source_noise=True, output_dir=None):
    """Freeze one common recipe per family using mean exact development success.

    Exactly budget candidates per family, each scored on the SAME development
    frames, channel and compilation. Ties keep the earliest candidate. Neither
    held-out observations nor orientation-specific noise tuning enter selection.
    Full runs belong to the orchestrator; callers can request tiny test settings.
    """
    import core
    import time
    from pathlib import Path
    from datetime import datetime, timezone
    from experiments.run import _density_probabilities
    from experiments import noise
    if not cases or len(set(cases)) != len(cases) or any(c not in range(1, 9) for c in cases):
        raise ValueError('search is restricted to development cases 1..8')
    start = time.monotonic()
    cpu_start = time.process_time()
    evidence = {family: [] for family in FAMILIES}
    costs = {family: {'source_operations': 0, 'receiver_operations': 0,
                      'compiled_operations': 0, 'candidate_seconds': []} for family in FAMILIES}
    def objective(family):
        def evaluate(recipe):
            tick = time.monotonic()
            successes, checks = [], []
            for case in cases:
                circuits, manifest = core.make_demo(case, recipe)
                checks.append(verify_equivalence(case, family, recipe, circuits, manifest))
                for circuit, block in zip(circuits, manifest['ordered_blocks']):
                    if block['family'] != family:
                        continue
                    probs = _density_probabilities(circuit, model, scale, source_noise=source_noise)
                    successes.append(sum(p for bits, p in probs.items()
                                         if block['decoder'][int(bits, 2)] == block['label']))
                    costs[family]['source_operations'] += block['source_gate_count']
                    costs[family]['receiver_operations'] += block['receiver_gate_count']
                    costs[family]['compiled_operations'] += len(noise.compile_circuit(circuit, model).data)
            costs[family]['candidate_seconds'].append(time.monotonic()-tick)
            evidence[family].append({'identity': recipe['identity'], 'checks': checks,
                                     'success_per_block': successes})
            return float(np.mean(successes))
        return evaluate
    result = equal_budget_search({f: objective(f) for f in FAMILIES}, budget=budget, seed=seed)
    settings = {'development_cases': list(cases), 'development_seeds': [core.CASE_SEEDS[c] for c in cases],
                'budget_per_family': budget, 'seed': seed, 'model': model, 'scale': scale,
                'source_noise': source_noise, 'noise': noise.effective_config(model, scale),
                'selection_rule': 'maximize equal-prior mean exact success over development cases; earliest candidate wins ties',
                'compiler': 'recipe: level 1, rx/ry/rz/cx; channel compiler: calibrated basis, level 1, seed 1234',
                'textbook_variants': 'standard/default decompositions and compiler seeds; no phase or relabel search',
                'full_budget_completed': budget == FULL_BUDGET and tuple(cases) == tuple(range(1, 9))}
    result['settings'] = settings
    result['verification'] = evidence
    result['cost_accounting'] = costs
    result['elapsed_seconds'] = time.monotonic()-start
    result['cpu_seconds'] = time.process_time()-cpu_start
    result['cost_accounting_note'] = ('Candidate trials count per family, not per label/frame; '
        'all frames and three labels use exact probabilities, without shot draws. '
        'Operation totals charge sources separately from receivers; elapsed/CPU time includes '
        'reference equivalence checks and construction of unused demo-family blocks.')
    result['utc_finished'] = datetime.now(timezone.utc).isoformat()
    result['recipe']['selection'] = settings
    result['recipe']['identity'] = 'development-selection-' + recipe_hash(result['recipe'])[:16]
    result['recipe_hash'] = recipe_hash(result['recipe'])
    result['h2_development_margin'] = .9*(1-result['searches']['textbook']['best']['objective']) - (1-result['searches']['collective']['best']['objective'])
    if output_dir is not None:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        # Exclusive writes prevent replacing a previously frozen selection.
        for name, value in (('recipe.json', result['recipe']), ('search.json', result)):
            with (directory/name).open('x', encoding='utf-8') as stream:
                json.dump(value, stream, indent=2, allow_nan=False)
    return result


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description='Development-only equal-budget synthesis; full runs are orchestrator-invoked')
    p.add_argument('--budget', type=int, default=FULL_BUDGET)
    p.add_argument('--cases', type=int, nargs='+', default=list(range(1, 9)))
    p.add_argument('--output-dir', required=True)
    p.add_argument('--model', choices=('aria', 'forte', 'fe'), default='aria')
    p.add_argument('--source-noise', action=argparse.BooleanOptionalAction, default=True)
    args = p.parse_args(argv)
    return development_search(budget=args.budget, cases=tuple(args.cases),
                              output_dir=args.output_dir, model=args.model, source_noise=args.source_noise)


if __name__ == '__main__':
    main()
