import bpy,bmesh,math,json,hashlib,sys,time
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).parent/(sys.argv[sys.argv.index('--')+1])
OUT=BASE/'evidence-clean'
if OUT.exists():raise RuntimeError('Preserve evidence')
OUT.mkdir()
prior=json.loads((BASE/'receipt.json').read_text())
actual_bytes=(BASE/'FDI36-authored.glb').read_bytes()
assert hashlib.sha256(actual_bytes).hexdigest()==prior['glb']['sha256'], 'Artifact bytes no longer match receipt'
assert len(actual_bytes)==prior['glb']['bytes'], 'Artifact size no longer matches receipt'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
bpy.ops.import_scene.gltf(filepath=str(BASE/'FDI36-authored.glb'))
ob=next(o for o in scene.objects if o.type=='MESH')
anchors={o.name for o in scene.objects if o.type=='EMPTY' and o.name!='FDI36_Authored_Educational'}
def check(obj):
 mesh=obj.data;mesh.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(mesh)
 edges={};vol=bm.calc_volume(signed=True);bad=sum(not e.is_manifold for e in bm.edges);bm.free()
 assert all(math.isfinite(q) for v in mesh.vertices for q in v.co)
 assert all(math.isfinite(q) for v in mesh.vertices for q in v.normal)
 assert all(abs(v.normal.length-1)<.0002 for v in mesh.vertices)
 assert all(t.area>1e-16 for t in mesh.loop_triangles)
 assert not bad and vol>0,(bad,vol)
 # Connectivity over actual vertex edges.
 adj=[[] for _ in mesh.vertices]
 for e in mesh.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();components=0
 for i in range(len(adj)):
  if i in seen:continue
  components+=1;stack=[i];seen.add(i)
  while stack:
   for k in adj[stack.pop()]:
    if k not in seen:seen.add(k);stack.append(k)
 assert components==1,components
 coords=[tuple(round(float(q),8) for q in v.co) for v in mesh.vertices]
 tris=sorted(tuple(sorted(coords[i] for i in t.vertices)) for t in mesh.loop_triangles)
 return {'vertices':len(mesh.vertices),'triangles':len(tris),'nonmanifold_edges':bad,'components':components,'volume_mm3':vol*1e9,'bounds_mm':[[min(p[k] for p in coords)*1000,max(p[k] for p in coords)*1000] for k in range(3)],'decoded_triangles_sha256':hashlib.sha256(repr(tris).encode()).hexdigest()}

original=ob.data
signature=lambda:hashlib.sha256(repr([(tuple(v.co),tuple(v.normal)) for v in original.vertices]).encode()).hexdigest()
unchanged=signature()
me=original.copy();tmp=bpy.data.objects.new('Topology_check_copy',me)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-9);bm.to_mesh(me);bm.free();me.update()
technical=check(tmp)
assert technical['decoded_triangles_sha256']==prior['before']['decoded_triangles_sha256']
bpy.data.objects.remove(tmp);bpy.data.meshes.remove(me)
# Reimported actual artifact, no authoring geometry or image-generation reference.
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.3;scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.curvature_ridge_factor=1.2;scene.display.shading.curvature_valley_factor=1.1;scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('World');scene.world.color=(.055,.065,.08)
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cam=bpy.data.objects.new('EvidenceCamera',bpy.data.cameras.new('EvidenceCamera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.lens=50;cam.data.clip_start=.001;cam.data.clip_end=10
views={};
from bpy_extras.object_utils import world_to_camera_view
for name,direction,target,scale in [('occlusal',(0,0,1),(0,.3,3),15),('buccal',(0,-1,0),(0,0,-3),27),('lingual',(0,1,0),(0,0,-3),27),('mesial',(-1,0,0),(0,0,-3),27),('distal',(1,0,0),(0,0,-3),27),('three-quarter',(-.8,-1,.85),(0,0,-2.0),27),('occlusal-detail',(0,0,1),(0,.3,5),13)]:
 target=Vector(target)/1000;cam.location=target+Vector(direction).normalized()*.10;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale/1000;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 loc={}
 for n in anchors:
  q=world_to_camera_view(scene,cam,scene.objects[n].matrix_world.translation);loc[n]=[round(q.x*1000),round((1-q.y)*1100)]
 views[name]={'direction':direction,'target_m':list(target),'ortho_scale_mm':scale,'anchor_pixels':loc,'sha256':hashlib.sha256((OUT/(name+'.png')).read_bytes()).hexdigest()}

assert signature()==unchanged
receipt={'artifact':prior['glb'],'technical':technical,'unaltered_reimport_coordinates_and_normals_sha256':unchanged,'views':views,'scope':'Clean GLB import rendered without seam welding or geometry changes. Topology check uses a disposable clone.'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'clean_evidence':str(OUT),'glb_sha256':prior['glb']['sha256']}))
