"""Render actual clean imports with fixed fields and test native-frame spatial context."""

import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
BASE = runpy.run_path(str(HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine/render.py"))
OVARY = ROOT / "models/ovaries/exports/hra-ovary-tubal-r01/ovary-tubal-context.glb"
BRAIN = ROOT / "models/brain/exports/bodyparts3d-4.0-atlas-r2/brain-source-frame.glb"
HYPO = ROOT / "models/hypothalamus/exports/source-candidate-01/hypothalamus_source_frame.glb"
PARA = ROOT / "models/parathyroids/exports/z-localization-r01/parathyroids_thyroid_context.glb"
PENIS = ROOT / "models/penis/exports/z-native-components-r04/penile_internal_components.glb"
URETHRA = ROOT / "models/urethra_male/exports/z-native-context-r01/urethral-context.glb"


def meshes(path, clear=True):
    if clear:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), merge_vertices=False)
    bpy.context.view_layer.update()
    return {o.name: o for o in bpy.data.objects if o not in before and o.type == "MESH"}


def triangles(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    pts = [obj.matrix_world @ v.co for v in mesh.vertices]
    faces = [tuple(t.vertices) for t in mesh.loop_triangles]
    return pts, faces, BVHTree.FromPolygons(pts, faces, all_triangles=True)


def capture(cam, name, show, all_objs, neutral=True):
    scene = bpy.context.scene
    for obj in all_objs:
        obj.hide_render = obj not in show
    scene.display.shading.color_type = "SINGLE" if neutral else "OBJECT"
    scene.display.shading.single_color = (0.55, 0.50, 0.46)
    scene.render.filepath = str(OUT / (name + ".png"))
    bpy.ops.render.render(write_still=True)
    return dict(
        file=name + ".png",
        sha256=hashlib.sha256((OUT / (name + ".png")).read_bytes()).hexdigest(),
        eye=list(cam.location),
        quaternion=list(cam.rotation_quaternion),
        orthoScaleM=cam.data.ortho_scale,
        visible=[o.name for o in show],
    )


def camera():
    scene = bpy.context.scene
    cam = BASE["configure"](scene)
    scene.render.resolution_x = scene.render.resolution_y = 480
    return cam


def ovary():
    rows = json.loads((ROOT / "reviews/ovaries/2026-11-21-form-assessment-r01/views.json").read_text())[
        "plates"
    ]
    record = {}
    base = {}
    for edition, path in (("original", OVARY), ("interpreted", OUT / "ovary.glb")):
        objs = meshes(path)
        cam = camera()
        frames = []
        stats = {}
        data = {name: triangles(o) for name, o in objs.items()}
        for side, plate in zip(("L", "R"), rows, strict=True):
            for row in plate["framesLeftToRight"]:
                if (row["angle"], row["material"]) not in (
                    ("alternate", "neutral"),
                    ("native", "palette"),
                ):
                    continue
                cam.location = row["cameraM"]
                cam.rotation_mode = "QUATERNION"
                cam.rotation_quaternion = Quaternion(row["cameraQuaternion"])
                cam.data.clip_start = 0.001
                cam.data.clip_end = 3
                cam.data.ortho_scale = row["orthoScaleM"]
                visible = [objs[n] for n in row["visibleNodes"]]
                for o in visible:
                    o.color = (0.77, 0.46, 0.44, 1) if "ovary" in o.name else (0.46, 0.65, 0.68, 1)
                frames.append(
                    capture(
                        cam,
                        f"ovary-{side}-{row['angle']}-{edition}",
                        visible,
                        objs.values(),
                        row["material"] == "neutral",
                    )
                )
            n = "VH_F_" + ("left" if side == "L" else "right") + "_ovary"
            t = f"VH_F_fibria_of_uterine_tube_{side}"
            pts, faces, tree = data[n]
            fringe_pts, fringe_faces, fringe_tree = data[t]
            distances = [tree.find_nearest(v)[3] * 1000 for v in fringe_pts]
            stats[side] = dict(
                ovaryTriangles=len(faces),
                fringeTriangles=len(fringe_faces),
                fringeMeshContacts=len(tree.overlap(fringe_tree)),
                nearestFringeVertexMm=min(distances),
                fringeVertexDistanceP10Mm=float(np.percentile(distances, 10)),
            )
            stats[side]["sameSideContacts"] = {
                k: len(tree.overlap(item[2])) for k, item in data.items() if k.endswith("_" + side)
            }
            stats[side]["ovarySelfContacts"] = sum(
                1 for i, j in tree.overlap(tree) if i < j and not set(faces[i]).intersection(faces[j])
            )
            if edition == "interpreted":
                for k, (q, f, bvh) in data.items():
                    if "ovary" not in k:
                        oldq, oldf, _ = base[k]
                        if f != oldf or q != oldq:
                            raise ValueError(f"Changed protected tubal part {k}")
                a, af, abvh = base[n]
                for tag, points, tris, target in (
                    ("sourceToInterpretation", a, af, tree),
                    ("interpretationToSource", pts, faces, abvh),
                ):
                    samples = points + [(points[i] + points[j] + points[k]) / 3 for i, j, k in tris]
                    drift = [target.find_nearest(v)[3] * 1000 for v in samples]
                    stats[side][tag] = dict(
                        samples=len(drift), p50mm=float(np.median(drift)), maxMm=max(drift)
                    )
        if edition == "original":
            base = data
        record[edition] = dict(
            frames=frames, measurements=stats, sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        )
    return record


def boundary_edges(obj):
    points, faces, _ = triangles(obj)
    vertices, remap = np.unique(np.asarray(points), axis=0, return_inverse=True)
    mapped = remap[np.asarray(faces)]
    edges = np.concatenate([mapped[:, [i, (i + 1) % 3]] for i in range(3)])
    pairs, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    return vertices, pairs[counts == 1], pairs[counts > 2]


def glans_rim(glans, urethra):
    points, open_edges, branched_edges = boundary_edges(glans)
    probe, ends, branches = boundary_edges(urethra)
    neighbors = {}
    for a, b in ends:
        neighbors.setdefault(int(a), set()).add(int(b))
        neighbors.setdefault(int(b), set()).add(int(a))
    loops = []
    while neighbors:
        pending = [next(iter(neighbors))]
        loop = []
        while pending:
            item = pending.pop()
            if item in neighbors:
                pending.extend(neighbors.pop(item))
                loop.append(item)
        loops.append(probe[loop])
    if len(loops) != 2 or len(branches):
        raise ValueError("Expected two source-curve ends")
    distal = min(loops, key=lambda ring: np.linalg.norm(ring.mean(axis=0) - points.mean(axis=0)))
    boundary = points[np.vstack((open_edges, branched_edges))]
    seg = boundary[:, 1] - boundary[:, 0]
    distances = []
    for point in distal:
        t = np.clip(np.sum((point - boundary[:, 0]) * seg, axis=1) / np.sum(seg * seg, axis=1), 0, 1)
        distances.append(
            float(np.linalg.norm(point - (boundary[:, 0] + t[:, None] * seg), axis=1).min() * 1000)
        )
    return dict(
        exactWorldPositionWeld=True,
        glansBoundaryEdges=len(open_edges),
        glansOverincidentEdges=len(branched_edges),
        distalEndVertices=len(distal),
        distalEndToDefectiveEdgeMinMm=min(distances),
        distalEndToDefectiveEdgeMaxMm=max(distances),
    )


def context(kind):
    p, addition = (HYPO, BRAIN) if kind == "hypothalamus" else (PENIS, URETHRA)
    targets = meshes(p)
    extra = meshes(addition, False)
    cam = camera()
    all_objs = [*targets.values(), *extra.values()]
    if kind == "hypothalamus":
        context = [
            o for n, o in extra.items() if n.startswith(("midbrain", "left thalamus", "right thalamus"))
        ]
        common = [o for n, o in extra.items() if n.startswith("hypothalamus")]
        near = targets.values()
        dirs = [(-0.59, 1, 0.33), (1, 0.22, 0.07)]
    else:
        context = [o for n, o in extra.items() if n.startswith("Urethra")]
        common = [o for n, o in extra.items() if n.startswith("Glans")]
        near = [o for n, o in targets.items() if n.startswith("Glans")]
        dirs = [(0.55, 0.65, -0.31), (-0.55, 0.65, -0.31)]
    ventricle = None
    if kind == "hypothalamus":
        with zipfile.ZipFile(OUT / "bp3d.zip") as archive:
            data = archive.read("partof_BP3D_4.0_obj_99/FJ1730.obj")
        if (
            hashlib.sha256(data).hexdigest()
            != "7acd4a30d13b409221aea7267ae302ef7c100162a6185d891c91843ec876dd79"
        ):
            raise ValueError("Unverified ventricular reference")
        lines = data.decode().splitlines()
        points = [
            tuple(float(x) / 1000 for x in line.split()[1:]) for line in lines if line.startswith("v ")
        ]
        faces = [
            tuple(int(x.split("/")[0]) - 1 for x in line.split()[1:])
            for line in lines
            if line.startswith("f ")
        ]
        mesh = bpy.data.meshes.new("BP3D FJ1730")
        mesh.from_pydata(points, [], faces)
        mesh.update()
        ventricle = bpy.data.objects.new("Third ventricle | FJ1730", mesh)
        bpy.context.scene.collection.objects.link(ventricle)
        ventricle.color = (0.27, 0.63, 0.68, 1)
        all_objs.append(ventricle)
    if not context or not common:
        raise ValueError("Missing registered source member")
    for o in targets.values():
        o.color = (0.75, 0.49, 0.41, 1)
    for o in context:
        o.color = (0.36, 0.62, 0.72, 1)
    witness = {}
    source_pts = [v for o in common for v in triangles(o)[0]]
    for o in near:
        pts, faces, tree = triangles(o)
        witness[o.name] = dict(
            commonWitnessNearestMm=min(tree.find_nearest(v)[3] for v in source_pts) * 1000, context={}
        )
        if kind == "penis":
            witness[o.name]["terminalRim"] = glans_rim(o, context[0])
        for c in context:
            q, f, other = triangles(c)
            pairs = tree.overlap(other)
            distances = np.array([other.find_nearest(v)[3] * 1000 for v in pts])
            witness[o.name]["context"][c.name] = dict(
                intersectingTrianglePairs=len(pairs),
                minVertexToSurfaceMm=float(distances.min()),
                medianVertexToSurfaceMm=float(np.median(distances)),
            )
    frames = []
    for i, d in enumerate(dirs):
        BASE["frame_camera"](cam, list(near), d)
        for name, selection in (
            ("original", list(targets.values())),
            ("registered", [*targets.values(), *context]),
        ):
            frames.append(capture(cam, f"{kind}-{i}-{name}", selection, all_objs, False))
        if kind == "penis":
            frames.append(capture(cam, f"penis-{i}-glans", list(near), all_objs, False))
        if ventricle:
            frames.append(
                capture(cam, f"{kind}-{i}-ventricle", [*targets.values(), ventricle], all_objs, False)
            )
    return dict(
        frames=frames,
        controlSha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        companionSha256=hashlib.sha256(addition.read_bytes()).hexdigest(),
        measurements=witness,
    )


def parathyroid():
    targets = meshes(PARA)
    cam = camera()
    glands = [o for n, o in targets.items() if "parathyroid" in n]
    (thyroid,) = [o for o in targets.values() if o not in glands]
    thyroid.color = (0.36, 0.50, 0.55, 1)
    markers = []
    oriented = []
    extents = {}
    for gland in glands:
        gland.color = (0.87, 0.63, 0.30, 1)
        pts, _, _ = triangles(gland)
        center = sum(pts, Vector((0, 0, 0))) / len(pts)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.00165, location=center)
        mark = bpy.context.object
        mark.name = gland.name + " | position symbol"
        mark.color = gland.color
        markers.append(mark)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=center)
        marker = bpy.context.object
        marker.name = gland.name + " | oriented extent symbol"
        cloud = np.asarray(pts, dtype=float) - np.asarray(center)
        _, axes = np.linalg.eigh(np.cov(cloud.T))
        projected = np.einsum("ij,jk->ik", cloud, axes)
        spans = np.ptp(projected, axis=0)
        template = np.array([list(v.co) for v in marker.data.vertices])
        scaled = template * (spans / np.ptp(template, axis=0))
        coords = np.einsum("ij,kj->ik", scaled, axes)
        for v, xyz in zip(marker.data.vertices, coords, strict=True):
            v.co = xyz
        marker.data.update()
        marker.color = gland.color
        oriented.append(marker)
        output = np.array([list(v.co) for v in marker.data.vertices])
        measured = np.ptp(np.einsum("ij,jk->ik", output, axes), axis=0)
        extents[gland.name] = dict(
            originalPrincipalSpansMm=(1000 * spans).tolist(),
            markerPrincipalSpansMm=(1000 * measured).tolist(),
            principalAxes=axes.tolist(),
            centerErrorMm=float(np.linalg.norm(output.mean(axis=0)) * 1000),
        )
    frames = []
    for i, d in enumerate([(0, 1, 0), (0.75, 0.66, 0.06)]):
        BASE["frame_camera"](cam, list(targets.values()), d)
        for name, selection in (("original", glands), ("symbols", markers), ("oriented", oriented)):
            frames.append(
                capture(
                    cam,
                    f"parathyroid-{i}-{name}",
                    [thyroid, *selection],
                    [*targets.values(), *markers, *oriented],
                    False,
                )
            )
    return dict(
        frames=frames,
        controlSha256=hashlib.sha256(PARA.read_bytes()).hexdigest(),
        orientedExtents=extents,
        symbolDiameterMm=3.3,
        centroidsM={m.name: list(m.location) for m in markers},
    )


