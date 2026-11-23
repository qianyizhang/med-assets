"""Verify assessed file identities without requiring generated display caches."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "transport/tools"))
from delivery_catalog import DELIVERY_INDEX, assets_by_path, source_path
from lfs_transport import HEX64, parse_pointer, unique_keys

GALLERY_SITE = Path("sites/anatomy-gallery")
DISPLAY_RECIPE = "display-images.json"
DISPLAY_ENCODERS = {"11.3.0": "1.5.0", "12.2.0": "1.6.0"}
PNG_SOURCE = re.compile(r"https://github\.com/qianyizhang/med-assets/blob/[0-9a-f]{7,40}/(.+\.png)")


def file_identity(repo, relative):
    """Read a local payload identity or the object declared by its LFS pointer."""
    path = repo / source_path(relative)
    if path != path.resolve() or not path.is_file():
        raise ValueError(f"Missing or linked repository file: {relative}")
    with path.open("rb") as stream:
        prefix = stream.read(1025)
        if prefix.startswith(b"version https://git-lfs.github.com/spec/"):
            return parse_pointer(prefix)
        stream.seek(0)
        return hashlib.file_digest(stream, "sha256").hexdigest(), path.stat().st_size


def validate_display_paths(source, target):
    output_dir = target.parent.parent
    if (source.suffix != ".png" or target.name != source.with_suffix(".webp").name
            or target.parent.name != "display"
            or source.parent not in (output_dir, output_dir / "media")):
        raise ValueError(f"Display destination does not match its source: {target}")


def display_recipes(site):
    recipes = json.loads((site / DISPLAY_RECIPE).read_text(), object_pairs_hook=unique_keys)
    targets = set()
    for encoder, pairs in recipes.items():
        if encoder not in DISPLAY_ENCODERS:
            raise ValueError(f"Unknown display encoder: {encoder}")
        for source, target in pairs:
            validate_display_paths(Path(source_path(source)), Path(source_path(target)))
            if target in targets:
                raise ValueError(f"Duplicate display binding: {target}")
            targets.add(target)
    return recipes


def delivery_by_path(index):
    return assets_by_path(json.loads(index.read_text(), object_pairs_hook=unique_keys))


class AssessmentIdentities:
    def __init__(self, repo):
        self.repo = repo.resolve()
        site = self.repo / GALLERY_SITE
        self.displays = {target: source for pairs in display_recipes(site).values() for source, target in pairs}
        self.deliveries = delivery_by_path(self.repo / DELIVERY_INDEX)

    def check(self, claim):
        """Bind a reviewed export or view to its exact identity."""
        path = claim["path"]
        delivery = self.deliveries.get(path, {})
        source_link = PNG_SOURCE.fullmatch(delivery.get("source", "")) if path.endswith(".webp") else None
        if path in self.displays or source_link:
            source = self.displays.get(path)
            if not source or not source_link or source != unquote(source_link[1]):
                raise ValueError(f"Invalid display source binding for {path}")
            original = self.deliveries.get(source, {})
            if file_identity(self.repo, source) != (original.get("sha256"), original.get("bytes")):
                raise ValueError(f"Display source identity mismatch for {source}")
            digest, size = delivery.get("sha256"), delivery.get("bytes")
            if not HEX64.fullmatch(digest or "") or type(size) is not int or size <= 0:
                raise ValueError(f"Invalid display delivery identity for {path}")
        else:
            digest, size = file_identity(self.repo, path)
        if digest != claim.get("sha256") or (claim.get("bytes") is not None and size != claim["bytes"]):
            raise ValueError(f"Identity mismatch for {path}")
        return digest, size
