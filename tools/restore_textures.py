"""Restore the frozen base-color and normal PNGs from their embedded GLB images."""
import argparse
from collections import defaultdict
from hashlib import sha256
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

# Blender executes --python scripts without adding their directory to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import decode

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "workshop": Path("body/anatomy-workshop-r1"),
    "cardiac": Path("heart/Cardiac_Atlas"),
}


def texture_sources(package):
    owner = PACKAGES[package]
    size = "1K" if package == "workshop" else "2K"
    sources = defaultdict(dict)
    for line in (ROOT / "sources/imports/SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        path = Path(name)
        if path.parent != owner / "textures":
            continue
        for suffix in (f"_BaseColor_{size}.png", f"_Normal_OpenGL_{size}.png"):
            if path.name.endswith(suffix):
                mesh = (Path("meshes") / (path.name.removesuffix(suffix) + ".glb")
                        if package == "workshop" else Path("exports/Cardiac_Walls_Baked_PBR_ED.glb"))
                sources[ROOT / owner / mesh][path.name] = digest
    if not sources:
        raise ValueError(f"No import pins for {package}")
    return sources


def embedded_pngs(mesh, expected):
    document, binary = decode(mesh.read_bytes())
    found = {}
    for image in document.get("images", []):
        name = image.get("name", "") + ".png"
        if name not in expected:
            continue
        if name in found or image.get("mimeType") != "image/png" or "bufferView" not in image:
            raise ValueError(f"{mesh}: expected one embedded PNG for {name}")
        view = document["bufferViews"][image["bufferView"]]
        offset, length = view.get("byteOffset", 0), view["byteLength"]
        if view["buffer"] != 0 or offset < 0 or length <= 0 or offset + length > len(binary):
            raise ValueError(f"{mesh}: invalid image range for {name}")
        data = binary[offset:offset + length]
        if sha256(data).hexdigest() != expected[name]:
            raise ValueError(f"{mesh}: changed texture bytes for {name}")
        found[name] = data
    if expected.keys() != found.keys():
        raise ValueError(f"{mesh}: missing embedded PNGs {sorted(expected.keys() - found.keys())}")
    return found


def restore(package, directory=None):
    directory = ROOT / PACKAGES[package] / "textures" if directory is None else Path(directory)
    if directory.absolute() != directory.resolve():
        raise ValueError(f"Symlink in texture directory: {directory}")
    pending = {}
    for mesh, expected in texture_sources(package).items():
        for name, data in embedded_pngs(mesh, expected).items():
            path = directory / name
            if path.is_symlink():
                raise ValueError(f"Refusing symlink: {path}")
            if path.exists():
                if path.read_bytes() != data:
                    raise ValueError(f"Existing texture differs: {path}")
            else:
                pending[path] = data
    directory.mkdir(parents=True, exist_ok=True)
    for path, data in pending.items():
        with NamedTemporaryFile(dir=directory) as staged:
            staged.write(data)
            staged.flush()
            try:
                os.link(staged.name, path)
            except FileExistsError:
                if path.is_symlink() or path.read_bytes() != data:
                    raise ValueError(f"Existing texture differs: {path}")
    return len(pending)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", choices=PACKAGES)
    parser.add_argument("--check", action="store_true", help="verify embedded PNGs without writing files")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    if args.check:
        count = sum(len(embedded_pngs(mesh, pins)) for mesh, pins in texture_sources(args.package).items())
        print(f"{args.package}: verified {count} embedded textures")
    else:
        print(f"{args.package}: restored {restore(args.package)} textures")
