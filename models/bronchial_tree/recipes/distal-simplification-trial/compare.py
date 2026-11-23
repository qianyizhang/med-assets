"""Reimport both GLBs, check the retained surfaces and render the teaching views."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simplify import HERE, R13, mesh_data, oriented, protection
from tools.render_teaching import area_light

CAMERAS = HERE / 'r13-cameras.json'
OLD_CAMERAS = HERE.parent / 'authored-central-fairing-r13' / 'baseline-cameras.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def decode_comparison(source, candidate):
    baseline, pos, nor, faces = mesh_data(source.read_bytes())
    updated, other_pos, other_nor, other_faces = mesh_data(candidate.read_bytes())
    scene_keys = ('scene', 'scenes', 'nodes', 'meshes', 'materials')
    if any(baseline[key] != updated[key] for key in scene_keys):
        raise ValueError('Scene, node, primitive or material changed')

    # An exact coordinate match identifies the original vertex, independent of
    # the builder's vertex IDs. Treat both arrays as rows of 3 coordinates.
    ids = {tuple(point): i for i, point in enumerate(pos)}
    mapped = np.array([ids.get(tuple(point), -1) for point in other_pos])
    if (mapped < 0).any():
        raise ValueError('Candidate contains vertices absent from r13')
    if len(ids) != len(pos) or len(np.unique(mapped)) != len(other_pos):
        raise ValueError('Expected a unique mapping to surviving r13 vertices')
    if not np.array_equal(nor[mapped], other_nor):
        raise ValueError('A surviving encoded normal changed')
    mapped_faces = mapped[other_faces]
    regions = {}
    for name, mask in protection(pos).items():
        before = oriented(faces[mask[faces].any(axis=1)])
        after = oriented(mapped_faces[mask[mapped_faces].any(axis=1)])
        if not mask.any() or not np.array_equal(before, after):
            raise ValueError(f'Protected oriented triangles changed: {name}')
        regions[name] = {'vertices': int(mask.sum()), 'exactIncidentTriangles': len(before)}
    return regions


def reimport(path):
    for obj in list(bpy.data.objects):
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), merge_vertices=False)
    obj, = (obj for obj in bpy.context.scene.objects if obj.type == 'MESH')
    mesh = obj.data
    mesh.calc_loop_triangles()
    positions = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', positions)
    matrix = np.array(obj.matrix_world)
    world = positions.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    corners = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int32)
    mesh.loop_triangles.foreach_get('vertices', corners)
    faces = corners.reshape(-1, 3)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    start = next(iter(bm.verts))
    seen, todo = {start}, [start]
    while todo:
        current = todo.pop()
        for edge in current.link_edges:
            neighbor = edge.other_vert(current)
            if neighbor not in seen:
                todo.append(neighbor)
                seen.add(neighbor)
    stats = {
        'name': obj.name,
        'worldMatrix': matrix.tolist(),
        'vertices': len(bm.verts),
        'triangles': len(faces),
        'euler': len(bm.verts) - len(bm.edges) + len(bm.faces),
        'oneComponent': len(seen) == len(bm.verts),
        'nonManifoldEdges': sum(not edge.is_manifold for edge in bm.edges),
        'inconsistentEdges': sum(not edge.is_contiguous for edge in bm.edges),
        'degenerateFaces': sum(face.calc_area() < 1e-13 for face in bm.faces),
        'signedVolumeCubicMeters': bm.calc_volume(signed=True),
        'boundsMeters': [world.min(axis=0).tolist(), world.max(axis=0).tolist()],
    }
    bm.free()
    return world, faces, stats


def sampled_distance(world, faces, toward, toward_faces):
    tree = BVHTree.FromPolygons(toward.tolist(), toward_faces.tolist(), all_triangles=True)
    result = {}
    for label, points in [('vertices', world), ('faceCenters', world[faces].mean(axis=1))]:
        distances = np.fromiter((tree.find_nearest(point)[3] for point in points),
                                dtype=float, count=len(points)) * 1000
        worst = int(distances.argmax())
        result[label] = {
            'samples': len(points),
            'p95Mm': float(np.percentile(distances, 95)),
            'maxMm': float(distances[worst]),
            'worstPointMeters': points[worst].tolist(),
        }
    return result


def geometry_passes(geometry):
    before, after = geometry['original'], geometry['updated']
    identity = ('name', 'worldMatrix')
    distances = [stat['maxMm'] for direction in ('originalToUpdated', 'updatedToOriginal')
                 for stat in geometry[direction].values()]
    return (
        before['triangles'] == 443_892
        and all(before[key] == after[key] for key in identity)
        and after['oneComponent'] and after['euler'] == 2
        and not any(after[key] for key in ('nonManifoldEdges', 'inconsistentEdges', 'degenerateFaces'))
        and after['triangles'] < before['triangles']
        and after['bytes'] < before['bytes']
        and max(distances) < .20
    )


def render_pairs(source, candidate, output):
    scene = bpy.context.scene
    scene.world.color = (.1, .1, .1)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = False
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'AgX'

    original = json.loads(CAMERAS.read_text())
    if original['sourceSha256'] != R13:
        raise ValueError('Expected camera coordinates bound to exact r13')
    views = original['views']
    whole = views['whole']
    center = Vector(whole['target'])
    scale = whole['ortho_scale'] / (1.12 * .15)
    for name, direction, energy in [('Key', (-.6, -.7, .8), 14), ('Fill', (.5, -.3, .1), 7),
                                    ('Rim', (0, .5, .5), 10)]:
        lamp = area_light(scene, center, scale, name, direction, energy, .4)
        lamp.data.shape = 'DISK'
    reverse = center * 2 - Vector(whole['position'])
    views['reverse-whole'] = dict(position=list(reverse), target=list(center),
                                  quaternion=list((center - reverse).to_track_quat('-Z', 'Y')),
                                  ortho_scale=whole['ortho_scale'])
    left = next(row for row in json.loads(OLD_CAMERAS.read_text())['cameras']
                if row['file'] == 'baseline-left_lobar_close.png')
    views['left-lobar-close'] = dict(left, quaternion=left['quaternion_wxyz'])

    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    camera.rotation_mode = 'QUATERNION'
    scene.camera = camera
    rows = {}
    for phase, path in [('original', source), ('updated', candidate)]:
        reimport(path)
        sha = digest(path)
        for name, view in views.items():
            camera.location = Vector(view['position'])
            camera.rotation_quaternion = Quaternion(view['quaternion'])
            camera.data.ortho_scale = view['ortho_scale']
            file = output / f'{name}-{phase}.png'
            scene.render.filepath = str(file.resolve())
            bpy.ops.render.render(write_still=True)
            rows.setdefault(name, {
                'position': view['position'], 'target': view['target'],
                'quaternion': view['quaternion'], 'orthoScaleMeters': view['ortho_scale'],
            })[phase] = {'file': file.name, 'sha256': digest(file), 'glbSha256': sha}
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('source', 'candidate', 'output'):
        parser.add_argument(f'--{flag}', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if digest(args.source) != R13:
        raise ValueError('Expected the exact hydrated r13 GLB')
    regions = decode_comparison(args.source, args.candidate)
    args.output.mkdir()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    world, faces, before = reimport(args.source)
    updated, new_faces, after = reimport(args.candidate)
    geometry = {
        'blender': bpy.app.version_string,
        'blenderBuild': bpy.app.build_hash.decode(),
        'original': dict(before, sha256=R13, bytes=args.source.stat().st_size),
        'updated': dict(after, sha256=digest(args.candidate), bytes=args.candidate.stat().st_size),
        'protectedRegions': regions,
        'originalToUpdated': sampled_distance(world, faces, updated, new_faces),
        'updatedToOriginal': sampled_distance(updated, new_faces, world, faces),
    }
    (args.output / 'geometry.json').write_text(json.dumps(geometry, indent=2) + '\n')
    views = render_pairs(args.source, args.candidate, args.output)
    (args.output / 'views.json').write_text(json.dumps(views, indent=2) + '\n')
    if not geometry_passes(geometry):
        raise SystemExit('Geometry comparison failed. See geometry.json.')


if __name__ == '__main__':
    main()