def fdi():
    original = ROOT / "models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb"
    frames = []
    cameras = {}
    for edition, path in (("original", original), ("projected", OUT / "fdi-bone.glb")):
        objs = meshes(path)
        cam = camera()
        for n, o in objs.items():
            o.color = {
                "bone": (0.49, 0.42, 0.37, 1),
                "dentin": (0.74, 0.62, 0.45, 1),
                "enamel": (0.85, 0.83, 0.72, 1),
                "pulp": (0.70, 0.42, 0.46, 1),
            }[n.split("/")[-1]]
        for i, direction in enumerate(((0.25, -0.72, 0.65), (0.78, 0.55, 0.2), (0.78, 0.55, 0.2))):
            if edition == "original":
                BASE["frame_camera"](cam, list(objs.values()), direction)
                if i == 2:
                    # Patient-independent native input indices (x=211, y=190, z=590);
                    # z lies above the root seat in the 12 mm bone detail.
                    rot = cam.rotation_quaternion
                    cam.location = Vector((0.00844, -0.02360, 0.00760)) + rot @ Vector((0, 0, 0.045))
                    cam.data.ortho_scale = 0.012
                cameras[i] = (cam.location.copy(), cam.rotation_quaternion.copy(), cam.data.ortho_scale)
            cam.rotation_mode = "QUATERNION"
            cam.location, cam.rotation_quaternion, cam.data.ortho_scale = cameras[i]
            cam.data.clip_start = 0.0001
            cam.data.clip_end = 2
            frames.append(capture(cam, f"fdi-{i}-{edition}", list(objs.values()), objs.values(), i == 2))
    return dict(frames=frames)


def material_views():
    # The same Cycles rig was already used to assess the original HRA export.
    rig = runpy.run_path(str(HERE.parent / "target-form/render.py"))
    plates = json.loads(rig["OVARY"].read_text())["plates"]
    rows = [
        view
        for plate in plates
        for view in plate["framesLeftToRight"]
        if (view["angle"], view["material"]) in (("native", "palette"), ("alternate", "neutral"))
    ]
    output = {}
    for label, path in (("source", OVARY), ("teaching", OUT / "ovary.glb")):
        _, output[label] = rig["capture_ovary"](rows, path, label, OUT)
    (OUT / "material-frames.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    results = {}
    for k, func in (
        ("ovary", ovary),
        ("hypothalamus", lambda: context("hypothalamus")),
        ("penis", lambda: context("penis")),
        ("parathyroid", parathyroid),
        ("fdi", fdi),
    ):
        results[k] = func()
        (OUT / "context-trials.json").write_text(json.dumps(results, indent=2) + "\n")
    if "--materials" in sys.argv:
        material_views()
