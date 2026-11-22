"""Exercise individual Blender selection on both clean static r01 imports."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy


def select_objects(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if bpy.ops.import_scene.gltf(filepath=str(path.resolve())) != {'FINISHED'}:
        raise ValueError(f'Import did not finish for {path.name}')
    objects = sorted(bpy.context.scene.objects, key=lambda obj: obj.name)
    if len(objects) != 124 or any(obj.type != 'MESH' for obj in objects):
        raise ValueError(f'Expected exactly 124 mesh objects in {path.name}')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
        if obj.hide_select or not obj.visible_get() or bpy.context.selected_objects != [obj]:
            raise ValueError(f'Selection failed for {obj.name} in {path.name}')
        obj.select_set(False)
    return {
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'individually_selected': [obj.name for obj in objects],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

    baseline, candidate = select_objects(args.source), select_objects(args.candidate)
    if baseline['individually_selected'] != candidate['individually_selected']:
        raise ValueError('Imported object names differ')
    with args.output.open('x') as stream:
        json.dump({
            'blender': bpy.app.version_string,
            'blender_build': bpy.app.build_hash.decode(),
            'baseline': baseline,
            'candidate': candidate,
        }, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print('PASS: selected each of the same 124 objects after both clean imports')


if __name__ == '__main__':
    main()
