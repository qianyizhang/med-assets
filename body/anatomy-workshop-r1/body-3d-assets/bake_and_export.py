import bpy,bmesh,json,os,math,hashlib
from pathlib import Path
from mathutils import Vector
from PIL import Image,ImageDraw
import numpy as np
R=Path(__file__).resolve().parent;D=R.parent/'body-3d-delivery';s=bpy.context.scene;c=bpy.data.objects['WORKSHOP CONTROL · material and cutaway'];c['material_mode']=0;c['cutaway']=0;s.cycles.samples=1;s.cycles.use_denoising=False
om=json.load(open(R/'object_map.json'));manifest=json.load(open(D/'manifest.json'));specs={a['id']:a for a in manifest['assets']};qa=[];baked={};saved_slots={}
for col in bpy.data.collections:col.hide_viewport=False
for id,names in om.items():
 for name in names:
  ob=bpy.data.objects[name]
  try:ob.driver_remove('hide_viewport')
  except:pass
  ob.hide_viewport=False;ob.hide_set(False)
bpy.context.view_layer.update()
for id,names in om.items():
 obs=[bpy.data.objects[n] for n in names];saved_slots[id]=[(ob,[m for m in ob.data.materials],[p.material_index for p in ob.data.polygons]) for ob in obs]
 if id=='heart_detailed':continue
 verts=[];faces=[];materials=[];indices=[];prov=[]
 for ob in obs:
  base=len(verts);verts.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices);local={}
  for i,ma in enumerate(ob.data.materials):
   if ma not in materials:materials.append(ma)
   local[i]=materials.index(ma)
  for p in ob.data.polygons:faces.append(tuple(base+i for i in p.vertices));indices.append(local.get(p.material_index,0));prov.append((ob.name,p.index))
 me=bpy.data.meshes.new(id+' bake atlas mesh');me.from_pydata(verts,[],faces);me.update();proxy=bpy.data.objects.new(id+' UV bake proxy',me);s.collection.objects.link(proxy)
 for ma in materials:me.materials.append(ma)
 for p,mi in zip(me.polygons,indices):p.material_index=mi;p.use_smooth=True
 bpy.ops.object.select_all(action='DESELECT');proxy.select_set(True);bpy.context.view_layer.objects.active=proxy;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(62),island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT');uv=proxy.data.uv_layers.active;uv.name='Teaching UV'
 # Copy packed atlas UVs to original topology using exact polygon provenance.
 for ob in obs:
  layer=ob.data.uv_layers.get('Teaching UV') or ob.data.uv_layers.new(name='Teaching UV')
  for other in list(ob.data.uv_layers):
   if other.name!='Teaching UV':ob.data.uv_layers.remove(other)
  layer=ob.data.uv_layers['Teaching UV'];ob.data.uv_layers.active=layer;layer.active_render=True
 for p,(name,idx) in zip(proxy.data.polygons,prov):
  orig=bpy.data.objects[name];target=orig.data.polygons[idx];layer=orig.data.uv_layers['Teaching UV']
  for a,b in zip(target.loop_indices,p.loop_indices):layer.data[a].uv=uv.data[b].uv
 # All three maps are actual Cycles bakes, including procedural bump in tangent normals.
 images={};res=1024
 for suffix,typ in [('BaseColor','DIFFUSE'),('Roughness','ROUGHNESS'),('Normal_OpenGL','NORMAL')]:
  im=bpy.data.images.new(id+' '+suffix+' 1K',width=res,height=res,alpha=True);im.colorspace_settings.name='sRGB' if suffix=='BaseColor' else 'Non-Color';im.generated_color=(0,0,0,0);im.use_fake_user=True
  for ma in materials:
   nt=ma.node_tree;n=nt.nodes.get('BAKE TARGET') or nt.nodes.new('ShaderNodeTexImage');n.name='BAKE TARGET';n.image=im;nt.nodes.active=n
  s.render.bake.use_selected_to_active=False;s.render.bake.margin=12;s.render.bake.use_clear=True
  if typ=='DIFFUSE':s.render.bake.use_pass_direct=False;s.render.bake.use_pass_indirect=False;s.render.bake.use_pass_color=True
  bpy.ops.object.bake(type=typ,normal_space='TANGENT');im.filepath_raw=str(D/'textures'/f'{id}_{suffix}_1K.png');im.file_format='PNG';im.save();im.pack();images[suffix]=im
 # Wire layout shows the actual packed shared UVs.
 plate=Image.new('RGB',(1024,1024),(13,25,35));dr=ImageDraw.Draw(plate)
 for p in proxy.data.polygons:
  xy=[(uv.data[i].uv.x*1023,(1-uv.data[i].uv.y)*1023) for i in p.loop_indices];dr.line(xy+[xy[0]],fill=(75,163,183),width=1)
 plate.save(D/'textures'/f'{id}_UV_1K.png')
 # Portable PBR node graph retained alongside the original editable procedural presets.
 ma=bpy.data.materials.new(id+' · baked portable PBR');ma.use_nodes=True;ma.use_fake_user=True;nt=ma.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.4
 for suffix,socket in [('BaseColor','Base Color'),('Roughness','Roughness')]:
  tx=nt.nodes.new('ShaderNodeTexImage');tx.image=images[suffix];nt.links.new(tx.outputs['Color'],p.inputs[socket])
 tx=nt.nodes.new('ShaderNodeTexImage');tx.image=images['Normal_OpenGL'];nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=1;nt.links.new(tx.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],p.inputs['Normal']);baked[id]=ma
 normal=np.asarray(Image.open(D/'textures'/f'{id}_Normal_OpenGL_1K.png').convert('RGBA'));mask=(normal[:,:,2]>200)&(normal[:,:,3]>0);rgb=normal[:,:,:3][mask]
 uvvals=np.array([list(d.uv) for d in uv.data]);maxerror=0
 for p,(name,idx) in zip(proxy.data.polygons,prov):
  original=bpy.data.objects[name];op=original.data.polygons[idx];layer=original.data.uv_layers['Teaching UV']
  for a,b in zip(op.loop_indices,p.loop_indices):maxerror=max(maxerror,(layer.data[a].uv-uv.data[b].uv).length)
 qa.append({'asset':id,'resolution':res,'objects':len(obs),'polygons':len(me.polygons),'loops':len(me.loops),'UV_bounds':[uvvals.min(0).tolist(),uvvals.max(0).tolist()],'UV_transfer_max_error':maxerror,'normal_RGB_min':rgb.min(0).tolist(),'normal_RGB_max':rgb.max(0).tolist(),'normal_RGB_stddev':rgb.std(0).tolist(),'normal_covered_pixels':int(mask.sum()),'normal_nonflat_pixels':int(((abs(rgb[:,0].astype(int)-128)>1)|(abs(rgb[:,1].astype(int)-128)>1)).sum()),'normal_convention':'Tangent-space OpenGL +Y; Non-Color','base_color_space':'sRGB','roughness_space':'Non-Color'})
 bpy.data.objects.remove(proxy,do_unlink=True);specs[id]['textureFiles']={k:f'textures/{id}_{k}_1K.png' for k in images};specs[id]['UVLayout']=f'textures/{id}_UV_1K.png'
 print('BAKED',id,flush=True)
