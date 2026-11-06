"""Locally authored, explicitly bounded display shading derivative. Does not move vertices."""
import pathlib,json,struct,hashlib,copy,collections,numpy as np
from extract_exact_subsets import write_glb
D=pathlib.Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def array(j,b,i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];assert a['type']=='VEC3' and a['componentType']==5126
 offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
 return np.ndarray((a['count'],3),dtype='<f4',buffer=b,offset=offset,strides=(stride,4)),offset,stride
groups={
 'spleen':[['VH_F_gastric_surface_of_spleen','VH_F_diaphragmatic_surface_of_spleen','VH_F_colic_surface_of_spleen','VH_F_renal_surface_of_spleen']],
 'pancreas':[['VH_F_tail_of_pancreas','VH_F_body_of_pancreas','VH_F_neck_of_pancreas','VH_F_head_of_pancreas','VH_F_ucinate_process1']],
 'bladder':[['VH_F_fundus_of_urinary_bladder_dome','VH_F_fundus_of_urinary_bladder_base']]
}
for parentid in ['spleen_hra_female_r02']:
 id=parentid.replace('r02','r03');organ=id.split('_')[0];src=D/'models'/parentid/(parentid+'.glb');raw=src.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+jl]);before=raw[28+jl:];after=bytearray(before);nodes={n['name']:n for n in j['nodes'] if 'mesh' in n};updates=[];per_group=[];allowed=set()
 for group in groups[organ]:
  coordinates=collections.defaultdict(list)
  for name in group:
   p=j['meshes'][nodes[name]['mesh']]['primitives'];assert len(p)==1;p=p[0];positions,_,_=array(j,before,p['attributes']['POSITION']);normals,off,st=array(j,before,p['attributes']['NORMAL'])
   for i,(v,n) in enumerate(zip(positions,normals)):coordinates[tuple(float(x) for x in v)].append((name,i,n.astype(float),off+i*st))
  count=0;skipped=0
  for coord,items in coordinates.items():
   if len({x[0] for x in items})<2:continue
   # Preserve intentional within-part split normals rather than joining a hard rim.
   byname=collections.defaultdict(list)
   for name,i,n,off in items:byname[name].append(n)
   if any(any(np.linalg.norm(v-vs[0])>1e-6 for v in vs[1:]) for vs in byname.values()):skipped+=1;continue
   mean=np.mean([vs[0]/np.linalg.norm(vs[0]) for vs in byname.values()],axis=0);length=np.linalg.norm(mean)
   if length<.5:skipped+=1;continue
   mean=(mean/length).astype('<f4');count+=1
   for name,i,n,off in items:
    new=mean.tobytes();after[off:off+12]=new;allowed.update(range(off,off+12));angle=float(np.degrees(np.arccos(np.clip(np.dot(n/np.linalg.norm(n),mean.astype(float)/np.linalg.norm(mean)),-1,1))))
    updates.append({'mesh':name,'vertex':i,'coordinate':coord,'old_normal':list(n),'new_normal':list(map(float,mean)),'angular_change_degrees':angle,'binary_byte_offset':off})
  per_group.append({'included_source_parts':group,'shared_exact_coordinates_updated':count,'shared_coords_skipped_for_within_part_hard_normal_or_opposition':skipped})
 diff={i for i,(a,b) in enumerate(zip(before,after)) if a!=b};assert diff<=allowed;assert len(before)==len(after)
 out=D/'models'/id;out.mkdir(exist_ok=True);p=out/(id+'.glb');write_glb(p,copy.deepcopy(j),bytes(after));outb=p.read_bytes();ojl=struct.unpack_from('<I',outb,12)[0];oj=json.loads(outb[20:20+ojl]);assert j==oj
 audit={'id':id,'parent_file':str(src.relative_to(D)),'parent_sha256':sha(raw),'file':str(p.relative_to(D)),'sha256':sha(outb),'all_json_identical':True,'all_non_normal_binary_bytes_identical':True,'binary_changed_bytes':len(diff),'changed_normal_vectors':len(updates),'max_normal_angular_change_degrees':max(x['angular_change_degrees'] for x in updates),'rms_normal_angular_change_degrees':float(np.sqrt(np.mean([x['angular_change_degrees']**2 for x in updates]))),'interface_groups':per_group,'method':'At exact shared POSITION tuples across the explicitly listed region patches only, replace participating normals by the normalized unweighted mean of one unit normal per named part. No proximity tolerance. Skip within-part split normals and near-opposed vectors. All other data remains byte-identical.','protected':'Bladder trigone/orifice/neck meshes fully untouched; spleen hilum fully untouched. No position, index, boundary, opening, source name, transform, tangent, UV or material changes. Tangents remain source values and are unused because no normal-map texture exists.','interpretation':'Reversible display-shading derivative, not corrected source anatomy. No smoothing, fill state change, hole fill, reconstructed tissue, registration, clinical or runtime validation.','approval':'unreviewed R03 shading trial; root must inspect exact-export pixels','updates':updates}
 (out/'normal-only-derivation-audit.json').write_text(json.dumps(audit,indent=2));print(id,len(updates),p.stat().st_size,audit['sha256'])
