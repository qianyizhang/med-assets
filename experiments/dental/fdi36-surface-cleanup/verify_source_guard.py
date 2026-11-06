"""Exercise scene-binding failures without saving or changing the input master."""
import ast,hashlib,json
from pathlib import Path
import bpy
BASE=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'baseline/FDI36-authored-master.blend'))
scene=bpy.context.scene;root=scene.objects['FDI36_Authored_Educational'];ob=scene.objects['FDI36_Exterior_AUTHORED']
OUT=BASE/'guard-cases'
if OUT.exists():raise RuntimeError('Choose a fresh guard-cases directory')
OUT.mkdir()
tree=ast.parse((BASE/'revise_surface.py').read_text())
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_source_scene' or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_BASELINE' for t in n.targets)]
exec(compile(ast.Module(body=selected,type_ignores=[]),'verify_source_scene','exec'))
verify_source_scene(OUT/'original.glb')
results={'original':'passed'}
def rejected(name):
 try:verify_source_scene(OUT/(name+'.glb'))
 except AssertionError:results[name]='correctly rejected'
 else:raise AssertionError(name+' was not rejected')
loc=ob.location.copy();ob.location.z+=.001;rejected('changed-transform');ob.location=loc
mat=ob.data.materials[0];socket=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'];color=tuple(socket.default_value);socket.default_value=(.2,.2,.2,1);rejected('changed-material');socket.default_value=color
anchor=scene.objects['CEJ_origin'];loc=anchor.location.copy();anchor.location.x+=.001;rejected('changed-anchor');anchor.location=loc
verify_source_scene(OUT/'restored.glb');results['restored']='passed'
(OUT/'result.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
