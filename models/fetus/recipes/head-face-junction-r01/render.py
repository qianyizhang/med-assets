import bpy,math,json,hashlib,pathlib,argparse,sys
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,required=True);parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);D=args.output
if D.exists():raise FileExistsError('Use a fresh evidence directory')
D.mkdir(parents=True)

for path,sha in [(args.source,'84d3f9559dac7bf175514194554d8ca5929f1d9d2666fae1bbc6b09512b4fca8'),(args.candidate,'3f4becca8672deb66267eac23e173ab62b75ac9e2c63510aecc7cd23f6a84272')]:
 if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Unexpected source/candidate identity')
 bindings=[]
for label,path in [('Original',args.source),('Updated',args.candidate)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=650;scene.render.resolution_y=650;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.12,.14,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
 scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
 for loc,power,size in [((.15,-.35,.2),7,.24),((.55,-.12,.1),4,.20),((.2,.15,.10),5,.25)]:
  bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((.31,-.1,-.12))-l.location).to_track_quat('-Z','Y').to_euler()
 for name,target,pos,scale in [('front-whole',(.31,-.10,-.12),(.31,-.6,-.12),.20),('left-whole',(.31,-.10,-.12),(.85,-.10,-.12),.20),('back-whole',(.31,-.10,-.12),(.31,.5,-.12),.20),('front-detail',(.315,-.10,-.073),(.315,-.6,-.073),.083),('left-detail',(.315,-.10,-.073),(.85,-.10,-.073),.083)]:
  bpy.ops.object.camera_add(location=pos);cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
  p=D/f'{label.lower()}-{name}.png';scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  bindings.append({'label':label,'view':name,'artifactSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'file':p.name,'imageSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'camera':pos,'target':target,'orthoScale':scale,'samples':24})
 if label=='Updated':bpy.ops.wm.save_as_mainfile(filepath=str(D/'candidate-v1-render-review.blend'))
(D/'render-bindings.json').write_text(json.dumps(bindings,indent=2))
