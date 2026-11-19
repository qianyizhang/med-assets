"""Build a reference-informed longitudinal cutaway through an enlarged airway."""
import argparse
import json
from math import atan2, cos, hypot, pi, radians, sin
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from teaching_scene import export, material

# Author coordinates in display millimetres. They occupy the old inset's display
# neighbourhood, with a transverse widening to show a continuous cut section.
X = (105.8, 110.8, 115.8, 122.7, 129.0, 137.2, 145.3)
ANGLES = tuple(map(radians, (-119, -41, 30, 103)))
DEPTHS = (
    (0, 0, 0),
    (0, 0, 0),
    (0, 3.3, 2.3),
    (5.6, 4.6, 5.3),
    (6.6, 6.9, 4.4),
    (5.6, 5.0, 6.9),
)
NAMES = (
    "Terminal bronchiole", "Respiratory bronchiole", "Alveolar duct",
    "Distal common space and alveoli",
)
BASE = (2.30, 2.39, 2.67, 3.13, 3.62, 4.15, 3.70)
MID = (122.7, 0, 133.6)
HALF_EDGE_SAMPLES = 3
WALL = .78
PATCH_STEPS = (
    (1.00, 0.00), (.91, .02), (.83, .13), (.76, .51),
    (.69, .68), (.49, .87), (.23, .97),
)


def mix(a, b, t):
    return a + (b - a) * t


def tube_point(x, angle, radius, offset):
    """Irregular common duct wall, with a gently rising proximal inlet."""
    t = (x - X[0]) / (X[-1] - X[0])
    y = 3.0 * (1 - t) ** 2 + .38 * sin(t * 6)
    z = 124.0 + 10.4 * sin(t * pi / 2) + .95 * sin(4.8 * t)
    # A bounded warp is shared by every tile along each of its borders.
    x += sin(t * pi) * (1.67 * sin(angle * 2.9 + t * 7) + .58 * cos(angle * 5.1))
    angle += .105 * sin(x * .62 + angle * 2.1) + .067 * cos(angle * 3 - t * 8) + .11 * sin(t * 7)
    radius += .18 * sin(angle * 3 + t * 7) + .11 * cos(t * 13 - angle)
    r = radius + offset
    return (x * .001, (y + r * cos(angle)) * .001, (z + r * sin(angle)) * .001)


def perimeter():
    """Counterclockwise on (axial x, angular around duct) rectangle."""
    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for start, end in zip(corners, corners[1:] + corners[:1]):
        for i in range(2 * HALF_EDGE_SAMPLES):
            t = i / (2 * HALF_EDGE_SAMPLES)
            yield mix(start[0], end[0], t), mix(start[1], end[1], t)


class Surface:
    def __init__(self):
        self.points = []
        self.faces = []
        self.regions = []
        self.index = {}

    def vertex(self, point):
        key = tuple(round(v, 9) for v in point)
        if key not in self.index:
            self.index[key] = len(self.points)
            self.points.append(point)
        return self.index[key]

    def ring(self, points):
        return [self.vertex(p) for p in points]

    def face(self, indices, region):
        self.faces.append(tuple(indices))
        self.regions.append(region)

    def bridge(self, a, b, region, reverse=False):
        for i in range(len(a)):
            j = (i + 1) % len(a)
            face = (a[i], a[j], b[j], b[i])
            self.face(face[::-1] if reverse else face, region)

    def object(self, name, materials):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.points, [], self.faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        for mat in materials:
            mesh.materials.append(mat)
        for face, region in zip(mesh.polygons, self.regions, strict=True):
            face.use_smooth = region != 2
            face.material_index = region
        obj["schematic"] = "Enlarged air-side cutaway. Dimensions are illustrative."
        return obj