json.dump(qa,open(D/'docs/UV_TEXTURE_QA.json','w'),indent=2)
# Export individually selectable organs. All role variants are present; viewer selects visibility.
topology=[]
for id,names in om.items():
 obs=[bpy.data.objects[n] for n in names]
 for col in bpy.data.collections:col.hide_render=False;col.hide_viewport=False
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:
  for prop in ['hide_render','hide_viewport']:
   try:ob.driver_remove(prop)
   except:pass
  ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False);ob.select_set(True)
  if id in baked:ob.data.materials.clear();ob.data.materials.append(baked[id]);ob['baked_material']=baked[id].name
  for p in ob.data.polygons:
   if id in baked:p.material_index=0
 bpy.context.view_layer.update();coords=[ob.matrix_world@v.co for ob in obs for v in ob.data.vertices];bv=np.array([(v.x,v.z,-v.y) for v in coords]);triangles=0
 for ob in obs:
  ob.data.calc_loop_triangles();triangles+=len(ob.data.loop_triangles)
  bm=bmesh.new();bm.from_mesh(ob.data);boundary=sum(e.is_boundary for e in bm.edges);nonman=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free();topology.append({'asset':id,'object':ob.name,'anatomy_id':ob.get('anatomy_id'),'view_role':ob.get('view_role'),'vertices':len(ob.data.vertices),'triangles':len(ob.data.loop_triangles),'boundary_edges':boundary,'nonmanifold_edges':nonman,'signed_local_volume_m3':volume,'UV_layers':[u.name for u in ob.data.uv_layers]})
 path=D/'meshes'/f'{id}.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_animations=False,export_texcoords=True,export_normals=True,export_materials='EXPORT')
 a=specs[id];a['bbox']=[bv.min(0).tolist(),bv.max(0).tolist()];a['vertices']=len(coords);a['triangles']=triangles;a['bytes']=path.stat().st_size;a['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();a['status']='ready';a['nodes']=[{'name':o.name,'anatomy_id':o.get('anatomy_id'),'view_role':o.get('view_role'),'derivation':o.get('derivation')} for o in obs]
 json.dump(manifest,open(D/'manifest.json','w'),ensure_ascii=False,indent=2)
 # Restore original editable three-preset materials and visibility drivers.
 for ob,slots,indices in saved_slots[id]:
  ob.data.materials.clear()
  for ma in slots:ob.data.materials.append(ma)
  for p,mi in zip(ob.data.polygons,indices):p.material_index=mi
  role=ob.get('view_role')
  if (role=='surface' and a['cutawaySupport']) or role in ['cutaway','detail']:
   for prop in ['hide_render','hide_viewport']:
    d=ob.driver_add(prop).driver;d.expression='c>.5' if role=='surface' else 'c<.5';v=d.variables.new();v.name='c';v.type='SINGLE_PROP';v.targets[0].id=c;v.targets[0].data_path='["cutaway"]'
 print('EXPORTED',id,a['bytes'],flush=True)
json.dump(topology,open(D/'docs/MESH_QA.json','w'),indent=2)
for col in bpy.data.collections:
 if col.name.startswith('heart_detailed'):col.hide_render=True;col.hide_viewport=True
c['material_mode']=0;c['cutaway']=0;s.camera=bpy.data.objects['CAM · complete assembly'];s.cycles.samples=64
for fn in ['build_collection.py','refine_and_preview.py','finalize_geometry.py','bake_and_export.py']:
 tx=bpy.data.texts.new(fn);tx.write(open(R/fn).read())
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
print('BAKING AND EXPORT COMPLETE',flush=True)
