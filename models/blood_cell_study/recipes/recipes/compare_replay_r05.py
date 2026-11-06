import pathlib,json,struct,numpy as np,hashlib
D=pathlib.Path(__file__).resolve().parents[1];paths=[D/'models/blood-cell-authored-study-r05.glb',D/'replay-r05/models/blood-cell-authored-study-r05.glb']
def read(p):
 b=p.read_bytes();o=12;c={}
 while o<len(b):n,k=struct.unpack_from('<II',b,o);c[k]=b[o+8:o+8+n];o+=8+n
 j=json.loads(c[0x4e4f534a]);raw=c[0x004e4942]
 def a(i):
  x=j['accessors'][i];v=j['bufferViews'][x['bufferView']];typ=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[x['componentType']]);dim={'VEC3':3,'SCALAR':1}[x['type']];s=v.get('byteOffset',0)+x.get('byteOffset',0);return np.ndarray((x['count'],dim),dtype=typ,buffer=raw,offset=s,strides=(v.get('byteStride',typ.itemsize*dim),typ.itemsize)).copy()
 out={}
 for node in j['nodes']:
  if 'mesh' not in node:continue
  ts=[];ns=[];unique=[]
  for pr in j['meshes'][node['mesh']]['primitives']:
   v=a(pr['attributes']['POSITION']);n=a(pr['attributes']['NORMAL']);ff=a(pr['indices']).reshape(-1,3);unique.append(v);t=v[ff];nn=n[ff];order=np.lexsort((t[:,:,2],t[:,:,1],t[:,:,0]),axis=1);ts.append(np.take_along_axis(t,order[:,:,None],axis=1).reshape(-1,9));ns.append(np.take_along_axis(nn,order[:,:,None],axis=1).reshape(-1,9))
  t=np.vstack(ts);n=np.vstack(ns);order=np.lexsort(tuple(t[:,i] for i in range(8,-1,-1)));out[node['name']]={'positions':np.unique(np.vstack(unique),axis=0),'triangles':t[order],'normals':n[order]}
 return j,out
(j1,x),(j2,y)=[read(p) for p in paths];rows=[]
for name in x:
 a,b=x[name],y[name];row={'node':name,'exactUniquePositionsEqual':bool(np.array_equal(a['positions'],b['positions'])),'exactTriangleCoordinateMultisetEqual':bool(np.array_equal(a['triangles'],b['triangles'])),'exactCorrespondingCornerNormalsEqual':bool(np.array_equal(a['normals'],b['normals'])),'maxCorrespondingNormalVectorDifference':float(np.linalg.norm((a['normals']-b['normals']).reshape(-1,3),axis=1).max())};rows.append(row)
r={'finalSha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'replaySha256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),'bytesIdentical':paths[0].read_bytes()==paths[1].read_bytes(),'nodesTransformsExtrasEqual':j1['nodes']==j2['nodes'],'materialsEqual':j1['materials']==j2['materials'],'allExactUniquePositionSetsEqual':all(r['exactUniquePositionsEqual'] for r in rows),'allExactTriangleCoordinateMultisetsEqual':all(r['exactTriangleCoordinateMultisetEqual'] for r in rows),'maxCorrespondingCornerNormalDifference':max(r['maxCorrespondingNormalVectorDifference'] for r in rows),'rows':rows,'interpretation':'No byte-reproducibility claim. Final review binds only final SHA. Geometry matches exactly after ignoring accessor/index storage order; report numeric normal differences separately. No approximate position welding.','runtime':'unverified'};(D/'reviews/replay-comparison-r05.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
