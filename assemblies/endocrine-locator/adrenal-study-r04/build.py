"""Build a separate illustrative exterior from the pinned s1233 r03 clean import."""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import bpy
from mathutils import Vector
import numpy as np

HERE = Path(__file__).resolve().parent
R03_RECIPE = HERE.parent / "adrenal-study-r03" / "build.py"
reference_spec = spec_from_file_location("adrenal_r03_recipe", R03_RECIPE)
reference = module_from_spec(reference_spec)
reference_spec.loader.exec_module(reference)

PIN = "e2bcc2e93a73c027480418109e4db06ce38ea7923b671e5dfe53cfd7d288caa4"
SOURCE = HERE.parent / "adrenal-study-r03" / "s1233-adrenals-teaching.glb"
NAME = "s1233-adrenals-illustrative"
STEP_MM = 0.6
GLAND = "Adrenals · ochre", (0.82, 0.355, 0.048), 0.40
KIDNEY = "Kidneys · muted burgundy", (0.16, 0.057, 0.064), 0.55
PANCREAS = "Pancreas · muted terracotta", (0.275, 0.155, 0.11), 0.53
EXPECTED_CLOSURES = {
    "adrenal-gland-left": 1,
    "adrenal-gland-right": 1,
    "kidney-left": 0,
    "kidney-right": 0,
    "pancreas": 3,
}
NEUTRAL = "Neutral surface diagnostic", (0.35, 0.35, 0.35), 0.43

# Gaussian sigma, maximum tested morphological closing radius, triangle budget, material.
PARTS = {
    "adrenal-gland-left": (1.55, 3.6, 1650, GLAND),
    "adrenal-gland-right": (1.55, 3.6, 1550, GLAND),
    "kidney-left": (2.70, 0, 3650, KIDNEY),
    "kidney-right": (2.70, 0, 3650, KIDNEY),
    "pancreas": (1.92, 3.6, 3350, PANCREAS),
}


def rasterize(shell):
    """Sample solid occupancy by alternating entry and exit along the positive X axis."""
    vertices_mm = shell[0] * 1000
    origin = np.floor(vertices_mm.min(0) / STEP_MM) * STEP_MM - 8.4 + 0.037
    maximum = np.ceil(vertices_mm.max(0) / STEP_MM) * STEP_MM + 8.4
    axes = [np.arange(a, b, STEP_MM) for a, b in zip(origin, maximum, strict=True)]
    x, y, z = (axis / 1000 for axis in axes)
    mask = np.zeros(tuple(map(len, axes)), dtype=bool)
    bvh = reference.tree(shell)
    direction = Vector((1, 0, 0))
    for yi, y_metres in enumerate(y):
        for zi, z_metres in enumerate(z):
            for jitter in (0, 0.0000031):
                run = []
                start = x[0]
                while True:
                    hit, _, _, _ = bvh.ray_cast(Vector((start, y_metres + jitter, z_metres - jitter)), direction)
                    if hit is None:
                        break
                    run.append(hit.x)
                    start = hit.x + 0.0000001
                if len(run) % 2 == 0:
                    break
            else:
                raise ValueError("Odd number of surface crossings on a scanline")
            for first, last in zip(run[::2], run[1::2], strict=True):
                mask[np.searchsorted(x, first):np.searchsorted(x, last), yi, zi] = True
    return mask, origin


def reduction(shell, budget):
    vertices, faces = shell
    mesh = bpy.data.meshes.new("Temporary exterior shell")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new("Quadric exterior reduction", "DECIMATE")
    modifier.ratio = min(1, budget / len(faces))
    modifier.use_collapse_triangulate = True
    evaluated = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    evaluated.calc_loop_triangles()
    result = np.array([v.co for v in evaluated.vertices]), np.array([t.vertices[:] for t in evaluated.loop_triangles])
    bpy.data.meshes.remove(evaluated)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return result


def reconstruction(shell, spec, scratch, python):
    sigma, close, budget, _ = spec
    mask, origin = rasterize(shell)
    original, updated = scratch / "source.npz", scratch / "exterior.npz"
    np.savez(original, mask=mask, points_mm=origin, step_mm=STEP_MM, sigma_mm=sigma,
             max_close_mm=close)
    subprocess.run([str(python), str(HERE / "exterior.py"), str(original), str(updated)], check=True)
    with np.load(updated, allow_pickle=False) as exterior:
        dense = exterior["vertices"], exterior["faces"]
        trace = {key: exterior[key].item() for key in exterior.files if key not in ("vertices", "faces")}
    reduced = reduction(dense, budget)
    if reference.shell_stats(reduced)["signedVolumeMm3"] < 0:
        reduced = reduced[0], reduced[1][:, ::-1]
    return reduced, trace


