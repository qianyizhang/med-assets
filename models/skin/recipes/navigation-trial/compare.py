"""Check both GLBs after clean import and replay the pinned teaching cameras."""

import argparse
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils.bvhtree import BVHTree
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import CONTROL_TRIANGLES, REPO, mesh_data, oriented, protection, read_control
from tools.render_teaching import configure_scene, render_pair, sha256

sys.path.insert(0, str(REPO / "sites/body-systems-survey"))
from render_gallery import material

BUILD = "fab76e95306d"
WIDTH, HEIGHT, DETAIL_SCALE = 680, 560, 4
ORTHO_METRES = 2.3763959407806396
PLATES = {
    "ortho": {
        "webpSha256": "58d9d731c6e5ffe763ff9986d61c3e6feee4466b89f16ccc1f9ece298be4325b",
        "originalPngSha256": "ca3deb6a834578e3caa5a39a954aec5f01c0953c8d52732aa0260c23c459fc59",
        "camera": [-.0006469935178756714, -8.698123931884766, .781624436378479],
    },
    "iso": {
        "webpSha256": "bcdba8977509992a8d0e487c454016b8431e7f0d1ec07ba7320d2000e52ee268",
        "originalPngSha256": "546497ee949a2adbd32f30a10c0a239036b1065442718fe3200cf8eb24a71476",
        "camera": [4.963038921356201, -5.064453601837158, 5.745310306549072],
    },
}


def check_protection(control, candidate):
    original, positions, normals, faces = mesh_data(control)
    updated, new_positions, new_normals, new_faces = mesh_data(candidate)
    for key in ("scene", "scenes", "nodes", "meshes", "materials"):
        if original[key] != updated[key]:
            raise ValueError(f"GLB {key} changed")
    ids = {(tuple(point), tuple(normal)): index
           for index, (point, normal) in enumerate(zip(positions, normals, strict=True))}
    mapped = np.array([ids.get((tuple(point), tuple(normal)), -1)
                       for point, normal in zip(new_positions, new_normals, strict=True)])
    if len(ids) != len(positions) or len(np.unique(mapped)) != len(mapped) or (mapped < 0).any():
        raise ValueError("Each candidate vertex and normal must match a distinct control pair")
    restored_faces = mapped[new_faces]
    regions = {}
    for name, region in protection(positions, faces).items():
        before = oriented(faces[region[faces].any(axis=1)])
        after = oriented(restored_faces[region[restored_faces].any(axis=1)])
        if not len(before) or not np.array_equal(before, after):
            raise ValueError(f"Protected oriented faces changed in {name}")
        regions[name] = len(before)
    return regions


def clean_import(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), merge_vertices=False,
                              disable_bone_shape=True)
    obj, = bpy.context.scene.objects
    mesh = obj.data
    mesh.calc_loop_triangles()
    array = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", array)
    matrix = np.array(obj.matrix_world)
    positions = array.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    corners = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int32)
    mesh.loop_triangles.foreach_get("vertices", corners)
    faces = corners.reshape(-1, 3)

    topology = bmesh.new()
    topology.from_mesh(mesh)
    unseen = set(topology.verts)
    components = 0
    while unseen:
        components += 1
        pending = [unseen.pop()]
        while pending:
            for edge in pending.pop().link_edges:
                first, second = edge.verts
                for vertex in (first, second):
                    if vertex in unseen:
                        unseen.remove(vertex)
                        pending.append(vertex)
    stats = {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "name": obj.name,
        "matrix": matrix.tolist(),
        "boundsMetres": [positions.min(axis=0).tolist(), positions.max(axis=0).tolist()],
        "vertices": len(positions),
        "triangles": len(faces),
        "components": components,
        "euler": len(topology.verts) - len(topology.edges) + len(topology.faces),
        "boundaryEdges": sum(edge.is_boundary for edge in topology.edges),
        "nonManifoldEdgesExcludingBoundary": sum(
            not edge.is_manifold and not edge.is_boundary for edge in topology.edges),
        "inconsistentWindingEdges": sum(edge.is_manifold and not edge.is_contiguous
                                        for edge in topology.edges),
        "degenerateFaces": sum(face.calc_area() < 1e-13 for face in topology.faces),
    }
    topology.free()
    return obj, positions, faces, stats


