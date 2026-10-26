import bpy,sys,argparse,hashlib,json
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.source);O=Path(a.out)
expected='9c9d980edd1bb2d576376c0c486a3e45db65188c6ede72f3b2e1a56a1f7f9ba7'
if hashlib.sha256(S.read_bytes()).hexdigest()!=expected:raise ValueError('Source hash mismatch')
if O.exists():raise ValueError('Output must be new')
O.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.wm.stl_import(filepath=str(S));o=bpy.context.object;o.name='NIH3D_3DPX-002305_airspace_cast';vs=[v.co for v in o.data.vertices];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)]);c=(lo+hi)/2;s=1/max(hi-lo);o.scale=(s,)*3;o.location=-c*s
for q in o.data.polygons:q.use_smooth=True
m=bpy.data.materials.new('Neutral airspace—not tissue color');m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(.42,.38,.33,1);b.inputs['Roughness'].default_value=.8;o.data.materials.append(m)
o['source']='https://3d.nih.gov/entries/2305';o['attribution']='nevitdilmen; CC BY 4.0';o['representation']='CT-derived airspace cast, not mucosa or conchae';o['limitations']='Disclosed right-maxillary retention-cyst indentation; source intersections retained; units and anatomical axes undocumented';o['display_transform']='Centered bounding box, longest extent 1 arbitrary display unit; no physical measurement claim'
bpy.ops.export_scene.gltf(filepath=str(O/'nasal_airspace.glb'),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False,export_animations=False)
r={'source_sha256':expected,'output_sha256':hashlib.sha256((O/'nasal_airspace.glb').read_bytes()).hexdigest(),'source_bounds':[list(lo),list(hi)],'source_center':list(c),'display_scale':s,'transform':'world=(source-center)*display_scale; standard Blender Z-up to glTF Y-up serialization','vertices':len(vs),'triangles':len(o.data.polygons),'geometry_edits':[],'display_only_changes':['uniform reversible fit transform','neutral material','smooth normals'],'whole_baseline_status':'Needs revision','count_delta':0}
(O/'record.json').write_text(json.dumps(r,indent=2))
