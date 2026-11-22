"""Build native exports for the parotid locator and salivary lessons."""

import argparse
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
from z_anatomy import load_native_surfaces, new_export_directory


def paired(*names):
    return tuple(f"{name}.{side}" for name in names for side in ("r", "l"))


PAROTID_PAIR = paired("Parotid gland")
PRIMARY = PAROTID_PAIR + paired("Submandibular gland", "Sublingual gland", "Parotid duct")
CONTEXT = ("Mandible",) + paired(
    "Mylohyoid muscle", "Superficial part of masseter", "Genioglossus muscle"
)
REJECTED = paired("Submandibular duct")

COLORS = {
    "Parotid gland": (0.42, 0.31, 0.22),
    "Submandibular gland": (0.34, 0.28, 0.20),
    "Sublingual gland": (0.44, 0.36, 0.22),
    "Parotid duct": (0.54, 0.49, 0.35),
    "Submandibular duct": (0.54, 0.49, 0.35),
    "Mandible": (0.22, 0.25, 0.28),
    "Mylohyoid muscle": (0.22, 0.13, 0.12),
    "Superficial part of masseter": (0.22, 0.13, 0.12),
    "Genioglossus muscle": (0.22, 0.13, 0.12),
}


def teaching_material(name, color, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return material


def display_object(name, surface, material, *, copy_mesh=False):
    mesh = surface.mesh.copy() if copy_mesh else surface.mesh
    mesh.materials.clear()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj.matrix_world = surface.matrix_world
    bpy.context.collection.objects.link(obj)
    return obj


def export_selection(path, objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    result = bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_animations=False, export_extras=True, export_texcoords=False,
    )
    if result != {"FINISHED"} or not path.is_file():
        raise RuntimeError(f"GLB export did not finish: {path.name}")


def build(source, output, *, edit=None):
    with new_export_directory(output) as staged:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        surfaces = load_native_surfaces(source, PRIMARY + CONTEXT, edit=edit)
        objects = {}
        for name, surface in surfaces.items():
            material = teaching_material(
                f"{name} teaching display", COLORS[name.split(".")[0]], 0.8
            )
            obj = display_object(f"{name} source display", surface, material)
            obj["source_object"] = name
            obj["role"] = "primary" if name in PRIMARY else "same-source context"
            objects[name] = obj

        export_selection(staged / "glands-and-parotid-ducts.glb", [objects[name] for name in PRIMARY])
        export_selection(staged / "same-source-context.glb", list(objects.values()))
        rose = teaching_material("Illustrative gland rose, not measured tissue", (0.46, 0.16, 0.13), 0.62)
        exterior = []
        for name in sorted(PAROTID_PAIR):
            identifier = name.replace(" ", "_")
            obj = display_object(f"{identifier} {name}", surfaces[name], rose, copy_mesh=True)
            obj.data.name = identifier
            obj["source_file_id"] = identifier
            obj["source_concept_id"] = "Z-Anatomy named object"
            obj["source_coordinates"] = "Z-Anatomy native world coordinates, no centering or cross-atlas registration"
            exterior.append(obj)
        export_selection(staged / "parotid-pair.glb", exterior)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    build(args.source, args.out)


if __name__ == "__main__":
    main()
