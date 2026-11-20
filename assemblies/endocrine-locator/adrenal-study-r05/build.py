"""Build, clean-import and review the adrenal regional teaching exterior."""

import argparse
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
R04 = HERE.parent / "adrenal-study-r04"
spec = spec_from_file_location("adrenal_r04", R04 / "build.py")
previous = module_from_spec(spec)
spec.loader.exec_module(previous)
ref = previous.reference
sys.path.insert(0, str(HERE))
import inspection

R04_GLB = R04 / "s1233-adrenals-illustrative.glb"
R04_SHA = "892a803078e586d6886da23a0435f35ec3792ed604a3acd85cea448ec10b8489"
NAME = "s1233-adrenals-regional"
GLANDS = ("adrenal-gland-left", "adrenal-gland-right")
GLAND = ("Adrenal capsule · rufous ochre", (0.69, 0.245, 0.128), 0.35)
KIDNEY = ("Kidney context · umber", (0.105, 0.042, 0.049), 0.59)
PANCREAS = ("Pancreas context · muted rose", (0.14, 0.105, 0.101), 0.54)
GLAND_BUDGET = 1500
POSTERIOR_OBLIQUE = (0.296198132726024, 0.813797681349374, 0.5)


def snapshot(path):
    return {key: ref.parts(obj) for key, obj in ref.load(path).items()}


def artifact(path):
    return {"file": path.name, "sha256": ref.sha256(path), "bytes": path.stat().st_size}


def gland_shell(original, label, work, python):
    mask, origin = previous.rasterize(original)
    input_path, output_path = work / "grid.npz", work / "surface.npz"
    np.savez(input_path, mask=mask, origin=origin, step=previous.STEP_MM, right=label == GLANDS[1])
    subprocess.run([str(python), str(HERE / "gland_field.py"), str(input_path), str(output_path)], check=True)
    with np.load(output_path, allow_pickle=False) as data:
        points, faces = data["vertices"], data["faces"]
        color_grid = data["solidFraction"], origin
        trace = {key: data[key].tolist() for key in ("levelMm", "terminalCenterMm", "terminalRadiiMm")}
    shell = previous.reduction((points, faces), GLAND_BUDGET)
    if ref.shell_stats(shell)["signedVolumeMm3"] < 0:
        shell = shell[0], shell[1][:, ::-1]
    return shell, trace, color_grid


def capsule_material():
    material = previous.look(GLAND)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Specular IOR Level"].default_value = 0.31
    shader.inputs["Coat Weight"].default_value = 0.135
    shader.inputs["Coat Roughness"].default_value = 0.22
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(shader.outputs["BSDF"], out.inputs["Surface"])
    vertex_color = nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = "Capsule palette"
    mix = nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    inputs = {sock.identifier: sock for sock in mix.inputs}
    inputs["Factor_Float"].default_value = 1.0
    inputs["A_Color"].default_value = (*GLAND[1], 1)
    links.new(vertex_color.outputs["Color"], inputs["B_Color"])
    links.new(
        next(sock for sock in mix.outputs if sock.identifier == "Result_Color"), shader.inputs["Base Color"]
    )
    # glTF carries spatial roughness in the green channel of its metal/rough map.
    # The 1D lookup is driven solely by the same smooth scalar as the palette.
    name = "Capsule roughness ramp"
    image = bpy.data.images.get(name)
    if not image:
        image = bpy.data.images.new(name, width=64, height=1, alpha=False)
        image.colorspace_settings.name = "Non-Color"
        image.pixels[:] = [v for t in np.linspace(0, 1, 64) for v in (1, 0.37 + 0.13 * t, 0, 1)]
        image.pack()
    texture = nodes.new("ShaderNodeTexImage")
    texture.image, texture.extension = image, "EXTEND"
    separate = nodes.new("ShaderNodeSeparateColor")
    links.new(texture.outputs["Color"], separate.inputs["Color"])
    links.new(separate.outputs["Green"], shader.inputs["Roughness"])
    links.new(separate.outputs["Blue"], shader.inputs["Metallic"])
    return material


