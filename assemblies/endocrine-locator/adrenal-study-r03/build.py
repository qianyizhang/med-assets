"""Build and verify the five-part s1233 adrenal teaching study from the r02 GLB."""

import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory

import bpy
from mathutils.bvhtree import BVHTree
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from render_teaching import configure_scene, render_pair, sha256
from teaching_scene import colorize, export, material

PIN = "84b8af5ad628ae328a2b32fb366c0e77fe84c33633df75fb01832a689659c32f"
NAME = "s1233-adrenals-teaching"
VOXEL_MM = 1.5
CAP_MM = 1.15
FRONT = (0, 1, 0)
PARTS = {
    "adrenal-gland-left": (1, 0.34, "Adrenals · warm amber", (0.88, 0.43, 0.078)),
    "adrenal-gland-right": (1, 0.34, "Adrenals · warm amber", (0.88, 0.43, 0.078)),
    "kidney-left": (1, 0.16, "Kidneys · slate", (0.14, 0.18, 0.22)),
    "kidney-right": (1, 0.16, "Kidneys · slate", (0.14, 0.18, 0.22)),
    "pancreas": (3, 0.19, "Pancreas · muted violet", (0.125, 0.095, 0.16)),
}


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), disable_bone_shape=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    objects = {obj.get("anatomy_id"): obj for obj in meshes}
    if set(objects) != set(PARTS) or len(meshes) != len(PARTS):
        raise ValueError("Unexpected s1233 selection IDs")
    return objects


def parts(obj):
    """Split precise world triangles into vertex-connected source shells."""
    obj.data.calc_loop_triangles()
    vertices = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
    faces = np.array([t.vertices[:] for t in obj.data.loop_triangles])
    # The GLB can encode coincident corners separately for vertex attributes.
    _, unique, remap = np.unique(vertices, axis=0, return_index=True, return_inverse=True)
    vertices, faces = vertices[unique], remap[faces]
    neighbors = defaultdict(set)
    for a, b, c in faces:
        neighbors[a].update((b, c))
        neighbors[b].update((a, c))
        neighbors[c].update((a, b))
    remaining = set(range(len(vertices)))
    groups = np.empty(len(vertices), dtype=int)
    component = 0
    while remaining:
        seed = remaining.pop()
        queue = [seed]
        groups[seed] = component
        for v in queue:
            fresh = remaining.intersection(neighbors[v])
            for index in fresh:
                groups[index] = component
            queue.extend(fresh)
            remaining.difference_update(fresh)
        component += 1
    shells = []
    for i in range(component):
        ids = np.flatnonzero(groups == i)
        face_ids = faces[groups[faces[:, 0]] == i]
        shells.append((vertices[ids], np.searchsorted(ids, face_ids)))
    return sorted(shells, key=lambda shell: (-len(shell[1]), *shell[0].mean(0)))


def smooth(shell):
    vertices, faces = shell
    edge = np.unique(np.sort(np.column_stack((faces.ravel(), np.roll(faces, -1, axis=1).ravel()))), axis=0)
    a, b = np.concatenate((edge, edge[:, ::-1])).T
    degree = np.bincount(a, minlength=len(vertices))[:, None]
    current = vertices.copy()
    for gain in [0.48] * 4 + [0.52, -0.50] * 12:
        sums = np.zeros_like(current)
        np.add.at(sums, a, current[b])
        proposed = current + gain * (sums / degree - current)
        displacement = proposed - vertices
        length = np.linalg.norm(displacement, axis=1, keepdims=True)
        current = vertices + displacement * (CAP_MM / np.maximum(length * 1000, CAP_MM))
    return current, faces


def decimate(shell, ratio):
    vertices, faces = smooth(shell)
    mesh = bpy.data.meshes.new("Temporary source shell")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new("Quadric surface reduction", "DECIMATE")
    modifier.ratio = ratio
    modifier.use_collapse_triangulate = True
    evaluated = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    evaluated.calc_loop_triangles()
    result = np.array([v.co for v in evaluated.vertices]), np.array([t.vertices[:] for t in evaluated.loop_triangles])
    bpy.data.meshes.remove(evaluated)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return result


