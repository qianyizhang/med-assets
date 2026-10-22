import os
import bpy,os,math,json
from mathutils import Vector
from PIL import Image,ImageDraw
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse'];c['material_set']=0;c['cutaway']=0;s.frame_set(1);s.cycles.use_denoising=False;s.cycles.samples=1
# Assemble exact, unmodified reference wall meshes; record polygon provenance so UVs
# can be copied back to the original separate editable anatomical objects.
names=['LV | complete wall','RV | complete wall','LA | complete wall','RA | complete wall']
verts=[];faces=[];mats=[];matinds=[];provenance=[]
for name in names:
 ob=bpy.data.objects[name];base=len(verts);verts.extend(tuple(v.co) for v in ob.data.vertices)
 local={}
 for i,ma in enumerate(ob.data.materials):
  if ma not in mats:mats.append(ma)
  local[i]=mats.index(ma)
 for po in ob.data.polygons:
  faces.append(tuple(base+v for v in po.vertices));matinds.append(local[po.material_index]);provenance.append((name,po.index))
me=bpy.data.meshes.new('Four-chamber wall • shared UV atlas');me.from_pydata(verts,[],faces);me.update()
ob=bpy.data.objects.new('TEXTURE STUDY • four-chamber walls • 2K baked atlas',me)
col=bpy.data.collections.new('11 TEXTURE PIPELINE STUDY • optional');s.collection.children.link(col);col.objects.link(ob)
for ma in mats:me.materials.append(ma)
for p,i in zip(me.polygons,matinds):p.material_index=i;p.use_smooth=True
uv=me.uv_layers.new(name='Baked tissue atlas')
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.25,correct_aspect=True,scale_to_bounds=False);bpy.ops.object.mode_set(mode='OBJECT');me=ob.data;uv=me.uv_layers['Baked tissue atlas']
# UV-only transfer changes neither vertices, faces, registration nor labels.
for name in names:
 me2=bpy.data.objects[name].data
 if not me2.uv_layers.get('Baked tissue atlas'):me2.uv_layers.new(name='Baked tissue atlas')
 me2.uv_layers.active=me2.uv_layers['Baked tissue atlas'];me2.uv_layers['Baked tissue atlas'].active_render=True
for dstpo,(name,pi) in zip(me.polygons,provenance):
 srcpo=bpy.data.objects[name].data.polygons[pi];target=bpy.data.objects[name].data.uv_layers['Baked tissue atlas']
 for a,b in zip(srcpo.loop_indices,dstpo.loop_indices):target.data[a].uv=uv.data[b].uv
# Image-based UV layout is the actual unwrap, not a generic wireframe illustration.
size=2048;im=Image.new('RGB',(size,size),(18,24,32));draw=ImageDraw.Draw(im)
for p in me.polygons:
 xy=[(float(uv.data[i].uv.x)*(size-1),(1-float(uv.data[i].uv.y))*(size-1)) for i in p.loop_indices]
 draw.line(xy+[xy[0]],fill=(74,156,169),width=1)
im.save(R+'/textures/wall_atlas_UV_layout_2K.png')
# Actual Cycles texture baking. No lighting is baked into color.
s.render.bake.use_pass_direct=False;s.render.bake.use_pass_indirect=False;s.render.bake.use_pass_color=True;s.render.bake.margin=8;s.render.bake.use_selected_to_active=False
images={}
for kind,typ,colorspace in [('BaseColor','DIFFUSE','sRGB'),('Roughness','ROUGHNESS','Non-Color'),('Normal_OpenGL','NORMAL','Non-Color')]:
 image=bpy.data.images.new('Wall atlas '+kind+' 2K',width=size,height=size,alpha=False);image.colorspace_settings.name=colorspace
 for ma in mats:
  nodes=ma.node_tree.nodes
  for no in nodes:no.select=False
  target=nodes.new('ShaderNodeTexImage');target.name='BAKE TARGET '+kind;target.label='Baked '+kind+' • 2K shared wall atlas';target.image=image;target.select=True;nodes.active=target
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.object.bake(type=typ,normal_space='TANGENT',use_clear=True,margin=8)
 image.filepath_raw=R+'/textures/wall_atlas_'+kind+'_2K.png';image.file_format='PNG';image.save();image.pack();images[kind]=image
 print('BAKED',kind,flush=True)
