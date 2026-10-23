import pathlib,json,struct,numpy as np,hashlib
D=pathlib.Path(__file__).resolve().parents[1];paths=[D/'models/blood-cell-authored-study-r05.glb',D/'replay-r05/models/blood-cell-authored-study-r05.glb']
def read(p):
 b=p.read_bytes();o=12;c={}
 while o<len(b):n,k=struct.unpack_from('<II',b,o);c[k]=b[o+8:o+8+n];o+=8+n
 j=json.loads(c[0x4e4f534a]);raw=c[0x004e4942]
 def a(i):
  x=j['accessors'][i];v=j['bufferViews'][x['bufferView']];typ=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1',5122:'<i2',5120:'i1'}[x['componentType']]);dim={'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}[x['type']];s=v.get('byteOffset',0)+x.get('byteOffset',0);return np.ndarray((x['count'],dim),dtype=typ,buffer=raw,offset=s,strides=(v.get('byteStride',typ.itemsize*dim),typ.itemsize)).copy()
 out={}
 for node in j['nodes']:
  if 'mesh' not in node:continue
  prims=[]
  for pr in j['meshes'][node['mesh']]['primitives']:
   ff=a(pr['indices']).reshape(-1,3);pos=a(pr['attributes']['POSITION'])[ff];co=np.lexsort((pos[:,:,2],pos[:,:,1],pos[:,:,0]),axis=1);pos=np.take_along_axis(pos,co[:,:,None],axis=1).reshape(-1,9);ro=np.lexsort(tuple(pos[:,i] for i in range(8,-1,-1)));attrs={}
   for key,accessor in pr['attributes'].items():
    v=a(accessor)[ff];attrs[key]=np.take_along_axis(v,co[:,:,None],axis=1).reshape(len(ff),-1)[ro]
   # Orientation retained separately after coordinate sorting: determinant sign of corner permutation.
   inversions=((co[:,0]>co[:,1]).astype(int)+(co[:,0]>co[:,2]).astype(int)+(co[:,1]>co[:,2]).astype(int))%2
   prims.append({'material':pr.get('material'),'mode':pr.get('mode',4),'attrs':attrs,'orientationParity':inversions[ro]})
  out[node['name']]=prims
 return j,out
(j1,x),(j2,y)=[read(p) for p in paths];rows=[]
for name in x:
 assert len(x[name])==len(y[name]);rr={'node':name,'primitives':[]}
 for i,(a,b) in enumerate(zip(x[name],y[name])):
  attrs={k:{'exactPerCornerEqual':bool(np.array_equal(a['attrs'][k],b['attrs'][k])),'maxAbsDifference':float(np.max(np.abs(a['attrs'][k].astype(float)-b['attrs'][k].astype(float))))} for k in a['attrs']};rr['primitives'].append({'primitive':i,'sameMaterialAssociation':a['material']==b['material'],'sameMode':a['mode']==b['mode'],'sameAttributeKeys':set(a['attrs'])==set(b['attrs']),'sameTriangleWinding':bool(np.array_equal(a['orientationParity'],b['orientationParity'])),'attributes':attrs})
 rows.append(rr)
passed=all(p['sameMaterialAssociation'] and p['sameMode'] and p['sameAttributeKeys'] and p['sameTriangleWinding'] and all(a['exactPerCornerEqual'] for a in p['attributes'].values()) for r in rows for p in r['primitives'])
r={'finalSha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'replaySha256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),'bytesIdentical':False,'allNodeCornerSemanticsExact':passed,'nodesTransformsExtrasEqual':j1['nodes']==j2['nodes'],'materialsEqual':j1['materials']==j2['materials'],'method':'Per named node and material primitive, sort each triangle corners by exact POSITION then sort triangles lexicographically. Compare all present attributes at corresponding corners, plus winding parity, primitive material association, node transforms/extras and material definitions. No coordinate welding or rounding.','attributesPresent':sorted({k for r in rows for p in r['primitives'] for k in p['attributes']}),'nodes':rows};(D/'reviews/replay-corner-attributes-r05.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='nodes'},indent=2))
