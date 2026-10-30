"""Export named Z-Anatomy objects, preserving their evaluated native frame.

Run with Blender 4.3.2 --background --factory-startup --python build.py -- ...
No upstream scripts are executed. The source archive stays external.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

SOURCE_SHA = "9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd"
NAMES = [f"{part}.{side}" for part in ("Testis", "Epididymis")
         for side in ("r", "l")]
COLORS = {"Testis": (.47, .32, .23), "Epididymis": (.37, .16, .14),
          "Ductus deferens": (.67, .60, .42)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--surface-level", type=int, choices=(1, 2), default=2)
    parser.add_argument("--include-deferens", action="store_true",
                        help="Diagnostic source context only; excluded from the accepted bounded study")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if sha(args.source) != SOURCE_SHA:
        raise ValueError("Pinned source hash mismatch")
    if args.out.exists():
        raise FileExistsError("Output must be a new directory")
    args.out.mkdir(parents=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    names = NAMES + (["Ductus deferens.r", "Ductus deferens.l"] if args.include_deferens else [])
    with bpy.data.libraries.load(str(args.source), link=False) as (available, selected):
        if not set(names).issubset(available.objects):
            raise ValueError("Missing required named source objects")
        selected.objects = names
    originals = list(selected.objects)
    for obj in originals:
        bpy.context.collection.objects.link(obj)
    # Source delta transforms must be evaluated before reading matrix_world.
    bpy.context.view_layer.update()
    rows = []
    for obj in originals:
        modifiers = [{"name": m.name, "type": m.type,
                      "viewport": getattr(m, "levels", None),
                      "render": getattr(m, "render_levels", None)} for m in obj.modifiers]
        for modifier in obj.modifiers:
            if modifier.type == "SUBSURF":
                modifier.levels = args.surface_level
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = bpy.data.meshes.new_from_object(evaluated)
        mesh.calc_loop_triangles()
        display = bpy.data.objects.new(obj.name + " native study", mesh)
        display.matrix_world = obj.matrix_world.copy()
        bpy.context.collection.objects.link(display)
        display["source_object"] = obj.name
        display["source_sha256"] = SOURCE_SHA
        display["scope"] = "Static gross relationship; no lumen or functional claim"
        display["license"] = "Z-Anatomy CC BY-SA 4.0; retain upstream attribution"
        color = COLORS[obj.name.rsplit(".", 1)[0]]
        material = bpy.data.materials.new(obj.name + " illustrative color")
        material.diffuse_color = (*color, 1)
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*color, 1)
        shader.inputs["Roughness"].default_value = .68
        mesh.materials.clear()
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.material_index = 0
        rows.append({"name": obj.name, "type": obj.type,
                     "native_matrix": [list(v) for v in obj.matrix_world],
                     "source_modifiers": modifiers,
                     "vertices": len(mesh.vertices), "triangles": len(mesh.loop_triangles),
                     "curve_bevel_depth": obj.data.bevel_depth if obj.type == "CURVE" else None,
                     "curve_capped": obj.data.use_fill_caps if obj.type == "CURVE" else None})
    for obj in originals:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene["scope"] = ("Native testis/epididymis/deferens gross relationship, static"
                      if args.include_deferens else "Native testis/epididymis gross form; deferens excluded")
    scene["limitations"] = "No scrotum, lumen, flow, full-tract, clinical or runtime validation"
    scene["coordinates"] = "Unscaled Z-Anatomy native world; no cross-atlas registration"
    scene["attribution"] = "Z-Anatomy CC BY-SA 4.0; BodyParts3D DBCLS historical CC BY-SA 2.1 Japan"
    bpy.ops.object.select_all(action="SELECT")
    glb = args.out / "testicular-region.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True,
                             export_animations=False, export_extras=True)
    receipt = {"source_sha256": SOURCE_SHA, "artifact_sha256": sha(glb),
               "artifact_bytes": glb.stat().st_size, "surface_level": args.surface_level,
               "blender_version": bpy.app.version_string, "objects": rows,
               "changes": "Selected source objects, evaluated modifiers/curves, display materials; no manual mesh repair or repositioning"}
    (args.out / "build.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
