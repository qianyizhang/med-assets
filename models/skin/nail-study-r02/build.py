"""Build a longitudinal half-section in the r01 local frame. Design dimensions are mm."""

import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector


MM = 0.001
X_ORIGIN = 4.05
Z_ORIGIN = 0.48
MATRIX_START = 0.24
MATRIX_END = 1.03
BED_END = 2.76
DIGIT_END = 3.19
PLATE_END = 3.34
ACROSS = 8
LONGITUDINAL = (
    (0, MATRIX_START, 3),
    (MATRIX_START, 0.68, 5),
    (0.68, MATRIX_END, 4),
    (MATRIX_END, BED_END, 11),
    (BED_END, DIGIT_END, 8),
    (DIGIT_END, PLATE_END, 3),
)


def smoothstep(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)


def field(s, profile):
    for (start, first), (end, last) in zip(profile, profile[1:]):
        if s <= end:
            return first + (last - first) * smoothstep((s - start) / (end - start))
    return profile[-1][1]


def point(s, u, z):
    width = 0.89 + 0.12 * math.sin(math.pi * s / 3.5)
    sweep = 0.10 * math.sin(math.pi * s / PLATE_END) - 0.46 * smoothstep((s - 1.85) / 1.49)
    return ((X_ORIGIN + s + sweep * u**2) * MM, width * u * MM, (Z_ORIGIN + z) * MM)


def plate_bottom(s, u):
    return 1.02 + 0.34 * (1 - math.exp(-1.7 * max(0, s - 0.12))) - 0.20 * (s / 3.34)**3 - 0.34 * u**2


def plate_top(s, u):
    thickness = 0.16 - 0.16 * math.exp(-5.7 * max(0, s - MATRIX_START))
    thickness += 0.014 * smoothstep((s - 2.74) / 0.30)
    return plate_bottom(s, u) + thickness * (1 - 0.30 * u**4)


def matrix_base(s, u):
    depth = field(s, [(0, 0), (0.24, 0), (0.51, 0.29), (1.03, 0.15)])
    return plate_bottom(s, u) - depth


def bed_base(s, u):
    depth = field(s, [(1.03, 0.15), (1.45, 0.185), (2.34, 0.15), (2.76, 0.09)])
    return plate_bottom(s, u) - depth


def digit_top(s, u):
    v = min(u, 1)
    if s <= MATRIX_END:
        top = matrix_base(s, v)
    elif s <= BED_END:
        top = bed_base(s, v)
    else:
        distal = (s - BED_END) / (DIGIT_END - BED_END)
        top = plate_bottom(s, v) - 0.09 - 0.55 * distal**1.75
    if u > 1:
        side = (u - 1) / 0.40
        fade = smoothstep((BED_END - s) / 0.42)
        outer_top = plate_top(s, 1) - 0.37 * side**2
        top += (outer_top - top) * fade * smoothstep(side / 0.55) - 0.13 * side**2
    return top


def digit_bottom(s, u):
    tip = max(0, (s - 2.06) / (DIGIT_END - 2.06))
    base = -0.10 + 0.067 * (s - 2.06)**2 + 0.53 * tip**4
    top = digit_top(s, u)
    base = min(base, top - 0.05)
    return base + (top - base) * smoothstep(u / 1.4)**3


def fold_bottom(s, u):
    if u > 1:
        weight = smoothstep((u - 1) / 0.40)
        blended = plate_top(s, 1) * (1 - weight) + digit_top(s, 1.40) * weight
        return max(blended, digit_top(s, u))
    return plate_top(s, u)


def fold_top(s, u):
    end = 0.68
    outer_profile = plate_top(end, 0) + 0.29 * (1 - s / end)**1.35
    thickness = max(0, outer_profile - plate_top(s, 0))
    return fold_bottom(s, u) + thickness * max(0, 1 - (u / 1.4)**3)


def stations(start, end):
    result = []
    for a, b, count in LONGITUDINAL:
        if a >= start and b <= end:
            result.extend(a + (b - a) * i / count for i in range(count))
    return [*result, end]


def material(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat


def shell(name, start, end, across, lower, upper, materials):
    along = stations(start, end)
    vertices = [
        point(s, u, height(s, u))
        for height in (lower, upper)
        for s in along
        for u in across
    ]
    width = len(across)
    layer = len(along) * width
    faces = []
    face_styles = []

    def face(indices, s, smooth):
        faces.append(indices)
        face_styles.append((int(len(materials) == 2 and s >= BED_END), smooth))

    for i, s in enumerate(along[:-1]):
        left = i * width
        right = left + width
        for j in range(width - 1):
            a, b = left + j, right + j
            face((a, a + 1, b + 1, b), s, True)
            face((a + layer, b + layer, b + 1 + layer, a + 1 + layer), s, True)
        face((left, right, right + layer, left + layer), s, False)
        a, b = right - 1, right + width - 1
        face((a, a + layer, b + layer, b), s, False)
    for j in range(width - 1):
        face((j, j + layer, j + 1 + layer, j + 1), start, False)
        a = layer - width + j
        face((a, a + 1, a + 1 + layer, a + layer), end, False)

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for mat in materials:
        mesh.materials.append(mat)
    for polygon, (slot, smooth) in zip(mesh.polygons, face_styles, strict=True):
        polygon.material_index = slot
        polygon.use_smooth = smooth
    # The buried root begins at zero thickness. Weld the shared ring to avoid degenerate faces.
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00000001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if any(not edge.is_manifold for edge in bm.edges):
        raise ValueError(f"Open shell: {name}")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)


def main():
    output = Path(sys.argv[sys.argv.index("--") + 1])
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"

    skin = material("Digit tissue · warm tan", (0.53, 0.31, 0.21), 0.69)
    fold = material("Proximal fold · warm brown", (0.34, 0.17, 0.115), 0.63)
    matrix = material("Germinal matrix · dark plum", (0.23, 0.082, 0.151), 0.66)
    bed = material("Nail bed · rose", (0.46, 0.155, 0.125), 0.65)
    plate = material("Nail plate · warm rose ivory", (0.62, 0.43, 0.34), 0.41)
    free_edge = material("Free edge · ivory", (0.83, 0.74, 0.59), 0.43)
    across = [i / ACROSS for i in range(ACROSS + 1)]
    outer = [*across, 1.08, 1.16, 1.24, 1.32, 1.40]
    shell("Nail | Distal digit tissue", 0, DIGIT_END, outer, digit_bottom, digit_top, [skin])
    shell("Nail | Germinal matrix", MATRIX_START, MATRIX_END, across, matrix_base, plate_bottom, [matrix])
    shell("Nail | Nail bed", MATRIX_END, BED_END, across, bed_base, plate_bottom, [bed])
    shell("Nail | Nail plate with free edge", MATRIX_START, PLATE_END, across, plate_bottom, plate_top, [plate, free_edge])
    shell("Nail | Proximal nail fold", 0, 0.68, outer, fold_bottom, fold_top, [fold])
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.clip_start = 0.00001
            space.region_3d.view_rotation = Vector((-1, 1, -1)).to_track_quat("-Z", "Y")
            space.region_3d.view_distance = 0.008
            space.region_3d.view_location = (0.0057, 0.0006, 0.0012)
            space.shading.color_type = "MATERIAL"
            space.overlay.show_floor = False
    bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve() / "nail.blend"), compress=True)
    bpy.ops.export_scene.gltf(filepath=str(output.resolve() / "nail.glb"), export_format="GLB", export_yup=True)


if __name__ == "__main__":
    main()