def look(rgb_spec):
    name, color, roughness = rgb_spec
    mat = reference.material(name, color)
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.34
    return mat


def bounds(groups, labels):
    points = np.concatenate([points for label in labels for points, _ in groups[label]])
    return [points.min(0).tolist(), points.max(0).tolist()]


def render(path, label, output, fixed_bounds, include=None, neutral=False):
    objects = reference.load(path)
    scene = bpy.context.scene
    reference.configure_scene(scene)
    if neutral:
        mat = look(NEUTRAL)
        for obj in objects.values():
            obj.data.materials.clear()
            obj.data.materials.append(mat)
    options = {"id": label, "front": reference.FRONT, "cameraBounds": fixed_bounds}
    if include:
        options["include"] = [objects[label].name for label in include]
    result = reference.render_pair(scene, list(objects.values()), options, output)
    result["glb"] = {"file": path.name, "sha256": reference.sha256(path)}
    result["materials"] = "Shared neutral override" if neutral else "Imported GLB materials"
    return result


def measure(base, candidate):
    before, after = reference.shell_stats(base), reference.shell_stats(candidate)
    delta = np.abs(np.array(before["boundsMm"]) - after["boundsMm"])
    original_tree, updated_tree = reference.tree(base), reference.tree(candidate)
    vertex_projections = [updated_tree.find_nearest(v) for v in base[0]]
    worst = max(range(len(vertex_projections)), key=lambda index: vertex_projections[index][3])
    nearest, normal, _, separation = vertex_projections[worst]
    displacement = Vector(base[0][worst]) - nearest
    return {
        "before": before,
        "after": after,
        "originalToUpdatedMm": reference.distances(base, updated_tree),
        "updatedToOriginalMm": reference.distances(candidate, original_tree),
        "worstOriginalVertex": {
            "originalPositionMm": (base[0][worst] * 1000).tolist(),
            "updatedShellNearestPointMm": list(nearest * 1000),
            "separationMm": separation * 1000,
            "updatedNormalDotDisplacementMm": normal.dot(displacement) * 1000,
        },
        "signedVolumeChangePct": 100 * (after["signedVolumeMm3"] / before["signedVolumeMm3"] - 1),
        "boundsAbsoluteDeltaMm": delta.tolist(),
        "areaCentroidShiftMm": np.linalg.norm(np.array(after["areaCentroidMm"]) - before["areaCentroidMm"]),
        "nonadjacentIntersectionPairs": {"original": len(reference.self_crossings(base)), "updated": len(reference.self_crossings(candidate))},
    }


