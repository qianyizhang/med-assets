import bpy,bmesh,math,json,hashlib,sys,argparse
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(args.source);assert hashlib.sha256(S.read_bytes()).hexdigest()=='d42747691a71eea955ca70371a404eecee082b63d1dd2f1787c09e903e2d90d2';O=Path(args.out);O.mkdir(exist_ok=False);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.75;return m
cordmat=mat('Cord teaching ivory',(.68,.59,.45));rootmat=mat('Root teaching ochre',(.57,.40,.21));filmat=mat('Filum teaching neutral',(.64,.65,.61))
def mesh(n,v,f,m):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);me.materials.append(m)
 for p in me.polygons:p.use_smooth=True
 o['derivation']='Authored gross-relationship teaching redesign; not patient registered or complete nerve reconstruction';return o
# Source-like global centerline frame retained; dimensions are illustrative.
def cy(z):return .055+.015*math.sin(math.pi*min(1,max(0,(.322-z)/.442)))
def radius(z):
 r=.0045+.0022*math.exp(-((z-.25)/.05)**2)+.0016*math.exp(-((z+.015)/.045)**2)
 if z<-.085:r*=max(.015,((z+.137)/.052))**.8
 return r
v=[];f=[];N=180;K=48
for i in range(N+1):
 z=.322-(.459)*i/N;r=radius(z)
 for j in range(K):
  a=2*math.pi*j/K;da=math.atan2(math.sin(a+math.pi/2),math.cos(a+math.pi/2));groove=1-.13*math.exp(-(da/.13)**2);v.append((r*math.cos(a)*groove,cy(z)+r*.78*math.sin(a)*groove,z))
for i in range(N):
 for j in range(K):a=i*K+j;b=i*K+(j+1)%K;c=(i+1)*K+(j+1)%K;d=(i+1)*K+j;f.extend([(a,b,c),(a,c,d)])
for i in [0,N]:
 c=len(v);v.append((0,cy(.322-.459*i/N),.322-.459*i/N))
 for j in range(K):f.append((c,i*K+j,i*K+(j+1)%K))
mesh('Authored cord with two enlargements and one conus',v,f,cordmat)
def tube(name,pts,r,m):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=r;cu.bevel_resolution=3;cu.use_fill_caps=True;sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for b,p in zip(sp.bezier_points,pts):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);cu.materials.append(m);o['scope']='Representative strand, not counted clinical root level';return o
# Representative paired anterior/posterior attachments, NOT31pair completeness.
records=[]
levels=[.295,.267,.235,.2,.16,.12,.08,.04,.005,-.03]
for i,z in enumerate(levels):
 for side in [-1,1]:
  rr=radius(z);y=cy(z);drop=.003+.025*i/(len(levels)-1);end=(side*.025,y,z-drop)
  for role,dy in [('dorsal',.003),('ventral',-.003)]:
   pts=[(side*rr*.72,y+math.copysign(rr*.45,dy),z),(side*.012,y+dy,z-drop*.35),(side*.020,y+dy*.5,z-drop*.8),end];tube(f'Representative {role} root upper {i+1} side{side}',pts,.00055,rootmat)
  tube(f'Representative mixed nerve upper {i+1} side{side}',[end,(side*.032,y,z-drop-.002)],.0008,rootmat)
# Lower roots descend along lower cord/conus before diverging; separated trajectories and depths.
for i,z in enumerate([-.045,-.058,-.071,-.084,-.097,-.110,-.123]):
 for side in [-1,1]:
  rr=radius(z);lane=.019-.00165*i;endz=-.158-.011*i;endy=.055-.0015*i;endx=side*(.026-.0017*i)
  for role,dy in [('dorsal',.003),('ventral',-.003)]:
   pts=[(side*rr*.72,cy(z)+math.copysign(rr*.45,dy),z),(side*lane,.055+dy-.0015*i,z-.025),(side*(lane+.001),endy+dy,-.14-.008*i),(endx,endy+dy*.2,endz)];tube(f'Representative descending {role} root {i+1} side{side}',pts,.00048,rootmat);records.append({'role':role,'side':side,'illustrative_lane':i+1,'control_points':pts})
  tube(f'Representative mixed distal nerve {i+1} side{side}',[(endx,endy,endz),(side*(abs(endx)+.006),endy,endz-.004)],.0007,rootmat)
tube('Filum terminale - nonneural teaching strand',[(0,cy(-.137),-.137),(0,.054,-.18),(0,.050,-.242)],.00032,filmat)
# No ganglia added to avoid pretending complete dorsal exit anatomy.
for o in list(bpy.context.scene.objects):
 if o.type=='CURVE':bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(O/'candidate.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False)
(O/'record.json').write_text(json.dumps({'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((O/'candidate.glb').read_bytes()).hexdigest(),'scope':'New authored representative gross-relationship model, source-like frame; not source-exact anatomy.17representative bilateral levels, each anterior/posterior strand. Counts illustrative, NOT31spinalnerve reconstruction. Rootlets, ganglia, meninges and vertebrae omitted. No vertebrallevel registration.','descending_root_controls':records},indent=2))
