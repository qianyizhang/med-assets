#!/usr/bin/env python3
"""Pinned parathyroid localization replay. Requires Python Pillow and Blender 4.3.2.
Never overwrites an existing output directory. Source archive is not bundled.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',required=True,type=Path,help='Pinned Z-Anatomy Startup.blend')
p.add_argument('--baseline',required=True,type=Path,help='Pinned original parathyroids.glb')
p.add_argument('--output',required=True,type=Path,help='New output directory; must not exist')
p.add_argument('--blender',default='blender')
p.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
a=p.parse_args();out=a.output.resolve();source=a.source.resolve();baseline=a.baseline.resolve();font_path=a.font.resolve()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if out.exists():p.error('--output already exists; choose a new directory (nothing overwritten)')
for f,want in [(source,'9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'),(baseline,'9741ddb9dabac9504c9587caafa7a6f51a6765d38a75be48c6229f00a769391f')]:
 if not f.is_file() or sha(f)!=want:p.error('missing or wrong pinned input: '+str(f))
if not font_path.is_file():p.error('Chinese-capable font missing; supply --font')
from PIL import Image
out.mkdir(parents=True,exist_ok=False)

BUILD = r"""
import bpy,pathlib,json,hashlib,math
D=pathlib.Path(OUTPUT); O=D/'candidate-r01'; O.mkdir(); S=pathlib.Path(SOURCE)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
names=['Superior parathyroid gland.r','Superior parathyroid gland.l','Inferior parathyroid gland.r','Inferior parathyroid gland.l','Thyroid gland']
with bpy.data.libraries.load(str(S),link=False) as(a,b): b.objects=names
for o in b.objects: bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get(); objs=[]; records=[]
def material(name,color):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.8;return m
p=material('Parathyroids | illustrative ochre',(.52,.32,.12)); t=material('Thyroid | same-source context only',(.27,.32,.35))
for o in b.objects:
 e=o.evaluated_get(dg);me=e.to_mesh();vs=[tuple(e.matrix_world@v.co) for v in me.vertices];fs=[tuple(p.vertices) for p in me.polygons];e.to_mesh_clear();m=bpy.data.meshes.new(o.name);m.from_pydata(vs,[],fs);m.update();n=bpy.data.objects.new(o.name,m);bpy.context.scene.collection.objects.link(n);m.materials.append(t if o.name=='Thyroid gland' else p)
 for f in m.polygons:f.use_smooth=True
 n['source_name']=o.name;n['role']='context' if o.name=='Thyroid gland' else 'target';n['scope']='One atlas representation; not universal number or placement. No clinical validation.'
 records.append({'name':o.name,'vertices':len(vs),'polygons':len(fs),'centroid':[sum(v[k] for v in vs)/len(vs) for k in range(3)],'bounds':[[min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]],'finite':all(math.isfinite(c) for v in vs for c in v),'zero_area':sum(f.area==0 for f in m.polygons),'modifiers':[{'name':x.name,'type':x.type} for x in o.modifiers],'matrix_world':[list(r) for r in o.matrix_world]});objs.append(n)