def assemble(source, output, scratch, python, geometry_only):
    objects = reference.load(source)
    bases = {label: reference.parts(obj) for label, obj in objects.items()}
    identity = {label: (obj.name, dict(obj.items())) for label, obj in objects.items()}
    original_primitives = reference.primitives(source)
    traces = {}
    for label, obj in objects.items():
        source_shell = bases[label][0]
        principal, trace = reconstruction(source_shell, PARTS[label], scratch, python)
        traces[label] = trace
        appearance = PARTS[label][3]
        reference.replace(obj, [principal, *bases[label][1:]], appearance[:2])
        obj.data.materials[0] = look(appearance)
        obj["derivation"] = "illustrative-exterior-from-segmentation"
        obj["parent_glb_sha256"] = PIN
        obj["inferred_tunnel_closures"] = EXPECTED_CLOSURES[label]

    reference.export(output, NAME)
    glb = output / f"{NAME}.glb"
    imported = reference.load(glb)
    result = {label: reference.parts(obj) for label, obj in imported.items()}
    updated_primitives = reference.primitives(glb)
    metrics = {}
    for label, original in bases.items():
        candidate = result[label]
        name, source_extras = identity[label]
        actual_extras = dict(imported[label].items())
        expected_extras = {
            **source_extras,
            "derivation": "illustrative-exterior-from-segmentation",
            "parent_glb_sha256": PIN,
            "inferred_tunnel_closures": EXPECTED_CLOSURES[label],
        }
        if len(candidate) != len(original) or imported[label].name != name or actual_extras != expected_extras:
            raise ValueError(f"Component count or object identity changed for {label}")
        if updated_primitives[label] != original_primitives[label]:
            raise ValueError(f"Primitive count changed for {label}")
        entries = [measure(a, b) for a, b in zip(original, candidate, strict=True)]
        for i, entry in enumerate(entries):
            topology = entry["after"]
            if (topology["euler"], topology["boundaryEdges"], topology["nonmanifoldEdges"]) != (2, 0, 0):
                raise ValueError(f"Expected closed genus-zero shell {label}/{i + 1}: {topology}")
            if entry["nonadjacentIntersectionPairs"]["updated"]:
                raise ValueError(f"Nonadjacent triangle intersection after reimport: {label}/{i + 1}")
            error = max(entry[k]["max"] for k in ("originalToUpdatedMm", "updatedToOriginalMm"))
            if i and error > 0.003:
                raise ValueError(f"Secondary shell moved: {label}/{i + 1}")
        closures = sum((entry["after"]["euler"] - entry["before"]["euler"]) // 2 for entry in entries)
        if closures != EXPECTED_CLOSURES[label]:
            raise ValueError(f"Unexpected closure count for {label}")
        x = entries[0]["after"]["areaCentroidMm"][0]
        if (label.endswith("-left") and x <= 0) or (label.endswith("-right") and x >= 0):
            raise ValueError(f"Laterality changed for {label}")
        metrics[label] = {"components": entries, "primitives": [original_primitives[label], updated_primitives[label]],
                          "construction": traces[label], "inferredTunnelClosures": closures}
    crossings = reference.crossing_pairs(result)
    if crossings != reference.crossing_pairs(bases):
        raise ValueError(f"Changed cross-component intersection pairs: {crossings}")

    def artifact(path):
        return {"file": path.name, "sha256": reference.sha256(path), "bytes": path.stat().st_size}

    geometry = output / "geometry.json"
    reference.write_json(geometry, {
        "blender": bpy.app.version_string,
        "recipeSha256": reference.sha256(Path(__file__)),
        "fieldRecipeSha256": reference.sha256(HERE / "exterior.py"),
        "referenceRecipeSha256": reference.sha256(R03_RECIPE),
        "source": artifact(source),
        "updated": artifact(glb),
        "editable": artifact(output / f"{NAME}.blend"),
        "workGridStepMm": STEP_MM,
        "sourceMaskSpacingMm": 1.5,
        "distanceReference": "Two-way nearest triangle distances sampled on the r03 and r04 GLBs",
        "frame": "s1233 Blender metres, +X left, +Y posterior, +Z superior",
        "surfaceIntersectionPairs": crossings,
        "parts": metrics,
    })
    if geometry_only:
        return
    renders = output / "renders"
    renders.mkdir()
    glands = [label for label in PARTS if label.startswith("adrenal-gland")]
    views = []
    for suffix, include, neutral in (
        ("", None, False), ("-detail", glands, False),
        ("-neutral", None, True), ("-neutral-detail", glands, True),
    ):
        camera = bounds(bases, include or PARTS)
        before, after = (render(path, view + suffix, renders, camera, include, neutral)
                         for path, view in ((source, "original"), (glb, "updated")))
        if before["orthographicScale"] != after["orthographicScale"] or any(
            (a["camera"], a["direction"]) != (b["camera"], b["direction"])
            for a, b in zip(before["images"], after["images"], strict=True)
        ):
            raise ValueError(f"Comparison used different camera parameters: {suffix}")
        views.extend((before, after))
    reference.write_json(renders / "renders.json", {"blender": bpy.app.version_string, "geometrySha256": reference.sha256(geometry), "views": views})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--science-python", required=True)
    parser.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if reference.sha256(args.source) != PIN:
        raise ValueError("Restore the pinned s1233 r03 GLB")
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{args.output.name}-", dir=args.output.parent) as tmp:
        work = Path(tmp)
        out = work / "verified"
        out.mkdir()
        assemble(args.source, out, work, args.science_python, args.geometry_only)
        out.rename(args.output)


if __name__ == "__main__":
    main()
