from pathlib import Path
import json,hashlib,struct,numpy as np,math
BASE=Path(__file__).parent;OUT=BASE/'updated'
def decode(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];j=json.loads(data[20:20+n]);offset=20+n;binlen=struct.unpack_from('<I',data,offset)[0];blob=data[offset+8:offset+8+binlen]
 def acc(k):
  a=j['accessors'][k];v=j['bufferViews'][a['bufferView']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];dim={'VEC3':3,'SCALAR':1}[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',np.dtype(dtype).itemsize*dim)
  return np.ndarray((a['count'],dim),dtype=dtype,buffer=blob,offset=start,strides=(stride,np.dtype(dtype).itemsize)).copy()
 triangles=[];count=0
 for mesh in j['meshes']:
  for p in mesh['primitives']:
   pos=acc(p['attributes']['POSITION']);norm=acc(p['attributes']['NORMAL']);indices=acc(p['indices']).ravel().reshape(-1,3)
   assert np.isfinite(pos).all() and np.isfinite(norm).all();assert np.max(abs(np.linalg.norm(norm,axis=1)-1))<.0002
   count+=len(indices)
   # GLB Y is occlusal. Keep only wholly unchanged lower triangles.
   for ids in indices:
    pts=[tuple(float(x) for x in pos[i]) for i in ids]
    if max(p[1] for p in pts)<=.0035:triangles.append(tuple(sorted(pts)))
 return {'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'triangles':count,'lower_triangles':len(triangles),'lower_triangle_sha256':hashlib.sha256(repr(sorted(triangles)).encode()).hexdigest()}
a=decode(BASE/'baseline/FDI36-authored.glb');b=decode(OUT/'FDI36-authored.glb');
assert a['sha256']=='54b29904746bf0a53a96143326e09cef84995d2e40a29cd1da634b43908fe38c'
assert b['sha256']=='cda5baeb7d517bc69f652bc3dcb3b62af18cfe423a8701e62fe3478b5534b9e4'
assert a['lower_triangle_sha256']==b['lower_triangle_sha256'];assert a['lower_triangles']==b['lower_triangles'];assert a['triangles']==b['triangles']
r={'original_v5':a,'updated_v6':b,'exported_lower_triangle_identity':'exactly unchanged for triangles with all vertex heights <= 3.5 mm','exported_position_normal_check':'finite, unit normals within 0.0002 tolerance'}
(OUT/'regression-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
