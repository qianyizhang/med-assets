import bpy,json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parents[1]
def load(paths):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 for p in paths:bpy.ops.import_scene.gltf(filepath=str(p))
 return {o.name:{'coords':sorted(set(tuple(round(float(v),7) for v in o.matrix_world@p.co) for p in o.data.vertices)),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in bpy.data.objects if o.type=='MESH'}
for organ,src,run in [('uterus_hra',['VH_F_Uterus.glb'],'source-candidate-02')]:
 a=load([D/'source/hra'/f for f in src]);p=D/'models'/organ/'exports'/run/f'{organ}_native_frame.glb';b=load([p]);out={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'method':'Every world vertex, tuple dedup and rounding to 1e-7 metres; exact sorted-set equality after source vs final independent imports. Triangle count also compared. No coordinate mutation.','checks':{k:{'all_vertex_coordinates_match_to_0_1_micrometre':v['coords']==a[k]['coords'],'triangle_count_match':v['triangles']==a[k]['triangles'],'unique_coordinates':len(v['coords'])} for k,v in b.items()},'excluded_source_nodes':sorted(set(a)-set(b))}
 (D/'reviews'/organ/run/'full-coordinate-tests.json').write_text(json.dumps(out,indent=2))
 print('COORDINATES',organ,all(x['all_vertex_coordinates_match_to_0_1_micrometre'] and x['triangle_count_match'] for x in out['checks'].values()))
