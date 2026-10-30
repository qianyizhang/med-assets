"""Check exact reimport vertex coordinates and first visible object for leaders."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--bindings',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.out.exists():raise FileExistsError('New locator receipt required')
b=json.loads(a.bindings.read_text());assert hashlib.sha256(a.glb.read_bytes()).hexdigest()==b['artifactSha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.glb))
objects={o.get('source_object'):o for o in bpy.context.scene.objects if o.type=='MESH'}
dg=bpy.context.evaluated_depsgraph_get();rows=[]
for v in b['views']:
 if v['file']=='whole-source.png':continue
 keys=['trunk','common','proper','scaphoid'] if v['file']=='hand-palmar.png' else ['trunk','scaphoid']
 toward_camera=(Vector(v['camera'])-Vector(v['target'])).normalized()
 for anchor in v['anchors']:
  if anchor['key'] not in keys:continue
  obj=objects[anchor['sourceObject']];point=obj.matrix_world@obj.data.vertices[anchor['vertex']].co
  error=(point-Vector(anchor['world'])).length;assert error<1e-7
  hit,loc,norm,index,visible,matrix=bpy.context.scene.ray_cast(dg,point+toward_camera*2,-toward_camera,distance=2.1)
  actual=visible.get('source_object') if hit else None
  rows.append({'panel':v['file'],'key':anchor['key'],'boundSourceObject':anchor['sourceObject'],'firstVisibleSourceObject':actual,'coordinateError':error,'passed':actual==anchor['sourceObject']})
result={'artifactSha256':b['artifactSha256'],'bindingsSha256':hashlib.sha256(a.bindings.read_bytes()).hexdigest(),'checks':rows,'passed':all(r['passed'] for r in rows),'scope':'Six displayed numeric leaders bind exact GLB vertices and first-hit source objects. Semantic identity still requires independent pixel/anatomy review.'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
assert result['passed']
