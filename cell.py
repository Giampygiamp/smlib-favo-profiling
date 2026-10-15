import numpy as np, sys
sys.path.insert(0, '.')
import _omni_solid as sm
from scipy.spatial import ConvexHull

def carica(path='favo_cells.txt'):
    out=[]
    for r in open(path):
        r=r.strip()
        if r: out.append(np.array([[float(v) for v in p.split()] for p in r.rstrip(';').split(';')]))
    return out

def facce(pts, tol=1e-4):
    h=ConvexHull(pts); g=[]
    for s,eq in zip(h.simplices,h.equations):
        n,d=eq[:3],eq[3]
        for x in g:
            if np.linalg.norm(x[0]-n)<tol and abs(x[1]-d)<tol*10: x[2].update(s.tolist()); break
        else: g.append([n.copy(),d,set(s.tolist())])
    res=[]
    for n,d,idx in g:
        P=pts[sorted(idx)]; c=P.mean(0)
        u=np.cross(n,[1,0,0]); 
        if np.linalg.norm(u)<1e-6: u=np.cross(n,[0,1,0])
        u/=np.linalg.norm(u); v=np.cross(n,u)
        a=np.arctan2((P-c)@v,(P-c)@u); res.append(P[np.argsort(a)])
    return res

def cella(pts):
    sheets=[]
    for F in facce(pts):
        P=[tuple(map(float,p)) for p in F]
        segs=[sm.create_line_segment(P[i],P[(i+1)%len(P)]) for i in range(len(P))]
        sheets.append(sm.create_planar_faces(segs))
    m=sheets[0]
    for s in sheets[1:]:
        m=sm.boolean_merge(m,s)
    b,ok,n,vg,eg=sm.stitch_into_solid(m)
    return b,ok
