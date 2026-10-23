import pathlib,json,struct,hashlib,copy
import argparse
parser=argparse.ArgumentParser(description='Exact material-only source derivative; no source mutation')
parser.add_argument('--source',required=True);parser.add_argument('--output',required=True);parser.add_argument('--audit',required=True)
args=parser.parse_args();s=pathlib.Path(args.source);p=pathlib.Path(args.output);audit=pathlib.Path(args.audit)
if p.exists() or audit.exists():raise RuntimeError('Output and audit must be new files')
b=s.read_bytes();assert hashlib.sha256(b).hexdigest()=='32381ebb2b2369e8e83c2b1e5f94cb1cafccf1e1e23439f80bada482ab9e57ef'
n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);original=copy.deepcopy(j);tail=b[20+n:]
p.parent.mkdir(parents=True,exist_ok=True);audit.parent.mkdir(parents=True,exist_ok=True)

colors={'pasted__Uterus_Mat':[.40,.12,.14,1],'pasted__Arteries_Mat':[.45,.045,.06,1],'pasted__mucosa_mat':[.70,.60,.48,1],'pasted__Vein_mat':[.08,.14,.32,1]}
for mat in j['materials']:
 mat['pbrMetallicRoughness'].update(baseColorFactor=colors[mat['name']],roughnessFactor=.8,metallicFactor=0.0)
a={'name':'Illustrative_Amnion_Transparent_R02','pbrMetallicRoughness':{'baseColorFactor':[.75,.8,.75,.12],'roughnessFactor':.8,'metallicFactor':0.0},'alphaMode':'BLEND','doubleSided':True};idx=len(j['materials']);j['materials'].append(a)
for node in j['nodes']:
 if node.get('name')=='VH_F_amnion':
  for prim in j['meshes'][node['mesh']]['primitives']:prim['material']=idx
jb=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();jb+=b' '*((-len(jb))%4);out=struct.pack('<III',0x46546c67,2,20+len(jb)+len(tail))+struct.pack('<II',len(jb),0x4e4f534a)+jb+tail;assert hashlib.sha256(out).hexdigest()=='7f9f215f810003fddc76ede225f051dc7014c67216e804403a4632d628ad82aa';p.write_bytes(out)
# Verify all source content except material definitions/assignments byte-semantically unchanged.
source_geometry=copy.deepcopy(original);output_geometry=copy.deepcopy(j)
for x in [source_geometry,output_geometry]:
 x.pop('materials',None)
 for mesh in x['meshes']:
  for prim in mesh['primitives']:prim.pop('material',None)
assert source_geometry==output_geometry
h=lambda z:hashlib.sha256(z).hexdigest()
rec={'source_file':s.name,'source_sha256':h(b),'derivative_file':p.name,'sha256':h(out),'binary_chunks_sha256':h(tail),'geometry_buffer_and_topology_json_unchanged':source_geometry==output_geometry,'binary_chunks_identical':True,'allowed_changes_only':['Material baseColorFactor: muted illustrative palette; not measured tissue color','Material roughnessFactor 0.8 and metallicFactor 0','Dedicated amnion material alphaMode BLEND alpha 0.12; illustrates visibility, not measured optical transmission'],'no_changes':['All vertex positions, normals, indices, node transforms, mesh names, ontology extras','No added anatomy, microtexture, fake perforations, repaired holes, or simulation'],'source_materials':original['materials'],'derivative_materials':j['materials'],'source_age_scope':'Full term only, exactly as source. No numerical week inferred.','license':'CC-BY-4.0','status':'Deterministic material-only replay; visual acceptance is separate historical evidence','boundary':'Illustrative gross morphology and named layers, not perfusion/exchange fidelity or diagnostic anatomy'}
audit.write_text(json.dumps(rec,indent=2));print(json.dumps(rec,indent=2))
