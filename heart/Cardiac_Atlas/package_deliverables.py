from pathlib import Path
import zipfile,hashlib,json
R=Path(__file__).resolve().parent
scripts=['build_heart.py','heart_geometry.py','finalize_and_render.py','bake_tissue_atlas.py','post_bake_finalize.py','export_details.py','export_meshes.py','prepare_portable_exports.py','fix_continuous_controls.py','render_animation.py','compose_animation.py','render_remaining.py','create_teaching_plates.py','render_normal_diagnostic.py','verify_final_model.py','package_deliverables.py']
files=[R/'Cardiac_Atlas.blend',*[R/x for x in scripts],R/'geometry_spec.json',R/'vessel_geometry.json',R/'anatomy_manifest.json']
files+=list((R/'docs').glob('*'))+list((R/'exports').rglob('*'))
files+=[p for p in (R/'textures').glob('*') if p.suffix=='.json' or p.name.startswith('wall_atlas_')]
files=[p for p in files if p.is_file() and p.name!='anatomy_details.json.gz']
media=list((R/'renders').glob('[0-9][0-9]_*.png'))+[R/'Cardiac_Atlas_Beating_Heart.mp4']
manifest=[]
for name,items in [('Cardiac_Atlas_Model_Package.zip',files),('Cardiac_Atlas_Media.zip',media)]:
 with zipfile.ZipFile(R/name,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(items):z.write(p,'Cardiac_Atlas/'+str(p.relative_to(R)))
 with zipfile.ZipFile(R/name) as z:assert z.testzip() is None
 p=R/name;manifest.append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'entries':len(items)})
json.dump(manifest,open(R/'PACKAGE_MANIFEST.json','w'),indent=2);print(json.dumps(manifest,indent=2))
