import bpy,json,hashlib,argparse,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--diagnostic-original',action='store_true',help='Rebuild rejected original ONLY for negative diagnostic evidence, never the default teaching asset');opts=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(opts.source);O=Path(opts.out)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd','Source hash mismatch'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
core=[f'{n}.{s}' for n in (['Parotid gland','Submandibular gland','Sublingual gland','Parotid duct']+(['Submandibular duct'] if opts.diagnostic_original else [])) for s in ['r','l']];context=['Mandible']+[f'{n}.{s}' for n in ['Mylohyoid muscle','Superficial part of masseter','Genioglossus muscle'] for s in ['r','l']];names=core+context;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(S),link=False) as(a,b):
 assert all(n in a.objects for n in names);b.objects=list(names)
originals=list(b.objects)
for old in originals:bpy.context.collection.objects.link(old);old.hide_set(False);old.hide_viewport=False;old.hide_render=False
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();rows=[];copies=[]
for old in originals:
 rec={'name':old.name,'type':old.type,'matrix_world':[list(x) for x in old.matrix_world],'modifiers':[m.type for m in old.modifiers]};ev=old.evaluated_get(dep);mesh=bpy.data.meshes.new_from_object(ev,depsgraph=dep);o=bpy.data.objects.new(old.name+' source display',mesh);o.matrix_world=old.matrix_world.copy();bpy.context.collection.objects.link(o);o['source_object']=old.name;o['role']='primary' if old.name in core else 'same-source context';copies.append(o)
 rec['evaluated_vertices']=len(mesh.vertices);rec['faces']=len(mesh.polygons)
 if old.type=='CURVE':rec['splines']=[{'type':s.type,'bezier_points':len(s.bezier_points),'points':len(s.points),'cyclic':s.use_cyclic_u} for s in old.data.splines]
 rows.append(rec);c=(.42,.31,.22) if 'Parotid gland' in old.name else (.34,.28,.20) if 'Submandibular gland' in old.name else (.44,.36,.22) if 'Sublingual gland' in old.name else (.54,.49,.35) if 'duct' in old.name else (.22,.25,.28) if old.name=='Mandible' else (.22,.13,.12)
 m=bpy.data.materials.new(old.name+' teaching display');m.use_nodes=True;q=m.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*c,1);q.inputs['Roughness'].default_value=.8;mesh.materials.clear();mesh.materials.append(m)
for old in originals:bpy.data.objects.remove(old,do_unlink=True)
bpy.context.view_layer.update()
for phase,keep in [('glands-ducts',core),('context',names)]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in copies:
  if o['source_object'] in keep:o.select_set(True)
 assert len(bpy.context.selected_objects)==len(keep)
 bpy.ops.export_scene.gltf(filepath=str(O/(phase+'.glb')),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
(O/'source-members.json').write_text(json.dumps({'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'members':rows,'exports':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in O.glob('*.glb')},'diagnostic_original_only':opts.diagnostic_original,'excluded_source_objects':([] if opts.diagnostic_original else ['Submandibular duct.r','Submandibular duct.l']),'exclusion_reason':'Unaccepted duct course; left mylohyoid intersection verified; no route repair. Original source shown only in separate failure diagnostic.','scope':'Native effective transforms and evaluated source geometry; visibility/material only. No inferred sublingual ducts or outlets.'},indent=2))
