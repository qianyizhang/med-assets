"""Verify clip identity, respiratory motion and clean Blender reimport."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_motion import AMPLITUDES, CLIP, PACKAGE, decode, manifest_assets, positions


def require(condition, message):
    if not condition:
        raise ValueError(message)


def float_accessor(document, binary, index, width):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    require(accessor['componentType'] == 5126 and accessor['type'] == {1: 'SCALAR', 3: 'VEC3'}[width],
            f'Unexpected channel accessor: {index}')
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return np.ndarray((accessor['count'], width), '<f4', buffer=binary, offset=offset,
                      strides=(view.get('byteStride', width * 4), 4))


def diaphragm_difference(expected, actual, document):
    baseline_json, baseline_bin = decode(expected)
    replay_json, replay_bin = decode(actual)
    require(baseline_json == replay_json, 'Diaphragm GLB metadata changed.')
    target = document['meshes'][0]['primitives'][0]['targets'][0]['POSITION']
    accessor = document['accessors'][target]
    view = document['bufferViews'][accessor['bufferView']]
    start = view['byteOffset']
    end = start + view['byteLength']
    require(baseline_bin[:start] == replay_bin[:start] and baseline_bin[end:] == replay_bin[end:],
            'Diaphragm bytes changed outside its position morph.')
    old = float_accessor(document, baseline_bin, target, 3)
    new = float_accessor(document, replay_bin, target, 3)
    max_diff = float(np.max(np.abs(old - new)))
    require(max_diff <= 1e-8, 'Diaphragm position morph differs by more than 10 nm.')
    return {'changedFloat32Values': int(np.count_nonzero(old != new)), 'maxDifferenceMetres': max_diff}


def check_clip(asset, clips, baseline):
    organ = asset['id']
    name = Path(asset['file']).name
    expected = (baseline / name).read_bytes()
    raw = (clips / name).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(len(expected) == asset['bytes'] and hashlib.sha256(expected).hexdigest() == asset['sha256'],
            f'Delivered baseline differs from the manifest: {name}')
    document, binary = decode(raw)
    report = {'sha256': digest, 'byteExact': raw == expected}
    if raw != expected:
        require(organ == 'diaphragm', f'Replay bytes differ: {name}')
        report.update(diaphragm_difference(expected, raw, document))

    animations = document['animations']
    require(len(animations) == 1 and animations[0]['name'] == asset['animation'].get('clip', CLIP),
            f'Wrong animation identity: {name}')
    animation = animations[0]
    nodes = {i for i, node in enumerate(document['nodes']) if 'mesh' in node}
    require({channel['target']['node'] for channel in animation['channels']} == nodes
            and len(animation['channels']) == len(animation['samplers']) == len(nodes),
            f'Missing or duplicate animation channel: {name}')
    peak_mm = []
    apex_height, apex_descent_mm = -np.inf, None
    for channel in animation['channels']:
        node = document['nodes'][channel['target']['node']]
        sampler = animation['samplers'][channel['sampler']]
        times = float_accessor(document, binary, sampler['input'], 1)[:, 0]
        require(np.array_equal(times, np.linspace(0, 4, 81, dtype=np.float32))
                and sampler['interpolation'] == 'LINEAR', f'Wrong breathing timeline: {name}')
        peak = 32
        if organ in AMPLITUDES:
            require(channel['target']['path'] == 'translation', f'Expected translation: {name}')
            values = float_accessor(document, binary, sampler['output'], 3)
            base = np.asarray(node.get('translation', [0, 0, 0]), dtype='<f4')
            apex = base + [0, -AMPLITUDES[organ], 0]
            require(np.array_equal(values[0], base) and np.array_equal(values[-1], base)
                    and np.allclose(values[peak], apex, rtol=0, atol=1e-8)
                    and np.array_equal(values[:, [0, 2]], np.broadcast_to(base[[0, 2]], (len(times), 2)))
                    and np.all(np.diff(values[:peak + 1, 1]) < 0)
                    and np.all(np.diff(values[peak:, 1]) > 0), f'Wrong translation cycle: {name}')
            peak_mm.append(1000 * float(base[1] - values[peak, 1]))
            continue

        require(channel['target']['path'] == 'weights', f'Expected shape weights: {name}')
        weights = float_accessor(document, binary, sampler['output'], 1)[:, 0]
        require(len(weights) == len(times) and weights[0] == weights[-1] == 0 and weights[peak] == 1
                and np.all(np.diff(weights[:peak + 1]) > 0) and np.all(np.diff(weights[peak:]) < 0),
                f'Wrong morph cycle: {name}')
        mesh = document['meshes'][node['mesh']]
        require(mesh['weights'] == [0] and mesh['extras']['targetNames'] == ['Inspiration'],
                f'Wrong morph identity: {name}')
        for primitive in mesh['primitives']:
            xyz = positions(document, binary, primitive['attributes']['POSITION'])
            delta = float_accessor(document, binary, primitive['targets'][0]['POSITION'], 3)
            peak_mm.append(-1000 * float(np.min(delta[:, 1])))
            if organ == 'diaphragm':
                require(np.all(delta[:, [0, 2]] == 0) and np.isclose(delta[:, 1].min(), -.021)
                        and np.isclose(delta[:, 1].max(), -.003), 'Expected central dome descent and a smaller rim descent.')
            else:
                apex = np.argmax(xyz[:, 1])
                if xyz[apex, 1] > apex_height:
                    apex_height = xyz[apex, 1]
                    apex_descent_mm = -1000 * float(delta[apex, 1])
                require(np.all(delta[:, 1] <= 0) and np.all(delta[:, 1] >= np.float32(-.018)),
                        f'Lung descent falls outside the authored field: {name}')
    if organ.startswith('lung'):
        require(apex_descent_mm <= .5 and max(peak_mm) > 10,
                f'Expected a restrained apex and inferior descent: {name}')
        report['apexDescentMm'] = apex_descent_mm
    return {**report, 'channels': len(nodes), 'peakDescentMm': max(peak_mm)}


def assembly_snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()), load_ui=False)
    scene = bpy.context.scene
    phase_samples = {}
    meshes = {}
    for obj in scene.objects:
        require(obj.type == 'MESH', f'Unexpected object in {path}: {obj.name}')
        shape = obj.data.shape_keys
        animation = shape.animation_data if shape else obj.animation_data
        action = animation.action
        bag = action.layers[0].strips[0].channelbag(animation.action_slot)
        require(action.name.startswith(CLIP), f'Wrong Blender action for {obj.name}: {action.name}')
        meshes[obj.name] = (
            len(obj.data.vertices), len(obj.data.polygons), tuple(action.frame_range),
            [(curve.data_path, curve.array_index, len(curve.keyframe_points)) for curve in bag.fcurves],
        )
    for frame in (1, 48, 49, 120, 121):
        scene.frame_set(frame)
        phase_samples[frame] = {}
        for obj in scene.objects:
            shape = obj.data.shape_keys
            phase_samples[frame][obj.name] = (
                [shape.key_blocks['Inspiration'].value] if shape else list(obj.matrix_world.translation)
            )
    return (scene.frame_start, scene.frame_end, scene.render.fps, scene.render.fps_base), meshes, phase_samples, len(bpy.data.actions)


def check_assembly(baseline, assembly, channels):
    baseline_timeline, baseline_meshes, baseline_samples, baseline_actions = assembly_snapshot(baseline)
    timeline, meshes, samples, actions = assembly_snapshot(assembly)
    require(timeline == baseline_timeline == (1, 121, 30, 1.0), 'Blender timeline differs.')
    different = [name for name in sorted(meshes.keys() | baseline_meshes.keys())
                 if meshes.get(name) != baseline_meshes.get(name)]
    require(len(meshes) == channels and not different, f'Blender mesh/action identities differ: {different}')
    max_diff = max(
        float(np.max(np.abs(np.asarray(values) - baseline_samples[frame][name])))
        for frame, frame_values in samples.items() for name, values in frame_values.items()
    )
    require(max_diff <= 1e-8, 'Sampled Blender motion differs from the delivered assembly.')
    return {'objectsWithActions': len(meshes), 'fps': timeline[2], 'sampledFrames': list(samples),
            'replayActionDatablocks': actions, 'baselineActionDatablocks': baseline_actions,
            'maxSampleDifference': max_diff}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clips', type=Path, required=True)
    parser.add_argument('--assembly', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, default=PACKAGE)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    try:
        clips = {asset['id']: check_clip(asset, args.clips, args.baseline) for asset in manifest_assets()}
        assembly = check_assembly(args.baseline / 'Breathing_Assembly.blend', args.assembly,
                                  sum(row['channels'] for row in clips.values()))
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(json.dumps({'clips': clips, 'assembly': assembly}, indent=2))


if __name__ == '__main__':
    main()
