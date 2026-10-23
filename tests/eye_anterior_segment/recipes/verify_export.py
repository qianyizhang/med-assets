import pathlib,struct,json,numpy as np,hashlib
D=pathlib.Path(__file__).resolve().parents[1]
def load(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);off=20+n;blen=struct.unpack_from('<I',b,off)[0];return j,b[off+8:off+8+blen]
def arr(j,b,i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];c={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];t={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];return np.ndarray((a['count'],c),dtype=t,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(t).itemsize*c),np.dtype(t).itemsize)).copy()
s=D/'sources/hra-source.glb';sj,sb=load(s);rows=[]
for p in sorted((D/'models').glob('*.glb')):
 j,b=load(p);rr=[]
 for n in j['nodes']:
  sn=next(x for x in sj['nodes'] if x['name']==n['name']);pr=j['meshes'][n['mesh']]['primitives'][0];sp=sj['meshes'][sn['mesh']]['primitives'][0];v=arr(j,b,pr['attributes']['POSITION']);sv=arr(sj,sb,sp['attributes']['POSITION']);ind=arr(j,b,pr['indices']);si=arr(sj,sb,sp['indices']);no=arr(j,b,pr['attributes']['NORMAL']);uv,iv=np.unique(v,axis=0,return_inverse=True);tris=iv[ind.reshape(-1,3)];edges=np.sort(np.concatenate([tris[:,[0,1]],tris[:,[1,2]],tris[:,[2,0]]]),axis=1);ue,ct=np.unique(edges,axis=0,return_counts=True)
  r={'node':n['name'],'positionsByteIdentical':v.tobytes()==sv.tobytes(),'indicesByteIdentical':ind.tobytes()==si.tobytes(),'normalsByteIdentical':no.tobytes()==arr(sj,sb,sp['attributes']['NORMAL']).tobytes(),'transformsIdentical':all(n.get(k)==sn.get(k) for k in ['matrix','translation','rotation','scale']),'finitePositions':bool(np.isfinite(v).all()),'finiteNormals':bool(np.isfinite(no).all()),'indicesInRange':bool(ind.max()<len(v)),'triangles':len(tris),'exactCoordinateDiagnosticBoundaryEdges':int((ct==1).sum()),'exactCoordinateDiagnosticNonTwoIncidentEdges':int((ct!=2).sum())};rr.append(r)
  assert r['positionsByteIdentical'] and r['indicesByteIdentical'] and r['transformsIdentical'] and r['finitePositions'] and r['finiteNormals'] and r['indicesInRange']
 rows.append({'file':str(p.relative_to(D)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'nodes':rr})
(D/'reviews/geometry-preservation.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(s.read_bytes()).hexdigest(),'scope':'Exact source/rendering byte-preservation and finite-accessor checks; no anatomical or watertight/self-intersection claim. Edge incidence uses float-tuple equality, not tolerance welding.','exports':rows},indent=2));print('PASS all',len(rows),'exports preserve every selected node POSITION/index accessor byte and transform; finite in-range. See diagnostic open-surface counts.')
