"""Extract registered comparison surfaces from a pinned, script-disabled Z-Anatomy library."""

import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
PIN = json.loads(
    (
        HERE.parents[2]
        / "sources/datasets/z-anatomy/diaphragm-static-study/external-source-map.json"
    ).read_text()
)
NAMES = [
    "Diaphragm",
    "Oesophagus",
    "Thoracic aorta",
    "Abdominal aorta",
    "Inferior vena cava (thoracic part)",
    "Inferior vena cava (abdominal part)",
    "Vertebra L1",
]


def main():
    source, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
    if hashlib.sha256(source.read_bytes()).hexdigest() != PIN["member_sha256"]:
        raise ValueError("Expected the pinned Z-Anatomy Startup.blend")
    output.mkdir(exist_ok=False)
    with bpy.data.libraries.load(str(source)) as (available, selected):
        selected.objects = [name for name in NAMES if name in available.objects]
    if len(selected.objects) != len(NAMES):
        raise ValueError("Missing diaphragm comparison surface")
    for obj in selected.objects:
        bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    for obj in selected.objects:
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        xyz = np.array([list(evaluated.matrix_world @ v.co) for v in mesh.vertices])
        np.savez_compressed(
            output / (obj.name + ".npz"),
            xyz=xyz,
            triangles=np.array([list(f.vertices) for f in mesh.loop_triangles]),
        )
        print(obj.name, len(xyz), xyz.min(0), xyz.max(0))
        evaluated.to_mesh_clear()
    receipt = {
        "sourceSha256": PIN["member_sha256"],
        "sectionInputs": {
            p.name: {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size,
            }
            for p in sorted(output.glob("*.npz"))
        },
    }
    (output / "atlas.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
