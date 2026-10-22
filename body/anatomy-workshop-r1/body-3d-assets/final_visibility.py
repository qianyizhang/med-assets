import bpy,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'body-3d-delivery';m=json.load(open(D/'manifest.json'))
for a in m['assets']:
 if a['id']=='bronchial_tree':
  a['notes'].append('Alternative to the source trachea/main-airway surface. Hide source trachea when showing this authored hierarchy to avoid duplicated proximal airways.');a['alternativeGroup']='proximal_airway';a['defaultVisible']=False
 if a['id']=='trachea':a['alternativeGroup']='proximal_airway';a['defaultVisible']=True
 if a['id']=='heart_detailed':a['defaultVisible']=False
for col in bpy.data.collections:
 if col.name.startswith('bronchial_tree ·') or col.name.startswith('heart_detailed ·'):col.hide_render=True;col.hide_viewport=True
bpy.data.objects['WORKSHOP CONTROL · material and cutaway']['display_note']='Source trachea and authored bronchial hierarchy are alternative displays. Enable one collection at a time; likewise source/detailed heart.'
json.dump(m,open(D/'manifest.json','w'),ensure_ascii=False,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
exec(open(Path(__file__).resolve().parent/'save_external.py').read())
