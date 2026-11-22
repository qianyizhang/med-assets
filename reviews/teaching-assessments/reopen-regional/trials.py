"""Build and photograph three task-specific interpretations with headless Blender."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMERAS = HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine/render.py"
MODELS = {
    "lymph": (
        "models/lymph-collecting-routes/source-context-r01/selected-source-routes.glb",
        "ff8c1e9cecc86b4287520d97e71e81792d26eb0b3017e6f302e213f64819b4ca",
        "route-diagram.glb",
    ),
    "adrenals": (
        "models/adrenals/exports/source-candidate-01/adrenals_source_frame.glb",
        "c7de1afa5394a7f64b106a62ff979eaa9e0b428db23a13fa34340c2d38ba13a7",
        "atlas-profiles.glb",
    ),
    "pancreas": (
        "models/pancreas/exports/hra-female-context-r04/pancreas_hra_female_context_r04.glb",
        "aa15f9248027c248886a9cf8d4f5f401b2753176c800851f648b03d88d97ebed",
        "gross-locator.glb",
    ),
}


def load(file):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(file), merge_vertices=False)
    bpy.context.view_layer.update()
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def points(obj):
    return np.array([list(obj.matrix_world @ v.co) for v in obj.data.vertices])


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    pbr = mat.node_tree.nodes.get("Principled BSDF")
    pbr.inputs["Base Color"].default_value = (*color, 1)
    pbr.inputs["Roughness"].default_value = 0.77
    return mat


def curve_mesh(name, stations, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 4
    curve.bevel_resolution = 0
    curve.bevel_depth = radius
    curve.use_fill_caps = True
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(stations) - 1)
    for i, p in enumerate(spline.bezier_points):
        p.co = stations[i]
        p.handle_left_type = p.handle_right_type = "FREE"
        left = stations[i] - stations[max(0, i - 1)]
        right = stations[min(i + 1, len(stations) - 1)] - stations[i]
        # Short symmetric handles round the interior corners without overshooting the end.
        tangent = left.normalized() + right.normalized()
        tangent.normalize()
        reach = (
            0.18 * min(left.length, right.length)
            if left.length and right.length
            else max(left.length, right.length) / 3
        )
        p.handle_left = p.co - tangent * reach
        p.handle_right = p.co + tangent * reach
    curve.materials.append(mat)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.select_set(False)
    return obj


def route_diagram(meshes):
    bpy.ops.object.select_all(action="DESELECT")
    colors = [
        material("Selected route", (0.08, 0.50, 0.39)),
        material("Other source traces", (0.21, 0.24, 0.26)),
        material("Sampled end position", (0.94, 0.51, 0.12)),
    ]
    stats = {}
    for original in list(meshes):
        coords = points(original)
        stations = [
            Vector(row.mean(axis=0))
            for row in np.split(coords[np.argsort(coords[:, 2])], len(coords) // 8)
        ]
        central = original.name.startswith("Thoracic")
        name = "Central collecting trace" if central else original.name
        obj = curve_mesh(
            name + " (diagram)",
            stations,
            0.0030 if central else 0.00105,
            colors[0 if central else 1],
        )
        obj["sourceName"] = original.name
        obj["representation"] = "Interpolated source stations; graphic line width"
        stats[name] = {
            "stations": [list(p) for p in stations],
            "radiusM": 0.0030 if central else 0.00105,
        }
        if central:
            for label, loc in zip(
                ("Lower source limit", "Upper source limit"),
                (stations[0], stations[-1]),
            ):
                bpy.ops.mesh.primitive_ico_sphere_add(
                    subdivisions=1, radius=0.0065, location=loc
                )
                marker = bpy.context.object
                marker.name = label + " (symbol)"
                marker.data.materials.append(colors[2])
                marker.select_set(False)
        bpy.data.objects.remove(original, do_unlink=True)
    return stats


def relax(obj, iterations, bound):
    # Weld for neighborhood calculations only. Seam and split vertices retain their original indexing.
    xyz = points(obj)
    unique, back = np.unique(xyz.round(8), axis=0, return_inverse=True)
    edge = np.array([list(e.vertices) for e in obj.data.edges])
    pairs = np.unique(np.sort(back[edge], axis=1), axis=0)
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    a, b = np.concatenate([pairs, pairs[:, ::-1]]).T
    weights = np.bincount(a, minlength=len(unique))
    cur = unique.copy()
    # Refit the smoothed profile to the original XYZ spans to avoid isolated pinned spikes.
    for _ in range(iterations):
        means = np.zeros_like(cur)
        np.add.at(means, a, cur[b])
        next_pos = cur + 0.48 * (means / np.maximum(weights[:, None], 1) - cur)
        delta = next_pos - unique
        delta *= np.minimum(
            1, bound / np.maximum(np.linalg.norm(delta, axis=1), 1e-10)
        )[:, None]
        cur = unique + delta
    cur = (cur - cur.min(axis=0)) * (
        np.ptp(unique, axis=0) / np.ptp(cur, axis=0)
    ) + unique.min(axis=0)
    inv = obj.matrix_world.inverted()
    for v, new in zip(obj.data.vertices, cur[back]):
        v.co = inv @ Vector(new)
    mesh = obj.data
    # Clear imported split normals, allowing the new surface to determine its smooth lighting.
    if mesh.has_custom_normals:
        mesh.normals_split_custom_set([(0, 0, 0)] * len(mesh.loops))
    for face in mesh.polygons:
        face.use_smooth = True
    mesh.update()
    offset = 1000 * np.linalg.norm(cur - unique, axis=1)
    return {
        "vertices": len(xyz),
        "matchedBoundsAxes": 3,
        "displacementMmP50P95Max": np.percentile(offset, [50, 95, 100]).tolist(),
    }


def gross_pancreas(meshes, lookup):
    gross = [
        o
        for o in meshes
        if lookup[o.name] in ("head", "body", "neck", "tail", "ucinate")
    ]
    refs = {o.name: points(o) for o in gross}
    reference_trees = []
    for obj in gross:
        reference_trees.append(
            BVHTree.FromPolygons(
                refs[obj.name].tolist(), [list(p.vertices) for p in obj.data.polygons]
            )
        )

    # Join copies in the source world frame before voxel reconstruction.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in gross:
        obj.select_set(True)
        obj.data.transform(obj.matrix_world)
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.objects.active = gross[0]
    bpy.ops.object.join()
    exterior = bpy.context.object
    exterior.name = "Pancreatic gross envelope (interpreted)"
    exterior.data.remesh_voxel_size = 0.00125
    exterior.data.use_remesh_preserve_volume = False
    bpy.ops.object.voxel_remesh()
    smooth = exterior.modifiers.new("Soften voxel steps", "SMOOTH")
    smooth.factor = 0.75
    smooth.iterations = 32
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    dec = exterior.modifiers.new("Gross display", "DECIMATE")
    dec.ratio = 0.065
    bpy.ops.object.modifier_apply(modifier=dec.name)
    subdiv = exterior.modifiers.new("Continuous gross contour", "SUBSURF")
    subdiv.levels = 2
    bpy.ops.object.modifier_apply(modifier=subdiv.name)
    final = exterior.modifiers.new(
        "Retain gross curvature at the reviewed zoom", "DECIMATE"
    )
    final.ratio = 0.20
    bpy.ops.object.modifier_apply(modifier=final.name)
    exterior.data.materials.clear()
    exterior.data.materials.append(
        material("Interpreted gross pancreas", (0.59, 0.41, 0.20))
    )
    for poly in exterior.data.polygons:
        poly.use_smooth = True
    xyz = points(exterior)
    tri = [list(f.vertices) for f in exterior.data.polygons]
    tree = BVHTree.FromPolygons(xyz.tolist(), tri)
    stats = {
        name: {
            "toEnvelopeMmP50P95Max": np.percentile(
                [tree.find_nearest(v)[3] * 1000 for v in cloud], [50, 95, 100]
            ).tolist()
        }
        for name, cloud in refs.items()
    }
    reverse_mm = [
        1000 * min(t.find_nearest(v)[3] for t in reference_trees) for v in xyz
    ]
    stats["envelopeToSourceMmP50P95Max"] = np.percentile(
        reverse_mm, [50, 95, 100]
    ).tolist()
    return stats


def kidney_context(archive):
    pin = json.loads(
        (
            ROOT / "sources/datasets/bp3d-4.0-glands/external-source-members.json"
        ).read_text()
    )
    if (
        not archive
        or hashlib.sha256(archive.read_bytes()).hexdigest() != pin["archive"]["sha256"]
    ):
        raise ValueError("Supply the pinned BP3D archive with --bp3d")
    color = material("Kidney context", (0.36, 0.43, 0.46))
    added = []
    with zipfile.ZipFile(archive) as atlas:
        for source_id, side in (("FJ3145", "left"), ("FJ3147", "right")):
            entry = next(v for v in pin["members"] if v["id"] == source_id)
            raw = atlas.read(entry["archive_member"])
            if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise ValueError("Kidney member differs")
            lines = raw.decode().splitlines()
            xyz = [
                tuple(float(x) * 0.001 for x in l.split()[1:4])
                for l in lines
                if l.startswith("v ")
            ]
            faces = [
                tuple(int(x.split("/")[0]) - 1 for x in l.split()[1:])
                for l in lines
                if l.startswith("f ")
            ]
            name = f"{source_id} {side} kidney (context)"
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(xyz, [], faces)
            mesh.update()
            for poly in mesh.polygons:
                poly.use_smooth = True
            obj = bpy.data.objects.new(name, mesh)
            bpy.context.collection.objects.link(obj)
            mesh.materials.append(color)
            added.append(obj)
    bpy.context.view_layer.update()
    return added


def regional_surface(key, meshes, archive):
    if key == "adrenals":
        result = {o.name: relax(o, 9, 0.0009) for o in meshes}
        kidney_context(archive)
        return result
    roles = json.loads(
        (
            ROOT
            / "models/pancreas/provenance/hra-female-context-r04/explicit-region-key.json"
        ).read_text()
    )
    lookup = {
        r["source_mesh_name"]: r["illustrative_display_role"] for r in roles["rows"]
    }
    for o in meshes:
        if lookup[o.name] == "duct":
            bpy.data.objects.remove(o, do_unlink=True)
    return gross_pancreas(
        [o for o in bpy.context.scene.objects if o.type == "MESH"], lookup
    )


def export(file):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(file),
        use_selection=True,
        export_format="GLB",
        export_extras=True,
        export_animations=False,
        export_cameras=False,
        export_lights=False,
    )


def selections(key, meshes):
    if key == "lymph":
        center = [
            m
            for m in meshes
            if m.name.startswith(
                ("Thoracic", "Central collecting", "Upper source", "Lower source")
            )
        ]
        return [
            (meshes, meshes, (0, -1, 0), True),
            (center, meshes, (0, -1, 0), True),
            (center, meshes, (0.55, -1, 0.24), True),
        ]
    if key == "adrenals":
        glands = [m for m in meshes if "adrenal" in m.name]
        return [
            (glands, glands, (0.22, 1, 0.16), True),
            (glands, glands, (-0.45, -1, 0.28), False),
            ([m for m in glands if "left" in m.name], glands, (-0.45, -1, 0.28), False),
            (meshes, meshes, (0, 1, 0), True),
        ]
    gross = [
        m
        for m in meshes
        if "duct" not in m.name
        and "ampulla" not in m.name
        or "duodenal_ampulla" in m.name
    ]
    head = [
        m
        for m in meshes
        if m.name
        in ("VH_F_head_of_pancreas", "Pancreatic gross envelope (interpreted)")
    ]
    regions = [
        m
        for m in meshes
        if any(
            k in m.name for k in ("of_pancreas", "ucinate", "Pancreatic gross envelope")
        )
    ]
    return [
        (meshes, gross, (0.23, -1, 0.12), True),
        (meshes, gross, (-0.59, 1, 0.33), False),
        (head, regions, (0.23, -1, 0.12), False),
    ]


def capture(key, file, side, out, cameras, presets, archive):
    meshes = load(file)
    if key == "adrenals" and side == "before":
        meshes.extend(kidney_context(archive))
    sc = bpy.context.scene
    camera = cameras["configure"](sc)
    for m in meshes:
        for mat in m.data.materials:
            if mat and mat.use_nodes:
                shader = next(
                    (n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"),
                    None,
                )
                if shader:
                    mat.diffuse_color = shader.inputs["Base Color"].default_value
    results = []
    for i, (framed, shown, direction, palette) in enumerate(selections(key, meshes)):
        if side == "before":
            cameras["frame_camera"](camera, framed, direction)
            presets.append(
                (
                    camera.location.copy(),
                    camera.rotation_quaternion.copy(),
                    camera.data.ortho_scale,
                    camera.data.clip_start,
                    camera.data.clip_end,
                )
            )
        camera.rotation_mode = "QUATERNION"
        (
            camera.location,
            camera.rotation_quaternion,
            camera.data.ortho_scale,
            camera.data.clip_start,
            camera.data.clip_end,
        ) = presets[i]
        results.append(
            cameras["shot"](
                sc,
                camera,
                meshes,
                direction,
                out / f"{key}-{side}-{i}.png",
                palette,
                visible=shown,
                fixed=True,
            )
        )
    return results


def main():
    args = sys.argv[sys.argv.index("--") + 1 :]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("models", choices=MODELS, nargs="+")
    parser.add_argument("--bp3d", type=Path)
    opts = parser.parse_args(args)
    output = opts.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cameras = runpy.run_path(str(CAMERAS))
    receipt = {}
    for key in opts.models:
        source, digest, name = MODELS[key]
        src = ROOT / source
        if hashlib.sha256(src.read_bytes()).hexdigest() != digest:
            raise ValueError("Changed baseline: " + source)
        meshes = load(src)
        measures = (
            route_diagram(meshes)
            if key == "lymph"
            else regional_surface(key, meshes, opts.bp3d)
        )
        result = output / name
        export(result)
        # Keep the teaching interpretation and credit with the separately downloadable GLB.
        sys.path.insert(0, str(ROOT / "tools"))
        from glb import decode, encode
        doc, blob = decode(result.read_bytes())
        label, provenance = {
            "lymph": ("Interpolated schematic lines and endpoint symbols. No lumen or terminal connection.",
                      "Commissioned Network Systems Draft. See source-identity.json in the source package."),
            "adrenals": ("Interpreted gross gland profiles; native same-atlas kidneys. No fine morphology claim.",
                         "BodyParts3D, copyright Database Center for Life Science. CC BY 4.0."),
            "pancreas": ("Interpreted gross pancreatic envelope and retained source context. Region interiors omitted.",
                         "Kristen Browne and Heidi Schlehlein, HRA Female v1.10. CC BY 4.0."),
        }[key]
        doc["asset"]["extras"] = {"interpretation": label, "sourcePath": source,
                                  "sourceSha256": digest, "credit": provenance}
        result.write_bytes(encode(doc, blob))
        presets = []
        before = capture(key, src, "before", output, cameras, presets, opts.bp3d)
        after = capture(key, result, "after", output, cameras, presets, opts.bp3d)
        imported = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        parts = {}
        for o in imported:
            o.data.calc_loop_triangles()
            xyz = points(o)
            edge_counts = {}
            neighbors = [set() for _ in xyz]
            for tri in o.data.loop_triangles:
                vertices = tuple(tri.vertices)
                for a, b in zip(vertices, vertices[1:] + vertices[:1]):
                    k = tuple(sorted((a, b)))
                    edge_counts[k] = edge_counts.get(k, 0) + 1
                    neighbors[a].add(b)
                    neighbors[b].add(a)
            unseen = set(range(len(xyz)))
            components = []
            while unseen:
                queue = [unseen.pop()]
                size = 0
                while queue:
                    node = queue.pop()
                    extra = neighbors[node] & unseen
                    queue.extend(extra)
                    unseen.difference_update(extra)
                    size += 1
                components.append(size)
            parts[o.name] = {
                "triangles": len(o.data.loop_triangles),
                "indexComponents": sorted(components, reverse=True),
                "edgesOtherThanTwo": sum(n != 2 for n in edge_counts.values()),
                "boundsM": [xyz.min(0).tolist(), xyz.max(0).tolist()],
            }
        measures["reimportParts"] = parts
        receipt[key] = {
            "source": source,
            "sourceSha256": digest,
            "candidateSha256": hashlib.sha256(result.read_bytes()).hexdigest(),
            "bytes": result.stat().st_size,
            "geometry": measures,
            "before": before,
            "after": after,
        }
    (output / "measurements.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
