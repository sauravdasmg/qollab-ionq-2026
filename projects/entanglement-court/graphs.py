"""Four-qubit connected bipartite graph utilities."""
N=4
_CASES=(((0,1),(1,2),(2,3)),((0,1),(0,2),(0,3)),((0,1),(1,2),(1,3)),((0,1),(0,2),(2,3)))
def edges(case=0): return _CASES[int(case)%len(_CASES)]
def validate_connected_bipartite(edge_list,n=N):
    adj=[set() for _ in range(n)]
    for a,b in edge_list:
        if a==b or not(0<=a<n and 0<=b<n): raise ValueError('invalid edge')
        adj[a].add(b); adj[b].add(a)
    seen={0}; todo=[0]
    while todo:
        u=todo.pop()
        for v in adj[u]-seen: seen.add(v); todo.append(v)
    if len(seen)!=n: raise ValueError('graph must be connected')
    colors={0:0}; todo=[0]
    while todo:
        u=todo.pop()
        for v in adj[u]:
            if v in colors and colors[v]==colors[u]: raise ValueError('graph must be bipartite')
            if v not in colors: colors[v]=1-colors[u]; todo.append(v)
    return tuple(tuple(i for i in range(n) if colors[i]==c) for c in (0,1))
def adjacency(edge_list,n=N):
    a=[[0]*n for _ in range(n)]
    for u,v in edge_list: a[u][v]=a[v][u]=1
    return a
