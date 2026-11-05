import json,struct,pathlib,numpy as np,hashlib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=pathlib.Path(__file__).resolve().parents[1];p=D/'source/tongue-surfaces-hra-female-r02.glb';r=p.read_bytes();n=struct.unpack_from('<I',r,12)[0];g=json.loads(r[20:20+n]);b=r[28+n:]
def arr(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];k={'SCALAR':1,'VEC3':3,'VEC2':2}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];return np.ndarray((a['count'],k),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy()
parts={};report=[]
for m in g['meshes']:
 pr=m['primitives'][0];x=arr(pr['attributes']['POSITION']);ids=arr(pr['indices']).reshape(-1,3);u,inv=np.unique(x,axis=0,return_inverse=True);f=inv[ids];edges=np.sort(np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);e,c=np.unique(edges,axis=0,return_counts=True);bd=e[c==1];adj={}
 for a,b0 in bd:adj.setdefault(int(a),[]).append(int(b0));adj.setdefault(int(b0),[]).append(int(a))
 loops=[];used=set()
 for a,b0 in bd:
  edge=tuple(sorted((int(a),int(b0))))
  if edge in used:continue
  loop=[int(a),int(b0)];used.add(edge);last=int(a);cur=int(b0)
  for _ in range(len(bd)+1):
   ns=[z for z in adj[cur] if z!=last]
   if not ns:break
   z=ns[0];edge=tuple(sorted((cur,z)))
   if edge in used:break
   used.add(edge);loop.append(z);last,cur=cur,z
  loops.append(loop)
 parts[m['name']]=(u,f,bd,loops)
 report.append({'name':m['name'],'uniqueVertices':len(u),'faces':len(f),'boundaryEdges':len(bd),'nonTwoEdges':int((c!=2).sum()),'boundaryDegrees':{str(k):sum(len(v)==k for v in adj.values()) for k in set(map(len,adj.values()))},'loops':[{'vertices':len(q),'closed':q[0]==q[-1],'bounds':[u[q].min(0).tolist(),u[q].max(0).tolist()]} for q in loops]})
(D/'reviews/source-boundaries.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(r).hexdigest(),'parts':report},indent=2))
fig,axes=plt.subplots(2,3,figsize=(15,9));zs=[-.025,-.015,-.005,.005,.015,.025]
for ax,z in zip(axes.flat,zs):
 for name,(u,*_) in parts.items():
  a=u[np.abs(u[:,2]-z)<.0006];ax.scatter(a[:,0]*1000,a[:,1]*1000,s=1,label=name.replace('VH_F_',''))
 ax.set_title(f'native Z = {z*1000:.0f} +/- 0.6 mm');ax.set_aspect('equal');ax.set_xlabel('native X mm');ax.set_ylabel('native up Y mm')
axes[0,0].legend(fontsize=6);fig.suptitle('Read-only source slices; native coordinates, not anatomical measurements');fig.tight_layout();fig.savefig(D/'reviews/source-cross-sections.png',dpi=130)
print(json.dumps(report,indent=2))
