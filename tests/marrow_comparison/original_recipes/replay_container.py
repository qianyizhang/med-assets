import bpy,bmesh,json,hashlib,pathlib
from mathutils import Vector
D=pathlib.Path(__file__).resolve().parent.parent/'replay-container';D.mkdir(exist_ok=False)
SRC=D.parent/'sources/BP3D-FJ3365.obj'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(SRC),forward_axis='Y',up_axis='Z')
o=bpy.context.selected_objects[0];o.name='BP3D_FJ3365_right_femur_source_exterior';o.scale=(.001,)*3;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.72;return m
bone=mat('Source exterior | neutral bone',(.68,.61,.45));inner=mat('Illustrative inner boundary | NOT measured cortex',(.39,.43,.45));cut=mat('Illustrative section rim | thickness arbitrary',(.9,.83,.66))
o.data.materials.clear();o.data.materials.append(bone)
o['source']='BodyParts3D 4.0 FJ3365 / FMA24474';o['source_sha256']=sha(SRC);o['license']='CC BY 4.0; historical OBJ header retained';o['geometry_scope']='Unchanged source vertices, millimetres to metres only'
bpy.ops.export_scene.gltf(filepath=str(D/'source-exterior.glb'),export_format='GLB',use_selection=True,export_extras=True)
# Derived teaching presentation. Cut away anterior part, retain posterior surface.
o.name='Proximal_femur_exterior__source_derived_crop_and_section'
# Exact-coordinate remap only in derivative: no tolerance welding and no moved vertices.
lookup={};points=[];mapping={}
for v in o.data.vertices:
 key=tuple(v.co)
 if key not in lookup:lookup[key]=len(points);points.append(key)
 mapping[v.index]=lookup[key]
faces=[[mapping[i] for i in p.vertices] for p in o.data.polygons]
mesh=bpy.data.meshes.new('Exact-coordinate seam-remapped derivative');mesh.from_pydata(points,[],faces);mesh.update();o.data=mesh;o.data.materials.append(bone)
bm=bmesh.new();bm.from_mesh(o.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=Vector((0,0,.65)),plane_no=Vector((0,0,1)),clear_inner=True,clear_outer=False)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=Vector((0,-.08,.75)),plane_no=Vector((0,1,-.06)),clear_inner=True,clear_outer=False)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
o.data.materials.append(inner);o.data.materials.append(cut)
mod=o.modifiers.new('ILLUSTRATIVE inward boundary 2.5 mm | NOT measurement','SOLIDIFY');mod.thickness=.0025;mod.offset=-1;mod.use_even_offset=True;mod.material_offset=1;mod.material_offset_rim=2
bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
# Separate conceptual layers by material, without changing positions.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='MATERIAL');bpy.ops.object.mode_set(mode='OBJECT')
objs=list(bpy.context.selected_objects)
for a in objs:
 ids={p.material_index for p in a.data.polygons};mats={a.data.materials[i].name for i in ids}
 if any('inner boundary' in x for x in mats): a.name='ILLUSTRATIVE_inner_boundary__not_measured_anatomy'; role='authored-illustrative-inner-boundary'
 elif any('section rim' in x for x in mats):a.name='ILLUSTRATIVE_section_rim__2p5mm_not_measured';role='authored-illustrative-section-rim'
 else:a.name='BP3D_exterior__cropped_and_sectioned';role='source-derived-cropped-exterior'
 a['geometry_scope']='Exterior cropped/sectioned from BP3D; inner boundary/rim independently illustrative';a['layer_role']=role;a['scope']='Conceptual proximal femur teaching section; no marrow segmentation; no trabeculae';a['thickness']='2.5 mm illustrative display choice, NOT a measurement';a['source_sha256']=sha(SRC)
 for p in a.data.polygons:p.use_smooth=role!='authored-illustrative-section-rim'
 bpy.context.view_layer.objects.active=a
 # Recompute custom normal representation only through export; keep mesh positions.
bpy.ops.export_scene.gltf(filepath=str(D/'container-r03.glb'),export_format='GLB',use_selection=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(D/'container-r03.blend'))
rep={'source':str(SRC),'sourceSha256':sha(SRC),'sourceUnit':'mm','displayUnit':'m','sourceConversion':'.001 uniform scale only','cutPlane':{'point_m':[0,-.08,.75],'normal':[0,1,-.06],'retained':'posterior half'},'crop':'z >= 0.650 m','illustrativeBoundaryThickness_m':.0025,'measuredThickness':False,'marrowSpace':'Unfilled visible teaching cavity; not segmented tissue or volume','derivativeSeamTreatment':'Exact-coordinate vertex remap before shell construction; no moved vertices; original exterior retained separately','noTrabeculae':True,'noRedYellowMarrowDistribution':True,'exports':[{ 'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in [D/'source-exterior.glb',D/'container-r03.glb']],'objects':[{'name':a.name,'vertices':len(a.data.vertices),'polygons':len(a.data.polygons),'role':a['layer_role']} for a in objs]}
(D/'build-binding.json').write_text(json.dumps(rep,indent=2))
print('BUILD_COMPLETE',json.dumps(rep))
