"""Clean reimport, source-bound camera replay and visible-surface cue receipts."""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb


def middle(bindings):
    return Vector([(min(b['nativeBounds'][0][a] for b in bindings)+max(b['nativeBounds'][1][a] for b in bindings))/2 for a in range(3)])


def check_reimport(meshes, document, payload, bindings):
    assert sorted(meshes) == sorted(b['name'] for b in bindings)
    rows = []
    for i, b in enumerate(bindings):
        obj = meshes[b['name']]; mesh = obj.data; mesh.calc_loop_triangles()
        primitive = document['meshes'][i]['primitives'][0]
        positions = [Vector(glb.vector_basis(v, inverse=True)) for v in glb.read_accessor(document, payload, primitive['attributes']['POSITION'])]
        normals = [Vector(glb.vector_basis(v, inverse=True)) for v in glb.read_accessor(document, payload, primitive['attributes']['NORMAL'])]
        indices = glb.read_accessor(document, payload, primitive['indices'])
        matrix = Matrix(b['matrixNative'])
        expected = [matrix @ positions[index] for index in indices]
        actual = [obj.matrix_world @ mesh.vertices[mesh.loops[loop].vertex_index].co for tri in mesh.loop_triangles for loop in tri.loops]
        assert len(actual) == len(expected) == b['triangles']*3
        world_delta = max(abs(a[k]-e[k]) for a,e in zip(actual,expected) for k in range(3))
        # Four float32 ULPs at the largest source world coordinate allow importer
        # matrix decomposition/recomposition; decoded source data above is exact.
        magnitude = max(abs(v) for p in expected for v in p)
        tolerance = 4 * 2**(math.floor(math.log2(magnitude))-23)
        matrix_delta = max(abs(obj.matrix_world[r][c]-matrix[r][c]) for r in range(4) for c in range(4))
        assert world_delta <= tolerance, (b['name'], world_delta, tolerance)
        local_actual = [mesh.corner_normals[loop].vector for tri in mesh.loop_triangles for loop in tri.loops]
        local_expected = [normals[index] for index in indices]
        normal_delta = max((a-e).length for a,e in zip(local_actual,local_expected))
        # Imported custom normals are not bit-identical in Blender. Keep a
        # separate 0.1-degree shading-direction budget; source NORMAL bytes
        # are still required to match exactly by the independent GLB decoder.
        normal_tolerance = 2*math.sin(math.radians(.1)/2)
        assert normal_delta <= normal_tolerance, (b['name'], normal_delta)
        role = b['displayRole']; mat = obj.data.materials[0]
        assert mat.name == 'Editorial neutral '+role
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        assert max(abs(a-e) for a,e in zip(bsdf.inputs['Base Color'].default_value, glb.PALETTE[role])) < 1e-7
        assert abs(bsdf.inputs['Roughness'].default_value-.62) < 1e-7 and bsdf.inputs['Metallic'].default_value == 0
        rows.append({'name': b['name'], 'triangles': len(actual)//3, 'maximumWorldCoordinateDelta': world_delta,
                     'worldCoordinateToleranceFourFloat32ULPs': tolerance, 'maximumNativeMatrixDelta': matrix_delta,
                     'maximumLocalNormalVectorDelta': normal_delta,
                     'shadingNormalDirectionBudgetDegrees': .1, 'neutralMaterialMatch': True})
    return rows


