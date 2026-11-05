import runpy,numpy as np,json,pathlib
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
D=pathlib.Path(__file__).resolve().parents[1]
e=runpy.run_path(str(D/'scripts/inspect_source.py'));parts=e['parts'];xs=[];fs=[];labels=[];off=0
for mi,(name,(x,f,*_)) in enumerate(parts.items()):xs.append(x);fs.append(f+off);labels.extend([mi]*len(f));off+=len(x)
x,inv=np.unique(np.concatenate(xs),axis=0,return_inverse=True);f=inv[np.concatenate(fs)];labels=np.array(labels);norm=np.cross(x[f[:,1]]-x[f[:,0]],x[f[:,2]]-x[f[:,0]]);areas=np.linalg.norm(norm,axis=1);norm/=areas[:,None];keep=norm[:,1]>0
ff=f[keep];ii=np.flatnonzero(keep);ed=np.vstack([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);sp=coo_matrix((np.ones(len(ed)),(ed[:,0],ed[:,1])),shape=(len(x),len(x))).tocsr();n,c=connected_components(sp,directed=False);cs,counts=np.unique(c[ff[:,0]],return_counts=True);order=np.argsort(counts)[::-1];comp=cs[order[0]];sel=ii[c[ff[:,0]]==comp];ff=f[sel];ed=np.sort(np.vstack([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1);eu,ec=np.unique(ed,axis=0,return_counts=True);bd=eu[ec==1];deg=np.bincount(bd.ravel());print('SUMMARY',len(x),len(f),'positive',len(ii),'components',counts[order[:20]],'largest',len(sel),'boundary',len(bd),'boundaryDeg',np.unique(deg[deg>0],return_counts=True))
np.savez(D/'reviews/upper-patch-analysis.npz',positions=x,faces=f,faceSource=labels,upperFaceIDs=sel,boundary=bd)
(D/'reviews/upper-patch-analysis.json').write_text(json.dumps({'sourceMeshOrder':list(parts),'criterion':'face geometric normal native Y > 0, largest connected component; analysis only','allUniqueVertices':len(x),'allFaces':len(f),'positiveYFaces':len(ii),'largestComponentFaces':len(sel),'boundaryEdges':len(bd),'componentFaceCounts':counts[order[:20]].tolist(),'boundaryDegreeHistogram':dict(zip(*[[str(v) for v in np.unique(deg[deg>0])],np.unique(deg[deg>0],return_counts=True)[1].tolist()]))},indent=2))
