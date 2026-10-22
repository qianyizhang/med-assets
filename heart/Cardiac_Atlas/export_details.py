import os
import bpy, json, re, os, gzip
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;s.frame_set(1)
c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse'];c['cutaway']=1;c['material_set']=1;bpy.context.view_layer.update()
vessels={v['anatomy_id']:v['label'] for v in json.load(open(R+'/vessel_geometry.json'))}
deps=bpy.context.evaluated_depsgraph_get();details=[]
for col in bpy.data.collections:
 if col.name[:2] not in ('02','03','04','05','06','01'):continue
 for ob in col.objects:
  if ob.type!='MESH':continue
  if col.name.startswith('01') and 'appendage' not in ob.name:continue
  if 'pericardium' in ob.name.lower():continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles()
  aid=ob.get('anatomy_id') or re.sub(r'[^a-z0-9]+','_',ob.name.lower()).strip('_')
  material=ob.data.materials[0] if ob.data.materials else None
  color=list(material.diffuse_color[:3]) if material else [.7,.7,.7]
  details.append({'object':ob.name,'anatomy_id':aid,'label':vessels.get(aid,0),'material_rgb':color,'vertices_BU':[[round(v,6) for v in (ob.matrix_world@vv.co)] for vv in me.vertices],'triangles':[list(t.vertices) for t in me.loop_triangles]})
  ev.to_mesh_clear()
obj={'format':'static ED anatomical detail meshes','phase':1,'coordinates':'native Blender BU; RASmm=(-25X,-25Y,+25Z)','units_mm_per_BU':25,'note':'Detail-only; no duplicate main chamber walls/pools/septa. label0 details are not resolved in the synthetic imaging volume.','meshes':details}
p=R+'/exports/anatomy_details.json';json.dump(obj,open(p,'w'),separators=(',',':'))
with open(p,'rb') as f,gzip.open(p+'.gz','wb',compresslevel=9) as out:out.write(f.read())
print('EXPORTED',len(details),'detail objects',os.path.getsize(p),'bytes')
