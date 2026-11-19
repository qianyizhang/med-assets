"""Build and check the gastroduodenal teaching section in Blender metres."""

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "r01" / "build.py"
BASELINE_SHA256 = "a09e3f7f4b6d17a8114666e75265d35e1158123f0ef4b2daae06c4dc1cfc27b9"
STEPS = 64
ANGLE_START = math.radians(160)
ANGLE_ARC = math.radians(220)

MATERIALS = {
    "Gastric exterior": ("#da9153", 0.64),
    "Gastric mucosa": ("#ba645f", 0.62),
    "Section face": ("#eed0aa", 0.79),
    "Pyloric rim": ("#ae524a", 0.65),
    "Papillary rim": ("#df9b88", 0.65),
    "Duodenal exterior": ("#509e99", 0.67),
    "Duodenal mucosa": ("#d98779", 0.61),
    "Common bile duct": ("#dcad39", 0.63),
    "Main pancreatic duct": ("#487db4", 0.63),
    "Common channel": ("#a47cab", 0.63),
}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def baseline_recipe():
    if sha256(BASELINE) != BASELINE_SHA256:
        raise ValueError("r01 route recipe differs from the pinned teaching frame")
    spec = importlib.util.spec_from_file_location("digestive_route_r01", BASELINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def colors(name):
    color, roughness = MATERIALS[name]
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        mat.diffuse_color = (*((c + 0.055) ** 2.4 / 1.055 ** 2.4 for c in rgb), 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = mat.diffuse_color
        shader.inputs["Roughness"].default_value = roughness
    return mat


def mesh(group, name, anatomy_id, role, points, faces, material, *, smooth=True):
    used = sorted({vertex for face in faces for vertex in face})
    lookup = {vertex: index for index, vertex in enumerate(used)}
    data = bpy.data.meshes.new(name)
    data.from_pydata(
        [points[i] / 1000 for i in used], [], [tuple(lookup[i] for i in f) for f in faces]
    )
    if data.validate():
        raise ValueError(f"Invalid generated mesh {name}")
    data.update()
    data.materials.append(colors(material))
    for polygon in data.polygons:
        polygon.use_smooth = smooth
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    obj["anatomy_id"] = anatomy_id
    obj["view_role"] = role
    obj["derivation"] = "Authored teaching section in the r01 schematic frame"
    return obj


def angle(index):
    return ANGLE_START + ANGLE_ARC * index / STEPS


def side_radii(stations):
    # A sweep folds over when its inside radius exceeds the bend radius.
    # Limit the inside of each bend and ease into the narrow region.
    limits = []
    lengths = [0.0]
    for index, here in enumerate(stations):
        before = stations[max(0, index - 1)].to_3d()
        after = stations[min(len(stations) - 1, index + 1)].to_3d()
        incoming = here.to_3d() - before
        outgoing = after - here.to_3d()
        if index:
            lengths.append(lengths[-1] + incoming.length)
        turn = math.atan2(-incoming.cross(outgoing).y, incoming.dot(outgoing))
        bend = (incoming.length + outgoing.length) / (2 * max(abs(turn), 1e-6))
        inside = max(3.6, 0.83 * bend)
        limits.append((min(here.w, inside) if turn > 0 else here.w,
                       min(here.w, inside) if turn < 0 else here.w))
    capped = [
        tuple(min(limit[side] + 0.25 * abs(position - lengths[j]) for j, limit in enumerate(limits))
              for side in range(2))
        for position in lengths
    ]
    softened = []
    for index, station in enumerate(stations):
        adjacent = capped[max(0, index - 3):index + 4]
        softened.append(tuple(
            min(station.w, sum(sides[side] for sides in adjacent) / len(adjacent))
            for side in range(2)
        ))
    return softened


def profile(samples, radii, row, azimuth, pylorus, inner):
    station = min(int(row), len(samples) - 2)
    mix = row - station
    a = samples[station]
    b = samples[station + 1]
    control = a.lerp(b, mix)
    here = control.to_3d()
    prev = samples[max(0, station - 1)]
    following = samples[min(len(samples) - 1, station + 2)]
    tangent = (b - prev).lerp(following - a, mix).to_3d().normalized()
    horizontal = tangent.cross(Vector((0, 1, 0))).normalized()
    anterior = tangent.cross(horizontal)
    radius = control.w
    cosine = math.cos(azimuth)
    blend = 0.5 + 0.5 * math.tanh(3 * cosine)
    sides = [radii[station][i] * (1 - mix) + radii[station + 1][i] * mix for i in (0, 1)]
    width = blend * sides[0] + (1 - blend) * sides[1]
    if inner:
        # Soft relief reads at close-up scale without representing histological layers.
        gastric = max(0, min(1, (radius - 8) / 7))
        phase = azimuth + 0.26 * math.sin(row * 0.13 + azimuth * 1.8)
        folds = 0.90 * (0.5 + 0.5 * math.cos(10 * phase)) ** 2
        circular = 0.40 * (0.5 + 0.5 * math.cos(row * 1.52)) ** 2
        relief = folds * gastric if row < pylorus else circular * max(0, min(1, (row - pylorus - 12) / 12))
        constriction = 1.35 * math.exp(-((row - pylorus) / 3.4) ** 2)
        inset = 1.35 + relief + constriction
        radius -= inset
        width -= inset
    return here + width * cosine * horizontal + radius * math.sin(azimuth) * anterior * 0.84


def build_section(group, stations, pylorus, papilla_row):
    # The retained 220-degree arc exposes the lumen from the anterior side.
    # Round a quad patch on the posteromedial descending wall into a sectioned ostium.
    papilla_col = 49
    span_row = 3
    span_col = 4
    rows = len(stations)
    width = STEPS + 1
    layer_size = rows * width
    points = []
    boundary = {}
    radii = side_radii(stations)
    for inner in (False, True):
        for row in range(rows):
            for col in range(width):
                dr, dc = row - papilla_row, col - papilla_col
                sample_row, sample_col = row, col
                normalized = max(abs(dr) / span_row, abs(dc) / span_col)
                if normalized == 1:
                    scale = math.hypot(dr / span_row, dc / span_col)
                    sample_row = papilla_row + dr / scale
                    sample_col = papilla_col + dc / scale
                    boundary[row * width + col] = math.atan2(dr / span_row, dc / span_col)
                points.append(profile(stations, radii, sample_row, angle(sample_col), pylorus, inner))

    regular = {"stomach": [], "duodenum": []}
    lining = {"stomach": [], "pyloric": [], "duodenum": []}
    edges = Counter()
    for row in range(rows - 1):
        for col in range(STEPS):
            if (
                papilla_row - span_row <= row < papilla_row + span_row
                and papilla_col - span_col <= col < papilla_col + span_col
            ):
                continue
            a = row * width + col
            face = (a, a + 1, a + 1 + width, a + width)
            organ = "stomach" if row < pylorus else "duodenum"
            regular[organ].append(face)
            lining["pyloric" if abs(row + 0.5 - pylorus) < 3 else organ].append(
                tuple(vertex + layer_size for vertex in reversed(face))
            )
            for u, v in zip(face, (*face[1:], face[0])):
                edges[tuple(sorted((u, v)))] += 1 if u < v else -1
    cut_faces = {"stomach": [], "duodenum": []}
    ostium_edges = []
    for (a, b), wind in edges.items():
        if not wind:
            continue
        u, v = (a, b) if wind > 0 else (b, a)
        if a in boundary and b in boundary:
            ostium_edges.append((u, v))
        else:
            organ = "stomach" if min(a, b) // width < pylorus else "duodenum"
            cut_faces[organ].append((v, u, u + layer_size, v + layer_size))

    # A papillary lip narrows inside the lumen, with one actual opening and a
    # through-wall sleeve. The ring stays welded geometrically to the section.
    inner = profile(stations, radii, papilla_row, angle(papilla_col), pylorus, True)
    outer = profile(stations, radii, papilla_row, angle(papilla_col), pylorus, False)
    radial = (outer - inner).normalized()
    papilla_points = {}
    for vertex in boundary:
        lip = inner.lerp(points[vertex + layer_size], 0.43) - radial * 0.8
        papilla_points[vertex] = len(points)
        points.append(lip)
    papilla_faces = []
    for u, v in ostium_edges:
        p, q = papilla_points[u], papilla_points[v]
        papilla_faces.append((v, u, p, q))
        papilla_faces.append((q, p, u + layer_size, v + layer_size))

    for organ, label, exterior, interior in (
        ("stomach", "Stomach", "Gastric exterior", "Gastric mucosa"),
        ("duodenum", "Duodenum", "Duodenal exterior", "Duodenal mucosa"),
    ):
        mesh(group, label + " wall", organ + "-wall", "section-wall", points, regular[organ], exterior)
        mesh(group, label + " mucosa", organ + "-mucosa", "lining", points, lining[organ], interior)
        mesh(group, label + " cut faces", organ + "-cut-faces", "cut-face", points, cut_faces[organ],
             "Section face", smooth=False)
    mesh(group, "Pyloric opening rim", "pyloric-opening", "lumen-rim", points, lining["pyloric"], "Pyloric rim")
    mesh(group, "Major duodenal papilla", "major-duodenal-papilla", "lumen-rim", points, papilla_faces, "Papillary rim")
    return inner - radial * 0.8, outer, radial, [points[index] for index in boundary]


def duct(group, name, anatomy_id, controls, recipe):
    samples = recipe.smooth([Vector((*point, radius)) for point, radius in controls])
    sides = 24
    points = []
    faces = []
    for row, control in enumerate(samples):
        prev = samples[max(0, row - 1)].to_3d()
        following = samples[min(len(samples) - 1, row + 1)].to_3d()
        tangent = (following - prev).normalized()
        u = tangent.cross(Vector((0, 0, 1))).normalized()
        v = tangent.cross(u)
        for col in range(sides):
            theta = math.tau * col / sides
            points.append(control.to_3d() + control.w * (math.cos(theta) * u + math.sin(theta) * v))
            if row:
                p = (row - 1) * sides
                following_col = (col + 1) % sides
                faces.append((p + col, p + following_col, p + sides + following_col, p + sides + col))
    return mesh(group, name, anatomy_id, "duct-route", points, faces, name)


def selected_shapes():
    shapes = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        world = obj.matrix_world
        obj.data.calc_loop_triangles()
        positions = {
            tuple(round(value, 6) for value in world @ vertex.co) for vertex in obj.data.vertices
        }
        shapes[obj.name] = (
            obj.get("anatomy_id"),
            obj.get("view_role"),
            len(obj.data.loop_triangles),
            tuple(sorted(mat.name for mat in obj.data.materials)),
            positions,
        )
    return shapes


def examine_section():
    # Rejoin only coincident material-seam positions from the clean import.
    # A connected shell with one hole through the wall has Euler number zero.
    vertices = []
    keys = {}
    faces = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.get("view_role") == "duct-route":
            continue
        local_indices = {}
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            key = tuple(round(value, 7) for value in world)
            if key not in keys:
                keys[key] = len(vertices)
                vertices.append(world)
            local_indices[vertex.index] = keys[key]
        obj.data.calc_loop_triangles()
        faces.extend(tuple(local_indices[i] for i in tri.vertices) for tri in obj.data.loop_triangles)

    edges = Counter()
    directions = Counter()
    linked = defaultdict(set)
    for face in faces:
        for a, b in zip(face, (*face[1:], face[0])):
            key = tuple(sorted((a, b)))
            edges[key] += 1
            directions[key] += 1 if a < b else -1
            linked[a].add(b)
            linked[b].add(a)
    remaining = set(range(len(vertices)))
    pending = [remaining.pop()]
    while pending:
        for neighbor in linked[pending.pop()] & remaining:
            remaining.remove(neighbor)
            pending.append(neighbor)
    euler = len(vertices) - len(edges) + len(faces)
    if remaining or euler or any(count != 2 for count in edges.values()) or any(directions.values()):
        raise ValueError("Clean-import section lost its joined wall, cut faces or papillary aperture")
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=True)
    crossings = sum(a < b and not (set(faces[a]) & set(faces[b])) for a, b in tree.overlap(tree))
    if crossings:
        raise ValueError(f"Clean-import section has {crossings} intersecting non-neighbour triangle pairs")
    return {"vertices": len(vertices), "edges": len(edges), "triangles": len(faces),
            "euler": euler, "connectedComponents": 1, "nonNeighbourTriangleIntersections": crossings}


def build(output):
    recipe = baseline_recipe()
    esophagus, old_stomach, duodenum = (points for _, points in recipe.FOOD[2:5])
    # Relax the body silhouette between the pinned cardia and pyloric axis.
    stomach = [(18, 132, 13), (36, 130, 21), (51, 112, 23), (45, 91, 20), (26, 82, 12), old_stomach[-1]]
    controls = [*esophagus[-2:], *stomach, *duodenum]
    stations = recipe.smooth([Vector((x + 1000 * recipe.ROUTE_X, 0, z, r)) for x, z, r in controls])
    # Begin below the longer esophageal plate, while retaining its connection pose.
    start = 6
    stations = stations[start:]
    pylorus = (1 + len(stomach)) * 8 - start
    papilla_row = pylorus + 3 * 8
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    group = bpy.data.collections.new("Gastroduodenal section")
    bpy.context.scene.collection.children.link(group)
    opening, approach, radial, rim = build_section(group, stations, pylorus, papilla_row)
    confluence = approach + 8 * radial
    joint = confluence - Vector((0, 0, 0.3))
    duct(group, "Common bile duct", "common-bile-duct",
         [(joint + Vector((2, 16, 38)), 1.7), (joint + Vector((13, 10, 25)), 1.6),
          (joint + Vector((11, 3, 8)), 1.5), (joint + Vector((0, 0, 0.8)), 1.45)], recipe)
    duct(group, "Main pancreatic duct", "main-pancreatic-duct",
         [(joint + Vector((43, 6, -8)), 1.55), (joint + Vector((26, 8, -7)), 1.5),
          (joint + Vector((8, 2, -3)), 1.35), (joint - Vector((0, 0, 0.8)), 1.3)], recipe)
    duct(group, "Common channel", "hepatopancreatic-common-channel",
         [(confluence + 0.8 * radial, 2.35), (confluence, 2.35),
          (approach + 2.2 * radial, 1.65), (approach - 0.2 * radial, 1.50)], recipe)

    bpy.context.view_layer.update()
    source = selected_shapes()
    scene = output / "gastroduodenal-section.blend"
    model = output / "gastroduodenal-section.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(scene), compress=True)
    bpy.ops.export_scene.gltf(filepath=str(model), export_extras=True,
                              export_animations=False, export_texcoords=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    exported = selected_shapes()
    if exported != source:
        differences = sorted(name for name in source.keys() | exported.keys()
                             if source.get(name) != exported.get(name))
        raise ValueError(f"Clean import changed part identity, geometry or material: {differences}")
    receipt = {
        "blender": bpy.app.version_string,
        "recipeSha256": sha256(Path(__file__)),
        "r01FrameRecipeSha256": BASELINE_SHA256,
        "schematicFrame": "+X patient left, -Y anterior, +Z superior in Blender metres",
        "glb": {"file": model.name, "sha256": sha256(model), "bytes": model.stat().st_size},
        "blend": {"file": scene.name, "sha256": sha256(scene), "bytes": scene.stat().st_size},
        "parts": {name: {"anatomyId": item[0], "role": item[1], "triangles": item[2], "materials": item[3]}
                  for name, item in sorted(exported.items())},
        "pyloricAxisMm": list(stations[pylorus].to_3d()),
        "pyloricMinimumRadiusMm": stations[pylorus].w - 2.70,
        "papillaApertureCentreMm": list(opening),
        "papillaExternalRimVertices": len(rim),
        "confluenceCentreMm": list(confluence),
        "sourceBackedContinuity": False,
        "closedSection": examine_section(),
    }
    (output / "geometry.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args(sys.argv[sys.argv.index("--") + 1 :]).output.resolve())
