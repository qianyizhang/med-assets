"""Build five teaching editions from exact historical owners into a fresh directory."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))
from tools.glb import decode
from med_assets.glb_repack import colors, index_blocks, normals, png_streams, verify_triangles
from med_assets.native_blend import recompress

CONTROLS = json.loads((HERE.parent / "refinement-form/controls.json").read_text())
CONTROLS["lymph"] = {
    "path": "models/lymph_node/exports/hra-tissue-layers-r01/lymph-node-tissue-layers.glb",
    "sha256": "bf4ffa85c96459f2666949196915244697f3f5e33ebf485482c8223ba1fcb23e",
}
EDITION = {
    "anatomy-workshop-r1": "body/anatomy-workshop-r1/Anatomy_Workshop_compact.blend",
    "heart": "models/heart/exports/texture-pack-r02/heart.glb",
    "diaphragm": "models/diaphragm/exports/normal-pack-r02/diaphragm.glb",
    "lymph": "models/lymph_node/exports/tissue-color-pack-r02/lymph-node.glb",
    "nose_sinuses": "models/nose_sinuses/exports/index-pack-r02/nasal_airspace.glb",
}


def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def build(key, dest):
    control = CONTROLS[key]
    data = (ROOT / control["path"]).read_bytes()
    if identity(data)["sha256"] != control["sha256"]:
        raise ValueError(f"Wrong source for {key}")
    if key == "anatomy-workshop-r1":
        candidate, metrics = recompress(data, level=17, threads=1)
    else:
        doc, binary = decode(data)
        operation = {
            "heart": png_streams,
            "diaphragm": normals,
            "lymph": colors,
            "nose_sinuses": index_blocks,
        }[key]
        candidate, metrics = operation(doc, binary)
        if key == "nose_sinuses":
            metrics["orderedCornerAttributesSha256"] = verify_triangles(data, candidate)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("xb") as handle:
        handle.write(candidate)
    return {
        "source": {"path": control["path"], **identity(data)},
        "edition": {"path": EDITION[key], **identity(candidate)},
        **metrics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = {key: build(key, args.output / path) for key, path in EDITION.items()}
    (args.output / "build.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
