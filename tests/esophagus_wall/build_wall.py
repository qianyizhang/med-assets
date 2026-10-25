import bpy,math,pathlib,json,hashlib,bmesh
from mathutils import Vector
import argparse,sys
parser=argparse.ArgumentParser(description='Generate independently authored teaching geometry into a NEW directory only.')
parser.add_argument('--output',required=True);parser.add_argument('--params',default=str(pathlib.Path(__file__).with_name('parameters.json')))
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
D=pathlib.Path(a.output).resolve();D.mkdir(parents=True,exist_ok=False)
params=json.loads(pathlib.Path(a.params).read_text())
N=int(params['angular_segments']);L=float(params['length_m']);folds=int(params['illustrative_fold_count'])
assert 24<=N<=1024 and .001<L<1 and 2<=folds<=20
radii=[params[x] for x in ['lumen_radius_m','mucosa_outer_radius_m','submucosa_outer_radius_m','circular_muscle_outer_radius_m','longitudinal_muscle_outer_radius_m','adventitia_outer_radius_m']]
f0=params['lumen_fold_amplitude_m'];f1=params['mucosa_outer_fold_amplitude_m']
assert all(radii[i]<radii[i+1] for i in range(5)) and 0<=f0<radii[0] and 0<=f1 and radii[0]+f0<radii[1]-f1 and radii[1]+f1<radii[2]
wedge=float(params['wedge_degrees_removed']);assert 30<=wedge<=180
A=math.radians(-90+wedge/2);B=math.radians(270-wedge/2)
(D/'parameters.json').write_text(json.dumps(params,indent=2))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# Independent explanatory segment, not a clinical cross-section or measured thickness.
boundary=[lambda t:radii[0]+f0*math.cos(folds*t),lambda t:radii[1]+f1*math.cos(folds*t),lambda t:radii[2],lambda t:radii[3],lambda t:radii[4],lambda t:radii[5]]
layers=[('01 Mucosa - composite',(.56,.22,.25),'Composite mucosa: epithelium, lamina propria and muscularis mucosae not separately resolved.'),('02 Submucosa',(.72,.57,.36),'Connective tissue compartment; glands, vessels and submucosal plexus omitted.'),('03 Muscularis externa - inner circular',(.43,.12,.14),'Inner circular muscle compartment. No individual muscle fibers reconstructed.'),('04 Muscularis externa - outer longitudinal',(.65,.30,.23),'Outer longitudinal muscle compartment. No individual muscle fibers reconstructed.'),('05 Adventitia',(.53,.42,.30),'Illustrative thoracic segment outer connective tissue; not serosa.')]
objects=[];records=[]
for k,(name,color,scope) in enumerate(layers):
 verts=[]
 for z in [0,L]:
  for rfunc in [boundary[k],boundary[k+1]]:
   for i in range(N+1):
    t=A+(B-A)*i/N;r=rfunc(t);verts.append((r*math.cos(t),r*math.sin(t),z))
 stride=N+1
 idx=lambda z,r,i:z*2*stride+r*stride+i
 faces=[]
 for i in range(N):
  faces.extend([(idx(0,0,i),idx(0,0,i+1),idx(1,0,i+1),idx(1,0,i)),(idx(0,1,i),idx(1,1,i),idx(1,1,i+1),idx(0,1,i+1)),(idx(0,0,i),idx(0,1,i),idx(0,1,i+1),idx(0,0,i+1)),(idx(1,0,i),idx(1,0,i+1),idx(1,1,i+1),idx(1,1,i))])
 for i in [0,N]:faces.append((idx(0,0,i),idx(1,0,i),idx(1,1,i),idx(0,1,i)))
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 for p in me.polygons:p.use_smooth=(p.index%4 in [0,1] and p.index<4*N)
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;pr=m.node_tree.nodes.get('Principled BSDF');pr.inputs['Base Color'].default_value=(*color,1);pr.inputs['Roughness'].default_value=.72;me.materials.append(m)
 o['anatomy_id']='esophagus_wall_teaching';o['layer_order_inside_out']=k+1;o['view_role']='authored_illustrative_cutaway';o['scope']=scope;o['not_to_scale']=f'Layer thickness, {"six" if folds==6 else folds}-fold lumen, length, colors and wedge are illustrative; not measured anatomy.'
 objects.append(o);bm=bmesh.new();bm.from_mesh(me);records.append({'node':name,'vertices':len(me.vertices),'polygons':len(me.polygons),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume_m3':bm.calc_volume(signed=True),'zero_area_faces':sum(f.calc_area()==0 for f in bm.faces)});bm.free()
# Direction keys are optional named explanatory cues, not tissue fibers: keep out of GLB.
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
p=D/'esophagus-wall-cutaway-r01.glb';bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
(D/'build-receipt.json').write_text(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'objects':records,'parameters':params,'source_geometry':'Independently authored analytic teaching geometry, not derived from Z-Anatomy or the baseline.'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(D/'editable.blend'),compress=True)