def cell(surface, row, col, depth):
    x0, x1 = X[row:row + 2]
    a0, a1 = ANGLES[col:col + 2]
    phase = 1.1 + row * 2.7 + col * 3.7
    shift_u, shift_v = .13 * sin(phase), .1 * cos(phase)
    border = list(perimeter())

    def position(u, v, offset, jacket=0):
        t = (u + 1) / 2
        x = mix(x0, x1, t)
        # Fill the tissue valleys between adjacent exterior lobules. It tapers
        # to the distal dome, with equal values on every shared tile seam.
        progress = (x - X[0]) / (X[-1] - X[0])
        fill = 1.8 * abs(sin(pi * progress)) ** .6 * min(1, max(0, (x - 115.8) / 5))
        angle = mix(a0, a1, (v + 1) / 2)
        margin = min(angle - ANGLES[0], ANGLES[-1] - angle)
        rim_taper = .28 + .72 * min(1, margin / .42)
        return tube_point(x, angle, mix(BASE[row], BASE[row + 1], t),
                          offset + fill * jacket * rim_taper)

    rings = []
    for outer in (False, True):
        depth_scale = .91 if outer else 1.0
        def offset(relief):
            return WALL + depth * depth_scale * relief if outer else depth * relief

        steps = PATCH_STEPS if depth else PATCH_STEPS[:1] + ((.54, 0),)
        previous = None
        for radius, relief in steps:
            points = []
            for u, v in border:
                angle = atan2(v, u)
                roundness = (1 - radius) ** .65
                distort = .06 * sin(angle * 3 + phase) + .035 * cos(angle * 2 - phase)
                rounding = mix(1, (1 + distort) / hypot(u, v), roundness)
                points.append(position(
                    radius * u * rounding + shift_u * (1 - radius),
                    radius * v * rounding + shift_v * (1 - radius),
                    offset(relief), (1 - relief) ** 1.6 if outer else 0,
                ))
            ring = surface.ring(points)
            if previous is None:
                rings.append(ring)
            else:
                surface.bridge(previous, ring, int(outer), reverse=outer)
            previous = ring
        tip = surface.vertex(position(shift_u, shift_v, offset(1)))
        for i in range(len(ring)):
            face = (ring[i], ring[(i + 1) % len(ring)], tip)
            surface.face(face[::-1] if outer else face, int(outer))

    # Join the two laminae only on the cut perimeter. Border samples on
    # adjoining cells and selectable parts use the same world coordinates.
    inner, outer = rings
    sides = 2 * HALF_EDGE_SAMPLES
    exposed = (col == 0, False, col == len(ANGLES) - 2, row == 0)
    for side, close in enumerate(exposed):
        if close:
            for i in range(side * sides, (side + 1) * sides):
                j = (i + 1) % len(inner)
                surface.face((inner[j], inner[i], outer[i], outer[j]), 2)
    return position(shift_u, shift_v, depth)


def distal_back(surface):
    """A recessed end wall in the section, with shared rim nodes."""
    angles = [
        mix(a, b, i / (2 * HALF_EDGE_SAMPLES))
        for a, b in zip(ANGLES, ANGLES[1:])
        for i in range(2 * HALF_EDGE_SAMPLES)
    ] + [ANGLES[-1]]
    end = X[-1] * .001
    # A center point independent of the angular perturbation in tube_point.
    center_y = .38 * sin(6) * .001
    center_z = (134.4 + .95 * sin(4.8)) * .001
    skin = []
    for outer in (False, True):
        rim = [tube_point(X[-1], a, BASE[-1], WALL if outer else 0) for a in angles]
        length = (2.3 + (WALL if outer else 0)) * .001
        rings = []
        for level in range(5):
            t = pi * .5 * level / 5
            rings.append(surface.ring([
                (end + length * sin(t), mix(center_y, y, cos(t)), mix(center_z, z, cos(t)))
                for _, y, z in rim
            ]))
        tip = surface.vertex((end + length, center_y, center_z))
        for a, b in zip(rings, rings[1:]):
            for i in range(len(angles) - 1):
                face = (a[i], a[i + 1], b[i + 1], b[i])
                surface.face(face if outer else face[::-1], int(outer))
        for i in range(len(angles) - 1):
            face = (rings[-1][i], rings[-1][i + 1], tip)
            surface.face(face if outer else face[::-1], int(outer))
        skin.append(([r[0] for r in rings] + [tip], [r[-1] for r in rings] + [tip]))
    for side, (inside, outside) in enumerate(zip(*skin, strict=True)):
        for i in range(len(inside) - 1):
            face = (inside[i], inside[i + 1], outside[i + 1], outside[i])
            surface.face(face[::-1] if side == 0 else face, 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args(sys.argv[sys.argv.index("--") + 1:]).output
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    airway = material("Bronchiole lumen | warm ivory", (.49, .30, .22))
    airway_outer = material("Bronchiole wall | warm ivory", (.57, .38, .28))
    mucosa = material("Alveolar lining | muted terracotta", (.53, .19, .157))
    septa = material("Alveolar septa | dusty rose", (.48, .145, .138))
    cut = material("Section edge | pale peach", (.74, .47, .38))
    groups = (0, 0, 1, 2, 2, 3)
    surfaces = [Surface() for _ in NAMES]
    targets = []
    for row, depths in enumerate(DEPTHS):
        for col, depth in enumerate(depths):
            p = cell(surfaces[groups[row]], row, col, depth)
            if depth:
                targets.append({"row": row, "col": col, "depthDisplayMillimetres": depth, "floor": p})
    distal_back(surfaces[-1])
    for i, (name, surface) in enumerate(zip(NAMES, surfaces, strict=True)):
        palette = (airway, airway_outer, cut) if i == 0 else (mucosa, septa, cut)
        obj = surface.object(name, palette)
        obj["studyPart"] = name
    bpy.context.scene.unit_settings.system = "METRIC"
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            view = area.spaces.active
            view.region_3d.view_rotation = Vector((-.4, 1, -.24)).to_track_quat("-Z", "Y")
            view.region_3d.view_distance = .062
            view.region_3d.view_location = Vector(MID) * .001
            view.shading.color_type = "MATERIAL"
    export(output, "terminal-airspaces")
    (output / "airspace-targets.json").write_text(json.dumps(targets, indent=2) + "\n")


if __name__ == "__main__":
    main()
