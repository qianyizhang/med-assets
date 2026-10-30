"""Extract a pinned native skeletal-localization subset without moving surfaces."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

SOURCE_SHA = '9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
NERVES = ['Median nerve.r', 'Common palmar digital branches of median nerve.r',
          'Proper palmar digital branches of median nerve.r']
CARPALS = [n + ' bone.r' for n in ['Scaphoid', 'Lunate', 'Triquetrum', 'Pisiform',
                                 'Trapezium', 'Trapezoid', 'Capitate', 'Hamate']]
METACARPALS = [n + ' metacarpal bone.r' for n in ['First', 'Second', 'Third', 'Fourth', 'Fifth']]
DIGITS = ['first', 'second', 'third', 'fourth', 'fifth']
PHALANGES = [f'{level} phalanx of {digit} finger of hand.r' for level in ['Proximal', 'Middle', 'Distal']
            for digit in DIGITS if not (level == 'Middle' and digit == 'first')]
NAMES = NERVES + ['Humerus.r', 'Radius.r', 'Ulna.r'] + CARPALS + METACARPALS + PHALANGES
LIMITS = ('Skeletal localization only. Native source pose and selected nerve groups; illustrative colors. '
          'Soft tissues, palmar cutaneous branch, recurrent/motor branching and complete skin territories omitted. '
          'Unresolved source nerve/flexor overlap screen excludes tendon-layer and carpal-tunnel teaching. '
          'No fused nerve continuity, clinical, physical-scale, motion or browser-runtime approval.')

def check_inputs(source, output):
    if output.exists():
        raise FileExistsError('Output directory must be new')
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Exact pinned Startup.blend required')

def build(source, output):
    check_inputs(source, output)
    import bpy
    started = time.monotonic()
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    dg = bpy.context.evaluated_depsgraph_get()
    copies, rows = [], []
    for name in NAMES:
        old = bpy.data.objects.get(name)
        if old is None:
            raise ValueError('Missing selected object: ' + name)
        evaluated = old.evaluated_get(dg)
        mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=dg)
        mesh.calc_loop_triangles()
        rows.append({'sourceObject': name, 'sourceType': old.type,
                     'vertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles),
                     'matrixWorld': [list(r) for r in evaluated.matrix_world],
                     'sourceMaterials': [m.name if m else None for m in mesh.materials]})
        copies.append((name, mesh, evaluated.matrix_world.copy()))
    scene = bpy.data.scenes.new('Right median nerve — skeletal localization')
    bpy.context.window.scene = scene
    for name, mesh, matrix in copies:
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        obj.matrix_world = matrix
        obj['source_object'] = name
        obj['role'] = 'selected median nerve group' if name in NERVES else 'native skeletal context'
        material = bpy.data.materials.new(name + ' — illustrative display')
        material.use_nodes = True
        p = material.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value = ((.60, .28, .01, 1) if name in NERVES else (.22, .25, .28, 1))
        p.inputs['Roughness'].default_value = .8
        mesh.materials.clear()
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.material_index = 0
    scene['assetId'] = 'peripheral_nerves_median_wrist_z'
    scene['variantId'] = 'native-skeletal-localization-r01-v1'
    scene['sourceBlendSha256'] = SOURCE_SHA
    scene['license'] = 'CC BY-SA 4.0'
    scene['attribution'] = ('Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0; '
                            'BodyParts3D — The Database Center for Life Science — CC BY-SA 2.1 Japan (historical credit)')
    scene['scope'] = LIMITS
    output.mkdir(parents=True)
    glb = output / 'median-wrist-v1.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', export_animations=False,
                             export_extras=True, use_active_scene=True)
    receipt = {'sourceSha256': SOURCE_SHA, 'artifactSha256': hashlib.sha256(glb.read_bytes()).hexdigest(),
               'artifactBytes': glb.stat().st_size, 'objects': rows,
               'evaluatedTriangles': sum(r['triangles'] for r in rows),
               'buildSeconds': round(time.monotonic() - started, 3),
               'scope': 'Evaluated source surfaces and effective world transforms retained; source masters untouched. '
                        'Subset hierarchy flattened; illustrative materials replace source action shaders.'}
    (output / 'source-bindings.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'objects'}, indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    build(a.source, a.out)
