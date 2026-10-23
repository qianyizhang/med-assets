import bpy,pathlib,json,hashlib,sys,math,bmesh
from mathutils import Vector
D=pathlib.Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ids=args or ['liver_hra_female_r01','spleen_hra_female_r01','pancreas_hra_female_r01','bladder_hra_female_r01']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reset():
 bpy.ops.wm.read_factory_settings(use_empty=True)
def row(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices];bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0)
 r=dict(name=o.name,vertices=len(vs),triangles=sum(len(p.vertices)-2 for p in o.data.polygons),matrix_world=[list(v) for v in o.matrix_world],bounds_blender_world=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],world_determinant=o.matrix_world.determinant(),finite=all(math.isfinite(x) for v in vs for x in v),legacy_bmesh_zero_distance_boundary_edges=sum(e.is_boundary for e in bm.edges),legacy_bmesh_zero_distance_nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),zero_area_faces=sum(f.calc_area()==0 for f in bm.faces),materials=[m.name for m in o.data.materials]);bm.free();return r
for id in ids:
 reset();p=D/'models'/id/(id+'.glb');R=D/'reviews'/id;R.mkdir(parents=True,exist_ok=True);bpy.ops.import_scene.gltf(filepath=str(p));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.context.view_layer.update();audit=[row(o) for o in obs]
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=False;sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.09,.09,.09)
 vs=[o.matrix_world@v.co for o in obs for v in o.data.vertices];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)]);target=(lo+hi)/2;dim=max(hi-lo);span=dim*1.3
 for d,power in [((-1,-2,2),180),((1,-1,1),110),((0,2,2),160)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(d)*dim*3);o=bpy.context.object;o.data.energy=power*(dim*3)**2;o.data.size=dim*3;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=span;cam.data.clip_start=.00001;cam.data.clip_end=100;sc.camera=cam;records=[]
 views=[('negative_y',(0,-3,0)),('positive_y',(0,3,0)),('positive_x',(3,0,0)),('oblique',(1,-3,.8)),('inferior',(0,0,-3))]
 if 'context' in id:views=[('oblique',(1,-3,.5)),('positive_x',(3,0,0)),('positive_y',(0,3,0))]
 modes=['source_material','neutral_clay'] if 'r01' in id else ['candidate_material','neutral_clay']
 for mode in modes:
  if mode=='neutral_clay':
   sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.studiolight_rotate_z=0;sc.display.shading.studio_light='paint.sl';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.65,.65,.65);sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.show_specular_highlight=False;sc.display.shading.background_type='WORLD';sc.world.color=(.07,.08,.10)
  for view,delta in views:
   cam.location=target+Vector(delta)*dim;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();fn=mode+'_'+view+'.png';sc.render.filepath=str(R/fn);bpy.ops.render.render(write_still=True);records.append(dict(file=fn,sha256=sha(R/fn),mode=mode,engine=sc.render.engine,camera_position=list(cam.location),target=list(target),orthographic_scale=span,hidden_meshes=[]))
 (R/'exact-export-render-manifest.json').write_text(json.dumps(dict(id=id,glb_file=str(p.relative_to(D)),glb_sha256=sha(p),source_frame='Source glTF +Y up, standard Blender +Z up conversion only; no registration, centering or geometry changes',resolution=[720,720],frame=1,samples=24,views=records,mesh_audit=audit,status='Unreviewed exact-export source screen; parent pixel approval required'),indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(D/'models'/id/(id+'_review_scene.blend')));print('READY',id,sha(p),flush=True)
