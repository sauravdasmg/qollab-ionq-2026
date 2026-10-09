"""One-sided Clopper-Pearson bounds and graph fidelity witness."""
from scipy.stats import beta
def cp_lower(successes,shots,alpha):
    if shots<=0 or not 0<=successes<=shots:raise ValueError('invalid binomial counts')
    if successes==0:return 0.0
    if successes==shots:return float(alpha**(1/shots))
    return float(beta.ppf(alpha,successes,shots-successes+1))
def allocate_alpha(alpha=.05,generators=4,preparations=2):
    if not 0<alpha<1 or generators<=0 or preparations<=0:raise ValueError('invalid alpha allocation')
    return alpha/(generators*preparations)
def simultaneous_witness(parities,alpha=.05,graph_connected=True,trusted=False,bias_bounds=None):
    n=len(parities); a=allocate_alpha(alpha,n,2); biases=bias_bounds or [0.]*n
    if len(biases)!=n:raise ValueError('bias bound length mismatch')
    terms=[]
    for i,(p,d) in enumerate(zip(parities,biases)):
        lo=cp_lower(int(p['successes']),int(p['shots']),a)
        est=2*int(p['successes'])/int(p['shots'])-1
        terms.append({'index':i,'estimate':est,'p_lower':lo,'L_lower':max(-1.,2*lo-1-2*float(d)),'bias_bound':float(d)})
    f=1-sum(1-t['L_lower'] for t in terms)/2
    yes=bool(graph_connected and f>.5)
    receipt=('conditional certificate under ideal/trusted rotations and readout; measurement systematic error unbounded' if yes and not trusted else ('conditional GME witness' if yes else 'inconclusive; this witness does not prove separability'))
    return {'alpha_round':alpha,'per_generator_alpha':a,'terms':terms,'F_lower':f,'threshold':.5,'conditional_gme':yes,'receipt':receipt,'trust_flag':bool(trusted),'scope':'per two-preparation round; shared histograms use union bound; no independence required'}
def two_color_witness(parities,alpha=.05,trusted=False):return simultaneous_witness(parities,alpha,trusted=trusted)
def biseparable_overlap_bound(edge_list):
    from graphs import validate_connected_bipartite
    validate_connected_bipartite(edge_list);return .5
