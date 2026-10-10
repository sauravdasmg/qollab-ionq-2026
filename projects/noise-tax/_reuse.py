"""One-time build-window source import; not part of the Qollab upload."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sources = []

def copy(source, target, transform=lambda text: text):
    p = REPO / source
    raw = p.read_bytes()
    text = transform(raw.decode('utf-8-sig'))
    (ROOT / target).write_text(text, encoding='utf-8')
    sources.append({'source': str(p), 'destination': target,
                    'source_sha256': hashlib.sha256(raw).hexdigest(),
                    'destination_sha256_at_import': hashlib.sha256(text.encode()).hexdigest(),
                    'utc': datetime.now(timezone.utc).isoformat()})

def whispers(text):
    text = text[:text.index('def _select_recipe')]
    text = text.replace('from synthesis import haar_su2, validate_recipe, recipe_hash', '')
    # Only the fixed textbook decoder/receivers survive; no synthesis search.
    text = text.replace("    validate_recipe(recipe)\n    return recipe.get('parameters', {})", "    raise ValueError('Noise Tax freezes the textbook recipe; no tuning')")
    text += '''
def haar_su2(seed):
    rng = np.random.default_rng(seed)
    z = (rng.normal(size=(2, 2)) + 1j*rng.normal(size=(2, 2)))/math.sqrt(2)
    q, r = np.linalg.qr(z)
    q = q @ np.diag(np.diag(r)/np.abs(np.diag(r)))
    return q/np.sqrt(np.linalg.det(q))

def make_instance(seed=None):
    frame = np.eye(2, dtype=complex) if seed is None else haar_su2(seed)
    return {'game': 'W', 'seed': seed,
            'frame': [[[float(z.real), float(z.imag)] for z in row] for row in frame]}

def frame_from_spec(spec):
    a = np.asarray(spec['frame'], float)
    return a[:, :, 0] + 1j*a[:, :, 1]

def make_demo(spec=None, include_oneway=False):
    spec = make_instance() if spec is None else spec
    frame = frame_from_spec(spec)
    circuits, blocks = [], []
    for label, state in enumerate(trine_states(frame)):
        for arm in (('joint', 'oneway') if include_oneway else ('joint',)):
            width = 2 if arm == 'joint' else 3
            qc = QuantumCircuit(width, width, name=f'W-{arm}-{label}')
            for signal in (0, 1):
                qc.append(StatePreparation(state), [signal])
            qc.barrier(label='receiver_start')
            if arm == 'joint':
                u, decoder = joint_receiver(frame)
                qc.unitary(u, [0, 1], label='fixed-square-root-receiver')
                unused = [3]
            else:
                first, control, decoder = sequential_receiver(frame)
                qc.unitary(first, [0, 2])
                qc.unitary(control, [0, 1, 2])
                unused = [5, 7]
            qc.measure(range(width), range(width))
            circuits.append(qc)
            blocks.append({'block_name': qc.name, 'arm': arm, 'label': label,
                           'width': width, 'decoder': decoder, 'unused_outcomes': unused})
    return circuits, {'game': 'W', 'specification': spec, 'ordered_blocks': blocks,
                      'reference_success': P_SEQ, 'reference': 'analytic optimal one-way ideal-source bound',
                      'recipe': 'fixed textbook square-root measurement, fourth outcome label 0'}

def analyze_counts(marginals, manifest):
    return analyze_probabilities(marginals, manifest)

def analyze_probabilities(distributions, manifest):
    if len(distributions) != len(manifest['ordered_blocks']):
        raise ValueError('distribution/manifest mismatch')
    rows = {}
    for dist, block in zip(distributions, manifest['ordered_blocks']):
        decoded = [0., 0., 0.]
        for bits, value in dist.items():
            ix = int(str(bits).replace(' ', ''), 2)
            if not 0 <= ix < 2**block['width'] or not math.isfinite(value) or value < 0:
                raise ValueError('invalid distribution')
            decoded[block['decoder'][ix]] += float(value)
        total = sum(decoded)
        if total <= 0:
            raise ValueError('empty distribution')
        rows.setdefault(block['arm'], []).append({'label': block['label'], 'total': total,
                    'decoded': [v/total for v in decoded], 'success': decoded[block['label']]/total})
    out = {}
    for arm, cells in rows.items():
        if sorted(c['label'] for c in cells) != [0, 1, 2]:
            raise ValueError('three equally weighted labels required')
        success = sum(c['success'] for c in cells)/3
        out[arm] = {'success': success, 'word_error': 1-success, 'rows': cells}
    out['advantage'] = P_SEQ - 1 + out['joint']['success'] if 'joint' in out else None
    return out
'''
    return text

def hedging(text):
    text = text.replace('from strategies import', 'from hedging_strategies import')
    text = text.replace('BLOCKS = ("attained_product", "published_hedge", "optimized_joint", "product_control")',
                        'BLOCKS = ("attained_product", "published_hedge")')
    text = text.replace('    start = len(qc.data)', '    qc.barrier(label="strategy_start")\n    start = len(qc.data)')
    text = text.replace('    audit_prover_ownership(qc,start,{2,3})', '    audit_prover_ownership(qc,start,{2,3})\n    qc.barrier(label="verifier_start")')
    text = text.replace('"ordered_blocks":list(BLOCKS),"widths":[4]*4,"offsets":[0,4,8,12],"total_width":16,',
                        '"ordered_blocks":list(BLOCKS),"widths":[4]*2,"offsets":[0,4],"total_width":8,')
    text += '''
def make_instance(seed=None):
    import numpy as np
    rng = np.random.default_rng(seed) if seed is not None else None
    return {'game': 'N', 'seed': seed,
            'alpha': math.pi/4 + (float(rng.uniform(-.04, .04)) if rng else 0.),
            'theta': math.pi/8 + (float(rng.uniform(-.04, .04)) if rng else 0.)}

def make_instance_demo(spec=None):
    spec = make_instance() if spec is None else spec
    circuits, manifest = make_demo(recipe={'alpha': spec['alpha'], 'theta': spec['theta'],
                                          'seed': spec['seed'], 'lambda_star': .02})
    manifest['specification'] = spec
    return circuits, manifest

def analyze_probabilities(distributions, manifest):
    # Use exactly the same projector and fixed prize as the live count decoder.
    out = {}
    if len(distributions) != len(manifest['ordered_blocks']):
        raise ValueError('distribution/manifest mismatch')
    for name, dist, decoder in zip(manifest['ordered_blocks'], distributions, manifest['decoding_maps']):
        probs = dict.fromkeys(('FF', 'FP', 'PF', 'PP'), 0.)
        for bits, value in dist.items():
            ix = int(str(bits).replace(' ', ''), 2)
            if not 0 <= ix < 16 or not math.isfinite(value) or value < 0:
                raise ValueError('invalid distribution')
            status = ''.join('P' if all(not ((ix >> b) & 1) for b in pair) else 'F'
                             for pair in decoder['test_pass_cbits'])
            probs[status] += float(value)
        total = sum(probs.values())
        if total <= 0:
            raise ValueError('empty distribution')
        probs = {k: v/total for k, v in probs.items()}
        mean = probs['FP'] + probs['PF'] + 2*probs['PP']
        out[name] = {'joint_probabilities': probs, 'double_failure': probs['FF'],
                     'mean_passes': mean, 'loss': probs['FF'] + .02*(2-mean)}
    out['advantage'] = out['attained_product']['loss'] - out['published_hedge']['loss']
    return out
'''
    return text

copy('projects/two-whispers/core.py', 'whispers_core.py', whispers)
copy('projects/never-lose-twice/core.py', 'hedging_core.py', hedging)
copy('projects/never-lose-twice/strategies.py', 'hedging_strategies.py')
copy('projects/never-lose-twice/product_bounds.py', 'product_bounds.py')
copy('projects/two-whispers/circuit_pack.py', 'circuit_pack.py')
for source in ('projects/two-whispers/synthesis.py', 'projects/two-whispers/experiments/noise.py',
               'projects/never-lose-twice/experiments/noise.py', 'projects/two-whispers/receipt.py',
               'tools/ionq_noise_params.json', 'tools/qollab_local.py'):
    p = REPO / source
    sources.append({'source': str(p), 'source_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                    'destination': 'adapted algorithm/reference; see REUSE_MANIFEST.md',
                    'utc': datetime.now(timezone.utc).isoformat()})
(ROOT / 'reuse_sources.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