def shade(obj, label, color_grid=None):
    if label not in GLANDS:
        ref.colorize(obj, previous.look(PANCREAS if label == "pancreas" else KIDNEY))
        return
    mat = capsule_material()
    colors = obj.data.color_attributes.new(name="Capsule palette", type="BYTE_COLOR", domain="POINT")
    density, origin = color_grid
    locations = np.array([v.co for v in obj.data.vertices]) * 1000
    uvw = (locations - origin) / previous.STEP_MM
    lower = np.floor(uvw).astype(int)
    blend = uvw - lower
    fraction = np.zeros(len(locations))
    for corner in product((0, 1), repeat=3):
        index = (lower + corner).T
        weight = np.prod(np.where(corner, blend, 1 - blend), axis=1)
        fraction += weight * density[tuple(index)]
    t = np.clip((fraction - 0.115) / 0.30, 0, 1)[:, None]
    honey, sienna = np.array([1.00, 0.97, 0.64]), np.array([0.39, 0.14, 0.22])
    rgb = honey + t * (sienna - honey)
    colors.data.foreach_set("color", np.column_stack((rgb, np.ones(len(rgb)))).ravel())
    uv = obj.data.uv_layers.new(name="Capsule roughness")
    corners = np.array([loop.vertex_index for loop in obj.data.loops])
    uv.uv.foreach_set("vector", np.column_stack((t[corners, 0], np.full(len(corners), 0.5))).ravel())
    ref.colorize(obj, mat)


def terminal_sample(base, other, lower, upper):
    """Measure both terminal slabs against the full opposing triangle surface."""
    ring = base[0] * 1000
    tree = ref.tree(other)
    result = {}
    for label, selected in (("inferior", ring[:, 2] <= lower), ("superior", ring[:, 2] >= upper)):
        points = ring[selected]
        distances = np.array([tree.find_nearest(p / 1000)[3] * 1000 for p in points])
        worst = np.argmax(distances)
        result[label] = {
            "vertices": len(points),
            "p95Mm": float(np.percentile(distances, 95)),
            "maxMm": float(distances[worst]),
            "worstPositionMm": points[worst].tolist(),
        }
    return result


def checks(groups, baseline):
    for label, shells in groups.items():
        if len(shells) != len(baseline[label]):
            raise ValueError(f"Changed shell count for {label}")
        for index, shell in enumerate(shells):
            stats = ref.shell_stats(shell)
            if (stats["euler"], stats["boundaryEdges"], stats["nonmanifoldEdges"]) != (2, 0, 0):
                raise ValueError(f"Invalid exterior topology for {label}")
            expected_sign = np.sign(ref.shell_stats(baseline[label][index])["signedVolumeMm3"])
            if np.sign(stats["signedVolumeMm3"]) != expected_sign or ref.self_crossings(shell):
                raise ValueError(f"Invalid winding or intersecting faces for {label}")
        x = shells[0][0][:, 0]
        if (label.endswith("left") and x.min() <= 0) or (label.endswith("right") and x.max() >= 0):
            raise ValueError(f"Lost laterality for {label}")
    if ref.crossing_pairs(groups) != ref.crossing_pairs(baseline):
        raise ValueError("Changed inter-organ intersections")


