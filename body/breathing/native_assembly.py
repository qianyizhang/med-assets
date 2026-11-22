"""Import the eleven respiratory clips into a fresh Blender assembly."""

import argparse
import sys
import tempfile
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_motion import PACKAGE, decode, manifest_assets


def assemble(source, output):
    if not bpy.app.background:
        raise RuntimeError('Run the recipe in background Blender.')
    if output.suffix != '.blend':
        raise ValueError('Choose an output filename ending in .blend.')
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Choose a fresh assembly filename: {output}')

    clips = [source / Path(asset['file']).name for asset in manifest_assets()]
    for clip in clips:
        decode(clip.read_bytes())

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    for clip in clips:
        if bpy.ops.import_scene.gltf(filepath=str(clip.resolve())) != {'FINISHED'}:
            raise RuntimeError(f'Blender could not import {clip}')
    scene.frame_start, scene.frame_end = 1, 121
    scene.frame_set(1)
    scene['educational_motion'] = (
        'Authored inspiration/expiration; not measured physiology. '
        '15 breaths/min, apex restrained, basal descent, modest neighbor displacement.'
    )
    with tempfile.TemporaryDirectory(prefix='.breathing-', dir=output.parent) as temporary:
        staged = Path(temporary) / output.name
        if bpy.ops.wm.save_as_mainfile(filepath=str(staged), copy=True) != {'FINISHED'}:
            raise RuntimeError('Blender could not save the replay assembly.')
        # File publication is exclusive, including if another replay wins the race.
        output.hardlink_to(staged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=PACKAGE, help='Directory with the eleven animated GLBs')
    parser.add_argument('--output', type=Path, required=True, help='Fresh .blend filename under an existing parent')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    try:
        assemble(args.source, args.output)
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
