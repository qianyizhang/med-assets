"""Capture task-focused views from the three pinned teaching assets in Blender."""

import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lib"))
from med_assets.blender_scene import evaluated_positions


OUTPUT = Path(sys.argv[sys.argv.index("--") + 1])
OWNER = Path("reviews/teaching-assessments")
BATCH = {
    "lymph": ("lymphatic-musculoskeletal-nervous", "models/lymph_node/"),
    "breath": ("respiratory", "body/breathing/Breathing_Assembly.blend"),
    "heart": ("body-cardiovascular-digestive-endocrine", "heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb"),
    "parathyroids": ("body-cardiovascular-digestive-endocrine", "models/parathyroids/exports/z-localization-r01/parathyroids_native.glb"),
    "urethra": ("dental-reproductive-skin-urinary", "models/urethra_male/exports/z-native-context-r01/"),
}
TISSUE = ("Yao_follicles", "Yao_paracortex", "Yao_medulla_of_lymph_node")
DOME = "Authored schematic diaphragm"
LIVER = "Liver | source surface"
LV = "LV | complete wall"
AORTA = "Aorta | root, ascending, arch and descending"
COLORS = {
    TISSUE[0]: (.89, .69, .23, 1),
    TISSUE[1]: (.59, .36, .53, 1),
    TISSUE[2]: (.40, .64, .79, 1),
    DOME: (.87, .69, .44, 1),
    LIVER: (.54, .28, .25, 1),
    LV: (.68, .30, .31, 1),
    AORTA: (.64, .51, .41, 1),
}
SIZE = 720
NEUTRAL = (.56, .54, .49, 1)


