"""Export sparse tissue volumes and registered landmarks from the stage models."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys

import numpy as np

OWNER = Path(__file__).resolve().parent
STUDY = OWNER.parents[1]
sys.path.insert(0, str(STUDY))

import build_early_pregnancy as early  # noqa: E402
import gestational_anatomy as gest  # noqa: E402
import pregnancy_anatomy as first  # noqa: E402

# Sample organ interiors and the native concentric fields in increasing priority.
EARLY = ["maternal_bladder", "uterus", "gestational_rim", "gestational_sac",
         "amnion", "yolk_sac", "embryo", "cardiac_region"]
FIRST = ["maternal_bladder", "uterus", "amniotic_fluid", "placenta", "fetus", "umbilical_cord",
         "calvarium", "nasal_bone", "falx", "spinal_echoes", "choroid_plexus", "fetal_bladder"]
LATE = ["maternal_bladder", "uterus", "amniotic_cavity", "placenta", "cervical_canal",
        "fetus", "cord", "lungs", "heart", "spine", "diaphragm", "femur", "hands", "feet",
        "calvarium", "orbits", "falx", "ventricles", "choroid", "cavum", "thalami", "cerebellum",
        "cisterna_magna", "upper_lip", "nares", "nasal_bone", "stomach", "kidneys", "renal_pelves",
        "fetal_bladder", "umbilical_arteries", "right_atrium", "left_atrium", "left_ventricle",
        "right_ventricle", "aortic_outflow", "pulmonary_outflow", "superior_vena_cava",
        "trachea", "umbilical_vein"]


def encode(values):
    """Run lengths are unsigned 16-bit little-endian, followed by a tissue ID."""
    flat = values.ravel()
    transitions = np.flatnonzero(np.diff(flat)) + 1
    bounds = np.r_[0, transitions, flat.size]
    packed = bytearray()
    for start, stop in zip(bounds[:-1], bounds[1:], strict=True):
        left = int(stop - start)
        while left:
            count = min(65535, left)
            packed.extend((count & 255, count >> 8, int(flat[start])))
            left -= count
    return base64.b64encode(packed).decode("ascii")


def vector(value):
    return np.round(value, 4).tolist()


def sample_stage(stage):
    if stage == "early":
        names, model, lo, hi, step = EARLY, early, (-68, -69, -74), (68, 68, 32), .9
    elif stage == "first":
        names, model, lo, hi, step = FIRST, first, (-45, -54, -59), (45, 61, 72), .75
    else:
        model = gest.Gestation(stage)
        if stage == "mid":
            names, lo, hi, step = LATE, (-71, -82, -118), (71, 107, 154), 1.35
        else:
            names, lo, hi, step = LATE, (-96, -91, -132), (96, 134, 227), 1.8
    xs, ys, zs = [np.arange(a, b + step / 2, step) for a, b in zip(lo, hi, strict=True)]
    values = np.zeros((len(zs), len(ys), len(xs)), dtype="uint8")
    for index in range(0, len(zs), 6):
        z, y, x = np.meshgrid(zs[index:index + 6], ys, xs, indexing="ij", sparse=True)
        local = (x, y, z)
        if stage in ("early", "first"):
            fields = {name: model.FIELDS[name][0](local) for name in names}
        else:
            world = tuple(sum(a * b for a, b in zip(row, local, strict=True)) + offset
                          for row, offset in zip(model.rotation, model.stage.centre, strict=True))
            fields = model.sample(world, names)
        chunk = values[index:index + 6]
        for value, name in enumerate(names, 1):
            chunk[np.broadcast_to(fields[name] <= 0, chunk.shape)] = value
    record = dict(origin=lo, spacing=step, size=[len(xs), len(ys), len(zs)], names=names,
                  data=encode(values))
    if stage in ("mid", "late"):
        links = {
            "cervix": vector(model.local_coordinates(model.cervical_opening)),
            "placenta": vector([*model.stage.placenta_site_xz[:1], model.stage.placenta_side * 33,
                                model.stage.placenta_site_xz[1]]),
            "placentalCord": vector(model.local_coordinates(model.cord_path[-1])),
            "cord": vector([model.local_coordinates(p) for p in model.cord_path]),
            "limbs": model.stage.limb_nodes,
            "maternalCentre": model.stage.centre,
            "axes": vector(model.rotation),
            "fluid": vector([model.local_coordinates(p) for p in model.fluid_span_endpoints])
                if stage == "late" else None,
        }
        record.update(links)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OWNER)
    parser.add_argument("--check", action="store_true",
                        help="Compare fresh stage volumes with the delivered modules")
    args = parser.parse_args()
    if not args.check:
        args.output.mkdir(parents=True, exist_ok=True)
    for stage in ("early", "first", "mid", "late"):
        record = sample_stage(stage)
        data = record.pop("data")
        header = json.dumps(record, separators=(",", ":"))
        chunks = [json.dumps(data[i:i + 120]) for i in range(0, len(data), 120)]
        output = "/* Generated by build_playable.py from the source stage fields. */\n"
        output += f"export const geometry = {header};\n"
        output += "export const runs = [\n" + ",\n".join(chunks) + "\n].join('');\n"
        destination = args.output / f"playable-volume-{stage}.js"
        if args.check:
            if not destination.is_file() or destination.read_bytes() != output.encode():
                parser.exit(1, f"Pregnancy stage volume replay mismatch: {destination}\n")
        else:
            destination.write_text(output)
    if args.check:
        print("Verified four playable pregnancy volumes")


if __name__ == "__main__":
    main()
