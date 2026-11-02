import bpy,json,hashlib,sys,argparse,shutil,struct
if not __debug__: raise RuntimeError('Optimized Python is unsupported; integrity assertions are required')
from pathlib import Path
from mathutils import Vector
SCRIPT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--output',required=True);a=parser.parse_args(args)
source=Path(a.source).resolve();P=Path(a.output).resolve()
sys.path.insert(0,str(SCRIPT))
from source_guard import verify_source,verify_camera,require_new_output
verify_source(source.read_bytes())
verify_camera((SCRIPT/'camera-source.json').read_bytes())
require_new_output(P)
P.mkdir(parents=True)
shutil.copyfile(SCRIPT/'camera-source.json',P/'camera-source.json')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
scene=bpy.context.scene; scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.58,0.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
meshes=sorted([o for o in scene.objects if o.type=='MESH'],key=lambda o:o.name)
labels=['gastric','diaphragmatic','colic','hilum','renal']
objs=[next(o for o in meshes if (('_'+k+'_') in o.name or ('_'+k+'_of') in o.name)) for k in labels]
def digest(o):
 return hashlib.sha256(json.dumps({'v':[list(v.co) for v in o.data.vertices],'p':[list(p.vertices) for p in o.data.polygons],'matrix':[list(r) for r in o.matrix_world]},sort_keys=True).encode()).hexdigest()
before={o.name:digest(o) for o in meshes};original_mats={o.name:list(o.data.materials) for o in meshes}
cam=bpy.data.cameras.new('locator_camera');co=bpy.data.objects.new('locator_camera',cam);scene.collection.objects.link(co);scene.camera=co;cam.type='ORTHO'
contract=json.load(open(P/'camera-source.json'));vs=[dict(contract['views'][1]),dict(contract['views'][2])]
a=dict(contract['views'][1]);a['position_three']=[2*t-p for t,p in zip(a['target_three'],a['position_three'])];a['label']={'en':'Derived opposite view','zh':'派生反向视图'};a['derivedFrom']={'view':'candidate_material_oblique.png','transform':'position = 2 * target - original position; unchanged target/up/span'};[a.pop(k,None) for k in ['file','source_evidence_file','source_evidence_sha256']];vs.insert(1,a)
def conv(v):return Vector((v[0],-v[2],v[1]))
for i,v in enumerate(vs):
 pos=conv(v['position_three']);target=conv(v['target_three']);up=conv(v['up_three']);co.location=pos
 # Camera local Z points backward, Y follows exact documented up vector.
 z=(pos-target).normalized();x=up.cross(z).normalized();y=z.cross(x).normalized()
 from mathutils import Matrix
 co.rotation_euler=Matrix((x,y,z)).transposed().to_euler();cam.ortho_scale=v['ortho_vertical_span'];cam.clip_start=.001;cam.clip_end=10
 lights=[]
 for j,(offset,energy,size) in enumerate([((.2,.25,.3),1.5,.45),((-.2,.1,.15),1,.45)]):
  ld=bpy.data.lights.new('neutral_light','AREA');lo=bpy.data.objects.new('neutral_light',ld);scene.collection.objects.link(lo);lo.location=target+Vector(offset);lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=energy;ld.shape='DISK';ld.size=size;lights.append(lo)
 for o in objs:
  o.data.materials.clear()
  for m in original_mats[o.name]:o.data.materials.append(m)
 scene.render.filepath=str(P/f'view-{i}-original.png');bpy.ops.render.render(write_still=True)
 # Opaque emission-ID pass uses the same meshes/camera and normal depth occlusion.
 for j,o in enumerate(objs):
  m=bpy.data.materials.new('ID_'+str(j));m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=((j+1)/6,0,0,1);nt.links.new(e.outputs[0],out.inputs[0]);o.data.materials.clear();o.data.materials.append(m)
 scene.render.filepath=str(P/f'view-{i}-ids.png');bpy.ops.render.render(write_still=True)
 for o in lights:bpy.data.objects.remove(o,do_unlink=True)
for o in objs:
 o.data.materials.clear()
 for m in original_mats[o.name]:o.data.materials.append(m)
assert before=={o.name:digest(o) for o in meshes}
assert all(list(o.data.materials)==original_mats[o.name] for o in objs)
(P/'render-receipt.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'geometryTransformsBeforeAfter':before,'objects':[o.name for o in objs],'views':vs,'sourceMaterialsRestored':True,'renderedFileHashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in P.glob('view-*.png')},'scope':'Exact source exterior annotation; no new geometry or anatomical validation. ID pass diagnostic only.'},indent=2))
