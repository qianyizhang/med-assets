"""Build four static teaching selections from the pinned Z-Anatomy right arm."""
import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from z_anatomy import load_native_surfaces, new_export_directory, pinned_member_hash


@dataclass(frozen=True)
class Finish:
    name: str
    rgb: tuple[float, float, float]
    roughness: float = 0.7
    alpha: float = 1.0


@dataclass(frozen=True)
class Study:
    filename: str
    title: str
    parts: tuple[tuple[str, Finish], ...]
    joint_region: str = ''


HUMERUS, RADIUS, ULNA, SCAPULA = 'Humerus.r', 'Radius.r', 'Ulna.r', 'Scapula.r'
NERVE = 'Ulnar nerve.r'
BONE = Finish('Bone | illustrative ivory', (.44, .40, .32))
LIGAMENT = Finish('Ligament | illustrative cream', (.52, .40, .18))
CAPSULE = Finish('Capsule | illustrative transparency', (.16, .34, .40), alpha=.08)
LABRUM = Finish('Meniscus or labrum | illustrative blue', (.08, .28, .34))
JOINT_ROLES = {BONE: 'bone', LIGAMENT: 'ligament', CAPSULE: 'capsule', LABRUM: 'fibrocartilage'}

STUDIES = (
    Study('elbow_z_native.glb', 'Right elbow ligaments and capsule', (
        ('Annular ligament of radius.r', LIGAMENT),
        ('Articular capsule of elbow joint.r', CAPSULE),
        ('Quadrate ligament.r', LIGAMENT),
        ('Radial collateral ligament.r', LIGAMENT),
        ('Ulnar collateral ligament.r', LIGAMENT),
        (HUMERUS, BONE), (ULNA, BONE), (RADIUS, BONE),
    ), 'elbow'),
    Study('shoulder_z_native.glb', 'Right shoulder ligaments and labrum', (
        ('Articular capsule of glenohumeral joint.r', CAPSULE),
        ('Coracohumeral ligament.r', LIGAMENT),
        ('Glenoid labrum.r', LABRUM),
        ('Inferior glenohumeral ligament.r', LIGAMENT),
        ('Middle glenohumeral ligament.r', LIGAMENT),
        ('Superior glenohumeral ligament.r', LIGAMENT),
        ('Transverse humeral ligament.r', LIGAMENT),
        (HUMERUS, BONE), (SCAPULA, BONE), ('Clavicle.r', BONE),
    ), 'shoulder'),
    Study(
        'right-rotator-cuff.glb',
        'Right cuff muscle surface localization; no attachments, tendon continuity, action or clinical validation',
        tuple(
            (name, Finish(f'{name} illustrative', rgb, .8))
            for name, rgb in (
                (HUMERUS, (.70, .67, .57)),
                (SCAPULA, (.70, .67, .57)),
                ('Supraspinatus muscle.r', (.72, .40, .12)),
                ('Infraspinatus muscle.r', (.53, .11, .085)),
                ('Teres minor muscle.r', (.32, .13, .39)),
                ('Subscapularis muscle.r', (.09, .38, .36)),
            )
        ),
    ),
    Study(
        'right-ulnar-elbow.glb',
        'Right ulnar nerve relative to the humerus, ulna and radius; '
        'static pose, illustrative colors and exposed source endpoints',
        (
            (NERVE, Finish('Ulnar nerve — illustrative ochre', (.22, .075, .008), .8)),
            *((name, Finish(f'{name} — illustrative slate', (.075, .09, .105), .8))
              for name in (HUMERUS, ULNA, RADIUS)),
        ),
    ),
)


def material(finish):
    result = bpy.data.materials.new(finish.name)
    result.use_nodes = True
    result.diffuse_color = (*finish.rgb, finish.alpha)
    surface = result.node_tree.nodes.get('Principled BSDF')
    surface.inputs['Base Color'].default_value = (*finish.rgb, 1)
    surface.inputs['Roughness'].default_value = finish.roughness
    surface.inputs['Alpha'].default_value = finish.alpha
    if finish.alpha < 1:
        result.surface_render_method = 'BLENDED'
    return result


def export_study(study, surfaces, output, source_hash):
    scene = bpy.context.scene
    if not study.joint_region:
        scene['source'] = 'Z-Anatomy / BodyParts3D'
        scene['license'] = 'CC BY-SA 4.0; retain historical BodyParts3D CC BY-SA 2.1 Japan credit'
        scene['scope'] = study.title
    objects = []
    finishes = {}
    for name, finish in study.parts:
        if finish not in finishes:
            finishes[finish] = material(finish)
        native = surfaces[name]
        mesh = native.mesh
        if study.joint_region:
            # Joint editions tessellate in baked native world coordinates.
            mesh = mesh.copy()
            mesh.name = name + ' evaluated'
            mesh.transform(native.matrix_world)
            mesh.update()
        mesh.materials.clear()
        mesh.materials.append(finishes[finish])
        suffix = ' candidate' if study.joint_region else ''
        obj = bpy.data.objects.new(name + suffix, mesh)
        bpy.context.collection.objects.link(obj)
        if study.joint_region:
            obj['source_object_name'] = name
            obj['component_role'] = JOINT_ROLES[finish]
            obj['anatomy_id'] = 'joints'
            obj['asset_id'] = f'regional_{study.joint_region}_r01'
            obj['view_role'] = 'context' if finish == BONE else 'surface'
            obj['source_frame'] = 'Z-Anatomy native evaluated world; not BP3D registered'
        else:
            obj.matrix_world = native.matrix_world
            obj['source_object'] = name
            obj['source_sha256'] = source_hash
        objects.append(obj)
    destination = output / study.filename
    result = bpy.ops.export_scene.gltf(
        filepath=str(destination), export_format='GLB',
        export_animations=False, export_extras=True, export_cameras=False, export_lights=False,
        export_texcoords=not study.joint_region,
    )
    if result != {'FINISHED'} or not destination.is_file():
        raise RuntimeError(f'GLB export did not finish: {study.filename}')
    for obj in objects:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if study.joint_region:
            bpy.data.meshes.remove(mesh)
    for finish in finishes.values():
        bpy.data.materials.remove(finish)


def build(source, output, *, edit=None):
    with new_export_directory(output) as exports:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        names = tuple(dict.fromkeys(name for study in STUDIES for name, _ in study.parts))
        surfaces = load_native_surfaces(source, names, edit=edit)
        source_hash = pinned_member_hash()
        for study in STUDIES:
            export_study(study, surfaces, exports, source_hash)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    build(args.source, args.out)


if __name__ == '__main__':
    main()
