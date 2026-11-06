"""35-degree dihedral threshold + dimensionless sliver guard; positions/topology untouched."""
import pathlib,json,struct,hashlib,collections,math,numpy as np
from extract_exact_subsets import write_glb
D=pathlib.Path(__file__).resolve().parents[1];threshold=35.;quality_threshold=1e-3;src=D/'models/pancreas_hra_female_r02/pancreas_hra_female_r02.glb'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 raw=p.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+jl]),raw[28+jl:]
def arr(j,b,i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dt={5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];n={'SCALAR':1,'VEC3':3}[a['type']];sz=np.dtype(dt).itemsize;off=v.get('byteOffset',0)+a.get('byteOffset',0);st=v.get('byteStride',sz*n);return np.ndarray((a['count'],n),dtype=dt,buffer=b,offset=off,strides=(st,sz)),off,st
raw,j,before=read(src);after=bytearray(before);unique={};coords=[];faces=[];face_records=[];by_part={};vertex_faces=collections.defaultdict(list);edges=collections.defaultdict(list)
for n in j['nodes']:
 if 'mesh' not in n:continue
 p=j['meshes'][n['mesh']]['primitives'][0];pos,_,_=arr(j,before,p['attributes']['POSITION']);norm,off,st=arr(j,before,p['attributes']['NORMAL']);indices,_,_=arr(j,before,p['indices']);local=[]
 for v in pos:
  key=tuple(float(x) for x in v)
  if key not in unique:unique[key]=len(coords);coords.append(key)
  local.append(unique[key])
 tris=indices.reshape(-1,3);by_part[n['name']]={'pos':pos,'norm':norm,'normal_offset':off,'normal_stride':st,'local':local,'index_faces':collections.defaultdict(list),'normal_accessor':p['attributes']['NORMAL']}
 for tri in tris:
  f=len(faces);vv=tuple(local[int(x)] for x in tri);faces.append(vv);face_records.append((n['name'],[int(x) for x in tri]))
  for k in range(3):vertex_faces[vv[k]].append(f);edges[tuple(sorted((vv[k],vv[(k+1)%3])))].append(f);by_part[n['name']]['index_faces'][int(tri[k])].append(f)
coords=np.array(coords);fn=[];angles=[];degenerate=[];illconditioned=[]
for i,(a,b,c) in enumerate(faces):
 v=coords[[a,b,c]];cross=np.cross(v[1]-v[0],v[2]-v[0]);mag=np.linalg.norm(cross)
 if mag<1e-20:degenerate.append(i);fn.append(np.array([0.,0.,0.]));angles.append([0.,0.,0.]);continue
 q=2*math.sqrt(3)*mag/sum(float(np.dot(v[(z+1)%3]-v[z],v[(z+1)%3]-v[z])) for z in range(3))
 if q<quality_threshold:illconditioned.append(i)
 fn.append(cross/mag);aa=[]
 for k in range(3):
  x=v[(k+1)%3]-v[k];y=v[(k+2)%3]-v[k];aa.append(float(np.arccos(np.clip(np.dot(x,y)/(np.linalg.norm(x)*np.linalg.norm(y)),-1,1))))
 angles.append(aa)
fn=np.array(fn);adj=collections.defaultdict(list);crease_edges=0;nonmanifold_edges=0
for edge,fs in edges.items():
 if len(fs)!=2:
  if len(fs)>2:nonmanifold_edges+=1
  continue
 f,g=fs
 if f in illconditioned or g in illconditioned or f in degenerate or g in degenerate:continue
 if np.dot(fn[f],fn[g])>=math.cos(math.radians(threshold)):
  for v in edge:adj[(v,f)].append(g);adj[(v,g)].append(f)
 else:crease_edges+=1
fans={};fan_normals={}
for v,ff in vertex_faces.items():
 remaining=set(ff);components=[]
 while remaining:
  seed=remaining.pop();component={seed};stack=[seed]
  while stack:
   for f in adj[(v,stack.pop())]:
    if f in remaining:remaining.remove(f);component.add(f);stack.append(f)
  idx=len(components);components.append(component);total=np.zeros(3)
  for f in component:
   fans[(v,f)]=idx;total+=fn[f]*angles[f][faces[f].index(v)]
  mag=np.linalg.norm(total);fan_normals[(v,idx)]=total/mag if mag>1e-15 else None
updates=[];allowed=set();skipped=0;protected_sliver_indices=0;protected_zero_normals=0;normals_by_name={};protected=[]
for name,p in by_part.items():
 target=p['norm'].copy()
 for i,ff in p['index_faces'].items():
  v=p['local'][i];groups={fans[(v,f)] for f in ff}
  if any(f in illconditioned or f in degenerate for f in ff):
   protected_sliver_indices+=1;protected_zero_normals+=int(np.linalg.norm(p['norm'][i])<=1e-12);protected.append({'mesh':name,'vertex':i,'source_normal':p['norm'][i].tolist(),'position':p['pos'][i].tolist(),'source_faces':ff,'reason':'Ill-conditioned source triangle; normal retained'});continue
  if np.linalg.norm(p['norm'][i])<=1e-12:
   protected_zero_normals+=1;protected.append({'mesh':name,'vertex':i,'source_normal':p['norm'][i].tolist(),'position':p['pos'][i].tolist(),'source_faces':ff,'reason':'Original zero normal retained'});continue
  if len(groups)!=1:skipped+=1;continue
  new=fan_normals[(v,next(iter(groups)))]
  if new is None:skipped+=1;continue
  new=new.astype('<f4');old=p['norm'][i].astype(float);mag=np.linalg.norm(old);angle=float(np.degrees(np.arccos(np.clip(np.dot(old/mag,new),-1,1)))) if mag>1e-12 else None
  off=p['normal_offset']+i*p['normal_stride'];after[off:off+12]=new.tobytes();allowed.update(range(off,off+12));target[i]=new;updates.append({'mesh':name,'vertex':i,'normal_angular_change_degrees':angle,'source_zero_normal':bool(mag<=1e-12),'byte_offset':off})
 normals_by_name[name]=target
diff={i for i,(x,y) in enumerate(zip(before,after)) if x!=y};assert diff<=allowed
id='pancreas_hra_female_normals35_guarded_r04';out=D/'models'/id;out.mkdir(exist_ok=True);p=out/(id+'.glb');write_glb(p,j,bytes(after));nr,nj,nb=read(p);assert nj==j
audit={'id':id,'file':str(p.relative_to(D)),'sha256':sha(nr),'parent_file':str(src.relative_to(D)),'parent_sha256':sha(raw),'all_json_identical':True,'all_non_normal_binary_bytes_identical':True,'normal_binary_bytes_changed':len(diff),'source_triangles':len(faces),'virtual_unique_coordinates':len(coords),'unchanged_geometric_crease_edges_above_threshold':crease_edges,'threshold_degrees':threshold,'illconditioned_triangle_quality_threshold':quality_threshold,'illconditioned_source_triangles_preserved':len(illconditioned),'protected_sliver_normal_indices':protected_sliver_indices,'source_zero_normals_preserved':protected_zero_normals,'protected_indices':protected,'nonmanifold_virtual_edges_not_smoothed':nonmanifold_edges,'degenerate_faces':len(degenerate),'original_indices_skipped_for_multiple_smoothing_fans':skipped,'normal_vectors_updated':len(updates),'max_angular_change_degrees':max(x['normal_angular_change_degrees'] or 0 for x in updates),'source_zero_normals_replaced_expected_zero':sum(x['source_zero_normal'] for x in updates),'method':'At exact source POSITION tuples only, build a virtual face adjacency. Smooth fans connect only manifold two-face shared edges with dihedral <=35 degrees. Average unit face normals weighted by geometric corner angle. Exclude triangle quality 4*sqrt(3)*area/sum(edge_squared)<1e-3 from fan adjacency; preserve normals of any original index touching those slivers or a degenerate face, all original zero normals, and any index spanning multiple crease-separated fans. No virtual welded geometry is exported.','protected':'POSITION/indices/names/transforms/materials/shape remain exactly unchanged. No boundary fill, topology edits, centering, scaling or fabricated lobules. Retained R02 remains available.','status':'Reconstruction only. Guarded numerical method unchanged; explicit context roles are applied before normal transfer. No new anatomy/runtime approval.','updates':updates}
(out/'normal-only-derivation-audit.json').write_text(json.dumps(audit,indent=2));print(id,audit['sha256'],{k:audit[k] for k in ['normal_vectors_updated','unchanged_geometric_crease_edges_above_threshold','original_indices_skipped_for_multiple_smoothing_fans','max_angular_change_degrees']})
# Apply exactly those per-name normal arrays to same-atlas context, with identity checks.
cid='pancreas_hra_female_context_r04';csrc=D/'models/pancreas_hra_female_context_r02/pancreas_hra_female_context_r02.glb';cr,cj,cb=read(csrc);ca=bytearray(cb);allow=set()
for n in cj['nodes']:
 if n.get('name') not in normals_by_name:continue
 pp=cj['meshes'][n['mesh']]['primitives'][0];pos,_,_=arr(cj,cb,pp['attributes']['POSITION']);nn,off,st=arr(cj,cb,pp['attributes']['NORMAL']);assert pos.tobytes()==by_part[n['name']]['pos'].tobytes();assert nn.tobytes()==by_part[n['name']]['norm'].tobytes()
 for i,v in enumerate(normals_by_name[n['name']]):start=off+i*st;ca[start:start+12]=v.tobytes();allow.update(range(start,start+12))
assert {i for i,(x,y) in enumerate(zip(cb,ca)) if x!=y}<=allow
co=D/'models'/cid;co.mkdir(exist_ok=True);cp=co/(cid+'.glb');write_glb(cp,cj,bytes(ca));(co/'normal-only-derivation-audit.json').write_text(json.dumps({'id':cid,'sha256':sha(cp.read_bytes()),'parent_file':str(csrc.relative_to(D)),'parent_sha256':sha(cr),'normal_source_candidate':id,'normal_source_candidate_sha256':audit['sha256'],'all_json_identical':True,'all_non_normal_binary_bytes_identical':True,'method':'Exact per-name pancreas NORMAL array transfer from standalone bounded 35-degree trial; other same-atlas context unchanged.','approval':'Reconstruction only; no new anatomy/runtime approval.'},indent=2));print(cid,sha(cp.read_bytes()))
