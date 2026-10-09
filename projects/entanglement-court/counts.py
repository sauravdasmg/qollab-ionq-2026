"""Classical count decoding and signed stabilizer parity estimates."""
def normalize_key(key,width):
    if isinstance(key,int):v=key
    else:
        s=str(key).replace(' ','').replace('_','')
        if s.startswith('0b'):s=s[2:]
        v=int(s or '0',2)
    return tuple((v>>i)&1 for i in range(width))
def counts_to_rows(counts,width):
    return [normalize_key(k,width) for k,n in counts.items() for _ in range(int(n))]
def parity_estimates(counts,width,maps):
    rows=counts_to_rows(counts,width)
    if not rows:raise ValueError('empty counts')
    out=[]
    for m in maps:
        vals=[m.get('sign',1)*(-1)**(sum(row[int(m.get('offset',0))+b] for b in m['bits'])%2) for row in rows]
        out.append({'generator':m.get('generator'),'successes':sum(v>0 for v in vals),'shots':len(vals),'estimate':sum(vals)/len(vals),'bits':list(m['bits']),'sign':m.get('sign',1)})
    return out
def block_parities(counts,manifest,block,local=False):
    s=manifest['blocks'][block]
    width=4 if local else manifest['total_width']
    return parity_estimates(counts,width,[dict(m,offset=0 if local else s['offset']) for m in s['parity_maps']])
