"""Development-only bounded synthesis and frozen JSON receiver recipes.

Full development: eight frames, seeds 2026100900..2026100907, exactly 128
objective/compiler calls per family/frame. No runtime search or noise evidence.
"""
from __future__ import annotations
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
    phase/relabel freedom as collective. The caller compiles/evaluates each
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
                  'optimization_level':i%2, 'compiler_seed':int(rng.integers(2**31)),
                  'decomposition':'standard' if family == 'textbook' and i%2 else 'default'}
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
