import bpy,bmesh,pathlib,json,hashlib,math,bisect,argparse,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--output',required=True);ap.add_argument('--render',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);P=pathlib.Path(args.baseline).resolve();O=pathlib.Path(args.output).resolve();assert hashlib.sha256(P.read_bytes()).hexdigest()=='5390537c1e27e9630ec93d4d5437d29081c26f88e87889834091e3fca47ccd45';assert not O.exists(),'Output directory must not exist';O.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P));host=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Trachea |'));old=[o for o in bpy.context.scene.objects if o.type=='MESH' and o!=host];levels=sorted(sum((o.matrix_world@v.co).z for v in o.data.vertices)/len(o.data.vertices) for o in old)
verts=[host.matrix_world@v.co for v in host.data.vertices];faces=[tuple(p.vertices) for p in host.data.polygons];hosthash=hashlib.sha256(json.dumps([list(v) for v in verts]).encode()).hexdigest();tree=BVHTree.FromPolygons(verts,faces,all_triangles=False);edges=set(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in faces for i in range(len(f)))
def center(z):
 pts=[]
 for a,b in edges:
  va,vb=verts[a],verts[b]
  if (va.z<=z<vb.z) or (vb.z<=z<va.z):pts.append(va+(vb-va)*((z-va.z)/(vb.z-va.z)))
 if not pts:raise ValueError('no section')
 return Vector(((min(v.x for v in pts)+max(v.x for v in pts))/2,(min(v.y for v in pts)+max(v.y for v in pts))/2,z))
for o in old:bpy.data.objects.remove(o,do_unlink=True)
mat=bpy.data.materials.new('Neutral diagnostic tissue');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.44,.39,.34,1);bs.inputs['Roughness'].default_value=.8;host.data.materials.clear();host.data.materials.append(mat)
records=[];miss=0;bands=[]
for k in range(18):
 z=levels[0]+(levels[-1]-levels[0])*k/17;c=center(z);t=(center(z+.0004)-center(z-.0004)).normalized();post=(Vector((0,1,0))-t*t.y).normalized();right=post.cross(t).normalized();gap=math.radians(80);N=96;M=12;vs=[];fs=[]
 for i in range(N+1):
  a=math.pi/2+gap/2+(2*math.pi-gap)*i/N;rad=right*math.cos(a)+post*math.sin(a)
  for j in range(M):
   q=2*math.pi*j/M;origin=c+t*(.00085*math.cos(q));hit,norm,idx,dist=tree.ray_cast(origin,rad,.04)
   if hit is None:miss+=1;raise ValueError('ray miss '+str((k,i,j)))
   # Elliptical ridge partially embedded; visible height max0.20mm, total illustrative band width1.7mm.
   vs.append(tuple(hit+rad*(.00026*math.sin(q)-.00006)))
 for i in range(N):
  for j in range(M):a=i*M+j;b=i*M+(j+1)%M;fs.append((a,b,b+M,a+M))
 fs.append(tuple(reversed(range(M))));fs.append(tuple(N*M+j for j in range(M)));me=bpy.data.meshes.new('Host conformed illustrative C-band');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Authored illustrative C-band '+str(k+1),me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 o['derivation']='authored anatomical illustration; not source segmented or patient cartilage';o['placement']='host-local sections and ray projections; posterior gap';o['educational_only']=True;bands.append(o);records.append({'z':z,'center':list(c),'tangent':list(t),'posterior':list(post),'vertices':len(vs)})
sc=bpy.context.scene
for k in list(sc.keys()):del sc[k]
sc['scope']='s1233 source-derived display surface unchanged;18 authored host-conforming illustrative C-bands, not segmented cartilage.';sc['coordinate_frame']='Inherited baseline Blender world frame; no registration or mixing with Z-Anatomy.';sc['clinical_status']='Educational illustration; not clinically validated. Shape/dimensions of bands are authored, not patient measurements.';sc['animation']='Static; no animation clips.'
for o in sc.objects:
 if o.type=='MESH' and 'baked_material' in o:del o['baked_material']
bpy.ops.object.select_all(action='DESELECT');host.select_set(True)
for o in bands:o.select_set(True)
bpy.context.view_layer.objects.active=host;bpy.ops.export_scene.gltf(filepath=str(O/'trachea_host_conforming_illustration.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=720;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
allv=verts;target=Vector([(min(v[k] for v in allv)+max(v[k] for v in allv))/2 for k in range(3)]);span=max(max(v[k] for v in allv)-min(v[k] for v in allv) for k in range(3));f=span/.15
for delta,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=target+Vector(delta)*f);l=bpy.context.object;l.data.energy=power*f*f;l.data.shape='DISK';l.data.size=.4*f;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam;cam.data.ortho_scale=span*1.25;cams=[]
for name,delta in ([('front',(0,-1,0)),('posterior',(0,1,0)),('side',(1,0,0)),('oblique',(.8,-1,.25))] if args.render else []):
 cam.location=target+Vector(delta).normalized()*span*4;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);cams.append({'file':name+'.png','position':list(cam.location),'target':list(target),'quaternion_wxyz':list(cam.rotation_euler.to_quaternion()),'ortho_scale':cam.data.ortho_scale})
endhash=hashlib.sha256(json.dumps([list(host.matrix_world@v.co) for v in host.data.vertices]).encode()).hexdigest();r={'baseline_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'export_sha256':hashlib.sha256((O/'trachea_host_conforming_illustration.glb').read_bytes()).hexdigest(),'host_before_world_vertices_sha256':hosthash,'host_after_world_vertices_sha256':endhash,'host_unchanged':hosthash==endhash,'host_faces_sha256':hashlib.sha256(json.dumps(faces).encode()).hexdigest(),'removed_authored_rings':len(old),'new_authored_bands':18,'count_and_dimensions':'Illustrative design within cited general16–20 count, NOT patient-specific measurement. Width1.7mm, maxradial elevation0.2mm; posterior gap80degrees illustrative. Existing baseline ring extent retained.','ray_misses':miss,'sections':records,'cameras':cams,'status':'pending visual and independent checks; not clinical/runtime pass'};(O/'qa.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(O/'review.blend'),compress=True)
