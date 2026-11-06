"""Geometry-bound SVG triangle projections. Not screenshots or Cycles renders."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(exist_ok=False,parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';s.camera=camera
views={'whole':((-.003,.012,.125),(.3,-1,.3),.145),'proximal':((0,-.003,.172),(.4,-.5,1),.045)}
panels={};rows=[];colors={};light=Vector((-.6,-.7,.8)).normalized()
for phase,path in [('baseline',a.baseline),('open',a.candidate_dir/'trachea-open.glb'),('cutaway',a.candidate_dir/'trachea-cutaway.glb')]:
 for ob in list(s.objects):
  if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=True)
 all_vertices=[];all_faces=[]
 for ob in s.objects:
  if ob.type!='MESH':continue
  ob.data.calc_loop_triangles();start=len(all_vertices)
  all_vertices.extend(ob.matrix_world@v.co for v in ob.data.vertices)
  all_faces.extend(tuple(start+i for i in tri.vertices) for tri in ob.data.loop_triangles)
 visibility=BVHTree.FromPolygons(all_vertices,all_faces,all_triangles=True)
 for name,(t,d,scale) in views.items():
  if phase=='cutaway' and name=='proximal':continue
  target=Vector(t);view=Vector(d).normalized();camera.location=target+view*.6;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;bpy.context.view_layer.update()
  triangles=[]
  for ob in s.objects:
   if ob.type!='MESH':continue
   ob.data.calc_loop_triangles();vs=[ob.matrix_world@v.co for v in ob.data.vertices]
   projected=[world_to_camera_view(s,camera,v) for v in vs]
   for tri in ob.data.loop_triangles:
    ids=tri.vertices;points=[vs[i] for i in ids];normal=(points[1]-points[0]).cross(points[2]-points[0])
    if normal.length<1e-15:continue
    center=sum(points,Vector())/3
    normal.normalize()
    if normal.dot(view)<0:normal=-normal
    xy=[(projected[i].x*900,(1-projected[i].y)*1000) for i in ids]
    if max(x for x,y in xy)<0 or min(x for x,y in xy)>900 or max(y for x,y in xy)<0 or min(y for x,y in xy)>1000:continue
    band=ob.name.startswith('Authored');mi=tri.material_index
    rgb=(217,205,179) if band else ((197,165,124) if phase=='baseline' or mi==0 else ((195,133,115) if mi==1 else (232,209,171)))
    blocked=visibility.ray_cast(center+normal*1e-6,light,1)[0] is not None
    shade=.30+(.18 if blocked else .70)*max(0,normal.dot(light));color='#'+''.join(f'{round(c*shade):02x}' for c in rgb)
    colors.setdefault(color,len(colors))
    shape='<path class="t c'+str(colors[color])+'" d="M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in xy)+'Z"/>'
    triangles.append((sum(p.dot(view) for p in points)/3,shape))
  panels[phase,name]=''.join(p for _,p in sorted(triangles))
  rows.append({'phase':phase,'view':name,'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera':list(camera.location),'target':t,'orthoscale':scale,'projection':'Two-sided triangles, painter depth ordering and illustrative directional shading; not a raster render'})
for name,phases in [('whole',['baseline','open','cutaway']),('proximal',['baseline','open'])]:
 width=1280 if len(phases)==3 else 900;panel_width=(width-40)/len(phases);factor=(panel_width-12)/900;height=round(110+1000*factor+55)
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">','<title>Trachea: cast and authored teaching shell</title>','<desc>Matched geometry projections, not screenshots. Shell thickness and section positions are illustrative, not segmented specimen wall.</desc>',f'<rect width="{width}" height="{height}" fill="#1c292f"/>','<style>text{font-family:Arial,sans-serif;fill:#eef0ed}.title{font-size:22px;font-weight:600}.label{font-size:18px;font-weight:600}.note{font-size:14px;fill:#bdc7c9}</style>','<text class="title" x="20" y="29">Trachea · '+('continuous airway teaching views' if name=='whole' else 'proximal opening')+'</text>','<text class="note" x="20" y="53">Matched geometry projections · not screenshots · existing cast preserved</text>','<defs><clipPath id="frame"><rect width="900" height="1000"/></clipPath></defs>']
 labels={'baseline':'Before · closed display cast','open':'Current · authored open shell','cutaway':'Current · editorial cutaway'}
 for i,phase in enumerate(phases):
  x=20+i*panel_width;parts.append(f'<text class="label" x="{x:.1f}" y="84">{labels[phase]}</text>')
  parts.append(f'<g transform="translate({x:.1f},100) scale({factor:.8f})" clip-path="url(#frame)"><rect width="900" height="1000" fill="#354046"/>{panels[phase,name]}</g>')
 parts.append(f'<text class="note" x="20" y="{height-23}">Shell thickness, inner surface and cut positions are authored. No measured wall layers or clinical claim.</text></svg>')
 css='<style>.t{stroke-width:.12}'+''.join(f'.c{i}{{fill:{color};stroke:{color}}}' for color,i in colors.items())+'</style>'
 output=a.out/f'comparison-{name}.svg';output.write_text(''.join(parts).replace('</defs>','</defs>'+css)+'\n')
(a.out/'projection-bindings.json').write_text(json.dumps({'views':rows,'files':[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(a.out.glob('*.svg'))]},indent=2)+'\n')