def distance(positions, faces, target, target_faces):
    tree = BVHTree.FromPolygons(target.tolist(), target_faces.tolist(), all_triangles=True)
    result = {}
    for label, points in (("vertices", positions), ("faceCentres", positions[faces].mean(axis=1))):
        values = np.fromiter((tree.find_nearest(point)[3] for point in points),
                             dtype=float, count=len(points)) * 1000
        worst = int(values.argmax())
        result[label] = {
            "samples": len(points),
            "maxMm": float(values[worst]),
            "p95Mm": float(np.percentile(values, 95)),
            "worstPointMetres": points[worst].tolist(),
        }
    return result


def capture(obj, bounds, directory, phase):
    scene = bpy.context.scene
    configure_scene(scene)
    scene.view_settings.view_transform = "Standard"
    scene.cycles.samples = 14
    neutral = obj.material_slots[0].material
    captures = {}
    for mode, scale, surface in (
        ("display", 1, material({"label": "External skin surface", "color": "#2B7948", "alpha": 1})),
        ("neutral", DETAIL_SCALE, neutral),
    ):
        obj.material_slots[0].material = surface
        scene.render.resolution_x, scene.render.resolution_y = WIDTH * scale, HEIGHT * scale
        view = {"id": f"{phase}-{mode}", "front": (0, -1, 0), "cameraBounds": bounds}
        receipt = render_pair(scene, [obj], view, directory)
        if receipt["orthographicScale"] != ORTHO_METRES:
            raise ValueError("Camera scale differs from the teaching plates")
        for row in receipt["images"]:
            angle = Path(row["file"]).stem.rsplit("-", 1)[-1]
            if row["camera"] != PLATES[angle]["camera"]:
                raise ValueError(f"Camera position differs from the {angle} teaching plate")
            captures[f"{mode}-{angle}"] = row
    return captures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("input", "candidate", "output"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if bpy.app.build_hash.decode() != BUILD:
        raise ValueError(f"Expected Blender build {BUILD}")
    for angle, pin in PLATES.items():
        path = REPO / f"lessons/body-systems/display/skin-assembly-{angle}.webp"
        if sha256(path) != pin["webpSha256"]:
            raise ValueError(f"Teaching plate changed: {path.name}")
    control = read_control(args.input)
    protected = check_protection(control, args.candidate.read_bytes())
    args.output.mkdir()
    _, positions, faces, before = clean_import(args.input)
    _, updated, new_faces, after = clean_import(args.candidate)
    if not (before["triangles"] == CONTROL_TRIANGLES and after["triangles"] < CONTROL_TRIANGLES
            and after["bytes"] < before["bytes"]):
        raise ValueError("Unexpected clean-import triangle or byte counts")
    for key in ("name", "matrix", "boundsMetres", "components", "euler", "boundaryEdges",
                "nonManifoldEdgesExcludingBoundary", "inconsistentWindingEdges", "degenerateFaces"):
        if before[key] != after[key]:
            raise ValueError(f"Clean-import {key} changed")
    distances = {
        "originalToUpdated": distance(positions, faces, updated, new_faces),
        "updatedToOriginal": distance(updated, new_faces, positions, faces),
    }
    captures = {}
    for phase, path, item in (("original", args.input, before), ("updated", args.candidate, after)):
        obj, _, _, _ = clean_import(path)
        captures[phase] = {"glbSha256": item["sha256"],
                           "images": capture(obj, before["boundsMetres"], args.output, phase)}
    receipt = {
        "blenderBuild": BUILD,
        "orthographicWidthMetres": ORTHO_METRES,
        "displaySize": [WIDTH, HEIGHT],
        "neutralScale": DETAIL_SCALE,
        "plates": PLATES,
        "original": before,
        "updated": after,
        "protectedIncidentTriangles": protected,
        "distances": distances,
        "captures": captures,
    }
    (args.output / "comparison.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if max(row["maxMm"] for direction in distances.values() for row in direction.values()) > 2:
        raise SystemExit("Sampled surface deviation exceeds 2 mm. See comparison.json.")


if __name__ == "__main__":
    main()
