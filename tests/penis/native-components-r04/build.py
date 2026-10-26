import bpy,json,hashlib,argparse,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.source);O=Path(a.out)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd','Source hash mismatch'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
names=['Glans penis','Corpus spongiosum of penis','Corpus cavernosum of penis'];bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(S),link=False) as(a,b):b.objects=list(names)
originals=list(b.objects)
for old in originals:bpy.context.collection.objects.link(old)
bpy.context.view_layer.update()
source_matrices={old.name:[list(x) for x in old.matrix_world] for old in originals}
for old,c in zip(originals,[(.40,.27,.24),(.38,.29,.23),(.31,.34,.37)]):
 o=bpy.data.objects.new(old.name+' source display',old.data.copy());o.matrix_world=old.matrix_world.copy();bpy.context.collection.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.hide_select=False;o.hide_set(False);bpy.context.view_layer.update();o.select_set(True);m=bpy.data.materials.new(o.name+' teaching material');m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*c,1);n.inputs['Roughness'].default_value=.75;o.data.materials.clear();o.data.materials.append(m)
for old in originals:bpy.data.objects.remove(old,do_unlink=True)
bpy.context.view_layer.update()
assert len(bpy.context.selected_objects)==3, 'Empty/incorrect selection'
bpy.ops.export_scene.gltf(filepath=str(O/'source_components.glb'),export_format='GLB',use_selection=True,export_animations=False)

(O/'build-receipt.json').write_text(json.dumps({'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((O/'source_components.glb').read_bytes()).hexdigest(),'source_matrices':source_matrices,'scope':'Source meshes unchanged, native effective transforms preserved; materials and visibility only; no anatomy repair'},indent=2))
