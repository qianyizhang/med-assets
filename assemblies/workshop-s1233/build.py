"""Build and check two clean-import assemblies from the exact prepared meshes."""

import argparse
from hashlib import file_digest
import json
from pathlib import Path
import shutil
import sys

import bpy
import numpy as np

OWNER = Path(__file__).resolve().parent
sys.path.insert(0, str(OWNER.parents[1] / "tools"))
from teaching_scene import export, material


def sha256(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def add_mesh(label, spec, source, summary, pin, case, derivative):
    path = source / f"{label}.npz"
    if sha256(path) != summary["meshSha256"]:
        raise ValueError(f"Prepared mesh differs: {path.name}")
    with np.load(path, allow_pickle=False) as mesh_file:
        vertices, faces = mesh_file["vertices"], mesh_file["faces"]
    mesh = bpy.data.meshes.new(spec["label"])
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.update()
    obj = bpy.data.objects.new(spec["label"], mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["source_case"] = case
    obj["source_label"] = label
    obj["source_sha256"] = pin
    obj["derived_from_binary_label"] = True
    if derivative:
        obj["overview_refinement"] = derivative
    srgb = [int(spec["color"][i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = tuple(c / 12.92 if c < 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)
    mesh.materials.append(material(spec["label"], linear))
    for polygon in mesh.polygons:
        polygon.use_smooth = True


def check_import(file, specs, audit, case):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(file), disable_bone_shape=True)
    objects = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH"}
    wanted = {spec["label"] for spec in specs.values()}
    if set(objects) != wanted:
        raise ValueError(f"Clean import node inventory differs for {file.name}")
    for label, spec in specs.items():
        obj = objects[spec["label"]]
        corners = np.array([obj.matrix_world @ vector for vector in _corners(obj)])
        got = np.array([corners.min(0), corners.max(0)])
        expected = audit["parts"][label]
        if not np.allclose(got, expected["boundsBlenderMetres"], atol=1e-6, rtol=0):
            raise ValueError(f"Clean import moved {obj.name}")
        if len(obj.data.polygons) != expected["triangles"]:
            raise ValueError(f"Clean import topology count differs for {obj.name}")
        if (obj.get("source_case"), obj.get("source_label"), obj.get("source_sha256")) != (
            case, label, audit["inputs"][label]
        ):
            raise ValueError(f"Clean import provenance differs for {obj.name}")
        if obj.get("overview_refinement") != audit.get("derivative"):
            raise ValueError(f"Clean import derivative identity differs for {obj.name}")
        if [mat.name for mat in obj.data.materials] != [spec["label"]]:
            raise ValueError(f"Clean import lost the named material for {obj.name}")


def _corners(obj):
    from mathutils import Vector
    return [Vector(corner) for corner in obj.bound_box]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    config_file = OWNER / "inputs.json"
    config = json.loads(config_file.read_text())
    audit_file = args.prepared / "mask-audit.json"
    audit = json.loads(audit_file.read_text())
    if (audit["case"], audit["labelGridRasMm"], audit["inputs"]) != (
        config["case"], config["rasMmFromVoxel"], config["maskSha256"]
    ):
        raise ValueError("Prepared label audit differs from the pinned source")
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(audit_file, args.output / "mask-audit.json")

    artifacts = {}
    for key, assembly in config["assemblies"].items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.unit_settings.system = "METRIC"
        for label, spec in assembly["parts"].items():
            add_mesh(label, spec, args.prepared, audit["parts"][label], audit["inputs"][label],
                     audit["case"], audit.get("derivative"))
        export(args.output, key)
        file = args.output / f"{key}.glb"
        check_import(file, assembly["parts"], audit, config["case"])
        artifacts[key] = {
            "sha256": sha256(file), "meshes": len(assembly["parts"]), "bytes": file.stat().st_size,
            "triangles": sum(audit["parts"][label]["triangles"] for label in assembly["parts"]),
            "blendSha256": sha256(file.with_suffix(".blend")),
        }
    receipt = {
        "case": config["case"], "configSha256": sha256(config_file),
        "maskAuditSha256": sha256(audit_file), "artifacts": artifacts,
        "blender": bpy.app.version_string,
    }
    (args.output / "assemblies.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