def identity(file):
    return {"sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "bytes": file.stat().st_size}


def baseline_asset(task):
    batch, prefix = BATCH[task]
    record = json.loads((OWNER / f"2026-11-22-{batch}/campaign-assessments.json").read_text())
    (asset,) = [row["export"] for row in record["assessments"] if row["export"]["path"].startswith(prefix)]
    return asset


def opening(asset):
    path = Path(asset["path"]).resolve()
    if identity(path) != {key: asset[key] for key in ("bytes", "sha256")}:
        raise ValueError(f"Wrong export revision: {path}")
    if path.suffix == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    scene = bpy.context.scene
    meshes = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.show_cavity = False
    shading.show_shadows = False
    shading.color_type = "OBJECT"
    shading.show_specular_highlight = True
    camera = bpy.data.objects.new("Review camera", bpy.data.cameras.new("Review camera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_start = .00001
    camera.data.clip_end = 8
    for name, mesh in meshes.items():
        mesh.color = COLORS.get(name, (.77, .59, .60, 1) if name.startswith("Lung ") else NEUTRAL)
    return scene, camera, meshes


def take(scene, camera, meshes, label, shown, target, direction, scale):
    for name, mesh in meshes.items():
        mesh.hide_render = name not in shown
    if not set(shown) <= meshes.keys():
        raise ValueError(f"Missing selected meshes: {set(shown) - meshes.keys()}")
    camera.location = Vector(target) + Vector(direction).normalized() * scale * 3
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = scale
    shot = OUTPUT / f"{label}.png"
    scene.render.filepath = str(shot.resolve())
    bpy.ops.render.render(write_still=True)
    return {
        "file": shot.name, **identity(shot), "frame": scene.frame_current, "visibleNodes": sorted(shown),
        "cameraM": list(camera.location), "targetM": list(target), "orthoScaleM": scale,
    }


def lymph_node():
    asset = baseline_asset("lymph")
    scene, camera, meshes = opening(asset)
    run = json.loads((OWNER / "2026-11-22-lymphatic-musculoskeletal-nervous/render-evidence.json").read_text())
    (row,) = [row for row in run["rows"] if row["id"] == "A03"]
    pinned = next(v for v in row["views"] if v["file"] == "A03-tinted.png")
    capsule = "Yao_capsule_of_lymph_node"
    shell = meshes[capsule]
    points = [shell.matrix_world @ Vector(point) for point in shell.bound_box]
    shots = []
    for angle, direction in (("primary", pinned["direction"]), ("reverse", (-.62, -.55, -.41))):
        target, scale = frame_points(points, direction)
        for state, shown in (("capsule", [capsule]), ("interior", TISSUE)):
            shots.append(take(scene, camera, meshes, f"lymph-{angle}-{state}", shown, target, direction, scale))
    return {"asset": asset, "views": shots}


def breathing():
    asset = baseline_asset("breath")
    scene, camera, meshes = opening(asset)
    pinned = json.loads((OWNER / "2026-11-22-respiratory/motion-compare.json").read_text())
    baseline = next(v for v in pinned["views"] if v["file"] == "motion-1-detail-side-palette.png")
    lungs = {name for name in meshes if name.startswith("Lung ")}
    if len(lungs) != 5:
        raise ValueError("Expected five source lung lobes")
    views = []
    for frame in (1, 49):
        scene.frame_set(frame)
        for name, nodes in (("context", lungs | {DOME, LIVER}), ("dome", {DOME})):
            target = Vector(baseline["targetM"])
            direction = Vector(baseline["cameraM"]) - target
            views.append(take(scene, camera, meshes, f"breath-{frame}-{name}", nodes, target,
                              direction, baseline["orthoScaleM"]))
    return {"asset": asset, "views": views}


def frame_points(points, direction):
    rotation = Vector(direction).to_track_quat("Z", "Y")
    projected = [rotation.inverted() @ position for position in points]
    lower = Vector([min(point[i] for point in projected) for i in range(3)])
    upper = Vector([max(point[i] for point in projected) for i in range(3)])
    target = rotation @ ((lower + upper) / 2)
    scale = max((upper - lower)[:2]) * 1.15
    return target, scale


def cardiac():
    asset = baseline_asset("heart")
    scene, camera, meshes = opening(asset)
    scene.frame_set(0)
    positions = {name: evaluated_positions(meshes[name]) for name in (LV, AORTA)}
    points = [p for group in positions.values() for p in group]
    direction = (.72, .67, .15)
    target, scale = frame_points(points, direction)
    # Import evaluated animation at its actual fps, covering the full 0.8 s clip.
    fps = scene.render.fps / scene.render.fps_base
    displacements = {}
    for frame in range(round(.8 * fps) + 1):
        scene.frame_set(frame)
        displacements[frame] = {
            name: max((a - b).length for a, b in zip(before, evaluated_positions(meshes[name]), strict=True)) * 1000
            for name, before in positions.items()
        }
    peak = max(displacements, key=lambda frame: displacements[frame][LV])
    views = []
    for frame in (0, peak):
        scene.frame_set(frame)
        for name, nodes in (("context", [LV, AORTA]), ("lv", [LV])):
            views.append(take(scene, camera, meshes, f"heart-{frame}-{name}", nodes, target, direction, scale))
    return {"asset": asset, "views": views, "fps": fps, "peakFrame": peak,
            "maxWorldVertexDisplacementMm": displacements[peak]}


def parathyroids():
    atlas = Path("reviews/parathyroids/2026-10-25-localization-r01/record.json")
    targets = baseline_asset("parathyroids")
    context_file = Path(targets["path"]).with_name("parathyroids_thyroid_context.glb")
    context = {"path": context_file.as_posix(), "bytes": 0,
               "sha256": json.loads(atlas.read_text())["context_glb_sha256"]}
    context["bytes"] = context_file.stat().st_size
    scene, camera, meshes = opening(context)
    direction = (0, 1, 0)
    locations = {name: evaluated_positions(mesh) for name, mesh in meshes.items()}
    target, scale = frame_points([p for group in locations.values() for p in group], direction)
    for name, mesh in meshes.items():
        mesh.color = (.85, .62, .30, 1) if "parathyroid" in name.lower() else (.54, .57, .60, 1)
    companion = take(scene, camera, meshes, "parathyroids-context", meshes, target, direction, scale)
    scene, camera, meshes = opening(targets)
    for name, mesh in meshes.items():
        mesh.color = (.85, .62, .30, 1)
        difference = max((a - b).length for a, b in
                         zip(locations[name], evaluated_positions(mesh), strict=True))
        if difference > 1e-7:
            raise ValueError(f"Source position drift for {name}: {difference} m")
    standalone = take(scene, camera, meshes, "parathyroids-targets", meshes, target, direction, scale)
    return {"asset": targets, "companion": context, "views": [standalone, companion]}


def urethra():
    asset = baseline_asset("urethra")
    scene, camera, meshes = opening(asset)
    binding_path = Path("reviews/urethra_male/2026-10-26-native-context-r01/translucent-view-bindings.json")
    binding = next(v for v in json.loads(binding_path.read_text()) if v["file"] == "context-oblique.png")
    if binding["glb_sha256"] != asset["sha256"]:
        raise ValueError("Urethra view asset mismatch")
    (route,) = [name for name, mesh in meshes.items() if mesh.get("source_object", name) == "Urethra"]
    meshes[route].color = (.93, .72, .36, 1)
    target = Vector(binding["target"])
    direction = Vector(binding["camera"]) - target
    scale = binding["ortho_scale"]
    return {"asset": asset, "views": [
        take(scene, camera, meshes, "urethra-opaque", meshes, target, direction, scale),
        take(scene, camera, meshes, "urethra-path", [route], target, direction, scale),
    ]}


def main():
    OUTPUT.mkdir(exist_ok=False, parents=True)
    result = {
        "blender": bpy.app.version_string,
        "build": bpy.app.build_hash.decode(),
        "engine": "Blender Workbench, orthographic, Standard, studio light, illustrative object colors",
        "resolution": [SIZE, SIZE],
        "review": {},
    }
    for label, render in (("lymph", lymph_node), ("breath", breathing), ("heart", cardiac),
                          ("parathyroids", parathyroids), ("urethra", urethra)):
        result["review"][label] = render()
        (OUTPUT / "render.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
