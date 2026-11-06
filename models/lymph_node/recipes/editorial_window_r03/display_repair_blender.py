"""Fresh stock import/export with explicit deindexed serialization and review renders."""
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gltf_source import load,write_glb,world_blender
from display_repair import deindex,attribute_faces,compare_attributes,NORMAL_ANGLE_DEGREES,validate_prepared,UNIT_LENGTH_ERROR
from import_audit import snapshot,check_transforms,material_semantics
from check import CANDIDATE_SHA


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inverse(v):return (v[0],v[2],-v[1])

def imported(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=False,import_shading='NORMALS')
    return {o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}

def scene_attributes(objects):
    result={}
    for name,o in objects.items():
        o.data.calc_loop_triangles();color=o.data.color_attributes.active_color
        if color is None:raise ValueError('Missing imported color layer')
        vertices=[inverse(o.matrix_world@v.co) for v in o.data.vertices];rows=[]
        for tri in o.data.loop_triangles:
            positions=tuple(vertices[i] for i in tri.vertices)
            k=min(range(3),key=lambda j:positions[j:]+positions[:j])
            loops=tuple(tri.loops);loops=loops[k:]+loops[:k]
            normals=tuple(inverse(o.data.corner_normals[i].vector) for i in loops)
            colors=tuple(tuple(color.data[i if color.domain=='CORNER' else o.data.loops[i].vertex_index].color)
                         for i in loops)
            rows.append((positions[k:]+positions[:k],normals,colors))
        result[name]=rows
    return result

def materials(doc):
    return {m['name']:material_semantics(doc['materials'][m['primitives'][0]['material']]) for m in doc['meshes']}

def measured_attributes(expected,actual):
    # Diagnostic full angular range does not replace the declared gate. Geometry,
    # multiplicity, color and unit-normal validity still fail closed.
    try:
        rows=compare_attributes(expected,actual,angle_degrees=180)
        passed=all(r['maxNormalAngleDegrees']<=NORMAL_ANGLE_DEGREES for r in rows)
        failure=None
    except ValueError as error:
        if 'output normal' not in str(error):raise
        # Preserve the failed normal-validity gate while still producing actual
        # matched renders. No invalid normal is replaced for this measurement.
        rows=[];passed=False;failure=str(error)
        if set(expected)!=set(actual):raise ValueError('Object inventory changed')
        for name,old in expected.items():
            new=actual[name]
            if Counter((p,c) for p,n,c in old)!=Counter((p,c) for p,n,c in new):
                raise ValueError('Geometry or vertex color changed')
            lengths=[math.sqrt(sum(x*x for x in v)) for p,n,c in new for v in n]
            rows.append({'mesh':name,'triangles':len(new),'maxNormalAngleDegrees':None,
                'zeroNormalCorners':sum(x==0 for x in lengths),
                'nonunitNormalCorners':sum(abs(x-1)>UNIT_LENGTH_ERROR for x in lengths),
                'minimumNormalLength':min(lengths),'maximumNormalLength':max(lengths),
                'vertexColorsExact':True,'orientedPositionsAndMultiplicityExact':True})
    return {'normalBudgetStatus':'passed' if passed else 'failed',
            'declaredBudgetDegrees':NORMAL_ANGLE_DEGREES,'normalValidityStatus':'passed' if failure is None else 'failed',
            'normalValidityFailure':failure,'meshes':rows}

