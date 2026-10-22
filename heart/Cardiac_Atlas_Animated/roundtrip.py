import bpy,json,os
from mathutils import Vector
R=os.path.dirname(os.path.abspath(__file__))
checks={}
for file in ['Heart_Clinical_Animated.glb','Heart_Cutaway_Animated.glb','Heart_Tissue_Animated.glb']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=R+'/'+file)
 s=bpy.context.scene;s.render.fps=30
 report={}
 names=['LV | complete wall','LA | complete wall','LV | anterior section','LA | anterior section','Mitral valve | leaflet 1','Aortic valve | leaflet 1']
 for name in names:
  o=bpy.data.objects.get(name)
  if not o:continue
  per=[]
  for f in [0,2,5,9,13,24]:
   s.frame_set(f);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();per.append(coords)
  movement=max(max((a-b).length for a,b in zip(per[0],p)) for p in per[1:])
  # importer timebase is default 24fps before changed; check full timeline range for motion; raw validation separately proves seam.
  assert movement>.0001,(name,movement)
  report[name]={'max_world_vertex_change_m':movement,'vertices':len(per[0])}
 checks[file]=report
json.dump(checks,open(R+'/BLENDER_ROUNDTRIP_QA.json','w'),indent=2)
print('ROUNDTRIP',json.dumps(checks),flush=True)
