"""Exact surface-support audit, separate from full winding/appearance preservation.

Only source-traced reversed indexed pairs may lose one occurrence at first
Blender import. This is NOT a culling, shading, anatomy or viewer approval.
Run with Blender --python-exit-code 1 --python this_file -- --help.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_source import load, accessor, world_blender, SOURCE_SHA
from check import CANDIDATE_SHA


def oriented(triangle):
    return min(triangle, triangle[1:] + triangle[:1], triangle[2:] + triangle[:2])


def support(triangle):
    return tuple(sorted(triangle))


def compare_faces(expected, actual, allowed_pairs=frozenset()):
    """Exact coordinates, winding and occurrence accounting; no distance snapping.

    allowed_pairs names individual geometric supports, not whole meshes. Each
    must contain exactly one face in each orientation before import and exactly
    one original orientation after import. All other multisets must match.
    """
    before = Counter(oriented(tuple(t)) for t in expected)
    after = Counter(oriented(tuple(t)) for t in actual)
    groups = defaultdict(Counter)
    other = defaultdict(Counter)
    for tri, count in before.items():
        groups[support(tri)][tri] = count
    for tri, count in after.items():
        other[support(tri)][tri] = count
    if set(groups) != set(other):
        raise ValueError('Distinct surface missing, moved or added')
    if not set(allowed_pairs) <= set(groups):
        raise ValueError('Unknown duplicate exception')
    for key, counts in groups.items():
        if key not in allowed_pairs:
            if counts != other[key]:
                raise ValueError('Unambiguous winding or unexpected duplicate change')
        else:
            if len(counts) != 2 or sorted(counts.values()) != [1, 1]:
                raise ValueError('Exception is not one opposite-winding pair')
            if sum(other[key].values()) != 1 or other[key] - counts:
                raise ValueError('Unexpected duplicate survival or orientation')
    missing = before - after
    return {'rawTriangles': sum(before.values()), 'actualTriangles': sum(after.values()),
            'distinctSupports': len(groups), 'distinctSupportsLost': 0,
            'oppositeWindingOccurrencesRemoved': sum(missing.values()),
            'fullOrientedMultisetPreserved': before == after}


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def material_semantics(material):
    pbr = material.get('pbrMetallicRoughness', {})
    # Fixed study materials have no textures/extensions. Fail closed otherwise.
    if set(material) - {'name', 'pbrMetallicRoughness', 'alphaMode', 'alphaCutoff',
                        'doubleSided', 'emissiveFactor'}:
        raise ValueError('Unsupported material fields')
    if set(pbr) - {'baseColorFactor', 'metallicFactor', 'roughnessFactor'}:
        raise ValueError('Unsupported PBR fields')
    return {'name': material.get('name'),
            'baseColor': tuple(map(f32, pbr.get('baseColorFactor', [1, 1, 1, 1]))),
            'metallic': f32(pbr.get('metallicFactor', 1)),
            'roughness': f32(pbr.get('roughnessFactor', 1)),
            'emissive': tuple(map(f32, material.get('emissiveFactor', [0, 0, 0]))),
            'alphaMode': material.get('alphaMode', 'OPAQUE'),
            'alphaCutoff': f32(material.get('alphaCutoff', .5)),
            'doubleSided': material.get('doubleSided', False)}


def check_materials(before, after):
    if before != after:
        raise ValueError('Material semantics or assignment changed')


def check_transforms(before, after):
    if before != after:
        raise ValueError('Object transforms or hierarchy changed')


def decoded(doc, binary):
    rows = {}
    for mesh in doc['meshes']:
        if len(mesh['primitives']) != 1:
            raise ValueError('Expected single primitive')
        p = mesh['primitives'][0]
        if p.get('mode', 4) != 4:
            raise ValueError('Expected triangles')
        vertices = [world_blender(v) for v in accessor(doc, binary, p['attributes']['POSITION'])]
        normals = [world_blender(v) for v in accessor(doc, binary, p['attributes']['NORMAL'])]
        indices = [x[0] for x in accessor(doc, binary, p['indices'])]
        tris = [tuple(indices[k:k+3]) for k in range(0, len(indices), 3)]
        rows[mesh['name']] = {'indices': tris, 'faces': [tuple(vertices[i] for i in t) for t in tris],
                              'normals': [tuple(normals[i] for i in t) for t in tris],
                              'material': material_semantics(doc['materials'][p['material']])}
    return rows


def source_pairs(source, candidate, mapping):
    """Prove each exception is an unchanged indexed opposite pair from source."""
    exceptions = {}; lineage = []
    for name, row in candidate.items():
        groups = defaultdict(list)
        for i, tri in enumerate(row['indices']):
            groups[tuple(sorted(tri))].append(i)
        allowed = set()
        for indexed, ids in groups.items():
            if len(ids) == 1:
                continue
            if len(ids) != 2 or oriented(row['indices'][ids[0]]) == oriented(row['indices'][ids[1]]):
                raise ValueError('Unexpected source duplicate multiplicity/winding')
            source_ids = [mapping[name][i] for i in ids]
            src = [source[name]['indices'][i] for i in source_ids]
            if any(tuple(sorted(t)) != indexed for t in src) or oriented(src[0]) == oriented(src[1]):
                raise ValueError('Duplicate not traced to reversed source indexed pair')
            for i, sid in zip(ids, source_ids):
                if oriented(row['faces'][i]) != oriented(source[name]['faces'][sid]):
                    raise ValueError('Source duplicate coordinates/winding changed')
            key = support(row['faces'][ids[0]])
            if key in allowed:
                raise ValueError('Multiple duplicate pairs at one support')
            allowed.add(key)
            lineage.append({'node': name, 'candidateFaces': ids, 'sourceFaces': source_ids,
                            'sourceVertexIndices': indexed, 'supportBlenderMetres': key})
        exceptions[name] = allowed
    return exceptions, lineage


def snapshot(bpy):
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        obj.data.calc_loop_triangles()
        vertices = [tuple(obj.matrix_world @ v.co) for v in obj.data.vertices]
        triangles = list(obj.data.loop_triangles)
        result[obj.name] = {'faces': [tuple(vertices[i] for i in t.vertices) for t in triangles],
                            'normals': [tuple(tuple(obj.data.corner_normals[i].vector) for i in t.loops)
                                        for t in triangles],
                            'transform': (tuple(tuple(r) for r in obj.matrix_world),
                                          tuple(tuple(r) for r in obj.matrix_local),
                                          obj.parent.name if obj.parent else None),
                            'materials': tuple(m.name for m in obj.data.materials),
                            'materialIndices': tuple(t.material_index for t in triangles),
                            'culling': tuple(m.use_backface_culling for m in obj.data.materials)}
    return result


def normal_audit(raw, imported, duplicate_supports=frozenset()):
    """Compare matched oriented corners; do not confuse winding and NORMAL."""
    def normalized(normals):
        result = []
        for normal in normals:
            length = math.sqrt(sum(x*x for x in normal))
            result.append(tuple(x/length for x in normal) if length else tuple(normal))
        return tuple(result)

    def normal_multiset(mesh):
        result = Counter()
        for face, normals in zip(mesh['faces'], mesh['normals']):
            k = min(range(3), key=lambda i: face[i:]+face[:i])
            result[(oriented(face), normalized(normals[k:]+normals[:k]))] += 1
        return result

    # Subset permits the separately audited removal of reversed faces; Counter
    # subtraction prevents reusing one source normal tuple for coincident faces.
    unmatched = normal_multiset(imported) - normal_multiset(raw)
    lookup = defaultdict(list)
    for face, normals in zip(raw['faces'], raw['normals']):
        k = min(range(3), key=lambda i: face[i:]+face[:i])
        lookup[oriented(face)].append(normals[k:]+normals[:k])
    maximum = 0; nonzero_maximum = 0; changed = 0; zero = 0; opposite = 0; matched = 0
    zero_on_duplicate = 0; zero_at_duplicate_vertex = 0
    zero_output = 0
    maxima = {'onDuplicateSupport': 0, 'atDuplicateVertexOnly': 0, 'elsewhere': 0}
    nonzero_maxima = dict(maxima)
    duplicate_vertices = {v for tri in duplicate_supports for v in tri}
    for face, normals in zip(imported['faces'], imported['normals']):
        k = min(range(3), key=lambda i: face[i:]+face[:i]); ns = normals[k:]+normals[:k]
        candidates = lookup[oriented(face)]
        def errors(original):
            values = []
            for old, new in zip(original, ns):
                length = math.sqrt(sum(x*x for x in old))
                normalized = tuple(x/length for x in old) if length else old
                values.append(max(abs(x-y) for x, y in zip(normalized, new)))
            return values
        original = min(candidates, key=lambda n: max(errors(n)))
        canonical_face = oriented(face)
        for corner, (old, new, error) in enumerate(zip(original, ns, errors(original))):
            matched += 1; zero += not any(old); changed += error != 0
            zero_output += not any(new)
            opposite += sum(x*y for x,y in zip(old,new)) < 0
            maximum = max(maximum, error)
            category = ('onDuplicateSupport' if support(face) in duplicate_supports else
                        'atDuplicateVertexOnly' if canonical_face[corner] in duplicate_vertices else 'elsewhere')
            maxima[category] = max(maxima[category], error)
            if any(old):
                nonzero_maximum = max(nonzero_maximum, error)
                nonzero_maxima[category] = max(nonzero_maxima[category], error)
            else:
                zero_on_duplicate += support(face) in duplicate_supports
                zero_at_duplicate_vertex += canonical_face[corner] in duplicate_vertices
    return {'matchedCorners': matched, 'zeroInputNormalCorners': zero,
            'changedNormalizedNormalCornersExact': changed,
            'negativeNormalDotCorners': opposite, 'maxNormalizedComponentDifference': maximum,
            'maxNonzeroInputNormalizedComponentDifference': nonzero_maximum,
            'zeroInputCornersOnDuplicateSupports': zero_on_duplicate,
            'zeroInputCornersAtDuplicateVertices': zero_at_duplicate_vertex,
            'zeroOutputNormalCorners': zero_output,
            'maxComponentDifferenceByDuplicateLocation': maxima,
            'maxNonzeroInputComponentDifferenceByDuplicateLocation': nonzero_maxima,
            'unmatchedNormalizedFaceNormalOccurrences': sum(unmatched.values()),
            'normalPreservation': 'passed' if not unmatched else 'failed-exact-preservation',
            'scope': 'Exact status uses the oriented face and normalized corner-normal multiset subset, with occurrence accounting. Component differences and changed-corner counts are best-available-match diagnostics, not correspondence proof. Geometry/multiplicity is gated separately; no angular tolerance or shading equivalence asserted.'}


def negative_controls(raw, first, exceptions):
    """Exercise guards on the freshly imported real geometry, not just hashes."""
    rows = []
    name = 'Yao_afferent_lymphatic_vessel'
    original = raw[name]['faces']; actual = first[name]['faces']
    def rejects(label, action, expected):
        try:
            action()
        except ValueError as error:
            if expected not in str(error):
                raise AssertionError('Wrong negative-control rejection: '+str(error)) from error
            rows.append({'case': label, 'rejection': str(error)})
        else:
            raise AssertionError('Negative control accepted: '+label)
    rejects('missing distinct actual face', lambda: compare_faces(original, actual[1:]), 'Distinct surface')
    flipped = [(actual[0][0], actual[0][2], actual[0][1]), *actual[1:]]
    rejects('flipped unambiguous actual face', lambda: compare_faces(original, flipped), 'Unambiguous winding')
    rejects('unexpected extra actual duplicate', lambda: compare_faces(original, [*actual, actual[0]]), 'duplicate')
    network = 'Yao_blood_vasculature'
    retained = next(t for t in first[network]['faces'] if support(t) in exceptions[network])
    rejects('unexpected source-pair duplicate retained',
            lambda: compare_faces(raw[network]['faces'], [*first[network]['faces'], retained], exceptions[network]),
            'Unexpected duplicate survival')
    rejects('missing duplicate authorization',
            lambda: compare_faces(raw[network]['faces'], first[network]['faces']), 'duplicate')
    for field, value in [('doubleSided', True), ('alphaMode', 'BLEND'),
                         ('baseColor', (0., 0., 0., 1.)), ('name', 'wrong tissue')]:
        changed = {**raw[name]['material'], field: value}
        rejects('changed actual material '+field,
                lambda changed=changed: check_materials(raw[name]['material'], changed), 'Material')
    transform = first[name]['transform']
    rejects('changed actual transform', lambda: check_transforms(transform, ((), *transform[1:])), 'transforms')
    return rows


def main():
    import bpy
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--candidate-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    candidate_path = a.candidate_dir / 'lymph-node-editorial-window-r03.glb'
    for path, digest in ((a.source, SOURCE_SHA), (candidate_path, CANDIDATE_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned input mismatch')
    a.output.mkdir(parents=True, exist_ok=False)
    sd, sb = load(a.source); cd, cb = load(candidate_path)
    source = decoded(sd, sb); raw = decoded(cd, cb)
    mapping = json.loads((a.candidate_dir / 'triangle-source-map.json').read_text())
    exceptions, lineage = source_pairs(source, raw, mapping)
    if {n: len(v) for n,v in exceptions.items() if v} != {
            'Yao_medulla_of_lymph_node': 18, 'Yao_blood_vasculature': 88}:
        raise ValueError('Pinned duplicate inventory changed')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(candidate_path))
    first = snapshot(bpy)
    if set(first) != set(raw):
        raise ValueError('Object inventory changed')
    identity = tuple(tuple(float(i == j) for j in range(4)) for i in range(4))
    direct = []; normal_rows = []
    for name, row in raw.items():
        check_transforms((identity, identity, 'Yao_lymph_node'), first[name]['transform'])
        check_materials((row['material']['name'],), first[name]['materials'])
        if any(first[name]['materialIndices']) or first[name]['culling'] != (not row['material']['doubleSided'],):
            raise ValueError('Material assignment or culling changed')
        result = compare_faces(row['faces'], first[name]['faces'], exceptions[name])
        missing = Counter(oriented(t) for t in row['faces']) - Counter(oriented(t) for t in first[name]['faces'])
        area = 0
        for tri, count in missing.items():
            ab = tuple(y-x for x,y in zip(tri[0],tri[1])); ac = tuple(y-x for x,y in zip(tri[0],tri[2]))
            cross = (ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
            area += count*math.sqrt(sum(x*x for x in cross))/2
        direct.append({'node': name, **result, 'removedOrientedAreaSquareMetres': area,
                       'material': row['material'], 'singleSidedFrontFaceSupportPreserved': not missing})
        normal_rows.append({'node': name, **normal_audit(row, first[name], exceptions[name])})
    negatives = negative_controls(raw, first, exceptions)
    path = a.output / 'blender-roundtrip.glb'
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                             export_extras=True, export_cameras=False, export_lights=False)
    ed, eb = load(path); exported = decoded(ed, eb)
    if set(exported) != set(raw):
        raise ValueError('Export mesh inventory changed')
    for name in raw:
        check_materials(raw[name]['material'], exported[name]['material'])
        compare_faces(first[name]['faces'], exported[name]['faces'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    second = snapshot(bpy)
    if set(second) != set(first):
        raise ValueError('Reimport object inventory changed')
    roundtrip = []
    for name in first:
        check_transforms(first[name]['transform'], second[name]['transform'])
        check_materials((first[name]['materials'], first[name]['culling']),
                        (second[name]['materials'], second[name]['culling']))
        if any(second[name]['materialIndices']):
            raise ValueError('Reimport material assignment changed')
        roundtrip.append({'node': name, **compare_faces(first[name]['faces'], second[name]['faces']),
                          'normals': normal_audit(first[name], second[name])})
    report = {'sourceSha256': SOURCE_SHA, 'candidateSha256': CANDIDATE_SHA,
              'blender': bpy.app.version_string,
              'surfaceSupportAndUnambiguousOrientation': 'passed',
              'directFullOrientedMultisetPreservation': 'failed',
              'singleSidedFrontFaceSupportPreservation': 'failed',
              'appearanceEquivalence': 'unverified; normals and front-face support differ',
              'directImport': direct, 'normalAudit': normal_rows, 'duplicateLineage': lineage,
              'negativeControls': negatives,
              'roundtrip': roundtrip, 'roundtripSha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'vertexColorPreservation': 'unverified; COLOR_0 is not compared by this support/material audit',
              'materialScope': 'Effective GLB PBR, alpha, doubleSided and assignment; float32 storage precision. No texture materials supported.',
              'scope': 'Exact surface support and winding except 106 individually traced source pairs. Original strict failure retained. No anatomy, clinical, browser-runtime or generic appearance approval.'}
    with (a.output / 'surface-audit.json').open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    print('PASS bounded surface support; FAIL full winding and single-sided front-face support; see surface-audit.json')


if __name__ == '__main__':
    main()