def restore_gland_volume(base, reduced):
    """Recover smoothing loss while holding directional extremes fixed."""
    vertices, faces = reduced
    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    direction = np.zeros_like(vertices)
    np.add.at(direction, faces.ravel(), np.repeat(normals, 3, axis=0))
    direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-16)
    to_bounds = np.minimum(vertices - vertices.min(0), vertices.max(0) - vertices)
    margin_mm = 1000 * to_bounds.min(axis=1, keepdims=True)
    # Fade the correction at each bound. Cap any displacement at a quarter voxel.
    direction *= np.clip((margin_mm - 0.25) / 1.25, 0, 1)
    target_volume = abs(shell_stats(base)["signedVolumeMm3"])
    lower, upper = 0, VOXEL_MM / 4 / 1000
    for _ in range(14):
        offset = (lower + upper) / 2
        adjusted = vertices + offset * direction, faces
        if abs(shell_stats(adjusted)["signedVolumeMm3"]) < target_volume:
            lower = offset
        else:
            upper = offset
    # Preserve original triangle normals' orientation under the offset.
    triangles = adjusted[0][faces]
    final_normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    if np.any(np.einsum("ij,ij->i", normals, final_normals) <= 0):
        raise ValueError("Gland volume recovery flipped a triangle")
    if self_crossings(adjusted) - self_crossings(reduced):
        raise ValueError("Gland volume recovery introduced a nonadjacent triangle intersection")
    return adjusted, float(1000 * np.linalg.norm(adjusted[0] - vertices, axis=1).max())


def tree(shell):
    return BVHTree.FromPolygons(*shell, all_triangles=True)


def self_crossings(shell):
    bvh = tree(shell)
    _, faces = shell
    return {
        (a, b) for a, b in bvh.overlap(bvh)
        if a < b and not set(faces[a]).intersection(faces[b])
    }


def distances(shell, target):
    """Sample vertices and barycentric lattices with subtriangle edges at most 0.75 mm."""
    vertices, faces = shell
    triangles = vertices[faces]
    edges = np.linalg.norm(triangles - np.roll(triangles, -1, axis=1), axis=2)
    steps = np.maximum(1, np.ceil(1000 * edges.max(axis=1) / (VOXEL_MM / 2)).astype(int))
    distances_mm = [1000 * target.find_nearest(p)[3] for p in vertices]
    for n in np.unique(steps):
        group = triangles[steps == n]
        weights = np.array([
            (a / n, b / n, (n - a - b) / n)
            for a in range(n + 1)
            for b in range(n + 1 - a)
            if max(a, b, n - a - b) < n
        ]).reshape(-1, 3)
        interior = np.einsum("pi,tij->tpj", weights, group).reshape(-1, 3)
        distances_mm.extend(1000 * target.find_nearest(p)[3] for p in interior)
    return {"samples": len(distances_mm), "p95": np.percentile(distances_mm, 95), "max": max(distances_mm)}


def shell_stats(shell):
    vertices, faces = shell
    tri = vertices[faces]
    normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(normal, axis=1)
    if np.min(lengths) <= 1e-13:
        raise ValueError("Degenerate triangles")
    weights = lengths / lengths.sum()
    edges = np.column_stack((faces.ravel(), np.roll(faces, -1, axis=1).ravel()))
    edges, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(inverse)
    double = counts == 2
    first = np.cumsum(counts) - counts
    pair = np.column_stack((order[first[double]], order[first[double] + 1])) // 3
    dots = np.einsum("ij,ij->i", normal[pair[:, 0]], normal[pair[:, 1]]) / np.prod(lengths[pair], axis=1)
    angle = np.degrees(np.arccos(np.clip(dots, -1, 1)))
    edge_lengths = np.linalg.norm(vertices[edges[double, 0]] - vertices[edges[double, 1]], axis=1)
    return {
        "triangles": len(faces),
        "vertices": len(vertices),
        "euler": len(vertices) - len(edges) + len(faces),
        "boundaryEdges": int(np.count_nonzero(counts == 1)),
        "nonmanifoldEdges": int(np.count_nonzero(counts > 2)),
        "signedVolumeMm3": float(np.einsum("ij,ij->i", tri[:, 0], normal).sum() / 6 * 1e9),
        "areaCentroidMm": (1000 * (weights[:, None] * tri.mean(1)).sum(0)).tolist(),
        "boundsMm": (1000 * np.array([vertices.min(0), vertices.max(0)])).tolist(),
        "edgeLengthFractionAbove20Degrees": float(np.sum(edge_lengths[angle > 20]) / np.sum(edge_lengths)),
    }


