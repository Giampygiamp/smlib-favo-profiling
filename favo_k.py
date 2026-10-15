"""Favo su sfera con il kernel SMLib diretto (usd-brep). Uso: python favo_k.py [N] [modo]"""
import sys, time, numpy as np
import cell, t4
import _omni_solid as sm
R,SP,MARG=111.0,20.0,8.0
N=int(sys.argv[1]) if len(sys.argv)>1 else 0
modo=sys.argv[2] if len(sys.argv)>2 else 'seq'
celle=[c for c in cell.carica() if c.mean(0)[0]>-MARG and c.mean(0)[2]>-MARG]
if N: celle=celle[:N]
print('celle',len(celle),flush=True)
t0=time.time()
solidi=[]; falliti=0
for k,c in enumerate(celle):
    try: solidi.append(t4.cella_hs(c)[0])
    except RuntimeError: falliti+=1
print('celle non costruite:',falliti)
t1=time.time(); print('costruzione celle %.1f s'%(t1-t0),flush=True)
g=sm.boolean_difference(sm.create_sphere((0,0,0),R),sm.create_sphere((0,0,0),R-SP))
print('guscio',g.volume(),g.face_count(),flush=True)
scart=0; tl=time.time()
for i,s in enumerate(solidi):
    try:
        g2=sm.boolean_difference(g.copy(),s)
        if g2.is_manifold_solid(): g=g2
        else: scart+=1; print('  scartata',i,flush=True)
    except RuntimeError as e:
        scart+=1; print('  errore cella',i,e,flush=True)
    if (i+1)%10==0:
        now=time.time(); print('  %d/%d  +%.2f s  faces=%d'%(i+1,len(solidi),now-tl,g.face_count()),flush=True); tl=now
t2=time.time()
print('tasche %.1f s  scartate %d  volume %.0f  facce %d'%(t2-t1,scart,g.volume(),g.face_count()))
