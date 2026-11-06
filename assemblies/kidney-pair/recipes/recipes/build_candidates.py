"""Material-only matte display + metadata derivative; original GLB BIN is exact; all changes explicitly enumerated."""
import copy,hashlib,json,struct,shutil
from pathlib import Path
D=Path(__file__).resolve().parent; S=D.parent/'kidney-reference-source-screen/source/hra'
sha=lambda b:hashlib.sha256(b).hexdigest()
def chunks(b):
 assert b[:4]==b'glTF' and struct.unpack_from('<II',b,4)==(2,len(b)); out=[];off=12
 while off<len(b):
  n,t=struct.unpack_from('<II',b,off);out.append((t,b[off+8:off+8+n]));off+=8+n
 assert off==len(b);return out
def layer(n):
 for token,key in [('capsule','capsule'),('hilum','hilum_surface'),('outer_cortex','outer_cortex'),('renal_column','renal_column_surface'),('renal_pyramid','renal_pyramids'),('renal_papilla','papilla_labeled_tip_surfaces')]:
  if token in n:return key
 raise ValueError(n)
records=[]
for side,short in [('left','l'),('right','r')]:
 id='kidney_'+side;sid='kidney-female-'+side;src=S/sid/('3d-vh-f-kidney-'+short+'.glb');b=src.read_bytes();cs=chunks(b);j=json.loads(cs[0][1]);original=copy.deepcopy(j);prov=json.loads((src.parent/'provenance.json').read_text());dst=D/'models'/id;dst.mkdir(parents=True,exist_ok=True)
 source_dir=D/'source'/sid;source_dir.mkdir(parents=True,exist_ok=True)
 for p in src.parent.iterdir():
  if p.is_file():shutil.copy2(p,source_dir/p.name)
 added=[];keys={};material_changes=[]
 for mi,mat in enumerate(j['materials']):
  pbr=mat['pbrMetallicRoughness'];old=pbr['roughnessFactor'];pbr['roughnessFactor']=0.72;material_changes.append({'materialIndex':mi,'materialName':mat['name'],'jsonPath':'materials/'+str(mi)+'/pbrMetallicRoughness/roughnessFactor','original':old,'candidate':0.72,'meaning':'Illustrative matte display material, not a measured tissue reflectance.'})
 for i,n in enumerate(j['nodes']):
  if 'mesh' not in n:continue
  lk=layer(n['name']);keys.setdefault(lk,[]).append(n['name']);x=n.setdefault('extras',{});extras={'anatomy_id':id,'candidate_id':id+'_hra_female_r02','layer_key':lk,'view_role':'surface' if lk in ['capsule','hilum_surface'] else 'detail','reference_sex':'female','source_release':'HRA ref-organ '+sid+' v1.3','source_sha256':sha(b),'frame_contract':'Native HRA glTF frame and scale, unchanged; not registered to s1233 or BP3D.','display_contract':'Explicit source layer isolation only. No fabricated cut, closure, deformation or internals. All source nodes remain in the default scene. Supported review modes are exterior (all source) and pyramids plus tip surfaces; column/pyramid combined isolation is diagnostic failure evidence only. Roughness 0.72 is illustrative display styling, not measured tissue appearance.'}
  assert not set(extras).intersection(x);x.update(extras);added.append({'node':i,'keys':list(extras)})
 ax=j['asset'].setdefault('extras',{});new={'candidate_status':'pending_root_visual_review_no_promotion','candidate_revision':'r02','source_asset':sid,'source_sha256':sha(b),'source_doi':prov['doi'],'source_version':'v1.3','reference_population':'Visible Human female reference organ; not s1233 and not a universal healthy/normal template','license':'CC BY 4.0','attribution':prov['citation'],'derivative_changes':'Metadata additions and three material roughness factors changed to 0.72 only. Illustrative matte display, not measured tissue appearance. Original base colors, all geometry, indices, normals, transforms, hierarchy, source extras and BIN chunk bytes retained.','missing_anatomy':'No renal pelvis, calyces, ureter or renal vasculature included. Papilla-labeled surfaces are retained and reported as source labels; no complete drainage system claimed.'}
 assert not set(new).intersection(ax);ax.update(new)
 jb=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();jb+=b' '*((-len(jb))%4);outchunks=[(cs[0][0],jb)]+cs[1:];body=b''.join(struct.pack('<II',len(v),t)+v for t,v in outchunks);out=struct.pack('<4sII',b'glTF',2,len(body)+12)+body;p=dst/(id+'_hra_female_r02.glb');p.write_bytes(out)
 # Reverse only our additions and prove every original parsed JSON value and binary chunk survived.
 check=json.loads(chunks(out)[0][1]);
 for rec in added:
  for k in rec['keys']:del check['nodes'][rec['node']]['extras'][k]
 for k in new:del check['asset']['extras'][k]
 if 'extras' not in original['asset']:del check['asset']['extras']
 for change in material_changes:check['materials'][change['materialIndex']]['pbrMetallicRoughness']['roughnessFactor']=change['original']
 assert check==original;assert chunks(out)[1:]==cs[1:]
 modes={'all_source_geometry':list(keys),'medulla_and_tip_surfaces':['renal_pyramids','papilla_labeled_tip_surfaces'],'capsule_only':['capsule']}
 rec={'id':id,'candidateFile':str(p.relative_to(D)),'candidateSha256':sha(out),'candidateBytes':len(out),'sourceFile':str((source_dir/src.name).relative_to(D)),'sourceSha256':sha(b),'sourceUrl':prov['files'][0]['url'],'sourceMetadataSha256':prov['metadataSha256'],'sourceDOI':prov['doi'],'sourceRelease':'v1.3','referenceSex':'female','originalJsonRecoveredAfterRevertingDocumentedChanges':True,'nonJsonChunksByteIdentical':True,'binaryChunks':[{'type':t,'bytes':len(v),'sha256':sha(v)} for t,v in cs[1:]],'geometryChanges':'none','transformChanges':'none','materialChanges':material_changes,'supportedModes':['all_source_geometry','medulla_and_tip_surfaces'],'diagnosticOnlyModes':['capsule_only'],'rejectedModes':['columns_and_medulla'],'illustrativeMaterial':'Source base colors unchanged; roughness 0.72. No tissue reflectance/normality claim, invented texture or subsurface parameter.','topologyChanges':'none','sourceLayerNodes':keys,'viewModes':modes,'sourceCitation':prov['citation'],'status':'pending_root_visual_review; no clinical accuracy claim; no canonical promotion'}
 (dst/'layer-key.json').write_text(json.dumps({'id':id,'modes':modes,'layers':keys,'supportedModes':['all_source_geometry','medulla_and_tip_surfaces'],'diagnosticOnlyModes':['capsule_only'],'rejectedModes':['columns_and_medulla'],'note':'Modes require consumer visibility control. GLB extras do not themselves hide anything; default GLB scene preserves all original source geometry. Source papilla labels describe retained tip surfaces, not verification of a full collecting system.'},indent=2));(dst/'provenance.json').write_text(json.dumps(rec,indent=2));records.append(rec)
(D/'candidate-manifest.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
