"""Matched clean-import Cycles geometry evidence; no browser/runtime claim."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

SOURCE = 'models/thyroid_ct_s0189/exports/source-candidate-02/thyroid_ct_s0189_source_frame.glb'
VIEWS = {
    'whole': {'target': (0, .180, .625), 'offset': (0, -.20, .035), 'scale': .078},
    'oblique': {'target': (0, .180, .625), 'offset': (.075, -.20, .065), 'scale': .074},
    'ridge-detail': {'target': (-.016, .173, .617), 'offset': (.075, -.20, .065), 'scale': .041},
    'reverse': {'target': (0, .180, .625), 'offset': (0, .20, .035), 'scale': .078},
    'side': {'target': (0, .180, .625), 'offset': (.20, -.015, .030), 'scale': .078},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.out.exists():
        raise FileExistsError('Use new render directory')
    args.out.mkdir(parents=True)
    records = []
    for label, path in [('original', args.root/SOURCE), ('updated', args.candidate)]:
        if label == 'original' and not args.baseline:
            continue
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(path))
        for name, config in VIEWS.items():
            for ob in list(bpy.context.scene.objects):
                if ob.type in {'LIGHT', 'CAMERA'}:
                    bpy.data.objects.remove(ob, do_unlink=True)
            target = Vector(config['target'])
            toward_camera = Vector(config['offset']).normalized()
            right = Vector((toward_camera.y, -toward_camera.x, 0)).normalized()
            up = Vector((0,0,1))
            light_positions = [(toward_camera*.10-right*.08+up*.12,.45,.10),
                               (toward_camera*.05+right*.08+up*.03,.15,.12),
                               (-toward_camera*.08+right*.03+up*.07,.25,.10)]
            for offset, energy, size in light_positions:
                bpy.ops.object.light_add(type='AREA', location=target+offset)
                light = bpy.context.object
                light.data.energy = energy
                light.data.size = size
                light.rotation_euler = (target-light.location).to_track_quat('-Z','Y').to_euler()
            bpy.ops.object.camera_add(location=target+Vector(config['offset']))
            camera = bpy.context.object
            camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
            camera.data.type = 'ORTHO'
            camera.data.ortho_scale = config['scale']
            camera.data.clip_start = .001
            camera.data.clip_end = 10
            scene = bpy.context.scene
            scene.camera = camera
            scene.render.engine = 'CYCLES'
            scene.cycles.samples = 40
            scene.cycles.use_denoising = False
            scene.render.resolution_x = 900
            scene.render.resolution_y = 900
            scene.render.resolution_percentage = 100
            scene.world.color = (.18,.18,.18)
            scene.view_settings.view_transform = 'AgX'
            output = args.out/f'{label}-{name}.png'
            scene.render.filepath = str(output)
            bpy.ops.render.render(write_still=True)
            records.append({'file': output.name, 'bytes': output.stat().st_size,
                            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                            'artifact_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'camera': list(camera.location), 'target': list(target),
                            'orthoscale': config['scale'], 'pixels': [900,900], 'samples': 40,
                            'material': 'Unchanged exported illustrative rose material; unchanged smooth normals mode.',
                            'scope': 'Clean GLB import, actual offline Cycles pixels. New matched cameras cover the retained oblique ridge region; old camera settings unavailable.'})
            (args.out/'raster-bindings.json').write_text(json.dumps(records,indent=2)+'\n')


if __name__ == '__main__':
    main()
