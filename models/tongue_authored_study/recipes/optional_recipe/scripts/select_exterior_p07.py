import numpy as np, pathlib,json,hashlib,struct
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
D=pathlib.Path(__file__).resolve().parents[1]
z=np.load(D/'reviews/upper-patch-analysis.npz');x=z['positions'].astype(np.float64);f=z['faces'];source=z['faceSource'];
# Geometry-derived contour: averaged vertex normals, not source semantic node names.
fn=np.cross(x[f[:,1]]-x[f[:,0]],x[f[:,2]]-x[f[:,0]]);vn=np.zeros_like(x)
for j in range(3):np.add.at(vn,f[:,j],fn)
vn/=np.maximum(np.linalg.norm(vn,axis=1)[:,None],1e-20);radial=x-np.array([-.005,.690,-.005]);scalar=np.einsum('ij,ij->i',vn,radial)/np.maximum(np.linalg.norm(radial,axis=1),1e-12)
ed=np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ed=np.unique(np.sort(ed,axis=1),axis=0);e=np.vstack([ed,ed[:,::-1]]);adj=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(x),len(x))).tocsr();cnt=np.asarray(adj.sum(1)).ravel()
for _ in range(3):scalar=.5*scalar+.5*(adj@scalar)/cnt
verts=x.tolist();edgevert={};tris=[];origIDs=[];original=[]
def crossing(a,b):
 key=tuple(sorted((int(a),int(b))))
 if key not in edgevert:
  t=scalar[a]/(scalar[a]-scalar[b]);edgevert[key]=len(verts);verts.append(((1-t)*x[a]+t*x[b]).tolist())
 return edgevert[key]
for i,tri in enumerate(f):
 s=scalar[tri]
 if np.all(s>0):tris.append(tri.tolist());origIDs.append(i);original.append(True);continue
 if np.all(s<=0):continue
 out=[]
 for j in range(3):
  a=int(tri[j]);b=int(tri[(j+1)%3]);pa=scalar[a]>0;pb=scalar[b]>0
  if pa:out.append(a)
  if pa!=pb:out.append(crossing(a,b))
 for j in range(1,len(out)-1):tris.append([out[0],out[j],out[j+1]]);origIDs.append(i);original.append(False)
x1=np.array(verts);f1=np.array(tris);oi=np.array(origIDs);orig=np.array(original);edges=np.sort(np.vstack([f1[:,[0,1]],f1[:,[1,2]],f1[:,[2,0]]]),axis=1);fid=np.tile(np.arange(len(f1)),3);sort=np.lexsort((edges[:,1],edges[:,0]));edges=edges[sort];fid=fid[sort];same=np.all(edges[1:]==edges[:-1],axis=1);pairs=np.column_stack([fid[:-1][same],fid[1:][same]]);sp=coo_matrix((np.ones(len(pairs)),(pairs[:,0],pairs[:,1])),shape=(len(f1),len(f1))).tocsr();nc,cc=connected_components(sp,directed=False);cs,cts=np.unique(cc,return_counts=True);comp=cs[np.argmax(cts)];keep=cc==comp;f2=f1[keep];oi=oi[keep];orig=orig[keep];ed2=np.sort(np.vstack([f2[:,[0,1]],f2[:,[1,2]],f2[:,[2,0]]]),axis=1);ee,ec=np.unique(ed2,axis=0,return_counts=True);bd=ee[ec==1];ad={}
for a,b in bd:ad.setdefault(int(a),[]).append(int(b));ad.setdefault(int(b),[]).append(int(a))
assert all(len(v)==2 for v in ad.values()), {k:len(v) for k,v in ad.items() if len(v)!=2}
loops=[];used=set()
for a,b in bd:
 a=int(a);b=int(b)
 if a in used:continue
 loop=[a];prev=a;cur=b
 while cur!=a:
  loop.append(cur);used.add(cur);ns=ad[cur];nxt=ns[0] if ns[0]!=prev else ns[1];prev,cur=cur,nxt
 used.add(a);loops.append(np.array(loop))
loops.sort(key=len,reverse=True)
report={'method':'Three neighbor-averaging iterations on radial-outward vertex-normal score relative to authored interior point [-.005,.690,-.005] m; clip at score 0; retain largest edge-connected component. No deformation of fully retained source triangles. Clipped source triangles are classified as authored seam.','candidateTopTriangles':len(f2),'fullyOriginalTriangles':int(orig.sum()),'clippedTriangles':int((~orig).sum()),'allComponentCounts':sorted(cts.tolist(),reverse=True)[:20],'boundaryLoops':[{'vertices':len(q),'bbox':[x1[q].min(0).tolist(),x1[q].max(0).tolist()]} for q in loops]}
(D/'reviews/prototype-p07-initial-selection.json').write_text(json.dumps(report,indent=2));np.savez(D/'reviews/prototype-p07-initial-selection.npz',positions=x1,faces=f2,originalFaceIDs=oi,isOriginal=orig,sourceFaceGroup=source[oi],**{'loop'+str(i):q for i,q in enumerate(loops)})
print(json.dumps(report,indent=2))
