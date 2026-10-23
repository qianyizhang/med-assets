import struct,json,pathlib,hashlib,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
D=pathlib.Path(__file__).resolve().parents[1];p=D/'models/blood-cell-authored-study-r05.glb';b=p.read_bytes();magic,version,total=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and total==len(b)
off=12;chunks={}
while off<len(b):
 n,k=struct.unpack_from('<II',b,off);chunks[k]=b[off+8:off+8+n];off+=8+n
j=json.loads(chunks[0x4e4f534a]);bin=chunks[0x004e4942];assert len(j['buffers'])==1 and 'uri' not in j['buffers'][0]
types={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'};dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def acc(i):
 a=j['accessors'][i];assert 'sparse' not in a;v=j['bufferViews'][a['bufferView']];t=np.dtype(types[a['componentType']]);d=dims[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',d*t.itemsize);assert start+(a['count']-1)*stride+d*t.itemsize<=len(bin)
 return np.ndarray((a['count'],d),dtype=t,buffer=bin,offset=start,strides=(stride,t.itemsize)).copy()
rows=[];cache={}
for m in j['meshes']:
 verts=[];faces=[];num=0
 for pr in m['primitives']:
  v=acc(pr['attributes']['POSITION']);f=acc(pr['indices']).reshape(-1,3);assert np.isfinite(v).all() and f.max()<len(v)
  verts.append(v);faces.append(f+num);num+=len(v)
 v=np.vstack(verts);f=np.vstack(faces)
 # Assemble all material primitives before exact-coordinate topology; material seams are not holes.
 vv,inv=np.unique(v,axis=0,return_inverse=True);ff=inv[f];e=np.vstack([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);e.sort(axis=1);ue,c=np.unique(e,axis=0,return_counts=True)
 a=np.linalg.norm(np.cross(vv[ff[:,1]]-vv[ff[:,0]],vv[ff[:,2]]-vv[ff[:,0]]),axis=1)/2
 gr=coo_matrix((np.ones(len(ue)),(ue[:,0],ue[:,1])),shape=(len(vv),len(vv)));cc=connected_components(gr,directed=False,return_labels=False)
 rec={'mesh':m['name'],'materialPrimitives':len(m['primitives']),'positions':len(v),'exactUniquePositions':len(vv),'triangles':len(f),'finite':True,'indicesInRange':True,'degenerateTrianglesAreaLT1e-12':int((a<1e-12).sum()),'boundaryEdgesExact':int((c==1).sum()),'nonManifoldEdgesExact':int((c>2).sum()),'topologicalComponentsExact':int(cc),'eulerExact':int(len(vv)-len(ue)+len(f))};rows.append(rec);cache[m['name']]=(vv,ff)
node_rows=[]
for n in j['nodes']:
 if 'mesh' not in n:continue
 m=j['meshes'][n['mesh']];node_rows.append({'name':n.get('name'),'mesh':m['name'],'extras':n.get('extras',{})})
byname={n['name']:n for n in node_rows}
n1=cache[byname['NEUTROPHIL_INTACT_one_connected_segmented_nucleus']['mesh']][0];n2=cache[byname['NEUTROPHIL_CUTAWAY_same_connected_nucleus']['mesh']][0]
rad=float(np.linalg.norm(n1,axis=1).max());nuc_equal=bool(np.array_equal(n1,n2));assert rad<1.45 and nuc_equal
# RBC topology is a closed sphere-like surface, not a torus: no edge boundaries and Euler 2.
rbcmesh=byname['RBC_A_closed_biconcave']['mesh'];rr=next(r for r in rows if r['mesh']==rbcmesh);assert rr['boundaryEdgesExact']==0 and rr['nonManifoldEdgesExact']==0 and rr['eulerExact']==2 and rr['topologicalComponentsExact']==1
nrow=next(r for r in rows if r['mesh']==byname['NEUTROPHIL_INTACT_one_connected_segmented_nucleus']['mesh']);assert nrow['topologicalComponentsExact']==1
result={'input':str(p),'sha256':hashlib.sha256(b).hexdigest(),'container':'GLB v2; exact file length; self-contained single buffer','allFinite':all(r['finite'] for r in rows),'allIndexRangesValid':True,'meshPrimitives':rows,'nodes':node_rows,'semanticChecks':{'RBC_closedSphereLikeTopologyNotTorus':True,'RBC_centerThicknessAuthored':.30,'nucleusConnected':True,'nucleusDuplicateGeometryIdentical':nuc_equal,'nucleusMaxRadiusInCellLocalCoordinates':rad,'cellOuterRadius':1.45,'minimumNuclearClearanceToOuterSphere':1.45-rad},'scope':'Exact-coordinate edge-incidence and graph checks, not comprehensive self-intersection/clinical/runtime validation. Cytoplasm has an enclosed nuclear cavity by design. Authored arbitrary units, not biological measurements.','runtime':'unverified'}
(D/'reviews/technical-r05.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('meshPrimitives','nodes')},indent=2));print('aggregate',len(rows),sum(r['triangles'] for r in rows),'triangles; boundary',sum(r['boundaryEdgesExact'] for r in rows),'nonmanifold',sum(r['nonManifoldEdgesExact'] for r in rows),'degenerate',sum(r['degenerateTrianglesAreaLT1e-12'] for r in rows))