for o in b.objects:bpy.data.objects.remove(o,do_unlink=True)
for filename,selection in [('parathyroids_native.glb',objs[:4]),('parathyroids_thyroid_context.glb',objs)]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in selection:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.export_scene.gltf(filepath=str(O/filename),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'source-selection.blend'),compress=True)
(O/'build.json').write_text(json.dumps({'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'objects':records,'export_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*.glb')},'geometry_edits':'None: evaluated source modifiers and native world transforms baked. Material role contrast only. Source extraction/localization correction, not morphology polish.','scope':'Four-gland atlas example with same-source thyroid context; no number/position variability, clinical, or runtime validation.'},indent=2))

"""
CHECK = r"""
import bpy,bmesh,pathlib,json,hashlib,math
from mathutils.kdtree import KDTree
D=pathlib.Path(OUTPUT);O=D/'candidate-r01';bpy.ops.wm.open_mainfile(filepath=str(O/'source-selection.blend'));src={o['source_name']:[tuple(o.matrix_world@v.co) for v in o.data.vertices] for o in bpy.context.scene.objects if o.type=='MESH'}
reports={}
for file in ['parathyroids_native.glb','parathyroids_thyroid_context.glb']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(O/file));rows=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  name=o.get('source_name',o.name);vs=[o.matrix_world@v.co for v in o.data.vertices];kd=KDTree(len(vs))
  for i,v in enumerate(vs):kd.insert(v,i)
  kd.balance();drift=max(kd.find(v)[2] for v in src[name]);bm=bmesh.new();bm.from_mesh(o.data)
  row={'source_name':name,'role':o.get('role'),'vertices':len(vs),'triangles':len(o.data.polygons),'finite':all(math.isfinite(c) for v in vs for c in v),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()==0 for f in bm.faces),'source_to_export_max_vertex_distance_m':drift};bm.free();rows.append(row)
 reports[file]={'sha256':hashlib.sha256((O/file).read_bytes()).hexdigest(),'nodes':rows}
assert len(reports['parathyroids_native.glb']['nodes'])==4
assert len(reports['parathyroids_thyroid_context.glb']['nodes'])==5
assert all(x['finite'] and x['source_to_export_max_vertex_distance_m']<1e-6 for r in reports.values() for x in r['nodes'])
(O/'exact-export-check.json').write_text(json.dumps({'exports':reports,'limitations':'Finite geometry and source/export distance checks only. Nonmanifold diagnostics are indexed GLB topology, not anatomical correctness. No anatomy/clinical/runtime pass.'},indent=2))

"""
EXACT = r"""
import bpy,pathlib,json,hashlib,sys
from mathutils import Vector
D=pathlib.Path(OUTPUT)
for kind,P in [('baseline',pathlib.Path(BASELINE)),('candidate',D/'candidate-r01/parathyroids_thyroid_context.glb')]:
 O=D/(kind+'-exact');O.mkdir(exist_ok=True);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P));objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
 vs=[o.matrix_world@v.co for o in objs for v in o.data.vertices];target=Vector([(min(v[k] for v in vs)+max(v[k] for v in vs))/2 for k in range(3)]);span=max(max(v[k] for v in vs)-min(v[k] for v in vs) for k in range(3));f=span/.15
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
 for delta,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(delta)*f);l=bpy.context.object;l.data.energy=power*f*f;l.data.shape='DISK';l.data.size=.4*f;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=span*1.25;sc.camera=cam;cams=[]
 for name,direction in [('front',(0,-1,0)),('posterior',(0,1,0)),('side',(1,0,0)),('posterior-oblique',(.7,1,.15))]:
  cam.location=target+Vector(direction).normalized()*span*4;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);cams.append({'file':name+'.png','position':list(cam.location),'target':list(target),'ortho_scale':cam.data.ortho_scale})
 (O/'render.json').write_text(json.dumps({'input':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'nodes':[o.name for o in objs],'cameras':cams,'settings':'Cycles CPU 32 samples, 640 square, AgX, no denoise, normalized identical camera directions and relative lights','comparison_limit':'Independent bounds normalization. Different source frames, NOT registered, NOT absolute size comparison. Original baseline materials retained; candidate role colors illustrative.'},indent=2))

"""
NEUTRAL = r"""
import bpy,pathlib,json,hashlib,sys
from mathutils import Vector
D=pathlib.Path(OUTPUT)
for kind,P in [('baseline',pathlib.Path(BASELINE)),('candidate',D/'candidate-r01/parathyroids_thyroid_context.glb')]:
 O=D/(kind+'-neutral');O.mkdir(exist_ok=True);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P));objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
 mat=bpy.data.materials.new('Matched neutral matte');mat.use_nodes=True;pr=mat.node_tree.nodes.get('Principled BSDF');pr.inputs['Base Color'].default_value=(.44,.39,.34,1);pr.inputs['Roughness'].default_value=.8
 for o in objs:o.data.materials.clear();o.data.materials.append(mat)
 vs=[o.matrix_world@v.co for o in objs for v in o.data.vertices];target=Vector([(min(v[k] for v in vs)+max(v[k] for v in vs))/2 for k in range(3)]);span=max(max(v[k] for v in vs)-min(v[k] for v in vs) for k in range(3));f=span/.15
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
 for delta,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(delta)*f);l=bpy.context.object;l.data.energy=power*f*f;l.data.shape='DISK';l.data.size=.4*f;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=span*1.25;sc.camera=cam;cams=[]
 for name,direction in [('posterior',(0,1,0)),('side',(1,0,0))]:
  cam.location=target+Vector(direction).normalized()*span*4;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);cams.append({'file':name+'.png','position':list(cam.location),'target':list(target),'ortho_scale':cam.data.ortho_scale})
 (O/'render.json').write_text(json.dumps({'input':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'nodes':[o.name for o in objs],'cameras':cams,'settings':'Cycles CPU 32 samples, 640 square, AgX, no denoise, normalized identical camera directions and relative lights','comparison_limit':'Independent bounds normalization. Different source frames, NOT registered, NOT absolute size comparison. Both exports rendered in identical neutral matte.'},indent=2))