def lighter_trial(glb, source_groups, output, color_grids):
    objs = ref.load(glb)
    for key, obj in objs.items():
        base = source_groups[key]
        reduced = previous.reduction(base[0], max(120, len(base[0][1]) // 3))
        mat = obj.data.materials[0]
        ref.replace(obj, [reduced, *base[1:]], (mat.name, tuple(mat.diffuse_color[:3])))
        if key in GLANDS:
            shade(obj, key, color_grids[key])
        else:
            ref.colorize(obj, mat)
    ref.export(output, "lighter")
    light = output / "lighter.glb"
    trial = snapshot(light)
    checks(trial, source_groups)
    measurements = {}
    for key, group in source_groups.items():
        metrics = previous.measure(group[0], trial[key][0])
        measurements[key] = {
            k: metrics[k] for k in ("originalToUpdatedMm", "updatedToOriginalMm", "worstOriginalVertex")
        }
        measurements[key]["triangles"] = [sum(len(s[1]) for s in g) for g in (group, trial[key])]
    if ref.primitives(light) != ref.primitives(glb):
        raise ValueError("Lighter trial changed primitive count")
    return {"export": artifact(light), "parts": measurements}, light


def render_set(output, geometry, glb, light, baseline):
    renders = output / "renders"
    renders.mkdir()
    views = []
    options = [
        ("", None, False, POSTERIOR_OBLIQUE),
        ("-posterior", None, False, ref.FRONT),
        ("-detail", GLANDS, False, ref.FRONT),
        ("-neutral", GLANDS, True, ref.FRONT),
        ("-reverse", GLANDS, True, (0, -1, 0)),
        ("-right", [GLANDS[1]], True, ref.FRONT),
        ("-tissue", [GLANDS[1]], False, (-1, -0.45, 0)),
        ("-fold", [GLANDS[1]], True, (-1, -0.45, 0)),
    ]
    for suffix, include, neutral, front in options:
        entries = []
        inputs = [(R04_GLB, "original"), (glb, "updated")]
        if suffix == "-right":
            inputs.append((light, "lighter"))
        for path, kind in inputs:
            objects = ref.load(path)
            scene = bpy.context.scene
            ref.configure_scene(scene)
            if neutral:
                mat = previous.look(previous.NEUTRAL)
                for obj in objects.values():
                    ref.colorize(obj, mat)
            view = {
                "id": kind + suffix,
                "front": front,
                "cameraBounds": previous.bounds(baseline, include or baseline),
            }
            if include:
                view["include"] = [objects[name].name for name in include]
            if suffix in ("-tissue", "-fold"):
                from mathutils import Vector
                from render_teaching import area_light

                lo, hi = map(Vector, view["cameraBounds"])
                area_light(scene, (lo + hi) / 2, max(hi - lo), "Capsule window", (1.3, 1.4, 0.75), 28, 0.65)
            entry = ref.render_pair(scene, list(objects.values()), view, renders)
            entry["glb"] = {"file": path.name, "sha256": ref.sha256(path)}
            entry["materials"] = "Shared neutral override" if neutral else "Imported GLB materials"
            entries.append(entry)
        for entry in entries[1:]:
            if entries[0]["orthographicScale"] != entry["orthographicScale"] or any(
                (a["camera"], a["direction"]) != (b["camera"], b["direction"])
                for a, b in zip(entries[0]["images"], entry["images"], strict=True)
            ):
                raise ValueError(f"Unmatched comparison cameras in {suffix}")
        views.extend(entries)
    ref.write_json(
        renders / "renders.json",
        {"blender": bpy.app.version_string, "geometrySha256": ref.sha256(geometry), "views": views},
    )


def build(case, output, work, python, geometry_only):
    traced = snapshot(case)
    objects = ref.load(R04_GLB)
    baseline = {key: ref.parts(obj) for key, obj in objects.items()}
    identity = {}
    process = {}
    color_grids = {}
    for key, obj in objects.items():
        if key in GLANDS:
            shell, process[key], color_grids[key] = gland_shell(traced[key][0], key, work, python)
            ref.replace(obj, [shell], GLAND[:2])
        shade(obj, key, color_grids.get(key))
        obj["parent_glb_sha256"] = R04_SHA
        obj["case_reference_glb_sha256"] = ref.PIN
        obj["derivation"] = "gland-exterior-from-r02" if key in GLANDS else "context-exterior-from-r04"
        identity[key] = obj.name, dict(obj.items())
    ref.export(output, NAME)
    glb = output / f"{NAME}.glb"
    imported = ref.load(glb)
    groups = {key: ref.parts(obj) for key, obj in imported.items()}
    if identity != {key: (obj.name, dict(obj.items())) for key, obj in imported.items()}:
        raise ValueError("Changed portable selection identity")
    if ref.primitives(R04_GLB) != ref.primitives(glb):
        raise ValueError("Changed material primitive count")
    checks(groups, baseline)
    metrics = {}
    for key, group in groups.items():
        r04 = baseline[key]
        comparisons = [previous.measure(before, after) for before, after in zip(r04, group, strict=True)]
        entry = {"components": comparisons, "primitives": ref.primitives(glb)[key]}
        if key in GLANDS:
            a, b = traced[key][0], group[0]
            low, high = float(np.min(a[0][:, 2]) * 1000 + 4.5), float(np.max(a[0][:, 2]) * 1000 - 4.5)
            entry["caseReference"] = previous.measure(a, b)
            entry["terminalSlabs"] = {
                "inferiorZMaxMm": low,
                "superiorZMinMm": high,
                "caseToR05": terminal_sample(a, b, low, high),
                "r05ToCase": terminal_sample(b, a, low, high),
                "caseToR04": terminal_sample(a, r04[0], low, high),
            }
            entry["field"] = process[key]
            for sided in ("caseToR05", "r05ToCase"):
                if max(end["maxMm"] for end in entry["terminalSlabs"][sided].values()) > 3:
                    raise ValueError(f"Terminal slab exceeds two source voxels in {key} ({sided})")
        elif any(record["originalToUpdatedMm"]["max"] > 0.003 for record in comparisons):
            raise ValueError(f"Context moved in {key}")
        metrics[key] = entry
    for key, entry in metrics.items():
        if key in GLANDS:
            entry["localization"] = inspection.regional_measurements(groups, key, POSTERIOR_OBLIQUE)
        else:
            entry["caseReference"] = previous.measure(traced[key][0], groups[key][0])
    light_receipt, light = lighter_trial(glb, groups, work, color_grids)
    trial_dir = output / "trial"
    trial_dir.mkdir()
    light = light.rename(trial_dir / light.name)
    geometry = output / "geometry.json"
    ref.write_json(
        geometry,
        {
            "blender": bpy.app.version_string,
            "source": artifact(R04_GLB),
            "caseReference": artifact(case),
            "updated": artifact(glb),
            "sourceMaskSpacingMm": 1.5,
            "frame": "s1233 Blender metres, +X left, +Y posterior, +Z superior",
            "workGridStepMm": previous.STEP_MM,
            "recipeSha256": ref.sha256(Path(__file__)),
            "fieldRecipeSha256": ref.sha256(HERE / "gland_field.py"),
            "referenceRecipeSha256": ref.sha256(previous.R03_RECIPE),
            "previousRecipeSha256": ref.sha256(R04 / "build.py"),
            "inspectionRecipeSha256": ref.sha256(HERE / "inspection.py"),
            "sectionRecipeSha256": ref.sha256(R04 / "section.py"),
            "sections": inspection.axial_sections(traced, baseline, groups),
            "rightCleft": inspection.cleft_sections(traced, baseline, groups),
            "surfaceIntersectionPairs": ref.crossing_pairs(groups),
            "capsule": inspection.portable_capsule(glb, GLANDS),
            "parts": metrics,
            "lighterTrial": light_receipt,
        },
    )
    if not geometry_only:
        render_set(output, geometry, glb, light, baseline)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--science-python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if ref.sha256(args.case) != ref.PIN or ref.sha256(R04_GLB) != R04_SHA:
        raise ValueError("Restore the pinned r02 case and r04 teaching GLBs")
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{args.output.name}-", dir=args.output.parent) as scratch:
        work = Path(scratch)
        out = work / "verified"
        out.mkdir()
        build(args.case, out, work, args.science_python, args.geometry_only)
        out.rename(args.output)


if __name__ == "__main__":
    main()
