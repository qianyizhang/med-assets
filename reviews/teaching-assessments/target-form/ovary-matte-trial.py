"""Reduce ovarian material glare on the exact bilateral HRA context GLB."""
import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from glb import decode, encode

CONTROL = ROOT / "models/ovaries/exports/hra-ovary-tubal-r01/ovary-tubal-context.glb"
CONTROL_SHA = "465a44b18df91ece95a236372a8cbe3e1a0de0207525955290e6b0fa519195d1"
MATERIALS = ("Ovary_mat", "Ovary_mat1")


def build(control):
    if hashlib.sha256(control).hexdigest() != CONTROL_SHA:
        raise ValueError("Expected the exact hydrated HRA ovary and tubal context r01")
    document, binary = decode(control)
    materials = {material["name"]: material for material in document["materials"]}
    for name in MATERIALS:
        pbr = materials[name]["pbrMetallicRoughness"]
        if pbr["roughnessFactor"] != 0.207408592:
            raise ValueError(f"Unexpected source roughness for {name}")
        pbr["roughnessFactor"] = 0.58
    return encode(document, binary, pad_binary=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    candidate = build(CONTROL.read_bytes())
    with args.output.open("xb") as stream:
        stream.write(candidate)
    print(hashlib.sha256(candidate).hexdigest(), len(candidate), args.output)


if __name__ == "__main__":
    main()
