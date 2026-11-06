import pathlib,json,numpy as np
D=pathlib.Path(__file__).resolve().parents[1];z=np.load(D/'reviews/prototype-p07-restored-upper.npz');x=z['positions'];f=z['faces'];sf=z['originalFaceIDs'];orig=z['isOriginal'];sg=z['sourceFaceGroup'];scalar=x[:,1]-(.696+(-.02-x[:,2])*.035);vs=x.tolist();es={};fs=[];ss=[];oo=[];gg=[]
def ix(a,b):
 k=tuple(sorted((int(a),int(b))))
 if k not in es:
  t=scalar[a]/(scalar[a]-scalar[b]);es[k]=len(vs);vs.append(((1-t)*x[a]+t*x[b]).tolist())
 return es[k]
for i,tri in enumerate(f):
 if np.all(scalar[tri]>0):fs.append(tri.tolist());ss.append(sf[i]);oo.append(orig[i]);gg.append(sg[i]);continue
 if np.all(scalar[tri]<=0):continue
 p=[]
 for j in range(3):
  a=int(tri[j]);b=int(tri[(j+1)%3]);sa=scalar[a]>0;sb=scalar[b]>0
  if sa:p.append(a)
  if sa!=sb:p.append(ix(a,b))
 for j in range(1,len(p)-1):fs.append([p[0],p[j],p[j+1]]);ss.append(sf[i]);oo.append(False);gg.append(sg[i])
x=np.array(vs);f=np.array(fs);edges=np.sort(np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);ed,c=np.unique(edges,axis=0,return_counts=True);bd=ed[c==1];adj={}
for a,b in bd:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
assert all(len(q)==2 for q in adj.values())
loops=[];seen=set()
for a in adj:
 if a in seen:continue
 q=[a];pr=a;cu=adj[a][0]
 while cu!=a:
  q.append(cu);seen.add(cu);ns=adj[cu];pr,cu=cu,ns[0] if ns[0]!=pr else ns[1]
 seen.add(a);loops.append(np.array(q))
loops.sort(key=len,reverse=True);np.savez(D/'reviews/prototype-p07-upper-selection.npz',positions=x,faces=f,originalFaceIDs=np.array(ss),isOriginal=np.array(oo),sourceFaceGroup=np.array(gg),**{'loop'+str(i):q for i,q in enumerate(loops)})
(D/'reviews/prototype-p07-upper-selection.json').write_text(json.dumps({'method':'Further clip external-dorsal selection at authored lateral join plane native Y = 0.696 + (-0.020-Z)*0.035 metres. This is an author-chosen seam, not an anatomical boundary. Removes low lateral/posterior return regions; fully retained source triangle coordinates unchanged.','faces':len(f),'originalTriangles':int(np.sum(oo)),'boundaryLoops':[{'count':len(q),'bbox':[x[q].min(0).tolist(),x[q].max(0).tolist()]} for q in loops]},indent=2));print(len(f),[len(q) for q in loops])
