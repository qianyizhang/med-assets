"""Clean import and evaluated geometry inspection for Blender recipes."""

import bpy


def scene_import(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    scene = bpy.context.scene
    objects = {o.name: o for o in scene.objects if o.type == "MESH"}
    if not objects:
        raise ValueError(f"No imported meshes for {path}")
    stats = {}
    for n, o in sorted(objects.items()):
        o.data.calc_loop_triangles()
        stats[n] = {
            "transform": [list(r) for r in o.matrix_world],
            "materials": [slot.name for slot in o.material_slots],
            "triangles": len(o.data.loop_triangles),
            "shapeKeys": [key.name for key in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],
        }
        for slot in o.material_slots:
            material = slot.material
            if material and material.node_tree:
                for shader in material.node_tree.nodes:
                    if shader.type == "BSDF_PRINCIPLED" and not shader.inputs["Base Color"].is_linked:
                        material.diffuse_color = shader.inputs["Base Color"].default_value
    return scene, objects, stats


def evaluated_positions(obj):
    """Read evaluated mesh vertices in the active Blender scene's world frame."""
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]
