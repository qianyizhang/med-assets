"""Build one bounded, inferred teaching junction from the exact retained BP3D shells."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector

SOURCES = {
    'hypothalamus': ('models/hypothalamus/exports/source-candidate-01/hypothalamus_source_frame.glb', 75720, 'b6d73d6b5a33006391a743c650ccc06b65b9b9afaaaebbcf1d05102d4399274c'),
    'pituitary': ('models/pituitary/exports/source-candidate-01/pituitary_source_frame.glb', 22296, '8eae4c6d05b0c9de5128ae6f574a97265cb392a44567fcac5ea0b9b7f1dbca68'),
}
FRAME = Vector((-0.00065, -0.103, 1.534))
BAND = (-2.25, 2.05)  # source-frame z=1.53175..1.53605 m, expressed in local mm

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def material(name, color):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(*color,1);node.inputs['Roughness'].default_value=.68
    return m

def topology(mesh):
    bm=bmesh.new();bm.from_mesh(mesh)
    result={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),
            'boundary_edges':sum(e.is_boundary for e in bm.edges),
            'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
            'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
    todo=set(bm.verts);sizes=[]
    while todo:
        seed=todo.pop();stack=[seed];n=0
        while stack:
            v=stack.pop();n+=1
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in todo:todo.remove(other);stack.append(other)
        sizes.append(n)
    result['component_vertices']=sorted(sizes,reverse=True);bm.free();return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--smooth-iterations',type=int,default=5);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if a.out.exists():raise FileExistsError('Use a new output directory')
    for _,(path,size,sha) in SOURCES.items():
        source=a.root/path
        if source.stat().st_size!=size or digest(source)!=sha:raise ValueError('Wrong source: '+path)
    a.out.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    mats=[material('Hypothalamus envelope — illustrative',(.59,.29,.27)),material('Pituitary envelope — illustrative',(.22,.49,.50)),material('Inferred single stalk junction — not a tissue boundary',(.73,.48,.20))]
    objects=[];inputs=[]
    for organ,(path,size,sha) in SOURCES.items():
        before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(a.root/path))
        for ob in [o for o in set(bpy.data.objects)-before if o.type=='MESH']:
            world=ob.matrix_world.copy()
            for v in ob.data.vertices:v.co=(world@v.co-FRAME)*1000
            ob.matrix_world.identity();ob.data.materials.clear()
            for m in mats:ob.data.materials.append(m)
            for f in ob.data.polygons:f.material_index=0 if organ=='hypothalamus' else 1
            bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
            inputs.append({'name':ob.name,'organ':organ,'topology_local_mm':topology(ob.data)});objects.append(ob)
    objects.sort(key=lambda ob: ('pituitary' in ob.name,ob.name))
    result=objects[0]
    for other in objects[1:]:
        bpy.context.view_layer.objects.active=result
        mod=result.modifiers.new('Remove intersecting source interiors','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=other
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(other,do_unlink=True)
    result.name='Hypothalamus–single stalk–pituitary teaching envelope'
    for key in list(result.keys()):del result[key]
    before_smooth=[v.co.copy() for v in result.data.vertices]
    group=result.vertex_groups.new(name='bounded inferred junction')
    for v in result.data.vertices:
        t=(v.co.z-BAND[0])/(BAND[1]-BAND[0])
        if 0<t<1:group.add([v.index],math.sin(math.pi*t)**2,'REPLACE')
    if a.smooth_iterations:
        bpy.context.view_layer.objects.active=result
        mod=result.modifiers.new('Bounded junction blend','SMOOTH');mod.factor=.5;mod.iterations=a.smooth_iterations;mod.vertex_group=group.name
        bpy.ops.object.modifier_apply(modifier=mod.name)
    movement=[(v.co-before_smooth[v.index]).length for v in result.data.vertices]
    outside=[movement[i] for i,v in enumerate(before_smooth) if not BAND[0]<v.z<BAND[1]]
    assert max(outside,default=0)<1e-9
    # Continuous editorial color transitions avoid suggesting serrated anatomical borders.
    result.data.materials.clear();display=material('Editorial regions — not tissue segmentation',(1,1,1));result.data.materials.append(display)
    colors=result.data.color_attributes.new(name='Teaching regions',type='FLOAT_COLOR',domain='CORNER')
    color_node=display.node_tree.nodes.new('ShaderNodeVertexColor');color_node.layer_name=colors.name
    display.node_tree.links.new(color_node.outputs['Color'],display.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    def mix(a,b,t):
        t=max(0,min(1,t));t=t*t*(3-2*t);return tuple(x*(1-t)+y*t for x,y in zip(a,b))
    def region(z):
        lower=mix((.22,.49,.50),(.73,.48,.20),(z-BAND[0])/.8)
        return mix(lower,(.59,.29,.27),(z-(BAND[1]-.8))/.8)
    for loop in result.data.loops:colors.data[loop.index].color=(*region(result.data.vertices[loop.vertex_index].co.z),1)
    for f in result.data.polygons:f.material_index=0;f.use_smooth=True
    status=topology(result.data)
    if status['boundary_edges'] or status['nonmanifold_edges'] or status['zero_area_faces']:raise ValueError(status)
    for v in result.data.vertices:v.co=v.co/1000+FRAME
    result['teaching_scope']='Single continuous exterior junction only; no lobes, nuclei, portal vessels, axons or tissue segmentation.'
    result['inferred_join']='Union and localized smoothing of the overlapping atlas stalk envelopes; color transitions are editorial, not histological boundaries.'
    result['source_components']='BP3D FJ1760 and FJ1808 hypothalamic envelopes plus FJ1796 pituitary envelope; original exports preserved separately.'
    result['source_sha256_hypothalamus']=SOURCES['hypothalamus'][2];result['source_sha256_pituitary']=SOURCES['pituitary'][2]
    result['native_source_frame']='Preserved world coordinates; local-mm transform used only for robust geometry operations and reversed before export.'
    result['runtime']='unverified';result['clinical']='not approved'
    bpy.ops.object.select_all(action='DESELECT');result.select_set(True);bpy.context.view_layer.objects.active=result
    output=a.out/'hypothalamus-pituitary-teaching.glb'
    bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_animations=False)
    record={'sources':{k:{'file':v[0],'bytes':v[1],'sha256':v[2]} for k,v in SOURCES.items()},'inputs':inputs,'operation':'Exact boolean union of the three retained exterior shells, then localized weighted smoothing; no new lobes/nuclei or clinical dimensions.','junction_z_m':[FRAME.z+BAND[0]/1000,FRAME.z+BAND[1]/1000],'smooth_iterations':a.smooth_iterations,'max_blend_movement_mm':max(movement,default=0),'outside_blend_band_movement_mm':max(outside,default=0),'topology_local_mm':status,'artifact':{'file':output.name,'bytes':output.stat().st_size,'sha256':digest(output)},'blender':bpy.app.version_string,'limitations':['Inferred exterior teaching junction; no measured anatomical boundary.','Paired source envelopes remain low-detail atlas localization surfaces.','No internal anatomy, physiology, clinical or live runtime validation.']}
    (a.out/'build-record.json').write_text(json.dumps(record,indent=2)+'\n');print('BUILD_RECORD',json.dumps(record))

if __name__=='__main__':main()