def reject_controls(expected,actual,document):
    rows=[];name=next(iter(actual))
    def rejects(label,action):
        try:action()
        except ValueError as e:rows.append({'case':label,'rejection':str(e)})
        else:raise AssertionError('Accepted negative control: '+label)
    for label,replace in [('vertex color corruption',lambda p,n,c:(p,n,((.25,1.,1.,1.),*c[1:]))),
                          ('missing normal',lambda p,n,c:(p,((0.,0.,0.),*n[1:]),c)),
                          ('reversed normal',lambda p,n,c:(p,(tuple(-x for x in n[0]),*n[1:]),c)),
                          ('lost oriented face',None)]:
        changed=dict(actual);changed[name]=list(actual[name])
        if replace is None:changed[name].pop()
        else:changed[name][0]=replace(*changed[name][0])
        rejects(label,lambda changed=changed:compare_attributes(expected,changed))
    for field,value in [('doubleSided',True),('alphaMode','BLEND'),('name','wrong material')]:
        changed=copy.deepcopy(document);changed['materials'][0][field]=value
        def check(changed=changed):
            if materials(changed)!=materials(document):raise ValueError('Material/culling semantics changed')
        rejects(field,check)
    return rows

def explicit_culling():
    # Cycles ignores use_backface_culling. Review-only graph models glTF's
    # single-sided visibility; it is never serialized into the artifact.
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        tree=m.node_tree;out=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL')
        link=out.inputs['Surface'].links[0];original=link.from_socket;tree.links.remove(link)
        geo=tree.nodes.new('ShaderNodeNewGeometry');transparent=tree.nodes.new('ShaderNodeBsdfTransparent')
        mix=tree.nodes.new('ShaderNodeMixShader');tree.links.new(geo.outputs['Backfacing'],mix.inputs[0])
        tree.links.new(original,mix.inputs[1]);tree.links.new(transparent.outputs[0],mix.inputs[2])
        tree.links.new(mix.outputs[0],out.inputs['Surface'])

