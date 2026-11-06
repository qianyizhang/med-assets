import pathlib,json,struct,copy,hashlib
from extract_exact_subsets import subset,write_glb
D=pathlib.Path(__file__).resolve().parents[1]
subset('liver_hra_female_exterior_r01',['VH_F_capsule_of_the_liver','VH_F_bare_area_of_liver','VH_F_ligament_of_liver'])
def sha(b):return hashlib.sha256(b).hexdigest()
pal={
'liver':{'capsule':(.34,.075,.055,1),'bare':(.46,.18,.12,1),'ligament':(.64,.57,.42,1)},
'spleen':{'gastric':(.35,.10,.16,1),'diaphragmatic':(.40,.14,.20,1),'colic':(.31,.13,.21,1),'hilum':(.52,.24,.24,1),'renal':(.39,.19,.20,1)},
'pancreas':{'head':(.52,.32,.13,1),'body':(.58,.40,.19,1),'tail':(.65,.47,.25,1),'neck':(.47,.28,.13,1),'ucinate':(.58,.35,.17,1),'duct':(.28,.48,.40,1),'duodenum':(.36,.22,.20,1),'spleen':(.26,.12,.20,1)},
'bladder':{'dome':(.48,.24,.20,1),'base':(.36,.14,.13,1),'neck':(.60,.38,.22,1),'trigone':(.36,.21,.29,1),'orifice':(.63,.45,.22,1),'ureter':(.70,.57,.34,1),'uterus':(.35,.22,.30,1),'vagina':(.42,.22,.27,1),'rectum':(.17,.32,.32,1)}}
def role(id,n):
 if id=='liver':return 'capsule' if 'capsule' in n else 'bare' if 'bare_area' in n else 'ligament'
 if id=='spleen':return next(k for k in pal[id] if k in n)
 if id=='pancreas':
  if any(x in n for x in ['duct','ampulla']):return 'duct'
  if any(x in n for x in ['duodenum','jejunum','sphincter']):return 'duodenum'
  if 'spleen' in n:return 'spleen'
  return next(k for k in ['head','body','tail','neck','ucinate'] if k in n)
 if 'bladder' in n:return 'dome' if 'dome' in n else 'base' if 'base' in n else 'neck' if 'neck' in n else 'trigone'
 if 'orifice' in n:return 'orifice'
 if 'ureter' in n:return 'ureter'
 if 'rectum' in n:return 'rectum'
 if 'vagina' in n:return 'vagina'
 return 'uterus'
rows=[]
for sourceid in ['liver_hra_female_exterior_r01','spleen_hra_female_r01']:
 id=sourceid.replace('r01','r02');organ=id.split('_')[0];src=D/'models'/sourceid/(sourceid+'.glb');b=src.read_bytes();jl=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+jl]);binary=b[28+jl:];original=copy.deepcopy(g);g['materials']=[];roles={};newmats={}
 for n in g['nodes']:
  if 'mesh' not in n:continue
  rr=role(organ,n['name']);roles[n['name']]=rr
  if rr not in newmats:
   newmats[rr]=len(g['materials']);g['materials'].append({'name':'Illustrative_matte_'+organ+'_'+rr,'pbrMetallicRoughness':{'baseColorFactor':pal[organ][rr],'metallicFactor':0,'roughnessFactor':.78},'emissiveFactor':[0,0,0],'doubleSided':True})
  for p in g['meshes'][n['mesh']]['primitives']:p['material']=newmats[rr]
 out=D/'models'/id;out.mkdir(exist_ok=True);path=out/(id+'.glb');write_glb(path,g,binary)
 gg=copy.deepcopy(g);oo=copy.deepcopy(original)
 for ggx in [gg,oo]:
  ggx.pop('materials',None)
  for m in ggx['meshes']:
   for p in m['primitives']:p.pop('material',None)
 assert gg==oo
 bb=path.read_bytes();jj=struct.unpack_from('<I',bb,12)[0];assert bb[28+jj:]==binary
 audit={'id':id,'parent_file':str(src.relative_to(D)),'parent_sha256':sha(b),'file':str(path.relative_to(D)),'sha256':sha(bb),'binary_sha256':sha(binary),'all_binary_bytes_identical':True,'all_non_material_json_identical':True,'changes':'Only new illustrative matte materials and primitive material indices. Source normals/positions/topology/UVs/transforms remain byte-identical. No invented textures or additional anatomy. Double-sided display explicit for source surface patches; this does not confer thickness.','role_colors':pal[organ],'named_mesh_roles':roles,'roughness':.78,'license':'CC-BY-4.0','status':'Unreviewed; exact-export pixel review required'}
 (out/'material-only-derivation-audit.json').write_text(json.dumps(audit,indent=2));rows.append(audit);print(id,audit['sha256'])
(D/'sources/r02-index.json').write_text(json.dumps(rows,indent=2))
