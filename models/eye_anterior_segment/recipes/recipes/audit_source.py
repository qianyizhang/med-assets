import json,struct,pathlib,hashlib,numpy as np
D=pathlib.Path(__file__).resolve().parents[1]
p=D/'sources/hra-source.glb'
b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);off=20+n;blen=struct.unpack_from('<I',b,off)[0];bin=bytearray(b[off+8:off+8+blen])
def arr(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];c={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];t={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];return np.ndarray((a['count'],c),dtype=t,buffer=bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(t).itemsize*c),np.dtype(t).itemsize)).copy()
rows=[]
for node in j['nodes']:
 if 'mesh' not in node:continue
 for prim in j['meshes'][node['mesh']]['primitives']:
  v=arr(prim['attributes']['POSITION']);norm=arr(prim['attributes']['NORMAL']);ix=arr(prim['indices']).reshape(-1,3);uv,inv=np.unique(v,axis=0,return_inverse=True);sums=np.zeros((len(uv),3));fc=np.cross(v[ix[:,1]]-v[ix[:,0]],v[ix[:,2]]-v[ix[:,0]])
  for k in range(3): np.add.at(sums,inv[ix[:,k]],fc)
  nl=np.linalg.norm(sums,axis=1);avg=sums/np.maximum(nl[:,None],1e-30);ang=np.degrees(np.arccos(np.clip(np.sum(norm*avg[inv],axis=1),-1,1)));flat=np.sum(norm[ix[:,0]]*norm[ix[:,1]],axis=1)>.999999
  rows.append({'name':node['name'],'sourceNodeId':j['nodes'].index(node),'meshId':node['mesh'],'sourceLabel':node.get('extras',{}).get('label'),'vertices':len(v),'triangles':len(ix),'exactUniquePositions':len(uv),'fractionTrianglesWithSameFirstTwoNormals':float(flat.mean()),'normalDifferenceFromAreaWeightedExactCoordinateMeanDegrees':{'median':float(np.median(ang)),'p95':float(np.quantile(ang,.95)),'max':float(ang.max())},'zeroNormalSums':int((nl==0).sum()),'zeroAreaTriangles':int((np.linalg.norm(fc,axis=1)==0).sum()),'boundsGltfM':[v.min(0).tolist(),v.max(0).tolist()],'material':j['materials'][prim['material']]})
report={'sourceSha256':hashlib.sha256(b).hexdigest(),'method':'Read-only original GLB accessor arrays. Angle difference compares source normals with area-weighted face normals grouped only by exact POSITION tuple, per original mesh. No smoothing or source edit yet.','objects':rows};(D/'reviews/source-diagnosis.json').write_text(json.dumps(report,indent=2))
for r in rows:print(r['name'], 'dup',r['vertices']-r['exactUniquePositions'],'same normals',round(r['fractionTrianglesWithSameFirstTwoNormals'],3),'angle',r['normalDifferenceFromAreaWeightedExactCoordinateMeanDegrees'])