def run(args):
    assert not args.output.exists()
    data = args.candidate.read_bytes(); binding_record = json.loads(args.bindings.read_text()); bindings = binding_record['objects']
    glb.verify(data, bindings); document,payload = glb.decode(data)
    contract = json.loads(args.cameras.read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    bpy.ops.import_scene.gltf(filepath=str(args.candidate), merge_vertices=False)
    bpy.context.view_layer.update()
    meshes = {o.name:o for o in bpy.context.scene.objects if o.type == 'MESH'}
    before = check_reimport(meshes, document, payload, bindings)
    scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
    scene.cycles.samples = 24; scene.cycles.seed = 0; scene.cycles.use_denoising = False
    scene.render.image_settings.file_format = 'PNG'; scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'; scene.view_settings.exposure = 0
    scene.world = bpy.data.worlds.new('Editorial neutral world'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.055,.065,.075,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .5
    mid = middle(bindings)
    for name,offset,power,size in contract['lights']:
        light = bpy.data.lights.new(name, 'AREA'); light.energy=power; light.shape='DISK'; light.size=size
        obj=bpy.data.objects.new(name,light); scene.collection.objects.link(obj); obj.location=mid+Vector(offset)
        obj.rotation_euler=(mid-obj.location).to_track_quat('-Z','Y').to_euler()
    camdata=bpy.data.cameras.new('Matched source/export camera'); camdata.type='ORTHO'
    camera=bpy.data.objects.new('Matched source/export camera',camdata); scene.collection.objects.link(camera); scene.camera=camera
    offsets={'source-R-oblique':(-.18,.12,.10),'source-R-posterior':(0,.24,.06),'source-L-oblique':(.18,.12,.10)}
    args.output.mkdir(parents=True); views=[]
    for reference in contract['views']:
        view=Path(reference['file']).stem; side=reference['sourceSide']; res=reference['resolution']
        source_image=args.source_images/reference['file']
        assert glb.sha(source_image.read_bytes()) == reference['sha256']
        shutil.copyfile(source_image, args.output/reference['file'])
        visible=[o for n,o in meshes.items() if n.endswith('.'+side)]
        for obj in meshes.values():
            obj.hide_render=obj not in visible
            obj.hide_set(obj not in visible)
        target=middle([b for b in bindings if b['name'].endswith('.'+side)])
        camera.location=target+Vector(offsets[view]); camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camdata.ortho_scale=reference['orthographicScaleNativeUnits']
        scene.render.resolution_x,scene.render.resolution_y=res; bpy.context.view_layer.update()
        assert [list(r) for r in camera.matrix_world] == reference['cameraMatrixWorld'], 'Camera replay differs'
        def project(point):
            v=world_to_camera_view(scene,camera,point); return [v.x*res[0],(1-v.y)*res[1]]
        points=[o.matrix_world @ v.co for o in visible for v in o.data.vertices]
        pixels=[project(p) for p in points]
        margins={'left':min(p[0] for p in pixels),'right':res[0]-max(p[0] for p in pixels),
                 'top':min(p[1] for p in pixels),'bottom':res[1]-max(p[1] for p in pixels)}
        assert min(margins.values()) >= 90
        anchors={}; direction=(target-camera.location).normalized(); deps=bpy.context.evaluated_depsgraph_get()
        roles={'lateral-course':'Lateral rectus muscle.', 'trochlea':'Trochlea of superior oblique muscle.', 'optic-segment':'Optic nerve (II).'}
        for role,stem in roles.items():
            name=stem+side; obj=meshes[name]
            pts=[obj.matrix_world @ v.co for v in obj.data.vertices]; px=[project(p) for p in pts]
            mean=[sum(p[a] for p in px)/len(px) for a in range(2)]
            # Optic cue targets the source's medialmost retained end, not a
            # neighboring muscle. Other cues favor central visible surface.
            key=(lambda item:abs(item[0].x)) if role=='optic-segment' else (lambda item:sum((item[1][a]-mean[a])**2 for a in range(2)))
            for point,pixel in sorted(zip(pts,px),key=key):
                hit,loc,normal,index,hitobj,matrix=scene.ray_cast(deps,point-direction*.5,direction,distance=1)
                if hit and hitobj.name==name:
                    anchors[role]={'sourceNode':name,'worldNative':list(point),'pixel':pixel,'rayHitNode':hitobj.name,
                                   'selection':'medialmost visible source end' if role=='optic-segment' else 'central visible source surface'}
                    break
            # Posterior view can occlude the anterior trochlea; absent anchors
            # remain absent, never guessed or borrowed from another view.
        assert 'optic-segment' in anchors
        path=args.output/('export-'+view+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        views.append({'view':view,'file':path.name,'sha256':glb.sha(path.read_bytes()),'bytes':path.stat().st_size,
                      'sourceImage':reference['file'],'sourceImageSha256':reference['sha256'],
                      'sourceSide':side,'visibleSourceNames':sorted(o.name for o in visible),'resolution':res,
                      'cameraMatrixWorld':[list(r) for r in camera.matrix_world], 'orthographicScaleNativeUnits':camdata.ortho_scale,
                      'frameMarginsPx':margins,'anchors':anchors})
    after=check_reimport(meshes,document,payload,bindings)
    assert after == before and args.candidate.read_bytes() == data
    receipt={'candidateSha256':glb.sha(data),'blender':bpy.app.version_string,'decodedSourceGeometryAndMatricesExact':True,
             'reimport':before,'views':views,'sourceCameraReplayExact':True,'sourceImagesReused':True,
             'geometryUnchangedDuringRender':True,'display':{'engine':'Cycles CPU','samples':24,'seed':0,'denoising':False,'lights':contract['lights'],
               'materials':'Neutral display colors. Source action-labelled shaders are metadata only.'},
             'sceneImportBehavior':'Blender imports both glTF scenes into one scene; review visibility selects the declared source side without altering geometry.',
             'runtime':'unverified','anatomyClinical':'unverified'}
    (args.output/'reimport-render.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'frames':len(views),'candidateSha256':receipt['candidateSha256'],
        'maxCoordinateDelta':max(r['maximumWorldCoordinateDelta'] for r in before),'minMarginPx':min(v for r in views for v in r['frameMarginsPx'].values())}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('candidate','bindings','cameras','source-images','output'):
        p.add_argument('--'+name, required=True, type=Path)
    run(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
