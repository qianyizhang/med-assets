"""Compare BP3D's named third ventricle to the unchanged hypothalamic teaching GLB."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOLS = runpy.run_path(str(HERE / "dental-sections.py"))
G = "models/hypothalamus/exports/source-candidate-01/hypothalamus_source_frame.glb"
MEMBER = "partof_BP3D_4.0_obj_99/FJ1730.obj"


def main(archive, out):
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    ref = json.loads(
        (ROOT / "sources/datasets/bp3d-4.0-glands/external-source-members.json").read_text()
    )
    if digest != ref["archive"]["sha256"]:
        raise ValueError("Wrong BP3D source archive")
    with zipfile.ZipFile(archive) as z:
        data = z.read(MEMBER)
    member_sha = hashlib.sha256(data).hexdigest()
    if member_sha != "7acd4a30d13b409221aea7267ae302ef7c100162a6185d891c91843ec876dd79":
        raise ValueError("Wrong third ventricle")
    lines = data.decode().splitlines()
    pts = np.array([[float(x) for x in line.split()[1:]] for line in lines if line.startswith("v ")])
    faces = np.array(
        [[int(x.split("/")[0]) - 1 for x in line.split()[1:]] for line in lines if line.startswith("f ")]
    )
    ctrl = hashlib.sha256((ROOT / G).read_bytes()).hexdigest()
    record = json.loads((HERE.parent / "refinement-form/controls.json").read_text())["hypothalamus"]
    if ctrl != record["sha256"]:
        raise ValueError("Changed hypothalamus teaching export")
    meshes = TOOLS["arrays"](ROOT / G, ctrl)
    parts = [(v[:, [0, 2, 1]] * [1, -1, 1], f) for v, f in meshes.values()] + [(pts, faces)]
    plate = Image.new("RGB", (1176, 625), TOOLS["BG"])
    title = TOOLS["title"]
    title(plate, (18, 12), "Hypothalamic recess  |  Registered atlas sections", 32)
    title(
        plate,
        (18, 58),
        "Coronal planes in the native BP3D 4.0 frame. The same planes intersect both original envelopes and FJ1730.",
        19,
    )
    title(
        plate,
        (18, 91),
        "Terracotta: hypothalamic envelopes       Teal: third ventricle       Pale gold: overlapping section pixels",
        18,
    )
    records = {}
    for i, y in enumerate([-101.7, -99.2, -96.7, -94.2]):
        masks = []
        for v, f in parts:
            segments = TOOLS["intersections"](v, f, y)
            im = Image.new("1", (272, 526), 0)
            pen = ImageDraw.Draw(im)
            for edge in segments:
                q = (edge - [-9.0, 1531.0]) * [15.0, -15.0] + [0, 504.0]
                pen.line([tuple(q[0]), tuple(q[1])], fill=1, width=2)
            masks.append(ndi.binary_fill_holes(np.asarray(im))[100:516, :])
        hyp = masks[0] | masks[1]
        vent = masks[2]
        common = hyp & vent
        colors = np.full((416, 272, 3), [47, 53, 57], dtype=np.uint8)
        colors[hyp] = (193, 130, 105)
        colors[vent] = (75, 162, 172)
        colors[common] = (238, 202, 126)
        plate.paste(Image.fromarray(colors), (18 + i * 291, 151))
        title(plate, (18 + i * 291, 122), f"y = {y:.1f} mm", 18)
        rows = []
        for j, r in enumerate(vent):
            x = np.flatnonzero(r)
            if len(x) and hyp[j, : x.min()].any() and hyp[j, x.max() + 1 :].any():
                rows.append(j)
        records[str(y)] = {
            "sectionScalePxPerMm": 15,
            "verticallyFlankedRows": len(rows),
            "overlapRasterPixels": int(common.sum()),
            "ventriclePixels": int(vent.sum()),
        }
    title(
        plate,
        (18, 581),
        "The lower ventricular tongue occupies the medial recess between the paired envelopes. Gold marks coincident section pixels at this resolution.",
        18,
    )
    plate.save(out / "hypothalamus-sections.webp", quality=94)
    (out / "ventricle-sections.json").write_text(
        json.dumps(
            dict(
                archiveSha256=digest,
                member=MEMBER,
                memberSha256=member_sha,
                controlSha256=ctrl,
                nativeTransform="glTF [x,-z,y] metres → BP3D millimetres",
                sections=records,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.archive, args.output)
