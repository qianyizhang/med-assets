"""Own Blender script: fixed historical camera/light recipe, fresh GLB reimport."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_source import SOURCE_SHA, load, accessor, world_blender
from check import CANDIDATE_SHA

parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,required=True)
parser.add_argument('--build-receipt',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--roundtrip',action='store_true')
parser.add_argument('--back-only',action='store_true')
parser.add_argument('--all-views',action='store_true')
parser.add_argument('--detail-only',action='store_true')
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
receipt=json.loads(a.build_receipt.read_text())
if receipt['sourceSha256'] != SOURCE_SHA or receipt['candidateSha256'] != CANDIDATE_SHA:
    raise ValueError('Pinned render receipt identity mismatch')
if hashlib.sha256(a.input.read_bytes()).hexdigest() not in (SOURCE_SHA, CANDIDATE_SHA):
    raise ValueError('Pinned render input mismatch')
source = Path(receipt['source'])
if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
    raise ValueError('Pinned framing source mismatch')
sdoc, sbin = load(source)
all_positions = [world_blender(v) for mesh in sdoc['meshes']
                 for v in accessor(sdoc, sbin, mesh['primitives'][0]['attributes']['POSITION'])]
expected_center = tuple((min(v[i] for v in all_positions) + max(v[i] for v in all_positions)) / 2
                        for i in range(3))
if tuple(receipt['window']['centerBlender']) != expected_center:
    raise ValueError('Pinned framing center mismatch')
a.output.mkdir(parents=True,exist_ok=False)
center=Vector(receipt['window']['centerBlender'])
labels={
 'Yao_afferent_lymphatic_vessel':('1','Afferent lymphatic vessel',(1,1,0)),
 'Yao_capsule_of_lymph_node':('2','Capsule of lymph node',(1,1,1)),
 'Yao_follicles':('3','Lymph node follicles',(0,0,1)),
 'Yao_efferent_lymph_node':('4','Efferent lymphatic vessel',(0,1,1)),
 'Yao_medulla_of_lymph_node':('5','Medulla of lymph node',(1,0,1)),
 'Yao_paracortex':('6','Paracortex / T-cell domain',(0,1,0)),
 'Yao_blood_vasculature':('7','Source vascular network (identity unresolved)',(1,0,0)),
}

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    obs={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
    if set(obs)!=set(labels):
        raise ValueError('Required seven source nodes missing')
    return obs

def geometry(obs):
    out={}
    for name,o in obs.items():
        o.data.calc_loop_triangles()
        vs=[tuple(o.matrix_world@v.co) for v in o.data.vertices]
        tris=[tuple(t.vertices) for t in o.data.loop_triangles]
        areas=[(Vector(vs[t[1]])-Vector(vs[t[0]])).cross(Vector(vs[t[2]])-Vector(vs[t[0]])).length/2 for t in tris]
        if not all(math.isfinite(v) for p in vs for v in p) or any(x==0 for x in areas):
            raise ValueError('Nonfinite position or zero-area triangle')
        out[name]={'vertices':vs,'triangles':tris,'triangleCount':len(tris),
            'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],
            'finite':True,'zeroAreaTriangles':0}
    return out

def compare(before,after):
    rows=[]
    for name,b in before.items():
        other=after[name]
        if b['triangleCount']!=other['triangleCount']:
            raise ValueError('Roundtrip changed triangle count: '+name)
        # Exact-coordinate IDs in the first import; compare the full oriented
        # triangle multiset after export and the second import.
        unique=list(dict.fromkeys(b['vertices']))
        index={v:i for i,v in enumerate(unique)}
        remap=[]; max_error=0
        for v in other['vertices']:
            if v not in index:
                raise ValueError('Roundtrip vertex differs from exact original coordinate: '+name)
            remap.append(index[v])
        def oriented(t):
            return min(t,t[1:]+t[:1],t[2:]+t[:2])
        first=Counter(oriented(tuple(index[b['vertices'][i]] for i in t)) for t in b['triangles'])
        second=Counter(oriented(tuple(remap[i] for i in t)) for t in other['triangles'])
        if first!=second:
            raise ValueError('Roundtrip changed oriented triangle geometry: '+name)
        rows.append({'node':name,'triangles':b['triangleCount'],'orientedTrianglesMatched':True,'maxVertexDisplacementMetres':max_error})
    return rows

clear();obs=import_glb(a.input)
first=geometry(obs); roundtrip=None
input_doc, input_binary = load(a.input)
direct_import_counts = []
for node in input_doc['nodes']:
    if 'mesh' not in node:
        continue
    mesh = input_doc['meshes'][node['mesh']]
    raw = sum(input_doc['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives'])
    direct_import_counts.append({'node': node['name'], 'rawGlbTriangles': raw,
                                 'firstBlenderImportTriangles': first[node['name']]['triangleCount'],
                                 'difference': raw - first[node['name']]['triangleCount']})
if a.roundtrip:
    bpy.ops.object.select_all(action='SELECT')
    out=a.output/'candidate-blender-roundtrip.glb'
    bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
    clear();obs=import_glb(out)
    second=geometry(obs)
    rows=compare(first,second)
    roundtrip={'file':str(out.resolve()),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'objects':rows,'scope':'First Blender import -> export -> second import: exact-coordinate oriented triangle multisets. Excludes direct GLB import; see separately recorded count differences and study decision. No anatomy or manifold acceptance.'}
    # Main comparison images are from the exact candidate, not the roundtrip derivative.
    clear();obs=import_glb(a.input)

sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.cycles.seed=0
sc.render.resolution_x=1100;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Historical review background');sc.world.color=(.045,.045,.045)
sc.view_settings.view_transform='AgX';sc.render.image_settings.file_format='PNG'
sc.render.film_transparent=False
for delta,power in [((-1,-2,2),130),((1,-1,-1),90),((0,2,1),110)]:
    bpy.ops.object.light_add(type='AREA',location=center+Vector(delta))
    light=bpy.context.object;light.data.energy=power;light.data.size=2
    light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam
# Compute scale from pinned full-source bounds, retaining the historical framing.
span=max(max(v[i] for v in all_positions)-min(v[i] for v in all_positions) for i in range(3))*1.18
cam.data.ortho_scale=span
views=[('oblique',(1,-2,.5)),('second-oblique',(.25,-2,.9))]
if a.back_only:
    views=[('reverse',(-1,2,-.5))]
if a.all_views:
    views += [('reverse',(-1,2,-.5)),('detail',(1,-2,.5))]
if a.detail_only:
    views=[('detail',(1,-2,.5))]
records=[]
for name,direction in views:
    cam.data.ortho_scale=span*(.57 if name=='detail' else 1)
    cam.location=center+Vector(direction)
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(a.output/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    records.append({'name':name,'file':name+'.png','camera':list(cam.location),'target':list(center),'orthographicScale':cam.data.ortho_scale,'sha256':hashlib.sha256((a.output/(name+'.png')).read_bytes()).hexdigest()})
bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'review.blend'),compress=True)
# Controlled object-ID render; original material renders above are the visual evidence.
for name,o in obs.items():
    m=bpy.data.materials.new('Visibility ID '+labels[name][0]);m.use_nodes=True
    m.node_tree.nodes.clear();em=m.node_tree.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value=(*labels[name][2],1)
    out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
    o.data.materials.clear();o.data.materials.append(m)
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.world.color=(0,0,0)
sc.cycles.samples=1
for name,direction in views:
    cam.data.ortho_scale=span*(.57 if name=='detail' else 1)
    cam.location=center+Vector(direction);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(a.output/(name+'-visibility.png'));bpy.ops.render.render(write_still=True)
summary={k:{x:v for x,v in row.items() if x not in ('vertices','triangles')} for k,row in first.items()}
(a.output/'render-receipt.json').write_text(json.dumps({'input':str(a.input.resolve()),'inputSha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),
    'directGlbImport':{'fullOrientedPreservation':'not passed by this roundtrip check','perNodeCounts':direct_import_counts,'knownR03Failure':'18 medulla and 88 network opposite-winding duplicates are dropped; this import limitation remains failed.'},
    'blender':bpy.app.version_string,'sourceMaterialsUnchangedInMainRenders':True,'views':records,'geometry':summary,'roundtrip':roundtrip,
    'engine':'Cycles CPU; 48 samples; no denoising; seed0; AgX; 1100x900',
    'detailScope':'Centered 0.57x source framing; same oblique target/camera/light recipe for both revisions',
    'completeSettings':{'lightDeltas':[[-1,-2,2],[1,-1,-1],[0,2,1]],'lightPowers':[130,90,110],'lightSize':2,'samples':48,'denoising':False,'seed':0,'resolution':[1100,900],'worldColor':[.045,.045,.045],'viewTransform':'AgX','filmTransparent':False},
    'lighting':'Same three area lights, powers130/90/110, source historical recipe',
    'maskColors':{n:{'key':v[0],'color':v[2]} for n,v in labels.items()},
    'note':'Object-ID passes replace materials only to measure surface visibility. No anatomical direction or clinical-plane claim.'},indent=2)+'\n')
print('RENDER_AND_REIMPORT_COMPLETE',a.input.name)
