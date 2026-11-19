"""Export independent endocrine teaching groups with checked named parts."""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKSHOP = HERE.parents[1] / "workshop-s1233"
SOURCE = HERE.parent / "r01" / "endocrine-locator.glb"
sys.path.insert(0, str(WORKSHOP))
from build import add_mesh, check_import, sha256
from teaching_scene import colorize, export, load_meshes, material


def geometry(obj):
    obj.data.calc_loop_triangles()
    points = [tuple(round(value, 6) for value in obj.matrix_world @ v.co) for v in obj.data.vertices]
    return Counter(tuple(sorted(points[i] for i in tri.vertices)) for tri in obj.data.loop_triangles)


def atlas_neck(output, pin):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objects = load_meshes(SOURCE.relative_to(ROOT), pin, select=lambda name: name.startswith("Neck -"))
    group = bpy.data.collections.new("Posterior thyroid and parathyroids")
    bpy.context.scene.collection.children.link(group)
    targets = material("Parathyroid - ochre", (0.72, 0.44, 0.11))
    thyroid = material("Thyroid context - muted rose", (0.49, 0.17, 0.15))
    expected = {}
    centres_left = []
    centres_right = []
    for obj in objects:
        for old_collection in list(obj.users_collection):
            old_collection.objects.unlink(obj)
        group.objects.link(obj)
        raw_name = obj["source_name"]
        if obj["role"] == "target":
            gland, side_code = raw_name.split(".")
            side = {"r": "Right", "l": "Left"}[side_code]
            centres = centres_left if side == "Left" else centres_right
            x = [vertex.co.x for vertex in obj.data.vertices]
            centres.append((min(x) + max(x)) / 2)
            obj.name = f"{side} {gland.lower()}"
            obj["view_role"] = "target-gland"
            colorize(obj, targets)
        else:
            obj.name = "Thyroid gland context"
            obj["view_role"] = "regional-context"
            colorize(obj, thyroid)
        obj["anatomy_id"] = obj.name.lower().replace(" ", "-")
        expected[obj.name] = geometry(obj), obj["source_name"], obj["anatomy_id"], obj.data.materials[0].name
    if len(expected) != 5 or len(centres_left) != 2 or len(centres_right) != 2 or min(centres_left) <= max(centres_right):
        raise ValueError("Atlas neck selection or laterality differs from the four-gland example")
    export(output, "atlas-neck-posterior")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(output / "atlas-neck-posterior.glb"))
    actual = {
        obj.name: (geometry(obj), obj["source_name"], obj["anatomy_id"], obj.data.materials[0].name)
        for obj in bpy.context.scene.objects if obj.type == "MESH"
    }
    if actual != expected:
        raise ValueError("Clean reimport changed the atlas neck geometry, source identity or materials")
    return {
        "source": {"glb": str(SOURCE.relative_to(ROOT)), "sha256": pin},
        "meshes": len(actual),
        "triangles": sum(sum(item[0].values()) for item in actual.values()),
        "leftTargetCentresXMetres": centres_left,
        "rightTargetCentresXMetres": centres_right,
        "geometry": "World triangle position triples unchanged at 1 micrometre rounded precision",
    }


def case_sections(output, prepared, config, audit):
    evidence = {}
    for name, assembly in config["assemblies"].items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.unit_settings.system = "METRIC"
        for label, spec in assembly["parts"].items():
            add_mesh(label, spec, prepared, audit["parts"][label],
                     audit["inputs"][label], audit["case"], audit["derivative"])
            obj = bpy.context.scene.objects[spec["label"]]
            obj["anatomy_id"] = label.replace("_", "-")
            obj["view_role"] = "regional-context" if "context" in obj.name else "target-gland"
        export(output, name)
        check_import(output / f"{name}.glb", assembly["parts"], audit, audit["case"])
        for label, spec in assembly["parts"].items():
            obj = bpy.context.scene.objects[spec["label"]]
            if obj.get("anatomy_id") != label.replace("_", "-"):
                raise ValueError(f"Clean import lost selection identity for {obj.name}")
        evidence[name] = {
            "case": audit["case"],
            "meshes": len(assembly["parts"]),
            "triangles": sum(audit["parts"][label]["triangles"] for label in assembly["parts"]),
        }
    return evidence


def build(prepared, output):
    config_path = HERE / "inputs.json"
    config = json.loads(config_path.read_text())
    frame = json.loads((WORKSHOP / "inputs.json").read_text())
    audit_path = prepared / "mask-audit.json"
    audit = json.loads(audit_path.read_text())
    if (audit["case"], audit["labelGridRasMm"], audit["inputs"]) != (
        frame["case"], frame["rasMmFromVoxel"], config["maskSha256"]
    ):
        raise ValueError("Prepared endocrine audit differs from the pinned source frame")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(audit_path, output / "mask-audit.json")
    captures = {"atlas-neck-posterior": atlas_neck(output, config["atlasLocatorSha256"])}
    captures.update(case_sections(output, prepared, config, audit))
    for name, result in captures.items():
        for extension in ("glb", "blend"):
            file = output / f"{name}.{extension}"
            result[extension] = {"file": file.name, "sha256": sha256(file), "bytes": file.stat().st_size}
    (output / "geometry.json").write_text(json.dumps({
        "blender": bpy.app.version_string,
        "recipeSha256": sha256(Path(__file__)),
        "inputsSha256": sha256(config_path),
        "maskAuditSha256": sha256(audit_path),
        "artifacts": captures,
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    build(args.prepared, args.output)
