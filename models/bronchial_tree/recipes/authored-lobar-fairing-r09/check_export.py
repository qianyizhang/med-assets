import pathlib,struct,json,numpy as np,hashlib,sys
P=pathlib.Path(__file__).resolve().parents[1]
def read(f):
 b=f.read_bytes(); off=12;parts={}
 while off<len(b):
  n,t=struct.unpack_from('<II',b,off);off+=8;parts[t]=b[off:off+n];off+=n
 j=json.loads(parts[0x4e4f534a]);buf=parts[0x004e4942]
 def a(k):
  ac=j['accessors'][k];v=j['bufferViews'][ac['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']];c={'SCALAR':1,'VEC3':3}[ac['type']];return np.frombuffer(buf,dtype=dt,count=ac['count']*c,offset=v.get('byteOffset',0)+ac.get('byteOffset',0)).reshape(-1,c)
 pr=j['meshes'][0]['primitives'][0];return a(pr['attributes']['POSITION']).astype(float),a(pr['indices']).reshape(-1,3),j
from scipy.spatial import cKDTree
s=pathlib.Path(sys.argv[1]);c=pathlib.Path(sys.argv[2]);z=np.load(sys.argv[3]);x,f,_=read(s);y,g,_=read(c)
def togl(v):return v[:,[0,2,1]]*np.array([1,1,-1])
b=togl(z['baseline']);a=togl(z['candidate']);dx,ix=cKDTree(b).query(x);dy,iy=cKDTree(a).query(y)
assert len(np.unique(ix))==len(x) and len(np.unique(iy))==len(y)
def oriented(fs):
 o=np.argmin(fs,axis=1);r=np.take_along_axis(fs,(o[:,None]+np.arange(3))%3,axis=1);return r[np.lexsort(r.T[::-1])]
ff=oriented(ix[f]);gg=oriented(iy[g]);xx=np.empty_like(x);yy=np.empty_like(y);xx[ix]=x;yy[iy]=y;d=np.linalg.norm(yy-xx,axis=1);n=np.cross(xx[ff[:,1]]-xx[ff[:,0]],xx[ff[:,2]]-xx[ff[:,0]]);m=np.cross(yy[ff[:,1]]-yy[ff[:,0]],yy[ff[:,2]]-yy[ff[:,0]]);ln=np.linalg.norm(n,axis=1);lm=np.linalg.norm(m,axis=1);cos=(n*m).sum(1)/np.maximum(ln*lm,1e-30);changed=(d[ff]>0).any(1)
def vol(v):return float(np.einsum('ij,ij->i',v[ff[:,0]],np.cross(v[ff[:,1]],v[ff[:,2]])).sum()/6)
r={'source_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(c.read_bytes()).hexdigest(),'unique_position_bijection':True,'source_map_max_error_m':float(dx.max()),'candidate_map_max_error_m':float(dy.max()),'oriented_faces_equal_after_bijection':bool(np.array_equal(ff,gg)),'changed_vertices':int((d>0).sum()),'max_displacement_m':float(d.max()),'outside_support_exact':bool(np.array_equal(xx[z['weights']==0],yy[z['weights']==0])),'zero_area_faces':int((lm<1e-18).sum()),'face_normal_dot_nonpositive':int((cos<=0).sum()),'min_face_normal_cosine':float(cos.min()),'changed_face_area_ratio_min':float((lm/ln)[changed].min()),'changed_face_area_ratio_max':float((lm/ln)[changed].max()),'whole_signed_volume_before':vol(xx),'whole_signed_volume_after':vol(yy),'caveat':'Vertex correspondence uses builder npz but validates fresh GLB positions and full oriented triangle topology independently. Positive face normal comparison is not exhaustive self-intersection testing.'}
print(json.dumps(r,indent=2))
