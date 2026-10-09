"""Matched graph/product demo factory and pure result analysis."""
from graphs import edges,validate_connected_bipartite
from measurements import append_preparation,append_measurement
from counts import block_parities
from witness import simultaneous_witness,two_color_witness
SEEDS=(2026100100,2026100101,2026100102,2026100103)
ANGLES=((.37,.81,1.13,1.71),(.2,.9,1.4,2.1),(.55,1.05,1.65,2.35),(.15,.75,1.25,1.95))
FRAMES=((0.,0.,0.,0.),(1.5707963267948966,-1.5707963267948966,1.5707963267948966,-1.5707963267948966),(3.141592653589793,-1.5707963267948966,0.,1.5707963267948966),(1.5707963267948966,3.141592653589793,-1.5707963267948966,0.))
def _maps(g,color):
    centers=set(validate_connected_bipartite(g)[color]);out=[]
    for i in sorted(centers):
        neighbors=[v for u,v in g if u==i]+[u for u,v in g if v==i]
        out.append({'generator':i,'bits':[i]+neighbors,'sign':1})
    return out
def make_demo(case=0,recipe=None):
    case=int(case)
    if not 0<=case<4:raise ValueError('case must be a frozen manifest ID 0..3')
    recipe=recipe or {}; omit=bool(recipe.get('audited16',False));g=edges(case);validate_connected_bipartite(g)
    names=['target_Z','impostor_Z','target_A','target_B','impostor_A','impostor_B']
    if omit:names=names[2:]
    from qiskit import QuantumCircuit
    width=16 if omit else 24
    qc=QuantumCircuit(width,width);blocks={}
    for j,name in enumerate(names):
        off=4*j; target=name.startswith('target')
        append_preparation(qc,off,g,FRAMES[case],ANGLES[case],'graph' if target else 'product')
        maps=[]
        if name.endswith('_Z'):
            for q in range(4):qc.measure(off+q,off+q)
        else:
            color=0 if name.endswith('_A') else 1
            append_measurement(qc,off,g,FRAMES[case],color);maps=_maps(g,color)
            for q in range(4):qc.measure(off+q,off+q)
        blocks[name]={'offset':off,'width':4,'parity_maps':maps}
    if omit:blocks={k:{**v,'offset':4*i} for i,(k,v) in enumerate(blocks.items())}
    manifest={'case_id':case,'seed':SEEDS[case],'generated_parameters':{'edges':[list(x) for x in g],'frame_radians':list(FRAMES[case]),'product_angles_radians':list(ANGLES[case]),'diagonal_preparation_noise':0.0},'ordered_blocks':names,'blocks':blocks,'total_width':width,'decoding_maps':{k:v['parity_maps'] for k,v in blocks.items()},'source_assumptions':['ideal graph preparation','equatorial product preparation','arbitrary diagonal frame inverse applied before witness basis','declared diagonal preparation noise 0'],'recipe_identity':{'audited16':omit},'exact_Z_reference':omit,'smoke_controls':['impostor_Z','impostor_A','impostor_B']}
    return [qc],manifest
def analyze_counts(marginals,manifest,**options):
    hist=marginals if isinstance(marginals,dict) and all(k in manifest['blocks'] for k in marginals) else {k:marginals for k in manifest['blocks']}
    r={'case_id':manifest['case_id'],'matched_distribution_reference':{'target_Z_uniform':True,'impostor_Z_uniform':True,'exact_total_variation':0.0,'basis':'computational Z'},'blocks':{},'assumptions':manifest['source_assumptions']}
    for name in manifest['blocks']:
        if name.endswith('_Z') or name not in hist:continue
        local=isinstance(marginals,dict) and all(k in manifest['blocks'] for k in marginals)
        r['blocks'][name]=block_parities(hist[name],manifest,name,local=local)
    pars=[]
    for name in ('target_A','target_B'):pars.extend(r['blocks'].get(name,[]))
    if len(pars)>=4:
        args={k:v for k,v in options.items() if k in ('alpha','trusted','bias_bounds')}
        r['simultaneous_witness']=simultaneous_witness(pars,**args);r['two_color_comparator']=two_color_witness(pars,alpha=options.get('alpha',.05),trusted=options.get('trusted',False))
    else:r['simultaneous_witness']={'receipt':'inconclusive; missing generator counts'}
    r['impostor_control']='product preparation is separable; inconclusive witness does not certify separability'
    return r
