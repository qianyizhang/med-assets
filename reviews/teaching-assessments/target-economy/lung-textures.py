"""Repack the exact embedded s1233 PNG pixels and verify retained GLB streams."""

import argparse
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.glb import buffer_view_bytes, decode, encode, pack_buffer_view

TRIALS = HERE.parent / "refinement-economy" / "trials.json"


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def image_data(data):
    with Image.open(BytesIO(data), formats=["PNG"]) as image:
        if image.mode not in {"RGB", "RGBA"} or image.size != (1024, 1024):
            raise ValueError("Expected sized RGB or RGBA source texture")
        if set(image.info) - {"exif", "dpi"}:
            raise ValueError("Unexpected PNG metadata requires a color-space check")
        return image.mode, image.tobytes(), image.info.copy()


def repack(control):
    doc, binary = decode(control)
    changed = deepcopy(doc)
    if len(doc["buffers"]) != 1 or len(doc["images"]) != 3:
        raise ValueError("Unexpected exact source structure")
    image_views = {image["bufferView"]: image for image in doc["images"]}
    payload = bytearray()
    measurements = {}
    for i, view in enumerate(changed["bufferViews"]):
        original = buffer_view_bytes(binary, view)
        data = original
        if i in image_views:
            image_record = image_views[i]
            if image_record["mimeType"] != "image/png":
                raise ValueError("Repack accepts PNG only")
            expected = image_data(original)
            with Image.open(BytesIO(original), formats=["PNG"]) as image:
                output = BytesIO()
                image.save(output, format="PNG", optimize=True, **expected[2])
                data = output.getvalue()
            if image_data(data) != expected or len(data) >= len(original):
                raise ValueError("Texture metadata, decoded pixels or encoded saving failed")
            measurements[image_record["name"]] = {
                "original": identity(original),
                "updated": identity(data),
                "decoded": {"mode": expected[0], "size": [1024, 1024], **identity(expected[1])},
            }
        changed["bufferViews"][i] = pack_buffer_view(payload, view, data)
    changed["buffers"][0]["byteLength"] = len(payload)
    output = encode(changed, payload)

    result, packed = decode(output)
    if {k: v for k, v in doc.items() if k not in {"buffers", "bufferViews"}} != {
            k: v for k, v in result.items() if k not in {"buffers", "bufferViews"}}:
        raise ValueError("Scene declarations changed")
    for i, (prior, current) in enumerate(zip(doc["bufferViews"], result["bufferViews"], strict=True)):
        if i not in image_views and buffer_view_bytes(binary, prior) != buffer_view_bytes(packed, current):
            raise ValueError(f"Non-image stream {i} changed")
        if i in image_views and image_data(buffer_view_bytes(binary, prior)) != image_data(buffer_view_bytes(packed, current)):
            raise ValueError(f"Texture stream {i} changed")
    return output, measurements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    folder = args.out.resolve()
    if not folder.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a fresh directory under .artifacts")
    task, = [row for row in json.loads(TRIALS.read_text()) if row["name"] == "lung_left"]
    source = (ROOT / task["path"]).read_bytes()
    if identity(source) != {key: task[key] for key in ("sha256", "bytes")}:
        raise ValueError("Wrong or unhydrated s1233 control")
    output, images = repack(source)
    folder.mkdir(exist_ok=False, parents=True)
    (folder / "candidate.glb").write_bytes(output)
    receipt = {"control": {"path": task["path"], **identity(source)},
               "candidate": identity(output), "textures": images}
    (folder / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
