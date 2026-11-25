"""Verify a prepared AAA acquisition against the normal sweep and the selected case chapters."""
from hashlib import sha256
import json
import shutil

from aaa_acquisition import acquisition_recipe_sha256
from build_study import CT_SHA


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


def install_acquisitions(bundle, destination, normal, evidence):
    if not normal:
        raise ValueError('The registered AAA acquisitions require the normal aortic screening sweep.')
    receipt = json.loads((bundle / 'verification.json').read_text())
    if (receipt['version'] != 1 or receipt['ctSha256'] != CT_SHA
            or receipt['recipeSha256'] != acquisition_recipe_sha256()):
        raise ValueError('Rebuild AAA acquisitions with the current case and rendering recipes.')
    native = {name: normal.get('meshPaths', {}).get(name, normal['assetRoot'] + 'scenes/' + name + '.mesh')
              for name in ('aorta', 'torso', 'vertebrae')}
    if receipt['sharedAssets'] != {name: file_hash(destination / path) for name, path in native.items()}:
        raise ValueError('AAA acquisitions do not match the selected normal aortic anatomy.')

    inventory = receipt['files']
    expected = set()
    manifests = {}
    count = 0
    color_count = 0
    for case_id, chapters in evidence.items():
        name = case_id + '.scene.json'
        expected.add(name)
        if file_hash(bundle / name) != inventory.get(name):
            raise ValueError(f'AAA scene identity mismatch: {name}')
        scenes = json.loads((bundle / name).read_text())
        if set(scenes) != {chapter['id'] for chapter in chapters}:
            raise ValueError(f'AAA chapter membership differs: {case_id}')
        for chapter in chapters:
            view = scenes[chapter['id']]
            count += chapter['frames']
            if len(view['frames']) != chapter['frames']:
                raise ValueError(f"AAA acquisition length differs: {case_id}/{chapter['id']}")
            root = f"assets/{case_id}/{chapter['id']}/"
            if view['mediaRoot'] != root:
                raise ValueError(f'Unexpected AAA frame directory: {view["mediaRoot"]}')
            if view.get('hasColor') != bool(chapter.get('color')):
                raise ValueError(f"AAA acquisition color mode differs: {case_id}/{chapter['id']}")
            kinds = ('scan', 'section', 'color') if view['hasColor'] else ('scan', 'section')
            if view['hasColor']:
                color_count += chapter['frames']
            expected.update(f'{root}{kind}-{i:02}.webp' for i in range(chapter['frames']) for kind in kinds)
            config = view['config']
            if set(config['meshPaths']) != {'torso', 'vertebrae', 'vein', 'lumen', 'wall'}:
                raise ValueError(f'Incomplete AAA anatomy: {case_id}')
            for part, path in config['meshPaths'].items():
                if part in ('torso', 'vertebrae'):
                    # A compact assembly may keep this same shared mesh under a sibling sweep.
                    config['meshPaths'][part] = '../../' + native[part]
                else:
                    model = 'positive' if case_id == 'aaa-positive' else 'normal'
                    if path != f'assets/{model}/{part}.mesh':
                        raise ValueError(f'Unexpected AAA case mesh: {part}/{path}')
                    expected.add(path)
        manifests[name] = scenes
    if expected != set(inventory) or (count, color_count) != (receipt['frameCount'], receipt['colorFrameCount']):
        raise ValueError('Incomplete or unexpected registered AAA acquisition files.')

    # Check the whole selection before copying any part into an in-place build.
    for name, digest in inventory.items():
        path = bundle / name
        if not path.is_file() or path.resolve() != bundle.resolve() / name or file_hash(path) != digest:
            raise ValueError(f'AAA acquisition identity mismatch: {name}')
    target = destination / 'tours/aaa'
    target.mkdir(parents=True, exist_ok=True)
    for name in sorted(expected - manifests.keys()):
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bundle / name, path)
    for name, scenes in manifests.items():
        (target / name).write_text(json.dumps(scenes, separators=(',', ':')) + '\n')
