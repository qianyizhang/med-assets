"""Verify the normal right-arm replay, clean imports and disposable source edit."""
import argparse
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as recipe

ROOT = HERE.parents[3]
ACTIVE = (
    'models/joints/exports/z-elbow-r02/elbow_z_native.glb',
    'models/joints/exports/z-shoulder-r02/shoulder_z_native.glb',
    'models/joints/exports/z-rotator-cuff-r01/right-rotator-cuff.glb',
    'models/peripheral_nerves/exports/ulnar-elbow-r02/right-ulnar-elbow.glb',
)
EDIT_METRES = .0001


def clean_import(path, expected):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    result = bpy.ops.import_scene.gltf(filepath=str(path))
    if result != {'FINISHED'}:
        raise ValueError(f'GLB import did not finish: {path}')
    bpy.context.view_layer.update()
    meshes = {}
    for obj in bpy.context.scene.objects:
        assert obj.type == 'MESH', obj.name
        name = obj.name.removesuffix(' candidate')
        mesh = obj.data
        mesh.calc_loop_triangles()
        meshes[name] = (
            tuple(obj.matrix_world @ vertex.co for vertex in mesh.vertices),
            tuple(tuple(face.vertices) for face in mesh.loop_triangles),
            tuple(tuple(normal.vector) for normal in mesh.corner_normals),
        )
    assert meshes.keys() == expected, path
    return meshes


def edit_humerus(objects):
    objects[recipe.HUMERUS].data.vertices[0].co.x += EDIT_METRES
    objects[recipe.HUMERUS].data.update()


def verify(source, work):
    rejected = work / 'rejected'
    wrong_source = work / 'wrong.blend'
    wrong_source.write_bytes(b'Not the pinned atlas')
    try:
        recipe.build(wrong_source, rejected)
    except ValueError as error:
        assert 'hash mismatch' in str(error).lower(), error
    else:
        raise AssertionError('Wrong source was accepted')
    assert not rejected.exists()

    reference = work / 'reference'
    export_study = recipe.export_study

    def fail_second(study, *args):
        if study is recipe.STUDIES[1]:
            raise RuntimeError('Injected export failure')
        export_study(study, *args)

    with patch.object(recipe, 'export_study', side_effect=fail_second):
        try:
            recipe.build(source, reference)
        except RuntimeError as error:
            assert str(error) == 'Injected export failure', error
        else:
            raise AssertionError('Failed export was accepted')
    assert not reference.exists() and not list(work.glob('.atlas-export-*'))

    recipe.build(source, reference)
    try:
        recipe.build(source, reference)
    except FileExistsError:
        pass
    else:
        raise AssertionError('Existing output directory was overwritten')

    edited = work / 'edited'
    recipe.build(source, edited, edit=edit_humerus)
    for study, relative in zip(recipe.STUDIES, ACTIVE, strict=True):
        path = ROOT / relative
        export = reference / study.filename
        assert export.read_bytes() == path.read_bytes(), relative
        expected = {name for name, _ in study.parts}
        before = clean_import(export, expected)
        after = clean_import(edited / study.filename, expected)
        for name, original in before.items():
            changed = after[name]
            if name != recipe.HUMERUS:
                assert original == changed, (relative, name)
                continue
            before_vertices, before_faces, _ = original
            after_vertices, after_faces, _ = changed
            assert before_faces == after_faces, relative
            movement = [
                b - a for a, b in zip(before_vertices, after_vertices, strict=True) if a != b
            ]
            displacement, = movement
            assert abs(displacement.x - EDIT_METRES) < 5e-7, relative
            assert abs(displacement.y) + abs(displacement.z) < 5e-7, relative
        print(f'PASS: {relative}, {len(before)} meshes, one humeral vertex moved {displacement.x * 1000:.6f} mm')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    with TemporaryDirectory(prefix='right-arm-verification-') as scratch:
        verify(args.source.resolve(), Path(scratch))


if __name__ == '__main__':
    main()
