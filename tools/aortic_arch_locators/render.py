"""New documented cameras for exact-source arch callouts, not historical pixel replay."""
import argparse
import array
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source import GROUPS, decode, inventory, positions, require, sha

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
raw = args.source.read_bytes()
record = inventory(raw)
args.output.mkdir(parents=True, exist_ok=False)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.source))
objects = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
require(set(objects) == {r["nodeName"] for r in record["nodes"]}, "Imported node inventory differs")


def signature(obj):
    data = array.array("f", [0]) * (len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", data)
    loops = array.array("i", [0]) * len(obj.data.loops)
    obj.data.loops.foreach_get("vertex_index", loops)
    return {"vertices": len(obj.data.vertices), "vertexBytesSha256": sha(data.tobytes()),
            "indexBytesSha256": sha(loops.tobytes()),
            "matrix": [list(row) for row in obj.matrix_world], "polygons": len(obj.data.polygons),
            "materials": [{"name": m.name, "nodes": [
                {"name": n.name, "baseColor": list(n.inputs["Base Color"].default_value),
                 "roughness": n.inputs["Roughness"].default_value}
                for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]}
                for m in obj.data.materials]}


before = {name: signature(o) for name, o in objects.items()}
doc, binary = decode(raw)
coordinate_checks = []
for row in record["nodes"]:
    obj = objects[row["nodeName"]]
    require(len(obj.data.vertices) == row["vertices"], "Imported vertex count changed")
    # The retained single-material export preserves the position multiset. Test
    # the importer basis against source coordinates, not a visually guessed side.
    source_xyz = sorted((x, -z, y) for x, y, z in positions(doc, binary, row["meshIndex"]))
    imported_xyz = sorted(tuple(obj.matrix_world @ v.co) for v in obj.data.vertices)
    error = max(abs(a - b) for p, q in zip(source_xyz, imported_xyz) for a, b in zip(p, q))
    require(error < 1e-6, "Source/import coordinate mapping differs")
    coordinate_checks.append({"nodeName": row["nodeName"], "maxCoordinateErrorM": error})
scene = bpy.context.scene
scene.world = bpy.data.worlds.new("LocatorWorld")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (.055, .070, .086, 1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = .45
scene.render.engine = "CYCLES"
scene.cycles.device, scene.cycles.samples = "CPU", 32
scene.cycles.use_denoising, scene.cycles.seed = False, 0
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
light_target = Vector((0, -.005, 1.37))
for delta, power, size in [((-0.6, -0.8, .7), 75, .65), ((.7, -.4, .15), 38, .6), ((.2, .6, .4), 60, .5)]:
    bpy.ops.object.light_add(type="AREA", location=light_target + Vector(delta))
    light = bpy.context.object
    light.data.energy, light.data.size = power, size
    light.rotation_euler = (light_target - light.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = "ORTHO"
scene.camera = camera


def project(location):
    p = world_to_camera_view(scene, camera, location)
    return [p.x * 900, (1 - p.y) * 900]


def hit_pixel(x, y):
    deps = bpy.context.evaluated_depsgraph_get()
    local = Vector(((x / 900 - .5) * camera.data.ortho_scale,
                    (.5 - y / 900) * camera.data.ortho_scale, 0))
    direction = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    return scene.ray_cast(deps, camera.matrix_world @ local, direction)


def anchor(group):
    # The target is a search neighborhood, never the final label claim. The
    # final endpoint must ray-hit this exact source-named object at a pixel center.
    x, y, z = group["targetSourceM"]
    target = Vector((x, -z, y))  # glTF Y-up to imported Blender Z-up
    px, py = project(target)
    candidates = []
    for iy in range(max(0, int(py) - 90), min(900, int(py) + 91)):
        for ix in range(max(0, int(px) - 90), min(900, int(px) + 91)):
            hit = hit_pixel(ix + .5, iy + .5)
            if hit[0] and hit[4].name == group["node"]:
                score = (hit[1] - target).length_squared
                candidates.append((score, ix, iy, hit))
    require(candidates, f"No visible anchor for {group['node']}")
    _, ix, iy, hit = min(candidates, key=lambda r: r[:3])
    roundtrip = project(hit[1])
    require(abs(roundtrip[0] - ix - .5) < .01 and abs(roundtrip[1] - iy - .5) < .01,
            "Projection/raycast pixel-center mismatch")
    return {"number": group["number"], "sourceNode": group["node"], "sourceNames": group["sourceNames"],
            "pixel": [ix + .5, iy + .5], "rayHitPolygon": hit[3],
            "hitSourceM": [hit[1].x, hit[1].z, -hit[1].y],
            "projectedHitPixel": roundtrip, "rayHitExactSourceNode": True}


views = []
for name, target, scale in [("overview", Vector((0, 0, 1.19)), .68),
                            ("junction", Vector((0, -.005, 1.385)), .225)]:
    camera.location = target + Vector((0, -1, 0))
    camera.rotation_euler = Vector((0, 1, 0)).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = scale
    bpy.context.view_layer.update()
    anchors = [anchor(group) for group in GROUPS]
    require(anchors[2]["pixel"][0] > anchors[3]["pixel"][0], "Projected source left/right swapped")
    scene.render.filepath = str(args.output / (name + ".png"))
    start = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    p = Path(scene.render.filepath)
    views.append({"view": name, "file": p.name, "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size,
                  "seconds": time.perf_counter() - start, "resolution": [900, 900],
                  "targetBlenderM": list(target), "cameraBlenderM": list(camera.location),
                  "cameraWorldMatrix": [list(row) for row in camera.matrix_world],
                  "orthoScaleM": camera.data.ortho_scale, "anchors": anchors})
require({name: signature(o) for name, o in objects.items()} == before, "Source objects changed during rendering")
require(args.source.read_bytes() == raw, "Source GLB bytes changed")
record.update({"render": {"blender": bpy.app.version_string, "engine": "Cycles CPU", "samples": 32,
               "seed": 0, "denoising": False, "viewTransform": "AgX", "look": scene.view_settings.look,
               "exposure": 0, "gamma": 1}, "imports": before, "sourceToImportCoordinates": coordinate_checks,
               "sourceToImportBasis": "glTF (x, y, z) -> Blender (x, -z, y), compared for all source vertices",
               "views": views,
               "sourceBytesAndImportedGeometryUnchanged": True,
               "cameraProvenance": "New recorded +Z-source / +Y-up orthographic cameras. Historical recipes explicitly unbundled; not historical pixel replay.",
               "scope": "Exact source-node raycast/projection and offline static images only. No clinical or browser approval."})
(args.output / "render.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print("PASS: source identity, 9 meshes/15 structures, laterality and 8 source-node raycast anchors")
