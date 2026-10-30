"""Blender-only matched visibility render; preserve all source coordinates and faces."""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source import (CAMERAS, POSTERIOR_BASIS, RESOLUTION, V1_RENDER_RECEIPT_SHA,
                    context_framing, geometry_sha, load_inputs, project, require,
                    require_framing_margin, reuse_v1_detail, sha)


def material(name, color, opacity=1):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links
    output = nodes.new('ShaderNodeOutputMaterial')
    surface = nodes.new('ShaderNodeBsdfPrincipled')
    surface.inputs['Base Color'].default_value = (*color, 1)
    surface.inputs['Roughness'].default_value = .8
    if opacity < 1:
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        mix = nodes.new('ShaderNodeMixShader')
        mix.inputs[0].default_value = opacity
        links.new(transparent.outputs[0], mix.inputs[1])
        links.new(surface.outputs[0], mix.inputs[2])
        # Only front faces contribute to the editorial translucent context.
        # Source triangles and normals are not rewritten.
        geometry = nodes.new('ShaderNodeNewGeometry')
        facing = nodes.new('ShaderNodeMixShader')
        links.new(geometry.outputs['Backfacing'], facing.inputs[0])
        links.new(mix.outputs[0], facing.inputs[1])
        links.new(transparent.outputs[0], facing.inputs[2])
        links.new(facing.outputs[0], output.inputs[0])
    else:
        links.new(surface.outputs[0], output.inputs[0])
    return mat


def add_mesh(name, vertices, faces, mat, context=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if context:
        # Adding context must not change the selected component's illumination.
        obj.visible_shadow = False
        obj.visible_diffuse = False
        obj.visible_glossy = False
        obj.visible_transmission = False
    require(mesh_identity(obj) == geometry_sha(vertices, faces), 'Mesh copy changed coordinates/faces: ' + name)
    return obj


def mesh_identity(obj):
    require(obj.matrix_world == Matrix.Identity(4), 'Unexpected display-object transform')
    return geometry_sha([v.co[:] for v in obj.data.vertices], [p.vertices[:] for p in obj.data.polygons])


def run(root, output, reuse_detail_from=None):
    record, vertices, faces, contexts = load_inputs(root)
    framing = context_framing(record['contexts'])
    require_framing_margin(framing)
    reused_rows, reused_payloads = reuse_v1_detail(reuse_detail_from, record) if reuse_detail_from else ([], {})
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    require(not bpy.context.preferences.filepaths.use_scripts_auto_execute, 'Run with --disable-autoexec')
    selected = add_mesh(record['node'], vertices, faces, material('Selected retained component', (.62, .18, .29)))
    ghost_objects = []
    for name, (vs, fs) in contexts.items():
        color, opacity = ((.34, .49, .65), .055) if name.startswith('lung') else ((.62, .48, .32), .10)
        ghost_objects.append(add_mesh(name, vs, fs, material(name + ' editorial context', color, opacity), True))
    identities = {o.name: mesh_identity(o) for o in [selected, *ghost_objects]}
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new('Comparison background')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.025, .035, .045, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.cycles.seed = 0
    scene.cycles.use_denoising = False
    scene.cycles.transparent_max_bounces = 20
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0
    target = Vector((0, 0, .065))
    lights = [((-.3, .4, .4), 8, .4), ((.3, .3, .1), 5, .4), ((0, -.3, -.3), 2, .4)]
    for offset, power, size in lights:
        bpy.ops.object.light_add(type='AREA', location=target + Vector(offset))
        obj = bpy.context.object
        obj.data.energy, obj.data.size = power, size
        obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.rotation_mode = 'QUATERNION'
    camera.rotation_quaternion = Matrix(POSTERIOR_BASIS).to_quaternion()
    views = []
    for view, config in CAMERAS.items():
        if view == 'detail' and reused_rows:
            for name, raw in reused_payloads.items():
                (output / name).write_bytes(raw)
            views.extend(reused_rows)
            continue
        camera.location = config['position']
        camera.data.ortho_scale = config['scale']
        for state in ('isolated', 'context'):
            for obj in ghost_objects:
                obj.hide_render = state == 'isolated'
            name = view + '-' + state + '.png'
            scene.render.filepath = str(output / name)
            bpy.ops.render.render(write_still=True)
            raw = (output / name).read_bytes()
            views.append({'view': view, 'state': state, 'file': name, 'sha256': sha(raw), 'bytes': len(raw),
                          'resolution': RESOLUTION, 'cameraPosition': list(camera.location),
                          'cameraWorldMatrix': [list(r) for r in camera.matrix_world],
                          'orthoScaleM': camera.data.ortho_scale,
                          'contextVisible': state == 'context', 'selectedGeometrySha256': mesh_identity(selected)})
    after = {o.name: mesh_identity(o) for o in [selected, *ghost_objects]}
    require(after == identities, 'Source geometry changed during rendering')
    reloaded, *_ = load_inputs(root)
    require(reloaded == record, 'Input bytes changed during rendering')
    left = sum((Vector(contexts[n][0][0]) for n in ('lung_upper_lobe_left', 'lung_lower_lobe_left')), Vector()) / 2
    right = sum((Vector(contexts[n][0][0]) for n in ('lung_upper_lobe_right', 'lung_lower_lobe_right')), Vector()) / 2
    orientation = {'leftContextPointBlenderM': list(left), 'rightContextPointBlenderM': list(right),
                   'leftPixelOverview': project(left, CAMERAS['overview']),
                   'rightPixelOverview': project(right, CAMERAS['overview'])}
    require(orientation['leftPixelOverview'][0] < orientation['rightPixelOverview'][0], 'Laterality is mirrored')
    result = {'schemaVersion': 1, 'source': record, 'views': views, 'orientationWitness': orientation,
              'overviewFraming': framing,
              'reusedDetail': {'fromV1RenderReceiptSha256': V1_RENDER_RECEIPT_SHA,
                               'images': [r['file'] for r in reused_rows]} if reused_rows else None,
              'sourceBytesAndGeometryUnchanged': True, 'blender': bpy.app.version_string,
              'display': {'lighting': lights, 'worldColor': [.025, .035, .045], 'worldStrength': .4,
                          'engine': 'Cycles CPU', 'samples': 48, 'seed': 0, 'denoise': False,
                          'colorManagement': 'AgX Medium High Contrast; exposure 0',
                          'context': 'Editorial translucent front-face display; invisible to lighting rays',
                          'componentMaterial': 'Opaque diagnostic rose; same in all four renders'},
              'scope': 'Matched new renders of exact retained component. Context is coarse same-case source geometry; no fitting, additions to the selected component, fusion, repair or lumen claim.'}
    (output / 'render.json').write_text(json.dumps(result, indent=2) + '\n')
    return {'views': [v['file'] for v in views], 'unchangedGeometry': True}


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Checkout containing exact hydrated GLB')
    parser.add_argument('--output', type=Path, required=True, help='New local directory')
    parser.add_argument('--reuse-detail-from', type=Path, help='Exact reviewed v1 render directory; only overview is rerendered')
    options = parser.parse_args(args)
    print(json.dumps(run(options.root, options.output, options.reuse_detail_from), indent=2))
