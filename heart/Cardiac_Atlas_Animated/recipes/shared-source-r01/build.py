"""Export the static arch and animated wall studies from one editable Cardiac Atlas."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parents[1]
ROOT = ATLAS.parents[1]
SOURCE = ATLAS / "Cardiac_Atlas_Animated_Source.blend"
NATIVE_UNIT_M = 0.025
CONTROL = "HEART CONTROL • material + cutaway + pulse"
AORTA = "Aorta | root, ascending, arch and descending"
LV = "LV | complete wall"
CLIP = "CardiacCycle_75BPM"
FIRST_FRAME = 1
LAST_FRAME = 25
FPS = 30
STATIC = "cardiac-static-ed.glb"
MOTION = "ventricular-wall-motion.glb"
FULL = "full-atlas.glb"
sys.path.insert(0, str(ROOT))
from tools.glb import decode, encode


def identity(path):
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def exterior_meshes():
    return [
        obj for obj in bpy.context.scene.objects
        if obj.type == "MESH"
        and any(col.name[:2] in {"01", "02", "03", "04", "05", "06"} for col in obj.users_collection)
        and "anterior section" not in obj.name
        and "pericardium" not in obj.name.lower()
    ]


def use_clinical_materials(objects):
    palette = {}
    for obj in objects:
        for slot in obj.material_slots:
            source = slot.material
            if source is None:
                continue
            if source.name not in palette:
                material = bpy.data.materials.new(f"Clinical | {source.name}")
                material.use_nodes = True
                material.diffuse_color = source.diffuse_color
                shader = material.node_tree.nodes["Principled BSDF"]
                shader.inputs["Base Color"].default_value = source.diffuse_color
                shader.inputs["Roughness"].default_value = 0.38
                palette[source.name] = material
            slot.link = "OBJECT"
            slot.material = palette[source.name]


def sample_rig(objects, scene):
    keyed = [obj for obj in objects if obj.data.shape_keys]
    samples = {obj.name: [] for obj in keyed}
    for frame in range(FIRST_FRAME, LAST_FRAME + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for obj in keyed:
            samples[obj.name].append([key.value for key in obj.data.shape_keys.key_blocks[1:]])
    return samples


def bake_leaflet_modifiers(obj):
    """Evaluate the source modifier stack individually on each morph target."""
    shape_names = [key.name for key in obj.data.shape_keys.key_blocks]
    positions = []
    base = None
    for index in range(len(shape_names)):
        keys = obj.data.shape_keys.key_blocks
        for key in keys[1:]:
            key.value = 0.0
        if index:
            keys[index].value = 1.0
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh = bpy.data.meshes.new_from_object(
            obj.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph,
        )
        positions.append([vertex.co.copy() for vertex in mesh.vertices])
        if index == 0:
            base = mesh
        else:
            bpy.data.meshes.remove(mesh)
    obj.modifiers.clear()
    obj.data = base
    for name, coords in zip(shape_names, positions, strict=True):
        shape = obj.shape_key_add(name=name)
        if len(shape.data) != len(coords):
            raise ValueError(f"Modifier topology changed between targets on {obj.name}")
        for vertex, co in zip(shape.data, coords, strict=True):
            vertex.co = co


def bake_rig(objects, samples):
    from bpy_extras.anim_utils import action_get_channelbag_for_slot

    for obj in objects:
        if obj.name not in samples:
            continue
        obj.data.shape_keys.animation_data_clear()
        if obj.modifiers:
            bake_leaflet_modifiers(obj)
        keys = obj.data.shape_keys
        for frame, values in enumerate(samples[obj.name], FIRST_FRAME):
            for key, value in zip(keys.key_blocks[1:], values, strict=True):
                key.value = value
                key.keyframe_insert("value", frame=frame, group="Cardiac cycle")
        track = keys.animation_data
        track.action.name = f"Cardiac cycle | {obj.name}"
        channelbag = action_get_channelbag_for_slot(track.action, track.action_slot)
        for curve in channelbag.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"


def export(path, objects, source, *, animated):
    scene = bpy.context.scene
    scene.frame_set(FIRST_FRAME)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    if set(bpy.context.selected_objects) != set(objects):
        raise ValueError("One or more required objects could not be selected")
    result = bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_animations=animated,
        export_animation_mode="SCENE",
        export_anim_scene_split_object=False,
        export_frame_range=True,
        export_force_sampling=True,
        export_skins=False,
        export_morph=animated,
        export_morph_normal=animated,
        export_apply=not animated,
        export_yup=True,
        export_texcoords=False,
        export_extras=True,
        export_anim_slide_to_zero=True,
    )
    if result != {"FINISHED"}:
        raise ValueError(f"Exporter failed for {path.name}: {result}")
    document, binary = decode(path.read_bytes())
    if len(document["scenes"]) != 1 or (len(document.get("animations", [])) != int(animated)):
        raise ValueError(f"Unexpected scene or animation inventory in {path.name}")
    if {node["name"] for node in document["nodes"] if "mesh" in node} != {obj.name for obj in objects}:
        raise ValueError(f"Exported mesh names differ from the declared selection in {path.name}")
    named = {"units": "metres", "native_BU_mm": 25,
             "axes": "+X patient left, +Y superior, +Z anterior", "reference_phase": "End diastole",
             "clinical_status": "Procedural educational idealization",
             "editable_source": source}
    if animated:
        document["animations"][0]["name"] = CLIP
        named["cycle_seconds"] = (LAST_FRAME - FIRST_FRAME) / FPS
    document["asset"]["extras"] = named
    nodes = document["nodes"]
    gltf_scene = document["scenes"][0]
    gltf_scene["nodes"], children = [len(nodes)], gltf_scene["nodes"]
    nodes.append({"name": "UNITS | 25 mm per native BU", "scale": [NATIVE_UNIT_M] * 3, "children": children})
    path.write_bytes(encode(document, binary))
    return {
        **identity(path),
        "meshNodes": len(objects),
        "triangles": sum(document["accessors"][p["indices"]]["count"] // 3
                         for mesh in document["meshes"] for p in mesh["primitives"]),
        "primitives": sum(len(mesh["primitives"]) for mesh in document["meshes"]),
        "channels": len(document.get("animations", [{}])[0].get("channels", [])),
    }


def build(source, output, full_model):
    source_id = identity(source)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=True)
    scene = bpy.context.scene
    if abs(scene.unit_settings.scale_length - NATIVE_UNIT_M) > 1e-9:
        raise ValueError("Expected the original 25 mm native unit")
    scene.frame_start, scene.frame_end, scene.render.fps = FIRST_FRAME, LAST_FRAME, FPS
    scene.render.fps_base = 1.0
    control = bpy.data.objects[CONTROL]
    control["cutaway"] = 0
    scene.frame_set(FIRST_FRAME)
    bpy.context.view_layer.update()
    exterior = exterior_meshes()
    by_name = {obj.name: obj for obj in exterior}
    focus = [by_name[LV], by_name[AORTA]]
    for collection in bpy.data.collections:
        collection.hide_viewport = False
    for obj in exterior:
        for prop in ("hide_render", "hide_viewport"):
            obj.driver_remove(prop)
        obj.hide_viewport = False
        obj.hide_render = False
        obj.hide_set(False)
    animated = exterior if full_model else focus
    samples = sample_rig(animated, scene)
    use_clinical_materials(exterior)
    results = [export(output / STATIC, exterior, source_id, animated=False)]
    bake_rig(animated, samples)
    results.append(export(output / MOTION, focus, source_id, animated=True))
    if full_model:
        results.append(export(output / FULL, exterior, source_id, animated=True))
    return {"blender": bpy.app.version_string, "source": source_id, "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Fresh output directory")
    parser.add_argument("--source", type=Path, default=SOURCE, help="Trusted editable Cardiac Atlas file")
    parser.add_argument("--full-model", action="store_true", help="Also write the complete animated GLB for QA")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    output = args.out.resolve()
    output.mkdir(parents=True)
    result = build(args.source.resolve(), output, args.full_model)
    (output / "build.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
