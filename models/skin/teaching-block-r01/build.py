"""Build the local skin and nail teaching sections. All design coordinates are in mm."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

MM = 0.001
TAU = 2 * math.pi


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = 0.74
    return mat


def surface(name, rings, mat, *, cap=True, smooth=False):
    width = len(rings[0])
    vertices = [tuple(v * MM for v in point) for ring in rings for point in ring]
    faces = []
    for i in range(len(rings) - 1):
        for j in range(width):
            a = i * width + j
            b = i * width + (j + 1) % width
            faces.append((a, b, b + width, a + width))
    if cap:
        faces += [tuple(reversed(range(width))), tuple(range(len(vertices) - width, len(vertices)))]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = smooth
    return obj


def top(x):
    return 4.1


def basal(x):
    return 3.74 + 0.1 * math.cos(2.9 * x) + 0.04 * math.cos(5.1 * x)


def deep(x):
    return 1.02 + 0.14 * math.cos(2.4 * x + .25) + .06 * math.sin(4.3 * x)


def layer(name, lower, upper, mat, grooves=False):
    # At the cut edge, reserve a semicircular channel for each appendage.
    def front(x, z):
        if not grooves:
            return 0
        hair_relief = min(1, max(0, (z - 1.48) / .28))
        duct_relief = min(1, max(0, (z - 2.28) / .40))
        openings = [(hair_x(z), hair_radius(z) * hair_relief), (duct_x(z), .155 * duct_relief)]
        return max(math.sqrt(max(0, radius**2 - (x - cx)**2)) for cx, radius in openings)

    def ring(x):
        low, high = lower(x), upper(x)
        depths = [high - (high - low) * i / 24 for i in range(25)]
        return [(x, 2.2, low), (x, 2.2, high)] + [(x, front(x, z), z) for z in depths]
    surface(name, [ring(-3.2 + .025 * i) for i in range(257)], mat)


def fat_lobules(mat):
    # Two staggered rows of low relief lobules under the dermis.
    for row, count in [(0, 8), (1, 7)]:
        for i in range(count):
            cx = -2.78 + .78 * i + .38 * row
            z = .27 + .39 * row + .06 * math.sin(i * 2.8)
            radius_z = min(.23, deep(cx) - z - .04)
            rings = []
            for j in range(18):
                lat = -math.pi/2 + math.pi * (.01 + .98 * j/17)
                rings.append([(cx + .365 * math.cos(lat) * math.cos(k*TAU/24),
                               .027 + .115 * math.cos(lat) * math.sin(k*TAU/24),
                               z + radius_z * math.sin(lat)) for k in range(24)])
            surface('Skin | Fat lobule %02d' % (1 + i + row * 8), rings, mat, smooth=True)



def hair_x(z):
    return -.98 + .18 * (z - 2.2) + .024 * (z - 2.2)**2


def hair_radius(z):
    return .17 + .13 * math.exp(-((z - 1.83) / .33)**2)


def duct_x(z):
    return 1.49 + .082 * math.sin((z - 2.28) * 8) * min(1, max(0, (4.00 - z) * 4))


def skin():
    epidermis = material('Epidermis • warm tan', (.74, .50, .32))
    dermis = material('Dermis • terra cotta', (.55, .23, .18))
    subcutis = material('Hypodermis • ochre', (.65, .42, .21))
    sheath = material('Follicular sheath • rose', (.82, .42, .32))
    hair = material('Hair • umber', (.14, .071, .047))
    sweat = material('Eccrine tubule • teal', (.19, .46, .48))
    layer('Skin | Epidermis', basal, top, epidermis, True)
    layer('Skin | Dermis', deep, basal, dermis, True)
    layer('Skin | Subcutaneous tissue', lambda x: .0, deep, subcutis)

    fat_lobules(material('Fat lobules • pale ochre', (.77, .54, .27)))

    # Half cutaway sheath reveals the hair root, then the shaft above the skin.
    rings, root = [], []
    for i in range(69):
        z = 1.48 + (4.1 - 1.48) * i / 68
        r = hair_radius(z) * min(1, math.sqrt(.006 + (z - 1.48) / .22))
        angles = [-.10 + (math.pi + .2) * j / 32 for j in range(33)]
        cx = hair_x(z)
        rings.append([(cx + r * math.cos(a), r * math.sin(a) - .07, z) for a in angles] +
                     [(cx + .61 * r * math.cos(a), .61 * r * math.sin(a) - .07, z) for a in reversed(angles)])
    surface('Skin | Follicle (cut sheath)', rings, sheath, smooth=True)
    for i in range(95):
        z = 1.51 + 3.80 * i / 94
        taper = max(.04, min(1, (5.31 - z) / 1.83))
        radius = hair_radius(z) * .6 * min(1, math.sqrt(.006 + (z - 1.51) / .20)) * taper
        root.append([(hair_x(z) + radius * math.cos(j * TAU / 24), -.07 + radius * math.sin(j * TAU / 24), z) for j in range(24)])
    surface('Skin | Hair root and shaft', root, hair, smooth=True)

    # The coil is sectioned forward of the tissue to keep all turns visible.
    turns = 3.2
    p = []
    for i in range(145):
        t = i / 144
        a = TAU * turns * (t - 1)
        envelope = math.sin(math.pi * t)
        p.append(Vector((1.11 + .38 * math.cos(a) + .16 * envelope * math.sin(.62*a),
                         -.27 + .19 * math.sin(a) - .16 * envelope,
                         1.42 + .86 * t + .16 * envelope * math.sin(a + .45))))
    coil_end = len(p) - 1
    for i in range(1, 92):
        t = i / 91
        z = 2.28 + 1.82 * t
        p.append(Vector((duct_x(z), -.27 * max(0, 1 - 2.5 * t), z)))
    # Sweep a genuinely hollow lumen with an annular rim at the superficial end.
    sections = []
    for i, center in enumerate(p):
        tangent = (p[min(i + 1, len(p) - 1)] - p[max(0, i - 1)]).normalized()
        first = tangent.cross(Vector((0, 1, 0))).normalized()
        second = tangent.cross(first).normalized()
        radius = .085 + .06 * max(0, (center.z - 3.88) / .22)**2
        sections.append([[tuple(center + (first * math.cos(j * TAU / 20) + second * math.sin(j * TAU / 20)) * radius * fraction) for j in range(20)] for fraction in (1, .62)])
    for name, segment in [('Skin | Eccrine secretory coil', sections[:coil_end+1]), ('Skin | Sweat duct and open pore', sections[coil_end:])]:
        # Join the outer and inner surfaces at the end; their boundaries coincide at the anatomical join.
        if name.endswith('coil'):
            # A blind end on the secretory portion; an open annulus at the junction.
            rings = [segment[0][0]] + [pair[0] for pair in segment[1:]] + [pair[1] for pair in reversed(segment)]
            surface(name, rings, sweat, smooth=True)
        else:
            rings = [pair[0] for pair in segment] + [pair[1] for pair in reversed(segment)] + [segment[0][0]]
            surface(name, rings, sweat, cap=False, smooth=True)


def nail():
    skin_mat = bpy.data.materials['Epidermis • warm tan']
    bed = material('Nail bed • salmon', (.66, .30, .23))
    matrix = material('Nail matrix • mauve', (.43, .21, .30))
    plate = material('Keratin plate • ivory', (.79, .71, .53))
    # Extrude sagittal cut profiles toward the far lateral margin; slight crown to plate.
    def prism(name, profile, mat):
        rings = []
        for i in range(21):
            y = i / 20
            rings.append([(4.05 + x, 1.30 * y, .48 + z - .20 * y**2) for x, z in reversed(profile)])
        surface('Nail | ' + name, rings, mat)

    # Shared x/z knots keep dorsal tissues in contact. The ventral side rounds toward the fingertip.
    prism('Distal digit tissue', [(0, .35), (.18, .12), (.70, .04), (2.30, .0), (2.75, .10), (3.06, .32), (3.22, .62), (3.21, .87), (3.01, 1.07), (2.72, 1.09), (2.3, 1.08), (1.60, 1.04), (.96, .95), (.62, .86), (.3, .82), (0, .88)], skin_mat)
    prism('Germinal matrix', [(.30, .82), (.62, .86), (.96, .95), (1.26, .992), (1.26, 1.17), (.96, 1.145), (.62, 1.04), (.30, .92)], matrix)
    prism('Nail bed', [(1.26, .992), (1.60, 1.04), (2.3, 1.08), (2.72, 1.09), (2.83, 1.083), (2.83, 1.24), (2.30, 1.25), (1.60, 1.21), (1.26, 1.17)], bed)
    prism('Nail plate with free edge', [(.31, .924), (.62, 1.04), (.96, 1.145), (1.26, 1.17), (1.60, 1.21), (2.30, 1.25), (2.83, 1.24), (3.23, 1.21), (3.26, 1.34), (2.83, 1.40), (2.3, 1.40), (1.6, 1.36), (1.26, 1.32), (.96, 1.30), (.62, 1.18), (.31, 1.02)], plate)
    prism('Proximal nail fold', [(0, .88), (.30, .82), (.30, 1.02), (.62, 1.18), (.91, 1.283), (.78, 1.43), (.56, 1.48), (.23, 1.46), (0, 1.37)], skin_mat)


def main():
    out = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
    skin()
    nail()
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.clip_start = .00001
            space.region_3d.view_rotation = Vector((-1, 2, -1)).to_track_quat('-Z', 'Y')
            space.region_3d.view_distance = .023
            space.region_3d.view_location = (.002, .001, .002)
            space.shading.color_type = 'MATERIAL'
            space.overlay.show_floor = False
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'skin-block.blend'), compress=True)
    bpy.ops.export_scene.gltf(filepath=str(out / 'skin-block.glb'), export_format='GLB', export_yup=True)


if __name__ == '__main__':
    main()
