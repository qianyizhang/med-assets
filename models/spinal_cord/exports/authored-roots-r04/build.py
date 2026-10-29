"""Build the r04 representative root/ganglion study from the frozen r03 cord.

Run with Blender 4.3.2. The generated GLB is a local build product, not bundled.
Coordinates and spacing are authored teaching choices, not registered anatomy.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

BASELINE_SHA256 = '5d9f0f88ff8498f611aea583e080558691d592a3ce50c89ecb847cf18b4d1471'


def cy(z):
    return .055 + .015 * math.sin(math.pi * min(1, max(0, (.322-z)/.442)))


def radius(z):
    r = .0045 + .0022 * math.exp(-((z-.25)/.05)**2) + .0016 * math.exp(-((z+.015)/.045)**2)
    return r * max(.015, (z+.137)/.052)**.8 if z < -.085 else r


def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = .78
    return m


def tube(name, controls, radii, mat, extras, ganglion_index=None):
    """Smooth centerline, continuous variable radius, capped manifold sweep."""
    points = [Vector(p) for p in controls]
    tangents = []
    for i, p in enumerate(points):
        if i == 0:
            t = points[1]-p
        elif i == len(points)-1:
            t = p-points[i-1]
        else:
            a, b = p-points[i-1], points[i+1]-p
            t = (a.normalized()+b.normalized()).normalized() * min(a.length, b.length)
        tangents.append(t)
    centers, widths, node_samples = [], [], []
    profile_radii = list(radii)
    if ganglion_index is not None:
        profile_radii[ganglion_index] = radii[ganglion_index-1]
    for i in range(len(points)-1):
        n = max(5, math.ceil((points[i+1]-points[i]).length/.0012))
        node_samples.append(len(centers))
        for j in range(n):
            t = j/n
            p = (2*t**3-3*t*t+1)*points[i] + (t**3-2*t*t+t)*tangents[i]
            p += (-2*t**3+3*t*t)*points[i+1] + (t**3-t*t)*tangents[i+1]
            centers.append(p)
            s = t*t*(3-2*t)
            widths.append(profile_radii[i]*(1-s)+profile_radii[i+1]*s)
    centers.append(points[-1]); widths.append(radii[-1])
    if ganglion_index is not None:
        distances = [0.0]
        for left, right in zip(centers, centers[1:]):
            distances.append(distances[-1]+(right-left).length)
        center_s = distances[node_samples[ganglion_index]]
        peak = radii[ganglion_index]-profile_radii[ganglion_index]
        widths = [r+peak*math.exp(-.5*((s-center_s)/.0021)**2)
                  for r, s in zip(widths, distances)]
    verts, faces = [], []
    sides = 16
    normal = None
    for i, (p, r) in enumerate(zip(centers, widths)):
        tangent = centers[min(i+1, len(centers)-1)] - centers[max(i-1, 0)]
        tangent.normalize()
        if normal is None:
            normal = tangent.cross(Vector((0, 1, 0))).normalized()
        else:
            normal = (normal-tangent*normal.dot(tangent)).normalized()
        bitangent = tangent.cross(normal).normalized()
        for j in range(sides):
            a = 2*math.pi*j/sides
            verts.append(tuple(p+r*(math.cos(a)*normal+math.sin(a)*bitangent)))
        if i:
            for j in range(sides):
                a = (i-1)*sides+j; b = (i-1)*sides+(j+1)%sides
                c = i*sides+(j+1)%sides; d = i*sides+j
                faces.extend([(a,b,c), (a,c,d)])
    for i in (0, len(centers)-1):
        c = len(verts); verts.append(tuple(centers[i]))
        for j in range(sides):
            faces.append((c, i*sides+j, i*sides+(j+1)%sides))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    for f in me.polygons:
        f.use_smooth = True
    for key, value in extras.items():
        ob[key] = value
    return ob


def build(baseline, output):
    raw = baseline.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA256:
        raise ValueError('Expected the exact r03 baseline payload; pointers are not geometry')
    output.mkdir(exist_ok=False, parents=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(baseline), merge_vertices=True)
    kept = []
    for ob in list(bpy.context.scene.objects):
        if ob.name.startswith(('Authored cord', 'Filum')):
            kept.append(ob.name)
        else:
            bpy.data.objects.remove(ob, do_unlink=True)
    if len(kept) != 2:
        raise ValueError('Expected exactly the retained cord and filum')
    dorsal = material('Dorsal root and ganglion - illustrative ochre', (.66,.47,.24))
    ventral = material('Ventral root - illustrative pale gold', (.78,.65,.42))
    mixed = material('Mixed nerve - illustrative ivory', (.73,.63,.45))
    records = []
    groups = [('upper', [.295,.267,.235,.2,.16,.12,.08,.04,.005,-.03]),
              ('descending', [-.045,-.058,-.071,-.084,-.097,-.110,-.123])]
    for region, levels in groups:
        for i, z in enumerate(levels):
            for side in (-1, 1):
                y, rr = cy(z), radius(z)
                if region == 'upper':
                    drop = .003+.025*i/9
                    end = Vector((side*.030, y, z-drop))
                    trunk_end = end + Vector((side*.007, 0, -.002))
                else:
                    lane = .019-.00165*i
                    end = Vector((side*(.031-.0017*i), .055-.0015*i, -.158-.011*i))
                    trunk_end = end + Vector((side*.007, 0, -.004))
                common = (trunk_end-end).normalized()
                for role, sign, mat in [('dorsal',1,dorsal),('ventral',-1,ventral)]:
                    origin = (side*rr*.72, y+sign*rr*.45, z)
                    if region == 'upper':
                        mid = (side*.012, y+sign*.0045, z-drop*.3+sign*.0015)
                        ganglion = end + Vector((-side*.009, sign*.004, .004+sign*.0012))
                        prior = Vector(mid)
                        controls = [origin, mid]
                    else:
                        mid = (side*lane, .055+sign*.003-.0015*i, z-.025)
                        prior = Vector((side*(lane+.001), end.y+sign*.003, -.14-.008*i))
                        ganglion = end + Vector((-side*.006, sign*.0035, .006+sign*.001))
                        controls = [origin, mid, tuple(prior)]
                    axis = (end-prior).normalized()
                    controls.extend([tuple(ganglion-axis*.0025), tuple(ganglion),
                                     tuple(ganglion+axis*.0025),
                                     tuple(end-common*.0016), tuple(end+common*.0005)])
                    base = .00055 if region == 'upper' else .00048
                    radii = [base]*len(controls)
                    # Only the dorsal root carries a smooth spindle enlargement.
                    gi = len(controls)-4
                    if role == 'dorsal':
                        radii[gi] = .00145 if region == 'upper' else .0013
                    radii[-2:] = [base, .00061]
                    name = f'Representative {role} root {region} {i+1} side{side}'
                    extras = {'role':role,'pair':f'{region}-{i+1}-{side}',
                              'scope':'Illustrative sampled roots; no vertebral registration',
                              'ganglion':role == 'dorsal'}
                    tube(name, controls, radii, mat, extras, gi if role == 'dorsal' else None)
                    records.append({'name':name,'role':role,'region':region,'level':i+1,
                                    'side':side,'controls':controls,'radii':radii,
                                    'ganglion_index':gi if role == 'dorsal' else None})
                name = f'Representative mixed nerve {region} {i+1} side{side}'
                controls = [tuple(end-common*.0014), tuple(end+common*.0014), tuple(trunk_end)]
                tube(name, controls, [.00008,.00082,.0008], mixed,
                     {'role':'mixed','pair':f'{region}-{i+1}-{side}',
                      'scope':'Short mixed spinal nerve; distal rami omitted'})
                records.append({'name':name,'role':'mixed','region':region,'level':i+1,
                                'side':side,'controls':controls,'radii':[.00008,.00082,.0008]})
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(output/'candidate.glb'), export_format='GLB',
                             use_selection=True, export_extras=True, export_animations=False)
    record = {'baseline_sha256':BASELINE_SHA256,
              'candidate_sha256':hashlib.sha256((output/'candidate.glb').read_bytes()).hexdigest(),
              'preserved_objects':kept,'roots':records,
              'scope':'34 illustrative dorsal ganglia and separate ventral roots converge into 34 mixed nerves. 17 bilateral samples, not 31 spinal nerve pairs. Rootlets, rami, meninges, vessels and vertebrae omitted. Shape, spacing and dimensions authored; not clinical anatomy.'}
    (output/'build-record.json').write_text(json.dumps(record, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    build(args.baseline, args.out)
