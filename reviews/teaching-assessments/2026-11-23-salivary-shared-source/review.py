"""Verify the three parotid/salivary exports by clean Blender imports."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import file_digest
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[3]
RECIPE = ROOT / "models/salivary_glands/recipes/native-region"
sys.path.insert(0, str(RECIPE))
from build import CONTEXT, PAROTID_PAIR, PRIMARY, REJECTED, build
from verify_crossing import crossing

EXTERIOR = "models/parotid_glands/exports/"
SALIVARY = "models/salivary_glands/exports/"
EXPORTS = {
    "parotid-pair": (
        EXTERIOR + "source-candidate-02/parotid_glands_source_frame.glb",
        EXTERIOR + "source-shared-r01/parotid-pair.glb",
        PAROTID_PAIR,
    ),
    "glands-ducts": (
        SALIVARY + "z-native-scoped-r02/glands-and-parotid-ducts.glb",
        SALIVARY + "z-native-shared-r01/glands-and-parotid-ducts.glb",
        PRIMARY,
    ),
    "context": (
        SALIVARY + "z-native-scoped-r02/same-source-context.glb",
        SALIVARY + "z-native-shared-r01/same-source-context.glb",
        PRIMARY + CONTEXT,
    ),
}
POSITION_LIMIT = 0.000002  # 0.002 mm in the source's metre-like frame


@dataclass
class Surface:
    positions: list
    normals: dict
    triangles: list
    material: list
    determinant: float


def identity(path):
    with path.open("rb") as stream:
        return {"sha256": file_digest(stream, "sha256").hexdigest(), "bytes": path.stat().st_size}


def open_clean(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    meshes = {}
    for obj in bpy.context.scene.objects:
        assert obj.type == "MESH", (path, obj.name, obj.type)
        assert len(obj.data.materials) == 1 and not obj.animation_data, obj.name
        source_id = obj.get("source_object") or obj["source_file_id"].replace("_", " ")
        assert source_id not in meshes, source_id
        mesh = obj.data
        matrix = obj.matrix_world
        positions = [matrix @ vert.co for vert in mesh.vertices]
        assert all(math.isfinite(value) for point in positions for value in point), source_id
        normal_transform = matrix.to_3x3().inverted().transposed()
        normals = defaultdict(set)
        for loop, normal in zip(mesh.loops, mesh.corner_normals, strict=True):
            vector = (normal_transform @ normal.vector).normalized()
            assert vector.length > 0.99, source_id
            normals[loop.vertex_index].add(tuple(vector))
        mesh.calc_loop_triangles()
        determinant = matrix.determinant()
        triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
        # A negative-determinant node reverses the effective front face in glTF.
        if determinant < 0:
            triangles = [triangle[::-1] for triangle in triangles]
        material = mesh.materials[0]
        shader = material.node_tree.nodes.get("Principled BSDF")
        appearance = [
            list(shader.inputs["Base Color"].default_value),
            shader.inputs["Roughness"].default_value,
            shader.inputs["Metallic"].default_value,
            material.use_backface_culling,
        ]
        meshes[source_id] = Surface(positions, normals, triangles, appearance, determinant)
    return meshes


def cyclic(triangle):
    return min(triangle, triangle[1:] + triangle[:1], triangle[2:] + triangle[:2])


def triangle_summary(rows):
    unoriented = Counter()
    for face, count in rows.items():
        unoriented[tuple(sorted(face))] += count
    return {
        "triangles": sum(rows.values()),
        "duplicate_unoriented": sum(count - 1 for count in unoriented.values()),
        "collapsed": sum(count for face, count in rows.items() if len(set(face)) < 3),
    }


def edges(faces):
    adjacent = defaultdict(list)
    for a, b, c in faces:
        for start, end, other in ((a, b, c), (b, c, a), (c, a, b)):
            adjacent[tuple(sorted((start, end)))].append(other)
    return adjacent


def count_diagonal_swaps(before, after):
    baseline = edges(before)
    updated = edges(after)
    old_quads = Counter(
        tuple(sorted(edge + tuple(others))) for edge, others in baseline.items()
        if edge not in updated and len(others) == 2
    )
    new_quads = Counter(
        tuple(sorted(edge + tuple(others))) for edge, others in updated.items()
        if edge not in baseline and len(others) == 2
    )
    return (old_quads & new_quads).total()


def sampled_surface_error(positions, before, after):
    points = list(map(Vector, positions))
    distances = []
    for start, end in ((before, after), (after, before)):
        tree = BVHTree.FromPolygons(points, list(end), all_triangles=True)
        for face in start:
            a, b, c = (points[index] for index in face)
            for sample in ((a + b + c) / 3, (a + b) / 2, (b + c) / 2, (c + a) / 2):
                distances.append(tree.find_nearest(sample)[3])
    return max(distances) * 1000


def compare(base, updated, offset=Vector((0, 0, 0))):
    ids = {point: i for i, point in enumerate(dict.fromkeys(tuple(v) for v in base.positions))}
    base_ids = [ids[tuple(point)] for point in base.positions]
    tree = KDTree(len(ids))
    for point, index in ids.items():
        tree.insert(point, index)
    tree.balance()
    nearest = [tree.find(point - offset) for point in updated.positions]
    new_ids = [index for _, index, _ in nearest]
    assert set(new_ids) == set(base_ids), "Geometric vertex coverage differs"
    max_error = max(distance for _, _, distance in nearest)
    assert max_error <= POSITION_LIMIT, f"World position error: {max_error} m"

    def faces(surface, vertex_ids):
        return Counter(cyclic(tuple(vertex_ids[i] for i in face)) for face in surface.triangles)

    def normals_by_position(surface, vertex_ids):
        normals = defaultdict(set)
        for index, values in surface.normals.items():
            normals[vertex_ids[index]].update(values)
        return {key: [Vector(value) for value in values] for key, values in normals.items()}

    base_normals = normals_by_position(base, base_ids)
    new_normals = normals_by_position(updated, new_ids)
    angle = max(
        min(math.degrees(math.atan2(a.cross(b).length, a.dot(b))) for b in right[index])
        for left, right in ((base_normals, new_normals), (new_normals, base_normals))
        for index, values in left.items()
        for a in values
    )
    before = faces(base, base_ids)
    after = faces(updated, new_ids)
    removed = before - after
    added = after - before
    flipped = sum((Counter({cyclic(face[::-1]): count for face, count in removed.items()}) & added).values())
    result = {
        "position_error_mm": max_error * 1000,
        "vertices": [len(base.positions), len(updated.positions)],
        "world_normal_angle_deg": angle,
        "triangle_summary": [triangle_summary(before), triangle_summary(after)],
        "oriented_triangles_removed": removed.total(),
        "oriented_triangles_added": added.total(),
        "exactly_reversed": flipped,
        "matrix_determinants": [base.determinant, updated.determinant],
        "material_match": base.material == updated.material,
    }
    if removed or added:
        result["quad_diagonal_swaps"] = count_diagonal_swaps(before, after)
        result["sampled_surface_error_mm"] = sampled_surface_error(ids, before, after)
    return result


def verify_change(result, *, diagonal_swaps=0, same_material=True):
    assert result["exactly_reversed"] == 0, result
    assert result["oriented_triangles_removed"] == result["oriented_triangles_added"] == diagonal_swaps * 2, result
    assert result.get("quad_diagonal_swaps", 0) == diagonal_swaps, result
    assert result.get("sampled_surface_error_mm", 0) < 0.5, result
    assert result["material_match"] is same_material, result
    assert result["world_normal_angle_deg"] < 0.1, result
    assert all(not t["duplicate_unoriented"] and not t["collapsed"] for t in result["triangle_summary"]), result


def source_edit(objects):
    target = objects["Parotid gland.r"]
    target.data = target.data.copy()
    for vertex in target.data.vertices:
        vertex.co.x += 0.001
    target.data.update()


def run(source, fresh, output):
    output.mkdir(parents=True, exist_ok=False)
    build(source, output / "disposable-edit", edit=source_edit)
    receipt = {
        "blender": bpy.app.version_string, "source": identity(source),
        "rejected_source_crossing": crossing(source), "exports": {},
    }
    for name, (old_path, new_path, expected) in EXPORTS.items():
        old = ROOT / old_path
        new = ROOT / new_path
        assert identity(new) == identity(fresh / new.name), name
        baseline = open_clean(old)
        accepted = open_clean(new)
        edited = open_clean(output / "disposable-edit" / new.name)
        assert set(baseline) == set(accepted) == set(edited) == set(expected), name
        assert set(REJECTED).isdisjoint(accepted), name
        assert accepted["Parotid gland.r"].determinant > 0 > accepted["Parotid gland.l"].determinant
        for part in set(accepted) & {"Parotid gland.r", "Parotid gland.l", "Parotid duct.r", "Parotid duct.l"}:
            sign = -1 if part.endswith(".r") else 1
            assert min(sign * point.x for point in accepted[part].positions) > 0, part
        components = {}
        for component in expected:
            offset = Vector((0.001, 0, 0)) if component == "Parotid gland.r" else Vector((0, 0, 0))
            updated = compare(baseline[component], accepted[component])
            diagonal_swaps = 852 if name == "parotid-pair" and component == "Parotid gland.l" else 0
            verify_change(updated, diagonal_swaps=diagonal_swaps)
            disposable = compare(accepted[component], edited[component], offset)
            verify_change(disposable)
            components[component] = {"original_to_updated": updated, "disposable_source_edit": disposable}
        receipt["exports"][name] = {
            "original": {"path": old_path, **identity(old)},
            "updated": {"path": new_path, **identity(new)},
            "geometry": components,
        }
    primary = open_clean(ROOT / EXPORTS["glands-ducts"][1])
    jaw = open_clean(ROOT / EXPORTS["context"][1])
    exterior = open_clean(ROOT / EXPORTS["parotid-pair"][1])
    receipt["shared_parts"] = {
        "primary_in_context": {name: compare(primary[name], jaw[name]) for name in PRIMARY},
        "outer_envelopes_in_primary": {name: compare(exterior[name], primary[name]) for name in PAROTID_PAIR},
    }
    for same_material, comparisons in (
        (True, receipt["shared_parts"]["primary_in_context"]),
        (False, receipt["shared_parts"]["outer_envelopes_in_primary"]),
    ):
        for match in comparisons.values():
            verify_change(match, same_material=same_material)
            assert match["position_error_mm"] == 0, match
    receipt["source_edit"] = "Translate right parotid source mesh vertices 1 mm along native +X before evaluating source modifiers. The left gland's original data is protected by a separate disposable data copy."
    (output / "geometry.json").write_text(json.dumps(receipt, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("source", "build", "out"):
        parser.add_argument("--" + argument, type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args.source, args.build, args.out)


if __name__ == "__main__":
    main()
