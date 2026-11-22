"""Replay regional teaching inspections on exact GLBs with Blender 5.2.3."""
import json
from pathlib import Path
import runpy

from mathutils import Vector

BASE_RENDERER = Path(__file__).resolve().parents[1] / "2026-11-22-body-cardiovascular-digestive-endocrine/render.py"
DETAILS = {
    "A08": ("Calcaneus.r", (.9, 1, .03), 2.0),
    "A09": ("Articular capsule of elbow", (.35, -1, .45), 1.55),
    "A10": ("Anterior cruciate ligament.r", (.25, -1, .28), 1.8),
    "A14": ("Infraspinatus muscle.r", (.25, 1, .2), 1.5),
    "A16": ("Articular capsule of glenohumeral", (.4, -1, .5), 1.75),
    "A18": ("Z-Anatomy source auricle", (1, .3, .15), 1.0),
    "A22": ("Scaphoid bone.r", (.20, -1, .35), 4.8),
    "A23": ("Hip bone", (-.35, 1, .06), 1.1),
    "A24": ("Representative dorsal root upper 4 side1", (.08, 1, .40), 2.0),
    "A25": ("Ulna.r", (.65, 1, .4), 1.0),
}


def find(meshes, prefix):
    matches = [obj for obj in meshes if obj.name.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one mesh matching {prefix}")
    return matches[0]


def main():
    helpers = runpy.run_path(str(BASE_RENDERER))
    helpers["main"]()
    output = helpers["OUTPUT"]
    receipt = output / "render.json"
    report = json.loads(receipt.read_text())
    for row in report["rows"]:
        if row["id"] not in DETAILS and row["id"] != "A03":
            continue
        scene, meshes = helpers["open_model"](row)
        camera = helpers["configure"](scene)
        if row["id"] == "A03":
            direction = (0.23, -1, 0.12)
            groups = {
                "whole": meshes,
                "tissue": [find(meshes, prefix) for prefix in (
                    "Yao_follicles", "Yao_medulla_of_lymph_node", "Yao_paracortex",
                )],
            }
            groups["tinted"] = groups["tissue"]
            colors = {
                "Yao_follicles": (0.73, 0.55, 0.20, 1),
                "Yao_medulla_of_lymph_node": (0.31, 0.55, 0.62, 1),
                "Yao_paracortex": (0.51, 0.26, 0.42, 1),
            }
            for obj in groups["tissue"]:
                obj.color = colors[obj.name]
            for name, visible in groups.items():
                view = helpers["shot"](
                    scene, camera, meshes, direction, output / f"A03-{name}.png", False, visible,
                )
                if name == "tinted":
                    scene.display.shading.color_type = "OBJECT"
                    helpers["bpy"].ops.render.render(write_still=True)
                    view.update(helpers["identity"](output / view["file"]))
                    view["illustrativeColors"] = colors
                row["views"].append(view)
            continue
        prefix, direction, factor = DETAILS[row["id"]]
        target = find(meshes, prefix)
        rotation = Vector(direction).to_track_quat("Z", "Y")
        if row["id"] in {"A18", "A25"}:
            coords = [target.matrix_world @ vertex.co for vertex in target.data.vertices]
            if row["id"] == "A18":
                middle = sum(point.x for point in coords) / len(coords)
                coords = [point for point in coords if point.x >= middle]
            else:
                upper_z = max(point.z for point in coords)
                depth = upper_z - min(point.z for point in coords)
                coords = [point for point in coords if point.z >= upper_z - 0.26 * depth]
        else:
            coords = [target.matrix_world @ Vector(point) for point in target.bound_box]
        projected = [rotation.inverted() @ point for point in coords]
        lower = Vector([min(point[i] for point in projected) for i in range(3)])
        upper = Vector([max(point[i] for point in projected) for i in range(3)])
        orthographic_scale = max((upper - lower)[:2]) * factor
        center = (lower + upper) / 2
        depth = max((rotation.inverted() @ (obj.matrix_world @ Vector(point))).z
                    for obj in meshes for point in obj.bound_box)
        center.z = depth + max(orthographic_scale * 3, 0.2)
        camera.location = rotation @ center
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = rotation
        camera.data.clip_start = 0.00001
        camera.data.clip_end = 100
        camera.data.ortho_scale = orthographic_scale
        shading = scene.display.shading
        shading.color_type = "SINGLE"
        shading.single_color = helpers["NEUTRAL"]
        scenes = {"detail": meshes}
        if row["id"] == "A10":
            scenes["inspection"] = [obj for obj in meshes if not obj.name.startswith((
                "Articular capsule of knee", "Infrapatellar fat pad", "Femur.r", "Patella.r",
            ))]
        for name, visible in scenes.items():
            for obj in meshes:
                obj.hide_render = obj not in visible
            file = output / f"{row['id']}-{name}.png"
            scene.render.filepath = str(file)
            helpers["bpy"].ops.render.render(write_still=True)
            row["views"].append({
                "file": file.name, **helpers["identity"](file), "direction": direction,
                "camera": list(camera.location), "orthoScale": orthographic_scale,
                "palette": False, "visible": sorted(obj.name for obj in visible),
            })
    receipt.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
