import bpy,bmesh,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;D=R.parent/'body-3d-delivery';s=bpy.context.scene;report=[]
for o in bpy.data.objects:
 if o.get('view_role')!='surface' or 'source_file' not in o:continue
 bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);bm.free()
 if not bad:continue
 oldv=[v.co.copy() for v in o.data.vertices];oldbvh=BVHTree.FromPolygons(oldv,[list(p.vertices) for p in o.data.polygons]);oldfaces=len(o.data.polygons)
 o.hide_viewport=False;o.hide_set(False);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;o.data.remesh_voxel_size=.0012;o.data.use_remesh_preserve_volume=True;bpy.ops.object.voxel_remesh()
 mod=o.modifiers.new('Volume-preserving repair cleanup','SMOOTH');mod.factor=.30;mod.iterations=2;bpy.ops.object.modifier_apply(modifier=mod.name)
 if len(o.data.polygons)>12000:
  mod=o.modifiers.new('Display remesh reduction','DECIMATE');mod.ratio=12000/len(o.data.polygons);bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 newbad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(o.data);bm.free()
 for p in o.data.polygons:p.use_smooth=True
 distances=[oldbvh.find_nearest(v.co)[3] for v in o.data.vertices];distances.sort();entry={'object':o.name,'before_nonmanifold_edges':bad,'after_nonmanifold_edges':newbad,'voxel_size_mm':1.2,'old_polygons':oldfaces,'new_polygons':len(o.data.polygons),'nearest_old_surface_median_mm':distances[len(distances)//2]*1000,'nearest_old_surface_max_mm':max(distances)*1000};report.append(entry);assert newbad==0,entry
 o['topology_repair']='Voxel remesh 1.2 mm, two mild smooth passes, mesh reduction; source surface modified for display; see REPAIR_QA.json'
# Reduce oversampled curve tessellation while retaining explicitly authored geometry.
for o in bpy.data.objects:
 if o.type!='MESH' or o.get('organ_id')=='heart_detailed' or 'source_file' in o:continue
 if ('cartilage' in o.name.lower() or 'ruga' in o.name.lower() or 'bronch' in o.name.lower() or 'distal illustration' in o.name.lower()) and len(o.data.vertices)>1200:
  o.hide_viewport=False;o.hide_set(False);bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Portable curve tessellation','DECIMATE');mod.ratio=.30;bpy.ops.object.modifier_apply(modifier=mod.name)
# Remove stale bake outputs before rebuilding atlas UVs after geometry changes.
for ma in list(bpy.data.materials):
 if 'baked portable PBR' in ma.name:bpy.data.materials.remove(ma,do_unlink=True)
for im in list(bpy.data.images):
 if im.name.endswith(' 1K'):bpy.data.images.remove(im,do_unlink=True)
json.dump(report,open(D/'docs/REPAIR_QA.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
print('REPAIR COMPLETE',report,flush=True)
