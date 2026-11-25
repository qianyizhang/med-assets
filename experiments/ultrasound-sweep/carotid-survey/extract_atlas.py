"""Export native Z-Anatomy vessels and their neck context in RAS millimetres."""

import json
from pathlib import Path
import sys

import bpy
from mathutils.geometry import interpolate_bezier
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
from z_anatomy import new_export_directory, verified_member_hash

# Blender patient left/anterior/superior correspond to +X/-Y/+Z.
RAS_MM = np.array([-1000., -1000., 1000.])
VESSELS = {'cca': '{side} common carotid artery', 'ica': 'Internal carotid artery.{s}',
           'eca': 'External carotid artery.{s}', 'vertebral': 'Vertebral artery.{s}',
           'subclavian': '{side} subclavian artery'}
PAIRED_CONTEXT = {'jugular': 'Internal jugular vein', 'scm': 'Sternocleidomastoid muscle',
                  'scalene': 'Scalenus anterior muscle', 'clavicle': 'Clavicle',
                  'omohyoid': 'Omohyoid muscle', 'sternohyoid': 'Sternohyoid muscle',
                  'temporal-bone': 'Temporal bone', 'first-rib': 'First rib'}
SKIN_PATCHES = (
    'Frontal region', 'Parietal region', 'Occipital region', 'Mastoid region',
    'Temporal region', 'Auricular region', 'Orbital region', 'Nasal region', 'Oral region',
    'Buccal region', 'Infra-orbital region', 'Mental region', 'Parotideomasseteric region',
    'Zygomatic region', 'Submandibular triangle', 'Submental triangle', 'Carotid triangle',
    'Muscular triangle', 'Sternocleidomastoid region', 'Lesser supraclavicular fossa',
    'Lateral region of neck', 'Greater supraclavicular fossa', 'Posterior region of neck',
    'Pectoral region', 'Deltopectoral triangle', 'Infraclavicular fossa', 'Presternal region',
    'Deltoid region', 'Scapular region', 'Interscapular region', 'Vertebral region',
)


def world_mm(points, obj):
    transform = np.array(obj.matrix_world)
    return ((np.asarray(points) @ transform[:3, :3].T + transform[:3, 3]) * RAS_MM).astype('<f4')


def surface(name, graph):
    obj = bpy.data.objects[name].evaluated_get(graph)
    mesh = obj.to_mesh()
    try:
        mesh.calc_loop_triangles()
        vertices = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        faces = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int32)
        mesh.vertices.foreach_get('co', vertices)
        mesh.loop_triangles.foreach_get('vertices', faces)
        return world_mm(vertices.reshape(-1, 3), obj), faces.reshape(-1, 3)
    finally:
        obj.to_mesh_clear()


def native_line(name):
    obj = bpy.data.objects[name]
    spline, = obj.data.splines
    points = spline.bezier_points
    line = []
    for a, b in zip(points, list(points)[1:]):
        interval = interpolate_bezier(a.co, a.handle_right, b.handle_left, b.co, 17)
        line.extend(interval[:-1])
    line.append(points[-1].co)
    return world_mm(line, obj)


def extract(destination):
    identity = verified_member_hash(Path(bpy.data.filepath))
    graph = bpy.context.evaluated_depsgraph_get()
    with new_export_directory(destination) as out:
        manifest = {'atlas': 'Z-Anatomy', 'memberSha256': identity, 'coordinates': 'RAS mm',
                    'skin': 'skin.npz', 'sides': {}, 'context': {}, 'objects': {}}

        def save(key, name, *, curve=False):
            vertices, faces = surface(name, graph)
            extra = {'centerline': native_line(name)} if curve else {}
            filename = key + '.npz'
            np.savez_compressed(out / filename, vertices=vertices, faces=faces, **extra)
            manifest['objects'][filename] = [name]
            return filename

        for side in ('right', 'left'):
            short = side[0]
            arteries = {}
            for key, template in VESSELS.items():
                name = template.format(side=side.title(), s=short)
                arteries[key] = save(side + '-' + key, name, curve=True)
            manifest['sides'][side] = {'arteries': arteries}
            for key, stem in PAIRED_CONTEXT.items():
                filename = save(side + '-' + key, stem + '.' + short)
                manifest['context'][side + '-' + key] = filename
        for key, name in {'thyroid': 'Thyroid gland', 'trachea': 'Trachea', 'mandible': 'Mandible',
                          'thyroid-cartilage': 'Thyroid cartilage',
                          **{f'c{i}': f'Vertebra C{i}' for i in range(3, 8)}}.items():
            manifest['context'][key] = save(key, name)

        names = [f'{patch}.{side}' for patch in SKIN_PATCHES for side in ('r', 'l')]
        parts = [surface(name, graph) for name in names]
        verts = np.concatenate([v for v, _ in parts])
        offsets = np.cumsum([0] + [len(v) for v, _ in parts[:-1]])
        faces = np.concatenate([f + offset for (_, f), offset in zip(parts, offsets, strict=True)])
        # The exterior is tiled by named regions. Weld coincident vertices at their seams.
        _, first, remap = np.unique(verts.round(3), axis=0, return_index=True, return_inverse=True)
        np.savez_compressed(out / manifest['skin'], vertices=verts[first], faces=remap[faces].astype('<i4'))
        manifest['objects'][manifest['skin']] = names
        (out / 'atlas.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    extract(Path(sys.argv[sys.argv.index('--') + 1]))
