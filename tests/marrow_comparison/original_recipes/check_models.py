import pathlib,json,struct,hashlib,numpy as np
D=pathlib.Path(__file__).resolve().parent.parent
def parse(p):
 b=p.read_bytes();assert b[:4]==b'glTF';assert struct.unpack_from('<I',b,8)[0]==len(b);n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);st=20+n;bn=struct.unpack_from('<I',b,st)[0];binary=b[st+8:st+8+bn]
 def acc(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];k={'SCALAR':1,'VEC3':3,'VEC2':2,'VEC4':4}[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',np.dtype(dt).itemsize*k);return np.ndarray((a['count'],k),dtype=dt,buffer=binary,offset=off,strides=(stride,np.dtype(dt).itemsize)).copy()
 res=[];allv=[]
 for m in j['meshes']:
  for pr in m['primitives']:
   v=acc(pr['attributes']['POSITION']);idx=acc(pr['indices']).reshape(-1,3);assert np.isfinite(v).all();assert idx.max()<len(v);area=np.linalg.norm(np.cross(v[idx[:,1]]-v[idx[:,0]],v[idx[:,2]]-v[idx[:,0]]),axis=1)/2;res.append({'mesh':m.get('name'),'vertices':len(v),'triangles':len(idx),'strictZeroArea':int((area==0).sum()),'minArea_m2':float(area.min())});allv.append(v)
 return j,res,np.concatenate(allv)
out={'scope':'GLB header/length, finite positions, valid triangle indices and exact zero-area triangles only. No anatomy/runtime/manifold pass.','files':[]}
for p in sorted((D/'models').glob('*.glb')):
 j,r,v=parse(p);out['files'].append({'file':'models/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'meshes':r,'animationCount':len(j.get('animations',[]))})
(D/'evidence/model-container-checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
