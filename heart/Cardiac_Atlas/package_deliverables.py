import argparse
from pathlib import Path
import zipfile,hashlib,json
from texture_inputs import ensure_wall_textures
from geometry_inputs import ensure_geometry_exports, GEOMETRY

parser = argparse.ArgumentParser()
parser.add_argument("--model-only", action="store_true", help="package the model without requiring rendered media")
model_only = parser.parse_args().model_only
ensure_geometry_exports()
ensure_wall_textures()
R=Path(__file__).resolve().parent
scripts=['build_heart.py','heart_geometry.py','finalize_and_render.py','bake_tissue_atlas.py','post_bake_finalize.py','export_details.py','export_meshes.py','prepare_portable_exports.py','fix_continuous_controls.py','render_animation.py','compose_animation.py','render_remaining.py','create_teaching_plates.py','render_normal_diagnostic.py','verify_final_model.py','package_deliverables.py','texture_inputs.py','geometry_inputs.py']
files=[R/'Cardiac_Atlas.blend',*[R/x for x in scripts],R/'geometry_spec.json',R/'vessel_geometry.json',R/'anatomy_manifest.json']
files+=list((R/'docs').glob('*'))+list((R/'exports').rglob('*'))
files+=[p for p in (R/'textures').glob('*') if p.suffix=='.json' or p.name.startswith('wall_atlas_')]
files=[p for p in files if p.is_file() and p.name not in {name + '.gz' for name in GEOMETRY}]
media=list((R/'renders').glob('[0-9][0-9]_*.png'))+[R/'Cardiac_Atlas_Beating_Heart.mp4']
manifest=[]
packages = [('Cardiac_Atlas_Model_Package.zip', files)]
if not model_only:
 packages.append(('Cardiac_Atlas_Media.zip', media))
for name,items in packages:
 with zipfile.ZipFile(R/name,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(items):z.write(p,'Cardiac_Atlas/'+str(p.relative_to(R)))
 with zipfile.ZipFile(R/name) as z:assert z.testzip() is None
 p=R/name;manifest.append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'entries':len(items)})
if not model_only:
 with (R / 'PACKAGE_MANIFEST.json').open('w') as record:
  json.dump(manifest, record, indent=2)
print(json.dumps(manifest, indent=2))
