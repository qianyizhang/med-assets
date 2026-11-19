"""Build the magnified schematic lymph-node section in an independent frame."""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from teaching_scene import ellipsoid, export, material, tube

NAME = "lymph-node-section"
SAMPLES = 112
MM = 0.001


def outline(theta, radius=1.0, depth=0.0):
    """Reniform section boundary in millimetres, with hilum at the right."""
    c = math.cos(theta)
    x = 31 * c - 16 * math.exp(9 * (c - 1))
    z = 39 * math.sin(theta) * (1 - 0.08 * c)
    return ((x + 6) * radius - 6, depth, z * radius)


def metres(point):
    return tuple(value * MM for value in point)


def mesh(name, points, faces, mat, role, *, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata([metres(point) for point in points], [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    for face in data.polygons:
        face.use_smooth = smooth
    tag(obj, role)
    return obj


def tag(obj, role):
    obj["anatomy_id"] = obj.name.lower().replace(" ", "_")
    obj["view_role"] = role
    obj["derivation"] = "Authored schematic lymph-node teaching section"
    return obj


def rings(profile):
    points = [outline(math.tau * i / SAMPLES, radius, depth)
              for radius, depth in profile for i in range(SAMPLES)]
    faces = []
    for j in range(len(profile) - 1):
        for i in range(SAMPLES):
            a, b = i, (i + 1) % SAMPLES
            k = j * SAMPLES
            faces.append((k + a, k + SAMPLES + a, k + SAMPLES + b, k + b))
    return points, faces


def capsule(mat):
    profile = [(0.88, -0.7), (0.90, -1.5), (0.94, -1.7), (0.98, -1.1), (1, 0)]
    profile += [(math.cos(i * math.pi / 24), 14 * math.sin(i * math.pi / 24))
                for i in range(1, 12)]
    points, faces = rings(profile)
    end = len(points)
    points.append((-6, 14, 0))
    faces.extend((end - SAMPLES + i, end, end - SAMPLES + (i + 1) % SAMPLES)
                 for i in range(SAMPLES))
    return mesh("Nodal capsule", points, faces, mat, "outer capsule and cut rim", smooth=True)


def section(mat):
    points, faces = rings([(0.82, -0.8), (0.87, -0.35), (0.89, 0)])
    center = len(points)
    points.append((-6, -0.8, 0))
    faces.extend((center, i, (i + 1) % SAMPLES) for i in range(SAMPLES))
    return mesh("Lymphoid section face", points, faces, mat, "illustrative cut face")


def flow_arrow(mat):
    """Direction cue on the section plane, stylistically distinct from vessels."""
    samples = 32
    shafts = []
    for i in range(samples + 1):
        t = i / samples
        x = -27 + 37 * t
        z = 4 * math.sin(math.tau * t * 0.8) + 1.5 * (1 - t)
        shafts.extend([(x, -3.2, z - 1.20), (x, -3.2, z + 1.20)])
    faces = [(i * 2, (i + 1) * 2, (i + 1) * 2 + 1, i * 2 + 1)
             for i in range(samples)]
    x, y, z = shafts[-1]
    center_z = z - 1.2
    # Share the shaft end with the head to avoid overlapping coplanar faces.
    head = len(shafts)
    shafts += [(x, y, center_z - 3.8), (18, y, center_z + 1.6),
               (x, y, center_z + 3.8)]
    faces.extend(((head - 2, head, head + 1),
                  (head - 2, head + 1, head - 1),
                  (head - 1, head + 1, head + 2)))
    return mesh("Intranodal transit arrow", shafts, faces, mat, "schematic flow cue")


def vessel(name, points, radius, mat, role):
    return tag(tube(name, [metres(p) for p in points], radius * MM, mat), role)


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tissue = material("Lymphoid tissue • mauve", (0.43, 0.22, 0.34))
    shell = material("Fibrous capsule • plum", (0.22, 0.073, 0.15))
    cortex = material("Cortical follicles • rose", (0.52, 0.30, 0.43))
    band = material("Subcapsular sinus cue • rose", (0.63, 0.38, 0.47))
    inlet = material("Afferent lymphatics • teal", (0.075, 0.39, 0.36))
    outlet = material("Efferent lymphatic • ochre", (0.71, 0.39, 0.095))
    flow = material("Transit illustration • ivory", (0.94, 0.80, 0.64))

    capsule(shell)
    section(tissue)
    points, faces = rings([(0.81, -0.95), (0.87, -0.93), (0.90, -0.70)])
    mesh("Subcapsular sinus band", points, faces, band, "illustrative subcapsular cue", smooth=True)
    for index, (x, z, rx, rz) in enumerate([
        (-14, 25, 6, 6), (0, 26, 7, 6), (13, 21, 5, 6),
        (-22, 14, 5, 6), (-19, -16, 6, 6), (-10, -25, 6, 6),
        (4, -24, 7, 6), (15, -17, 5, 5),
    ], 1):
        patch = ellipsoid(f"Cortical follicle cue {index}", metres((x, -0.48, z)),
                          metres((rx, 1.15, rz)), cortex)
        tag(patch, "representative cortical follicle")
    for number, (degrees, outside) in enumerate(
        [(128, (-46, 3, 42)), (180, (-57, 3, 3)), (232, (-45, 3, -45))], 1
    ):
        theta = math.radians(degrees)
        x, _, z = outline(theta)
        entry = outline(theta, 0.92, 0.7)
        vessel(f"Afferent lymphatic {number}", [outside, (x - 8, 2, z), (x, 1, z), entry],
               2.6, inlet, "afferent lymphatic entry")
    vessel("Efferent lymphatic at hilum", [(12, 1, -1), (23, 1, -1), (37, 2, 1), (54, 3, 6)],
           3.2, outlet, "efferent lymphatic exit")
    flow_arrow(flow)

    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                view = area.spaces.active.region_3d
                view.view_distance = 0.19
                view.view_rotation = Quaternion((1, 0, 0), math.pi / 2)
                view.view_perspective = "ORTHO"
                area.spaces.active.shading.color_type = "MATERIAL"
    bpy.context.scene.unit_settings.system = "METRIC"
    export(output, NAME)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args(sys.argv[sys.argv.index("--") + 1:]).output)
