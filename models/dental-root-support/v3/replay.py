import struct,pathlib,hashlib,json,math,zipfile
import argparse,sys
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser(description='Replay the source-qualified teaching crop into a NEW directory.')
parser.add_argument('--source',type=pathlib.Path,required=True,help='Extracted Human Lower Jaw Dataset directory')
parser.add_argument('--output',type=pathlib.Path,required=True)
a=parser.parse_args(args);S=a.source.resolve();R=a.output.resolve()
if R.exists():raise RuntimeError('Output already exists; preserve previous drafts and choose a new directory')
expected=json.loads((pathlib.Path(__file__).resolve().parent/'source-inventory.json').read_text())
if len(expected)!=8:raise RuntimeError('Expected exactly 8 pinned source surfaces')
for record in expected:
 source=(S/record['source_file']).resolve()
 if not source.is_relative_to(S):raise RuntimeError('Source path escapes source directory')
 raw=source.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=record['source_sha256']:raise RuntimeError('Source identity mismatch: '+record['source_file'])
 if len(raw)!=84+50*record['triangles']:raise RuntimeError('Source STL size mismatch: '+record['source_file'])
import bpy,bmesh
from mathutils import Vector
R.mkdir(parents=True)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c,alpha=1):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,alpha);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.48;p.inputs['Alpha'].default_value=alpha
 if alpha<1:m.surface_render_method='DITHERED'
 return m
mats=[mat('Illustrative ivory tooth',(0.83,.75,.55)),mat('Synthetic PDL orange',(0.85,.29,.07),1),mat('Cortical bone blue gray',(.32,.49,.57)),mat('Cancellous bone muted rose',(.61,.39,.37))]
records=[];objs=[]
paths=[*(S/'Teeth/STL'/('D'+str(i)+'.stl') for i in [35,36,37]),*(S/'PDL/STL'/('L'+str(i)+'.stl') for i in [35,36,37]),S/'Bones/Cortical/Cortical bone lower jaw with boolean.stl',S/'Bones/Cancellous/Alveolar bone lower jaw with boolean.stl']
for p in paths:
 b=p.read_bytes();n=struct.unpack_from('<I',b,80)[0];vs=[];fs=[];lookup={}
 for i in range(n):
  q=struct.unpack_from('<9f',b,96+50*i);face=[]
  for k in (0,3,6):
   v=tuple(q[k:k+3]);idx=lookup.get(v)
   if idx is None:idx=len(vs);lookup[v]=idx;vs.append(v)
   face.append(idx)
  fs.append(face)
 mesh=bpy.data.meshes.new(p.stem);mesh.from_pydata(vs,[],fs);mesh.update();ob=bpy.data.objects.new(p.stem,mesh);bpy.context.collection.objects.link(ob)
 typ=0 if p.name.startswith('D') else 1 if p.name.startswith('L') else 2 if 'Cortical' in str(p) else 3
 ob.data.materials.append(mats[typ]);ob['source_sha256']=hashlib.sha256(b).hexdigest();ob['source_units']='mm from paired IGES header';ob['source_role']='synthetic PDL 0.25mm, not measured' if typ==1 else 'source tooth whole surface, no internal segmentation' if typ==0 else 'source bone'
 records.append({'name':ob.name,'source_file':str(p.relative_to(S)),'source_sha256':ob['source_sha256'],'vertices':len(vs),'triangles':n,'native_bounds':[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]});objs.append(ob)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.001
# Source master includes all selected unchanged surfaces in native millimetres.
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source-selected-master.blend'))
# Deliberate bone-only window: clip to segment envelope and remove buccal side.
# Exact solid intersection generates explicitly editorial planar section faces.
bpy.ops.mesh.primitive_cube_add(size=1,location=(-228.5,-250,5))
cutter=bpy.context.object;cutter.name='Editorial inspection box';cutter.dimensions=(13,32,20)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for ob in objs[-2:]:
 bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Editorial section, not anatomy','BOOLEAN');mod.operation='INTERSECT';mod.solver='FAST' if ob.name.startswith('Alveolar') else 'EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name)
 if ob.name.startswith('Alveolar'):
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-6);bm.to_mesh(ob.data);bm.free()
 section=mat('Editorial planar section face',(.74,.53,.45) if ob.name.startswith('Alveolar') else (.46,.66,.73));ob.data.materials.append(section)
 cap_count=0
 for poly in ob.data.polygons:
  if any(all(abs(ob.data.vertices[v].co[axis]-value)<1e-4 for v in poly.vertices) for axis,value in [(0,-235),(0,-222),(1,-266),(1,-234),(2,-5),(2,15)]):poly.material_index=1;cap_count+=1
 ob['editorial_section_faces']=cap_count
 ob['derived_edit']='Bone-only box intersection: x[-235,-222], y[-266,-234], z[-5,15] mm. Synthesized planar section faces are editorial, not anatomy.'
bpy.data.objects.remove(cutter,do_unlink=True)
# glTF stores native coordinate numeric values scaled to metres; apply only common unit conversion.
for ob in objs:ob.scale=(.001,)*3
bpy.ops.object.select_all(action='DESELECT')
for ob in objs:ob.select_set(not ob.name.startswith('L'))
bpy.ops.export_scene.gltf(filepath=str(R/'molar-support-v3.glb'),use_selection=True,export_format='GLB',export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'molar-support-v3.blend'))
for ob in objs:ob.select_set(not ob.name.startswith('D'))
bpy.ops.export_scene.gltf(filepath=str(R/'synthetic-pdl-v3.glb'),use_selection=True,export_format='GLB',export_extras=True)
(R/'source-inventory.json').write_text(json.dumps(records,indent=2))
# Clean reimport of the exact candidate, never render the pre-export scene.
bpy.context.scene.unit_settings.scale_length=1.0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(R/'molar-support-v3.glb'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12);scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
# glTF import restores Blender's original Z-up orientation.
target=Vector((-.225,-.252,.004));camdata=bpy.data.cameras.new('Inspection camera');cam=bpy.data.objects.new('Inspection camera',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.clip_start=.0001;camdata.type='ORTHO';camdata.ortho_scale=.054
for n,loc,power,size in [('Key',(-.16,-.29,.08),15,.10),('Fill',(-.28,-.20,.07),8,.10),('Rim',(-.27,-.28,.03),5,.08)]:
 d=bpy.data.lights.new(n,'AREA');d.energy=power*.003;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
for name,delta in [('detail',(1,-.65,.55)),('occlusal',(.2,-.25,1.5))]:
 cam.location=target+Vector(delta)*.07;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(R/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'reimport-review.blend'))
for ob in list(scene.objects):
 if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(R/'synthetic-pdl-v3.glb'))
cam.location=target+Vector((1,-.65,.55))*.07;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(R/'pdl-only.png');bpy.ops.render.render(write_still=True)
checks=[]
for ob in scene.objects:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data);checks.append({'name':ob.name,'vertices':len(bm.verts),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)});bm.free()
(R/'reimport-checks.json').write_text(json.dumps(checks,indent=2))
