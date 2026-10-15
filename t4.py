import cell, numpy as np, time
import _omni_solid as sm
L=400.0
def slab(n,d):
    n=np.asarray(n,float); n/=np.linalg.norm(n)
    a=np.cross(n,[1,0,0])
    if np.linalg.norm(a)<1e-6: a=np.cross(n,[0,1,0])
    a/=np.linalg.norm(a); b=np.cross(n,a)
    bx=sm.create_box((-L/2,-L/2,-L),L,L,L)
    p=-d*n
    return sm.transform(bx, sm.Axis2Placement(tuple(p),tuple(a),tuple(b)))
def cella_hs(pts):
    h=cell.ConvexHull(pts); seen=[]
    for eq in h.equations:
        n,d=eq[:3],eq[3]
        if any(np.linalg.norm(n-m)<1e-4 and abs(d-dd)<1e-3 for m,dd in seen): continue
        seen.append((n,d))
    cur=slab(*seen[0])
    for n,d in seen[1:]:
        cur=sm.boolean_intersection(cur,slab(n,d))
    return cur,len(seen)
if __name__=='__main__':
    c=cell.carica()[0]
    t=time.time(); b,nf=cella_hs(c)
    print(nf,'planes ->',b.face_count(),b.vertex_count(),b.volume(),b.is_manifold_solid(),time.time()-t)
    print('hull volume',cell.ConvexHull(c).volume)
