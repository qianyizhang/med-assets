import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
bpy.context.preferences.filepaths.save_version=0
D=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=json.loads((D/'candidate-manifest.json').read_text());records=[]
def setup_scene(s,center,span):
 s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False;s.view_settings.view_transform='Standard';s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.studiolight_rotate_z=0;sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=False;sh.show_specular_highlight=False;sh.background_type='WORLD';s.world=bpy.data.worlds.new('ReviewWorld');s.world.color=(.035,.04,.05)
 cd=bpy.data.cameras.new('ExactExportReviewCamera');cam=bpy.data.objects.new('ExactExportReviewCamera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=span*1.18;cd.clip_start=.00001;cd.clip_end=10;return cam
for item in manifest:
 bpy.ops.wm.read_factory_settings(use_empty=True);p=D/item['candidateFile'];assert sha(p)==item['candidateSha256'];bpy.ops.import_scene.gltf(filepath=str(p));bpy.context.view_layer.update();s=bpy.context.scene;meshes=[o for o in s.objects if o.type=='MESH'];co=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box];lo=Vector([min(q[i] for q in co) for i in range(3)]);hi=Vector([max(q[i] for q in co) for i in range(3)]);center=(lo+hi)/2;span=max(hi-lo);cam=setup_scene(s,center,span);out=D/'reviews'/item['id'];out.mkdir(parents=True,exist_ok=True)
 rec={'id':item['id'],'exportFile':str(p),'exportSha256':sha(p),'renderIdentity':'Every image below is from this GLB freshly imported into an empty scene. Geometry/materials/transforms not edited; explicit source-layer hide_render only.','frame':'Native HRA glTF metre coordinates preserved, imported using standard glTF-to-Blender axis conversion. Camera labels are review axes, not a new anatomical registration.','boundsBlenderM':[list(lo),list(hi)],'coordinateConversion':'glTF (x,y,z) to Blender (x,-z,y)','cameraViews':{'front':'Blender -Y = native glTF +Z','back':'Blender +Y = native glTF -Z','medial':'Blender -X for left / +X for right; source-side-informed review view'},'nodes':[],'views':{}}
 for ob in meshes:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-9);rec['nodes'].append({'name':ob.name,'sourceLabel':ob.get('label'),'sourceOntology':ob.get('ontologyid'),'sourceNodeType':ob.get('node_type'),'layer_key':ob.get('layer_key'),'vertices':len(ob.data.vertices),'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons),'boundaryEdgesAfterDiagnostic1nmWeld':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdgesAfterDiagnostic1nmWeld':sum(not e.is_manifold for e in bm.edges),'degenerateFacesAfterDiagnostic1nmWeld':sum(f.calc_area()<1e-16 for f in bm.faces)});bm.free()
 views=[('front',(0,-3,0)),('back',(0,3,0)),('medial',(-3,0,0) if item['id'].endswith('left') else (3,0,0))]
 for mode,layers in item['viewModes'].items():
  visible=[];hidden=[]
  for ob in meshes:ob.hide_render=ob.get('layer_key') not in layers;(hidden if ob.hide_render else visible).append(ob.name)
  for view,offset in views:
   cam.location=center+Vector(offset)*span;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();im=out/(mode+'_'+view+'.png');s.render.filepath=str(im);bpy.ops.render.render(write_still=True);rec['views'][mode+'_'+view]={'path':str(im),'sha256':sha(im),'engine':'Workbench neutral, source material base colors, specular off; not runtime PBR proof','visibleNodes':visible,'hiddenNodes':hidden,'cameraPositionM':list(cam.location),'lookAtM':list(center),'orthographicScaleM':cam.data.ortho_scale}
 # Save an editable inspection scene, all geometry visible, neutral Workbench diagnostic settings.
 for ob in meshes:ob.hide_render=False;ob.hide_set(False)
 cam.location=center+Vector(views[0][1])*span;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();blend=D/'models'/item['id']/(item['id']+'_hra_female_r02_review.blend');bpy.ops.wm.save_as_mainfile(filepath=str(blend));rec['reviewBlend']={'path':str(blend),'sha256':sha(blend),'note':'Review setup only, GLB remains authoritative candidate; no animation or geometry cleanup.'}
 # Illustrative matte PBR materials in path-traced renders, with broad soft area lights.
 s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=False;s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.06,.07,.09,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
 for name,pos,power,size in [('Key',(-2,-3,4),5,2),('Fill',(3,-1,1),2,2),('Rim',(0,3,3),3,2)]:
  ld=bpy.data.lights.new(name,'AREA');lo_=bpy.data.objects.new(name,ld);s.collection.objects.link(lo_);lo_.location=center+Vector(pos)*span;lo_.rotation_euler=(center-lo_.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.shape='DISK';ld.size=size*span
 for view,offset in views:
  cam.location=center+Vector(offset)*span;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();im=out/('pbr_all_source_'+view+'.png');s.render.filepath=str(im);bpy.ops.render.render(write_still=True);rec['views']['pbr_all_source_'+view]={'path':str(im),'sha256':sha(im),'engine':'Cycles64samples, no denoising, source base colors with illustrative matte roughness 0.72; diagnostic lighting not a runtime/browser proof','visibleNodes':[o.name for o in meshes],'hiddenNodes':[],'cameraPositionM':list(cam.location),'lookAtM':list(center),'orthographicScaleM':cam.data.ortho_scale}
 (out/'record.json').write_text(json.dumps(rec,indent=2));records.append(rec)
(D/'exact-export-render-manifest.json').write_text(json.dumps(records,indent=2));print('DONE exact exports',[(r['id'],len(r['views'])) for r in records])
