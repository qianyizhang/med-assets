"""Compare named selections in the clean-import campaign controls."""

import argparse
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
CONTROL = HERE / "controls.json"
CAMERAS = HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine" / "render.py"
HEART_SOURCE = Path("body/anatomy-workshop-r1/body-3d-source/tb3/presentation/task-explorer/anatomy/heart.json")
HEART_SOURCE_SHA = "545f45eb67d47965c6e86aa6bd9442069e603a600adaf278db2b90c11cc5f61d"

# Unlike atlas colors, this restricted palette is consistent within each pair.
TEAL = (.16, .60, .55, 1)
ROSE = (.75, .29, .32, 1)
GOLD = (.88, .62, .26, 1)
BONE = (.59, .54, .50, 1)
DUSK = (.29, .37, .48, 1)
IVORY = (.93, .85, .69, 1)


def load_camera_tools():
    # The previous wave's module reads two CLI slots at import.
    spec = spec_from_file_location("campaign_cameras", CAMERAS)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot_visible_meshes(meshes):
    """Use the evaluated Workshop surfaces without inherited collection or driver visibility."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    snapshot = bpy.data.scenes.new("Workshop teaching selection")
    evaluated = []
    for source in meshes:
        original = source.evaluated_get(depsgraph)
        data = bpy.data.meshes.new_from_object(original, depsgraph=depsgraph)
        name = source.name
        source.name = f"Source · {name}"
        obj = bpy.data.objects.new(name, data)
        snapshot.collection.objects.link(obj)
        obj.matrix_world = original.matrix_world
        evaluated.append(obj)
    bpy.context.window.scene = snapshot
    return snapshot, evaluated


def paint(obj, color):
    obj.color = color


def choose(names, keys):
    missing = set(keys) - names.keys()
    if missing:
        raise ValueError(f"Missing exact selection: {sorted(missing)}")
    return [names[name] for name in keys]


def record_shots(row, output, views, tools, scene, meshes, camera):
    names = {o.name: o for o in meshes}
    shots = []
    for name, direction, framing, show, palette in views:
        framed = choose(names, framing) if framing else meshes
        visible = choose(names, show) if show else meshes
        tools.frame_camera(camera, framed, direction)
        for obj in meshes:
            obj.hide_render = obj not in visible
            obj.hide_set(obj not in visible)
        shading = scene.display.shading
        shading.color_type = "OBJECT" if palette else "SINGLE"
        shading.single_color = tools.NEUTRAL
        path = output / f"{row}-{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        shots.append({"file": path.name, **tools.identity(path), "direction": direction,
                      "camera": list(camera.location), "orthoScale": camera.data.ortho_scale,
                      "palette": palette, "visible": sorted(obj.name for obj in visible)})
    return shots


def dental(names):
    enamel, dentin, pulp, bone = ("SWIRendo_31_T2/" + role for role in ("enamel", "dentin", "pulp", "bone"))
    for name, color in ((enamel, IVORY), (dentin, GOLD), (pulp, ROSE), (bone, BONE)):
        paint(names[name], color)
    first = (.25, -.72, .65)
    second = (.78, .55, .20)
    return [
        ("all", first, None, None, True),
        ("tooth", first, None, (enamel, dentin), True),
        ("reverse", second, None, None, True),
        ("reverse-tooth", second, None, (enamel, dentin), True),
    ]


def penis(names):
    glans = "Glans penis source display"
    spongiosum = "Corpus spongiosum of penis source display"
    cavernosum = "Corpus cavernosum of penis source display"
    for name, color in ((glans, GOLD), (spongiosum, ROSE), (cavernosum, TEAL)):
        paint(names[name], color)
    direction = (.76, -.34, -.72)
    return [
        ("all", direction, None, None, True),
        ("spongiosum", direction, None, (spongiosum, glans), True),
        ("glans-detail", (.55, .65, -.31), (glans,), None, False),
    ]


def vagina(names):
    target = "VH_F_vagina"
    cervix = "VH_F_cervix"
    junction = "VH_F_cervicovaginal_junction"
    rectum = "VH_F_rectum"
    bladder = ("VH_F_fundus_of_urinary_bladder_dome", "VH_F_fundus_of_urinary_bladder_base",
               "VH_F_urinary_bladder_neck_smooth_muscle")
    keep = (target, cervix, junction, rectum, *bladder)
    for obj in names.values():
        paint(obj, BONE)
    for name, color in ((target, ROSE), (cervix, GOLD), (junction, GOLD), (rectum, DUSK),
                        *((name, TEAL) for name in bladder)):
        paint(names[name], color)
    side = (1, -.21, .16)
    alternate = (-1, -.24, .16)
    return [
        ("all", side, None, None, True),
        ("selected", side, None, keep, True),
        ("detail", side, keep, keep, True),
        ("alternate", alternate, keep, keep, False),
    ]


def workshop(names):
    heart = "Heart | source surface"
    liver = "Liver | source surface"
    right = tuple(f"Lung {part} Lobe Right | source surface" for part in ("Upper", "Middle", "Lower"))
    left = tuple(f"Lung {part} Lobe Left | source surface" for part in ("Upper", "Lower"))
    keep = (heart, liver, *right, *left)
    for obj in names.values():
        paint(obj, BONE)
    for name, color in ((heart, ROSE), (liver, GOLD), *((name, DUSK) for name in right),
                        *((name, TEAL) for name in left)):
        paint(names[name], color)
    anterior = (.23, -1, .12)
    rear = (-.59, 1, .16)
    return [
        ("all", anterior, keep, None, True),
        ("selected", anterior, keep, keep, True),
        ("reverse", rear, keep, keep, True),
    ]


def pancreas(names):
    key_path = HERE.parents[2] / "models/pancreas/provenance/hra-female-context-r04/explicit-region-key.json"
    roles = json.loads(key_path.read_text())["rows"]
    ducts = tuple(r["source_mesh_name"] for r in roles if r["illustrative_display_role"] == "duct")
    duodenum = tuple(r["source_mesh_name"] for r in roles if r["illustrative_display_role"] == "duodenum")
    ductless = tuple(n for n in names if n not in ducts)
    if not ducts or not duodenum:
        raise ValueError("Expected named duct and duodenal selections")
    first = (.23, -1, .12)
    second = (-.59, 1, .33)
    isolated_ducts = [(f"role-{i}", first, None, (name,), True) for i, name in enumerate(ducts)]
    return [
        ("all", first, None, None, True),
        ("selected", first, None, ductless, True),
        ("reverse", second, None, ductless, True),
        *isolated_ducts,
    ]


def diaphragm(names):
    return [
        ("front", (0, -1, 0), None, None, False),
        ("above", (0, -.23, 1), None, None, False),
        ("below", (0, -.25, -1), None, None, False),
    ]


def raw_heart(scene):
    data = HEART_SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest() != HEART_SOURCE_SHA:
        raise ValueError("Wrong retained heart declaration")
    source = json.loads(data)
    # Workshop's documented RAS-mm to Blender-m conversion.
    vertices = [(-r / 1000, -(a - 155) / 1000, (s - 430) / 1000)
                for r, a, s in source["vertices"]]
    mesh = bpy.data.meshes.new("s1233 retained source triangles")
    # The documented axis conversion has positive determinant.
    mesh.from_pydata(vertices, [], source["faces"])
    mesh.update()
    obj = bpy.data.objects.new("s1233 retained source shell", mesh)
    scene.collection.objects.link(obj)
    return obj


def heart(names):
    reference = ("s1233 retained source shell",)
    control = ("Heart | source surface",)
    ante = (.23, -1, .12)
    reverse = (-.59, 1, .33)
    return [("control", ante, None, control, False), ("source", ante, None, reference, False),
            ("control-reverse", reverse, None, control, False),
            ("source-reverse", reverse, None, reference, False)]


SELECTIONS = {"swirendo_fdi31": dental, "penis": penis, "vagina_hra": vagina,
              "anatomy-workshop-r1": workshop, "pancreas": pancreas,
              "diaphragm": diaphragm, "heart": heart}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    # Compatibility position for the previous camera module's CLI initializer.
    parser.add_argument("camera_output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--asset", choices=SELECTIONS, action="append")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    tools = load_camera_tools()
    controls = json.loads(CONTROL.read_text())
    args.output.mkdir(exist_ok=False, parents=True)
    result = {"blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(), "assets": {}}
    for key in args.asset or SELECTIONS:
        row = controls[key]
        scene, meshes = tools.open_model(row)
        frame = scene.frame_current
        if key == "anatomy-workshop-r1":
            scene, meshes = snapshot_visible_meshes(meshes)
        if key == "heart":
            meshes.append(raw_heart(scene))
            bpy.context.view_layer.update()
        camera = tools.configure(scene)
        for obj in meshes:
            for material in obj.data.materials:
                if material and material.node_tree:
                    shader = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                    if shader and not shader.inputs["Base Color"].is_linked:
                        obj.color = shader.inputs["Base Color"].default_value
        views = SELECTIONS[key]({obj.name: obj for obj in meshes})
        result["assets"][key] = {
            "export": {k: row[k] for k in ("path", "sha256", "bytes")},
            "frame": frame,
            "views": record_shots(key, args.output, views, tools, scene, meshes, camera),
        }
        if key == "heart":
            result["assets"][key]["source"] = {"path": str(HEART_SOURCE), "sha256": HEART_SOURCE_SHA}
        (args.output / "selection-render.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