"""
SHEETS = r"""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
D=out
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for output,sub,views in [('comparison.png','exact',['front','posterior','side','posterior-oblique']),('neutral-comparison.png','neutral',['posterior','side'])]:
 w=480;h=480;im=Image.new('RGB',(len(views)*w,2*(h+42)+75),'#161c24');d=ImageDraw.Draw(im);d.text((16,10),'PARATHYROIDS | localization-only candidate | NOT an anatomy/runtime pass',font=font,fill='white');d.text((16,38),'Independent normalized bounds; same view/light directions. No absolute size comparison.',font=font,fill='#b5c2d2')
 for row,kind in enumerate(['baseline','candidate']):
  for col,v in enumerate(views):
   x=col*w;y=75+row*(h+42);d.text((x+12,y+10),f'{kind.upper()} / {v}',font=font,fill='white');im.paste(Image.open(D/f'{kind}-{sub}'/f'{v}.png').convert('RGB').resize((w,h)),(x,y+42))
 im.save(D/output)

"""
TEACH = r"""
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1280,900),'#161c24');im.paste(Image.open(D/'candidate-exact/posterior.png').convert('RGB'),(320,130));d=ImageDraw.Draw(im)
f=ImageFont.truetype(str(font_path),21);small=ImageFont.truetype(str(font_path),18)
d.text((24,18),'PARATHYROIDS / 甲状旁腺 — posterior localization / 后侧定位示例',font=f,fill='white')
d.text((24,53),'Exact export / 精确导出模型：ochre targets / 黄褐色为目标；gray context / 灰色为甲状腺参照',font=small,fill='#becad8')
def label(lines,xy,leader):
 d.multiline_text(xy,'\n'.join(lines),font=small,fill='#e7ecf3',spacing=6);d.line(leader,fill='#acb9c8',width=2);x,y=leader[-1];d.ellipse((x-3,y-3,x+3,y+3),fill='#e7ecf3')
label(['Superior pair / 上方一对','Source-named targets','沿用来源命名的目标'],(20,275),[(292,334),(360,334),(468,362)])
label(['Inferior pair / 下方一对','Source-named targets','沿用来源命名的目标'],(20,490),[(292,553),(400,553),(525,571)])
label(['Uninterpreted atlas','midline projection','未作解剖判定的图谱正中突起','Not a universal shape','不代表普遍形态'],(975,140),[(970,237),(850,237),(640,275)])
label(['Thyroid context only','仅为甲状腺参照','Not a thyroid quality pass','不表示甲状腺质量通过'],(975,465),[(970,526),(900,526),(836,495)])
d.text((24,790),'One four-gland atlas example; number and position vary. Ectopic locations not represented.',font=small,fill='#d3deeb')
d.text((24,816),'仅为四腺图谱示例；数量、位置存在变异，未展示异位情况。简化镜像形态问题仍在。',font=small,fill='#d3deeb')
d.text((24,850),'No whole-anatomy / clinical / motion / runtime pass. 无完整解剖、临床、运动或运行通过结论。',font=small,fill='#d3deeb')
im.save(D/'teaching-posterior.png')

"""

script=out/'replay-internal.py'
script.write_text('SOURCE='+repr(str(source))+'\nBASELINE='+repr(str(baseline))+'\nOUTPUT='+repr(str(out))+'\n'+BUILD+'\n'+CHECK+'\n'+EXACT+'\n'+NEUTRAL)
with (out/'replay.log').open('w') as log:subprocess.run([a.blender,'-b','--disable-autoexec','-t','2','--python',str(script)],stdout=log,stderr=subprocess.STDOUT,check=True)
expected={'parathyroids_native.glb':'b6fbbabfa7efd12b8c377f5bc56193bd81776daab999a8c1ac8286f693b85b45','parathyroids_thyroid_context.glb':'7759008c5682ac76e77f39f68f5cd421ea42cfe5252cebe9bd82ecc54dc04345'}
for name,want in expected.items():
 if sha(out/'candidate-r01'/name)!=want:raise RuntimeError('Export replay differs: '+name)
exec(SHEETS);D=out;exec(TEACH)
raw=out/'candidate-exact/posterior-oblique.png';clean=out/'posterior-oblique-display.png'
with Image.open(raw) as im:
 pixels=im.convert('RGBA');before=hashlib.sha256(pixels.tobytes()).hexdigest();pixels.save(clean)
with Image.open(clean) as im:after=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
assert before==after
(out/'display-receipt.json').write_text(json.dumps({'source_sha256':sha(raw),'display_sha256':sha(clean),'decoded_rgba_sha256':before,'pixel_identity_verified':True,'operation':'Strip metadata only; no pixel alteration','bound_glb_sha256':expected['parathyroids_thyroid_context.glb']},indent=2))
(out/'replay-receipt.json').write_text(json.dumps({'source_sha256':sha(source),'baseline_sha256':sha(baseline),'exports':expected,'byte_identical_to_frozen_exports':True,'font_sha256':sha(font_path),'output_was_new':True,'scope':'Technical replay only. Localization candidate; no whole anatomy/clinical/runtime pass.'},indent=2))
print('PASS: both GLBs byte-identical; new evidence in '+str(out))
