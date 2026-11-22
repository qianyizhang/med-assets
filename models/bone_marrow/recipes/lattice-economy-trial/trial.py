"""Test two weighted lattice-only GLB reductions against the exact r05 control."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CONTROL_SHA = '7b21b74fb3712b2816801337bd4d0732ef8bb035a999ad36558b8235609cfe02'
LATTICE = 'Connected illustrative trabecular network - not patient microar'
SHELL = 'Source exterior with authored cortical shell - cut after offset'
RATIOS = {'moderate': .72, 'strong': .48}
LIGHTS = [((-.6, -.7, .8), 14), ((.5, -.3, .1), 7), ((0, .5, .5), 10)]
VIEWS = [
    ('front', (.091, -.078, .761), .18, (0, -1, 0)),
    ('oblique', (.091, -.078, .761), .18, (.7, -1, .15)),
    ('reverse', (.091, -.078, .761), .18, (-.6, 1, .1)),
    ('close', (.091, -.078, .783), .13, (0, -1, .1)),
]


def identity(path):
    data = path.read_bytes()
    return dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def read_glb(path):
    data = path.read_bytes()
    magic, version, total, json_size, json_kind = struct.unpack_from('<4sIII4s', data)
    assert (magic, version, total, json_kind) == (b'glTF', 2, len(data), b'JSON')
    document = json.loads(data[20:20 + json_size])
    bin_size, bin_kind = struct.unpack_from('<I4s', data, 20 + json_size)
    assert bin_kind == b'BIN\x00'
    binary = data[28 + json_size:]
    assert len(binary) == bin_size
    return document, binary


def stitch_lattice(control, standalone, output):
    """Keep the original scene and non-lattice accessor content byte-for-byte."""
    doc, binary = read_glb(control)
    original_doc, original_bin = read_glb(control)
    small_doc, small_bin = read_glb(standalone)
    mesh_index = next(node['mesh'] for node in doc['nodes'] if node['name'] == LATTICE)
    old_primitive, = doc['meshes'][mesh_index]['primitives']
    new_primitive, = small_doc['meshes'][0]['primitives']
    assert old_primitive['attributes'].keys() == new_primitive['attributes'].keys()
    assert len(doc['buffers']) == len(small_doc['buffers']) == 1
    replacements = {
        **{i: new_primitive['attributes'][key] for key, i in old_primitive['attributes'].items()},
        old_primitive['indices']: new_primitive['indices'],
    }
    owners = {a['bufferView']:i for i,a in enumerate(doc['accessors'])}
    assert len(owners) == len(doc['bufferViews']) == len(doc['accessors'])
    buffer = bytearray()
    for vi, view in enumerate(doc['bufferViews']):
        owner = owners[vi]
        source = binary
        old_offset = view.get('byteOffset', 0)
        if owner in replacements:
            new = dict(small_doc['accessors'][replacements[owner]])
            view = dict(small_doc['bufferViews'][new['bufferView']])
            old_offset = view.get('byteOffset', 0)
            source = small_bin
            new['bufferView'] = vi
            doc['accessors'][owner] = new
        view['byteOffset'] = len(buffer)
        end = old_offset + view['byteLength']
        buffer.extend(source[old_offset:end])
        buffer.extend(bytes(-len(buffer) % 4))
        doc['bufferViews'][vi] = view
    doc['buffers'][0]['byteLength'] = len(buffer)
    raw = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
    raw += b' ' * (-len(raw) % 4)
    output.write_bytes(struct.pack('<4sIII4s', b'glTF', 2, 28 + len(raw) + len(buffer), len(raw), b'JSON')
                       + raw + struct.pack('<I4s', len(buffer), b'BIN') + buffer)
    result_doc, result_bin = read_glb(output)
    for key in ('nodes', 'meshes', 'materials', 'scenes', 'scene'):
        assert original_doc[key] == result_doc[key]

    def values(document, data, accessor):
        view = document['bufferViews'][document['accessors'][accessor]['bufferView']]
        start = view.get('byteOffset', 0)
        return data[start:start + view['byteLength']]

    for i in range(len(doc['accessors'])):
        if i not in replacements:
            assert values(original_doc, original_bin, i) == values(result_doc, result_bin, i)


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    scene = bpy.context.scene
    objects = {obj.name: obj for obj in scene.objects if obj.type == 'MESH'}
    assert len(objects) == 3 and LATTICE in objects and SHELL in objects
    return scene, objects


def weld_lattice(obj):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    bmesh.ops.remove_doubles(mesh, verts=list(mesh.verts), dist=0)
    mesh.to_mesh(obj.data)
    mesh.free()
    obj.data.update()


def surface(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    coords = [tuple(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
    weld = list(dict.fromkeys(coords))
    ids = {point:i for i,point in enumerate(weld)}
    faces = [tuple(ids[coords[i]] for i in face.vertices) for face in mesh.loop_triangles]
    return [Vector(point) for point in weld], faces


def topology(points, faces):
    incidence = Counter()
    orientation = Counter()
    parent = list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    degenerate = 0
    for a, b, c in faces:
        if (points[b]-points[a]).cross(points[c]-points[a]).length_squared == 0:
            degenerate += 1
        for u, v in ((a,b),(b,c),(c,a)):
            edge = min(u,v), max(u,v)
            incidence[edge] += 1
            orientation[edge] += 1 if u < v else -1
            parent[find(v)] = find(u)
    return dict(vertices=len(points), triangles=len(faces), edges=len(incidence),
                components=len({find(i) for i in range(len(points))}),
                euler=len(points) - len(incidence) + len(faces), degenerate=degenerate,
                notTwoIncident=sum(n != 2 for n in incidence.values()),
                inconsistent=sum(n != 0 for n in orientation.values()))


def bvh(surface_data):
    points, faces = surface_data
    return BVHTree.FromPolygons(points, faces, all_triangles=True)


def displacement(source, target):
    points, faces = source
    tree = bvh(target)
    worst = (0., None, None, '')
    for name, positions in [('vertex', points), ('face center', (
            (points[a]+points[b]+points[c])/3 for a,b,c in faces))]:
        for point in positions:
            hit, _, _, distance = tree.find_nearest(point)
            if distance > worst[0]:
                worst = (distance, tuple(point), tuple(hit), name)
    return dict(meters=worst[0], pointM=worst[1], nearestM=worst[2], sample=worst[3])


def protect(obj, shell):
    """Bias collapse away from cortical interfaces and thin strut cross sections."""
    shell_tree = bvh(surface(shell))
    lattice_tree = bvh(surface(obj))
    group = obj.vertex_groups.new(name='Simplification allowed')
    bins = Counter()
    protected = {'interface': [], 'thin': []}
    for vertex in obj.data.vertices:
        p = obj.matrix_world @ vertex.co
        normal = (obj.matrix_world.to_3x3() @ vertex.normal).normalized()
        _, _, _, shell_distance = shell_tree.find_nearest(p)
        _, _, _, width = lattice_tree.ray_cast(p - normal * .00001, -normal, .00052)
        if shell_distance < .00034:
            weight = .01
            bins['interface'] += 1
            protected['interface'].append(p)
        elif width is not None and width < .00044:
            weight = .04
            bins['thin'] += 1
            protected['thin'].append(p)
        else:
            weight = 1.0
            bins['ordinary'] += 1
        group.add([vertex.index], weight, 'REPLACE')
    return group, dict(bins), protected


def protected_displacement(protected, target):
    tree = bvh(target)
    result = {}
    for region, points in protected.items():
        distance, point = max(
            ((tree.find_nearest(p)[3], tuple(p)) for p in points),
            key=lambda row: row[0],
        )
        result[region] = dict(samples=len(points), maxMeters=distance, pointM=point)
    return result


def render(scene, output, key, model, extra_views=()):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.seed = 17
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.world = bpy.data.worlds.new('r05 world')
    scene.world.color = (.1, .1, .1)
    scene.view_settings.view_transform = 'AgX'
    light_target = Vector((.091, -.078, .761))
    factor = .18/.15
    for direction,power in LIGHTS:
        light = bpy.data.lights.new('Owner broad light', 'AREA')
        light.energy = power * factor ** 2
        light.shape = 'DISK'
        light.size = .4 * factor
        lamp = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(lamp)
        lamp.location = light_target + Vector(direction)*factor
        lamp.rotation_euler = (light_target-lamp.location).to_track_quat('-Z','Y').to_euler()
    cam = bpy.data.cameras.new('Owner orthographic camera')
    cam.type = 'ORTHO'
    obj = bpy.data.objects.new(cam.name, cam)
    scene.collection.objects.link(obj)
    scene.camera = obj
    views = []
    for name, center, scale, direction in (*VIEWS,*extra_views):
        target = Vector(center)
        obj.location = target + Vector(direction).normalized()
        obj.rotation_euler = (target-obj.location).to_track_quat('-Z','Y').to_euler()
        cam.ortho_scale = scale
        path = output / f'{key}-{name}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        views.append(dict(file=path.name, **identity(path), model=model, direction=direction,
                          targetM=center, orthoScaleM=scale))
    return views


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    control = args.control.resolve()
    ref = identity(control)
    if ref['sha256'] != CONTROL_SHA:
        raise ValueError('Wrong r05 control digest')
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    _, layers = load(control)
    before = surface(layers[LATTICE])
    summary = {'control':ref, 'lattice':topology(*before), 'variants':[]}
    files = [('control', control)]
    for name, ratio in RATIOS.items():
        _, layers = load(control)
        lattice = layers[LATTICE]
        weld_lattice(lattice)
        mask, weights, protected = protect(lattice, layers[SHELL])
        modifier = lattice.modifiers.new('Weighted lattice-only reduction', 'DECIMATE')
        modifier.ratio = ratio
        modifier.vertex_group = mask.name
        modifier.vertex_group_factor = 100
        bpy.context.view_layer.objects.active = lattice
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.ops.object.select_all(action='DESELECT')
        lattice.select_set(True)
        temporary = output / f'{name}-lattice.glb'
        bpy.ops.export_scene.gltf(filepath=str(temporary), export_format='GLB', use_selection=True)
        candidate = output / f'{name}.glb'
        stitch_lattice(control, temporary, candidate)
        temporary.unlink()
        files.append((name,candidate))
        _, layers = load(candidate)
        after = surface(layers[LATTICE])
        summary['variants'].append(dict(name=name, ratio=ratio, asset=identity(candidate),
                                     maskVertices=weights, topology=topology(*after),
                                     protectedDisplacement=protected_displacement(protected, after),
                                     fromControl=displacement(before,after),
                                     toControl=displacement(after,before)))
        (output/'geometry.json').write_text(json.dumps(summary,indent=2)+'\n')
    if not args.check_only:
        extra_views = []
        for direction in ('fromControl', 'toControl'):
            worst = max(summary['variants'], key=lambda item: item[direction]['meters'])
            extra_views.append((f'worst-{direction}', worst[direction]['pointM'], .018, (.7, -1, .15)))
        views = {}
        for name,path in files:
            scene,_ = load(path)
            views[name] = render(scene,output,name,identity(path),extra_views)
        (output/'views.json').write_text(json.dumps(views,indent=2)+'\n')


if __name__ == '__main__':
    main()
