"""Make the two baked wall maps available to the atlas recipes."""
from pathlib import Path
from runpy import run_path


def ensure_wall_textures():
    package = Path(__file__).resolve().parent
    names = ("wall_atlas_BaseColor_2K.png", "wall_atlas_Normal_OpenGL_2K.png")
    if all((package / "textures" / name).is_file() for name in names):
        return
    helper = package.parents[1] / "tools/restore_textures.py"
    if not helper.is_file():
        raise FileNotFoundError("Restore the wall textures from the repository or re-extract the complete model package.")
    run_path(str(helper))["restore"]("cardiac")
