import bpy,json,hashlib,argparse,sys
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);opts=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S=opts.source;O=opts.out;assert hashlib.sha256(S.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd','Source hash mismatch';assert not O.exists(),'Output must be new';O.mkdir(parents=True)
core=['Urethra'];context=['Urinary bladder','Prostate','Corpus spongiosum of penis','Corpus cavernosum of penis','Glans penis'];names=core+context;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(S),link=False) as(a,b):
 assert all(n in a.objects for n in names);b.objects=list(names)
originals=list(b.objects)
for old in originals:bpy.context.collection.objects.link(old);old.hide_set(False);old.hide_viewport=False;old.hide_render=False
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();rows=[];copies=[]
for old in originals:
 rec={'name':old.name,'type':old.type,'matrix_world':[list(x) for x in old.matrix_world],'modifiers':[m.type for m in old.modifiers]};ev=old.evaluated_get(dep);mesh=bpy.data.meshes.new_from_object(ev,depsgraph=dep);o=bpy.data.objects.new(old.name+' source display',mesh);o.matrix_world=old.matrix_world.copy();bpy.context.collection.objects.link(o);o['source_object']=old.name;o['role']='primary' if old.name in core else 'same-source context';copies.append(o)
 rec['evaluated_vertices']=len(mesh.vertices);rec['faces']=len(mesh.polygons)
 if old.type=='CURVE':rec['splines']=[{'type':s.type,'bezier_points':len(s.bezier_points),'points':len(s.points),'cyclic':s.use_cyclic_u} for s in old.data.splines]
 rows.append(rec);c=(.55,.40,.14) if old.name=='Urethra' else (.31,.33,.35) if old.name=='Urinary bladder' else (.22,.27,.30) if old.name=='Prostate' else (.28,.21,.19) if old.name in ['Corpus spongiosum of penis','Glans penis'] else (.27,.29,.31)
 m=bpy.data.materials.new(old.name+' teaching display');m.use_nodes=True;q=m.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*c,1);q.inputs['Roughness'].default_value=.8;mesh.materials.clear();mesh.materials.append(m)
for old in originals:bpy.data.objects.remove(old,do_unlink=True)
bpy.context.view_layer.update()
for phase,keep in [('urethra',core),('context',names)]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in copies:
  if o['source_object'] in keep:o.select_set(True)
 assert len(bpy.context.selected_objects)==len(keep)
 bpy.ops.export_scene.gltf(filepath=str(O/(phase+'.glb')),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
(O/'source-members.json').write_text(json.dumps({'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'members':rows,'exports':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in O.glob('*.glb')},'scope':'Native effective transforms and evaluated source geometry; visibility/material only. No inferred lumen, outlet, or clinical route validation.'},indent=2))