def measure(base, updated, limit_mm):
    before, after = shell_stats(base), shell_stats(updated)
    directed = distances(base, tree(updated)), distances(updated, tree(base))
    bounds = np.abs(np.array(before["boundsMm"]) - after["boundsMm"]).max()
    center = np.linalg.norm(np.array(before["areaCentroidMm"]) - after["areaCentroidMm"])
    volume_delta = abs(after["signedVolumeMm3"] / before["signedVolumeMm3"] - 1)
    if any(before[k] != after[k] for k in ("euler", "boundaryEdges", "nonmanifoldEdges")):
        raise ValueError("Component topology changed")
    if (
        max(d["max"] for d in directed) > limit_mm
        or max(d["p95"] for d in directed) > VOXEL_MM / 2
        or bounds > VOXEL_MM
        or center > VOXEL_MM / 2
        or volume_delta > 0.13
    ):
        raise ValueError(f"Component outside fidelity limits: {directed}, bounds {bounds}, centroid {center}, volume {volume_delta}")
    return {"before": before, "after": after, "originalToUpdatedMm": directed[0], "updatedToOriginalMm": directed[1],
            "maxBoundsDeltaMm": bounds, "areaCentroidShiftMm": center, "relativeVolumeDifference": volume_delta}


def replace(obj, shells, appearance):
    mesh = bpy.data.meshes.new(obj.data.name + " teaching")
    vertices, faces = [], []
    for points, triangles in shells:
        faces.extend((triangles + len(vertices)).tolist())
        vertices.extend(points.tolist())
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj.data = mesh
    obj.parent = None
    obj.matrix_world.identity()
    for face in mesh.polygons:
        face.use_smooth = True
    colorize(obj, material(*appearance))


def crossing_pairs(groups):
    all_shells = [(f"{label}/{i + 1}", tree(shell)) for label, shells in groups.items() for i, shell in enumerate(shells)]
    return [
        [left, right]
        for (left, a), (right, b) in combinations(all_shells, 2)
        if a.overlap(b)
    ]


def primitives(path):
    with path.open("rb") as stream:
        magic, version, _, length, kind = struct.unpack("<4sIII4s", stream.read(20))
        if (magic, version, kind) != (b"glTF", 2, b"JSON"):
            raise ValueError(f"Unexpected GLB header in {path.name}")
        gltf = json.loads(stream.read(length))
    return {
        node["extras"]["anatomy_id"]: len(gltf["meshes"][node["mesh"]]["primitives"])
        for node in gltf["nodes"] if "mesh" in node
    }


def write_json(path, record):
    path.write_text(json.dumps(record, indent=2) + "\n")


def render(path, view, output, reference_bounds):
    objects = load(path)
    scene = bpy.context.scene
    configure_scene(scene)
    result = render_pair(scene, list(objects.values()), {"id": view, "front": FRONT, "cameraBounds": reference_bounds}, output)
    result["glb"] = {"file": path.name, "sha256": sha256(path)}
    return result


