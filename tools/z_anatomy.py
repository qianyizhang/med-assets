"""Evaluate named surfaces from the pinned Z-Anatomy Startup.blend member."""

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import file_digest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Mapping, Sequence

import bpy
from mathutils import Matrix


PROVENANCE = (
    Path(__file__).resolve().parents[1]
    / "sources/datasets/z-anatomy/ulnar-elbow/provenance.json"
)


@contextmanager
def new_export_directory(destination: Path):
    """Expose all lesson exports together and leave a failed build retryable."""
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Output directory must be new: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".atlas-export-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "exports"
        staged.mkdir()
        yield staged
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"Output directory must be new: {destination}")
        staged.rename(destination)


@dataclass
class NativeSurface:
    mesh: bpy.types.Mesh
    matrix_world: Matrix


def pinned_member_hash() -> str:
    return json.loads(PROVENANCE.read_text())["member"]["sha256"]


def verified_member_hash(source: Path) -> str:
    """Check the exact source member before loading any Blender datablocks."""
    if bpy.context.preferences.filepaths.use_scripts_auto_execute:
        raise ValueError("Run Blender with --disable-autoexec for the external atlas source")
    with source.open("rb") as handle:
        actual = file_digest(handle, "sha256").hexdigest()
    if actual != pinned_member_hash():
        raise ValueError(f"Source hash mismatch for {source}: {actual}")
    return actual


def load_native_surfaces(
    source: Path,
    names: Sequence[str],
    *,
    edit: Callable[[Mapping[str, bpy.types.Object]], None] | None = None,
) -> dict[str, NativeSurface]:
    """Load a selection once, evaluate it, and retain its source-world frame.

    The optional edit operates on the appended, disposable source objects. It
    can verify that an intentional source change reaches dependent exports.
    The caller owns the scene, presentation, and export scope.
    """
    verified_member_hash(source)
    if not names or len(set(names)) != len(names):
        raise ValueError("Expected a nonempty selection of unique source names")
    with bpy.data.libraries.load(str(source), link=False) as (available, selected):
        missing = set(names) - set(available.objects)
        if missing:
            raise ValueError(f"Missing source objects: {', '.join(sorted(missing))}")
        selected.objects = list(names)

    originals = dict(zip(names, selected.objects, strict=True))
    result = {}
    try:
        for obj in originals.values():
            bpy.context.collection.objects.link(obj)
            obj.hide_set(False)
            obj.hide_viewport = False
            obj.hide_render = False
        if edit is not None:
            edit(originals)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for name, obj in originals.items():
            evaluated = obj.evaluated_get(depsgraph)
            result[name] = NativeSurface(
                mesh=bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph),
                matrix_world=evaluated.matrix_world.copy(),
            )
    finally:
        for obj in originals.values():
            bpy.data.objects.remove(obj, do_unlink=True)
    return result
