import bpy,json,hashlib,argparse,sys
from mathutils.kdtree import KDTree
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);opts=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);s=opts.source;d=opts.work;m=json.loads((d/'r01/source-members.json').read_text());assert hashlib.sha256(s.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd';assert hashlib.sha256((d/'r01/context.glb').read_bytes()).hexdigest()=='d2d88c936287f4ea5978aba1f17e86975c587a102e498595dd7a58aa07c269e7';assert not opts.out.exists();opts.out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(s),link=False) as(a,b): b.objects=[r['name'] for r in m['members']]
src={}
for o in b.objects:bpy.context.collection.objects.link(o);o.hide_set(False);o.hide_viewport=False
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
for o in b.objects:
 ev=o.evaluated_get(dep);me=ev.to_mesh();src[o.name]=[o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(d/'r01/context.glb'));bpy.context.view_layer.update()
out={'source_hash_match':hashlib.sha256(s.read_bytes()).hexdigest()==m['source_sha256'],'export_hash_match':hashlib.sha256((d/'r01/context.glb').read_bytes()).hexdigest()==m['exports']['context.glb'],'objects':{}}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 n=o['source_object'];a=src[n];b=[o.matrix_world@v.co for v in o.data.vertices];k=KDTree(len(a));[k.insert(v,i) for i,v in enumerate(a)];k.balance();k2=KDTree(len(b));[k2.insert(v,i) for i,v in enumerate(b)];k2.balance();out['objects'][n]={'source_vertices':len(a),'export_vertices':len(b),'max_bidirectional_world_vertex_error':max(max(k.find(v)[2] for v in b),max(k2.find(v)[2] for v in a))}
print('VERIFY_RESULT',json.dumps(out))

assert len(out['objects'])==6 and out['source_hash_match'] and out['export_hash_match']
assert all(x['max_bidirectional_world_vertex_error']<2e-7 for x in out['objects'].values())
opts.out.write_text(json.dumps(out,indent=2))