def assemble(source, output, render_images):
    objects = load(source)
    base = {label: parts(obj) for label, obj in objects.items()}
    identity = {label: (obj.name, dict(obj.items())) for label, obj in objects.items()}
    source_primitive_count = primitives(source)
    context = np.concatenate([points for group in base.values() for points, _ in group])
    bounds = [context.min(0).tolist(), context.max(0).tolist()]
    candidate, gland_offsets = {}, {}
    for label, (count, ratio, *appearance) in PARTS.items():
        shells = base[label]
        if len(shells) != count:
            raise ValueError(f"{label}: expected {count} source components, found {len(shells)}")
        principal = decimate(shells[0], ratio)
        if label.startswith("adrenal-gland-"):
            principal, gland_offsets[label] = restore_gland_volume(shells[0], principal)
        candidate[label] = [principal, *shells[1:]]
        replace(objects[label], candidate[label], appearance)

    export(output, NAME)
    path = output / f"{NAME}.glb"
    imported = load(path)
    portable = {label: parts(obj) for label, obj in imported.items()}
    portable_primitives = primitives(path)
    metrics = {}
    for label, shells in base.items():
        obj = imported[label]
        emitted = portable[label]
        if (obj.name, dict(obj.items())) != identity[label] or len(emitted) != len(shells):
            raise ValueError(f"Clean import changed selection identity or components for {label}")
        if portable_primitives[label] != source_primitive_count[label]:
            raise ValueError(f"Clean import changed primitive count for {label}")
        # Decimation can reorder secondary shells by triangle count. Match by position.
        centres = np.array([vertices.mean(0) for vertices, _ in emitted])
        indices = [
            int(np.argmin(np.linalg.norm(centres - vertices.mean(0), axis=1)))
            for vertices, _ in shells
        ]
        if len(set(indices)) != len(shells):
            raise ValueError(f"Ambiguous component pairing for {label}")
        portable[label] = [emitted[index] for index in indices]
        # Hold secondary source shells at GLB roundtrip precision.
        try:
            measurements = [
                measure(before, after, VOXEL_MM if index == 0 else 0.003)
                for index, (before, after) in enumerate(zip(shells, portable[label], strict=True))
            ]
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from exc
        if label in gland_offsets and measurements[0]["relativeVolumeDifference"] > 0.005:
            raise ValueError(f"Gland volume drift exceeded 0.5% for {label}")
        x = measurements[0]["after"]["areaCentroidMm"][0]
        if (label.endswith("-left") and x <= 0) or (label.endswith("-right") and x >= 0):
            raise ValueError(f"Laterality changed for {label}")
        metrics[label] = {
            "primitives": {"before": source_primitive_count[label], "after": portable_primitives[label]},
            "components": measurements,
        }
    crossings = crossing_pairs(base)
    if crossing_pairs(portable) != crossings:
        raise ValueError("Changed cross-component surface intersection pairs")
    receipt = output / "geometry.json"
    write_json(receipt, {
        "blender": bpy.app.version_string,
        "recipeSha256": sha256(Path(__file__)),
        "original": {"file": source.name, "sha256": PIN, "bytes": source.stat().st_size},
        "updated": {"file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size},
        "editable": {"file": f"{NAME}.blend", "sha256": sha256(output / f"{NAME}.blend")},
        "voxelSpacingMm": VOXEL_MM,
        "reference": "Same-case r02 clean import. Surface distance estimates sampled at vertices and subtriangle lattice points.",
        "coordinateFrame": "Blender metres, +X left, +Y posterior, +Z superior",
        "surfaceIntersectionPairs": crossings,
        "glandVolumeAdjustmentMaxMm": gland_offsets,
        "parts": metrics,
    })
    if render_images:
        renders = output / "renders"
        renders.mkdir()
        views = [render(glb, view, renders, bounds) for view, glb in (("original", source), ("updated", path))]
        before, after = views
        if before["orthographicScale"] != after["orthographicScale"] or any(
            (a["camera"], a["direction"]) != (b["camera"], b["direction"])
            for a, b in zip(before["images"], after["images"], strict=True)
        ):
            raise ValueError("The comparison used different camera parameters")
        write_json(renders / "renders.json", {
            "blender": bpy.app.version_string,
            "geometrySha256": sha256(receipt),
            "setup": "Clean imports in the same source bounds. Shared orthographic camera and CPU Cycles lighting.",
            "views": views,
        })


def build(source, output, render_images):
    if sha256(source) != PIN:
        raise ValueError("Restore the pinned r02 s1233-adrenals.glb")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{output.name}-", dir=output.parent) as scratch:
        candidate = Path(scratch) / "verified"
        candidate.mkdir()
        assemble(source, candidate, render_images)
        candidate.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    build(args.source, args.output, not args.geometry_only)