# Single standard PBR texture material on the optional pipeline study mesh.
ma=bpy.data.materials.new('BAKED TISSUE • shared 2K PBR atlas');ma.use_nodes=True;nodes=ma.node_tree.nodes;links=ma.node_tree.links;p=nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.35;p.inputs['Coat Weight'].default_value=.12
uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map='Baked tissue atlas';uvnode.location=(-800,0)
for i,(kind,image) in enumerate(images.items()):
 tx=nodes.new('ShaderNodeTexImage');tx.image=image;tx.location=(-560,240-i*260);links.new(uvnode.outputs['UV'],tx.inputs['Vector'])
 if kind=='BaseColor':links.new(tx.outputs['Color'],p.inputs['Base Color'])
 elif kind=='Roughness':links.new(tx.outputs['Color'],p.inputs['Roughness'])
 else:
  normal=nodes.new('ShaderNodeNormalMap');normal.space='TANGENT';normal.uv_map='Baked tissue atlas';normal.location=(-250,-280);links.new(tx.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],p.inputs['Normal'])
me.materials.clear();me.materials.append(ma)
for po in me.polygons:po.material_index=0
ob['purpose']='Actual mesh / UV / baked base-color, roughness, tangent-normal pipeline demonstration. Shares exact reference wall positions. Do not display together with original walls because surfaces coincide.'
ob['scope']='Atlas covers four major chamber walls including inner/outer surfaces. Fine details retain native procedural materials.'
# Standalone textured GLB demo. Use scene root metre correction in postprocess.
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=R+'/exports/Cardiac_Walls_Baked_PBR_ED.glb',export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_extras=True)
ob.hide_render=True;ob.hide_set(True);col.hide_render=True
# The original three shader presets remain intact. UVs and packed texture assets are
# available on the original editable objects, and the standard-PBR study mesh shows use.
readme=bpy.data.texts.new('TEXTURE ATLAS • actual baked maps')
readme.write('Actual 2048×2048 Cycles bakes cover all four major chamber walls, inner and outer surfaces. UV layer Baked tissue atlas is present on the original separate wall meshes. The optional 11 TEXTURE PIPELINE STUDY collection contains a coincident single-material demonstration mesh; hide the original walls before unhiding it. BaseColor=sRGB, Roughness=Non-Color, Normal_OpenGL=Non-Color tangent-space +Y normal. Fine anatomy retains procedural nodes; the clinical and transparent looks are material presets. The original procedural tissue branch is retained for the complete model. Textures are packed and also exported as PNGs.\n')
bpy.ops.object.select_all(action='DESELECT');c.select_set(True);bpy.context.view_layer.objects.active=c
bpy.ops.wm.save_as_mainfile(filepath=R+'/Cardiac_Atlas.blend')
json.dump({'atlas_resolution':[2048,2048],'scope':'LV,RV,LA,RA complete wall meshes, outer and inner surfaces','UV_layer':'Baked tissue atlas','base_color':'sRGB','roughness':'linear Non-Color','normal':'tangent-space OpenGL +Y, Non-Color','method':'Actual Blender Cycles DIFFUSE COLOR-only, ROUGHNESS and NORMAL bakes','fine_details':'remain procedural; not all anatomy baked','native_presets':'tissue procedural; clinical and transparent materials','demo_mesh':'11 TEXTURE PIPELINE STUDY / Cardiac_Walls_Baked_PBR_ED.glb'},open(R+'/textures/ATLAS_MANIFEST.json','w'),indent=2)
print('ATLAS COMPLETE',flush=True)