def render(path,folder,center,span):
    imported(path);explicit_culling();folder.mkdir()
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=48
    sc.cycles.use_denoising=False;sc.cycles.seed=0;sc.render.resolution_x=1100;sc.render.resolution_y=900
    sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
    sc.world=bpy.data.worlds.new('Matched review world');sc.world.color=(.045,.045,.045)
    sc.view_settings.view_transform='AgX';sc.render.film_transparent=False
    center=Vector(center)
    for delta,power in [((-1,-2,2),130),((1,-1,-1),90),((0,2,1),110)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(delta));o=bpy.context.object
        o.data.energy=power;o.data.size=2;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam
    rows=[]
    for name,direction,scale in [('oblique',(1,-2,.5),1),('detail',(1,-2,.5),.57),('reverse',(-1,2,-.5),1)]:
        cam.data.ortho_scale=span*scale;cam.location=center+Vector(direction)
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        output=folder/(name+'.png');sc.render.filepath=str(output);bpy.ops.render.render(write_still=True)
        rows.append({'view':name,'file':str(output),'sha256':sha(output),'camera':list(cam.location),
                     'target':list(center),'orthographicScale':cam.data.ortho_scale})
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--render',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if sha(a.baseline)!=CANDIDATE_SHA:raise ValueError('Pinned baseline mismatch')
    a.output.mkdir(parents=True,exist_ok=False)
    pd,pb=load(a.prepared)
    prepared_changes=validate_prepared(*load(a.baseline),pd,pb)
    if len(prepared_changes)!=164:
        raise ValueError('Pinned normal-repair count changed; expected 164 corners')
    full_split=pd['extras']['displayRepair']['cornerStrategy']=='full-split'
    expected=attribute_faces(pd,pb)
    objects=imported(a.prepared);first=scene_attributes(objects);first_state=snapshot(bpy)
    first_check=measured_attributes(expected,first)
    # Controls use a passing self-baseline so pre-existing source/import drift
    # cannot masquerade as rejection of the injected corruption.
    control_baseline={'Yao_afferent_lymphatic_vessel':first['Yao_afferent_lymphatic_vessel']}
    compare_attributes(control_baseline,control_baseline)
    negatives=reject_controls(control_baseline,control_baseline,pd)
    stock=a.output/'intermediate-stock-export.glb'
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(stock),export_format='GLB',use_selection=True,
                             export_extras=True,export_cameras=False,export_lights=False)
    ed,eb=load(stock)
    if materials(pd)!=materials(ed):raise ValueError('Export material semantics changed')
    stock_check=measured_attributes(expected,attribute_faces(ed,eb))
    stock_objects=imported(stock);stock_counts={n:len(o.data.polygons) for n,o in stock_objects.items()}
    # Stock exporter may share corners again. Repeat each exported corner only;
    # positions, winding, colors and the actual exported normals are unchanged.
    fd,fb,_=deindex(ed,eb,repair=False,full_split=full_split)
    derivative=a.output/'roundtrip-split-derivative.glb';write_glb(derivative,fd,fb)
    objects=imported(derivative);last=scene_attributes(objects);last_state=snapshot(bpy)
    roundtrip_check=measured_attributes(expected,last)
    for name in first_state:
        check_transforms(first_state[name]['transform'],last_state[name]['transform'])
        if first_state[name]['materials']!=last_state[name]['materials'] or first_state[name]['culling']!=last_state[name]['culling']:
            raise ValueError('Imported material assignment/culling changed')
        if not all(last_state[name]['culling']):raise ValueError('Single-sided material lost')
    # Final candidate is the policy-validated artifact, preserving valid source
    # normal bytes. The actual scene export is retained separately as evidence.
    final=a.output/'lymph-node-display-repair-r01.glb'
    with final.open('xb') as stream:stream.write(a.prepared.read_bytes())
    final_check=measured_attributes(expected,scene_attributes(imported(final)))
    result={'baselineSha256':sha(a.baseline),'preparedSha256':sha(a.prepared),'finalSha256':sha(final),
            'finalBytes':final.stat().st_size,'blender':bpy.app.version_string,
            'directPreparedImport':first_check,'stockExportAttributes':stock_check,
            'stockExportReimportCounts':stock_counts,'finalFreshReimport':final_check,
            'splitRoundtripDerivative':roundtrip_check,'splitRoundtripSha256':sha(derivative),
            'rawInvalidNormalCornersRepaired':len(prepared_changes),
            'cornerStrategy':pd['extras']['displayRepair']['cornerStrategy'],
            'normalAngularBudgetDegrees':NORMAL_ANGLE_DEGREES,'negativeControls':negatives,
            'singleSidedMaterialSemanticsPreserved':True,'transformsPreserved':True,
            'exportPolicy':'Actual stock scene exporter followed by the declared corner-splitting strategy, retained as a separate roundtrip derivative. Final candidate retains valid source normals and only documented invalid-normal substitutions.',
            'scope':'Local display shading repair. Original r03 failures retained. No anatomical-outward-normal, clinical, browser runtime or source topology repair claim.'}
    if a.render:
        # Framing fixed to original r03 source bounds, exactly shared across both.
        positions=[world_blender(v) for rows in attribute_faces(*load(a.baseline)).values() for face,n,c in rows for v in face]
        center=[(min(v[i] for v in positions)+max(v[i] for v in positions))/2 for i in range(3)]
        span=max(max(v[i] for v in positions)-min(v[i] for v in positions) for i in range(3))*1.18
        result['renders']={'baseline':render(a.baseline,a.output/'baseline-renders',center,span),
                           'candidate':render(final,a.output/'candidate-renders',center,span)}
        result['renderSettings']={'engine':'Cycles CPU','samples':48,'seed':0,'denoising':False,
            'resolution':[1100,900],'viewTransform':'AgX','worldColor':[.045,.045,.045],
            'lightDeltas':[[-1,-2,2],[1,-1,-1],[0,2,1]],'lightPowers':[130,90,110],'lightSize':2,
            'culling':'Review-only Geometry.Backfacing -> Transparent on both variants; stock Cycles ignores material flag. Not a glTF viewer.'}
    if result['rawInvalidNormalCornersRepaired']!=164:
        raise ValueError('Incorrect repair count in receipt')
    (a.output/'repair-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('DISPLAY_REPAIR_REVIEW_COMPLETE; normal budget '+final_check['normalBudgetStatus'].upper(),result['finalSha256'])

if __name__=='__main__':main()
