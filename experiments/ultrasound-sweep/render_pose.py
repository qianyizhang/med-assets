"""Render the authored curvilinear transducer on the same-case abdominal surface in Blender."""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

# Blender may invoke this as a text block without adding its directory to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geometry import (
    LENS_RADIUS_MM, PIP_POSITION, PIP_SCALE, PROBE_RINGS,
    SECTOR_DEPTH_MM, SECTOR_HALF_ANGLE_DEG, VOXEL_MM, probe_geometry,
)


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    return mat


def mesh_object(name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def grip(name, rings, mat, parent):
    vertices, faces = probe_geometry(rings)
    obj = mesh_object(name, vertices, faces, mat)
    obj.parent = parent
    return obj


def main():
    output = Path(sys.argv[sys.argv.index('--')+1]).resolve()
    frames = json.loads((output / 'sweep.js').read_text().removeprefix('const sweep = ').strip()[:-1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    torso = np.load(output / 'torso.npz')
    vertices = torso['vertices']
    faces = torso['faces'][:, ::-1]
    skin = mesh_object('s1233 abdominal surface', vertices.tolist(), faces.tolist(),
                       material('Teaching skin', (.66, .46, .35)))
    organs = []
    for name, color in [('ribs', (.88, .80, .65)), ('liver', (.49, .22, .16)),
                        ('gallbladder', (.14, .46, .33))]:
        part = np.load(output / f'{name}.npz')
        obj = mesh_object(name, part['vertices'].tolist(), part['faces'][:, ::-1].tolist(), material(name, color))
        organs.append(obj)
    probe = bpy.data.objects.new('Transducer', None)
    bpy.context.collection.objects.link(probe)
    rubber = material('Acoustic lens', (.024, .045, .048))
    white = material('Transducer housing', (.84, .89, .87))
    teal = material('Orientation marker', (.022, .40, .39))
    grip('Convex face', PROBE_RINGS['lens'], rubber, probe)
    grip('Housing', PROBE_RINGS['housing'], white, probe)
    grip('Strain relief', PROBE_RINGS['relief'], rubber, probe)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    dot=bpy.context.object
    dot.name='Orientation pip on image-left end'
    dot.parent=probe
    dot.location=PIP_POSITION
    dot.scale=PIP_SCALE
    dot.data.materials.append(teal)
    curve=bpy.data.curves.new('Cable','CURVE')
    curve.dimensions='3D'
    curve.bevel_depth=1.7
    curve.bevel_resolution=3
    curve.resolution_u=20
    path=curve.splines.new('BEZIER')
    path.bezier_points.add(3)
    cable=bpy.data.objects.new('Cable',curve)
    bpy.context.collection.objects.link(cable)
    curve.materials.append(rubber)

    camera=bpy.data.cameras.new('Abdominal window')
    cam=bpy.data.objects.new('Abdominal window',camera)
    bpy.context.collection.objects.link(cam)
    scene.camera=cam
    anchor=Vector((151,177,204))
    direction=Vector((.68,.66,-.44)).normalized()
    cam.location=anchor+direction*480
    right=Vector((0,0,1)).cross(direction).normalized()
    up=direction.cross(right).normalized()
    tilt=math.radians(50)
    cam.rotation_euler=Matrix((right*math.cos(tilt)+up*math.sin(tilt),
                               up*math.cos(tilt)-right*math.sin(tilt),direction)).transposed().to_euler()
    camera.type='ORTHO'
    camera.ortho_scale=330
    camera.clip_end=1200
    scene.render.engine='BLENDER_WORKBENCH'
    style=scene.display.shading
    style.light='STUDIO'
    style.studio_light='paint.sl'
    style.studiolight_rotate_z=0.7
    style.color_type='MATERIAL'
    style.show_shadows=True
    style.show_cavity=True
    style.cavity_type='WORLD'
    style.cavity_ridge_factor=1.05
    style.cavity_valley_factor=1.0
    style.background_type='WORLD'
    world=bpy.data.worlds.new('Studio')
    scene.world=world
    world.color=(.11,.15,.15)
    scene.view_settings.view_transform='Standard'
    scene.render.resolution_x=650
    scene.render.resolution_y=455
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='WEBP'
    scene.render.image_settings.quality=91
    # Render internal anatomy once on transparency. Composite it below the probe
    # and above the skin with a soft window in the review plates.
    props = [probe, *probe.children, cable]
    for obj in [skin, *props]:
        obj.hide_render = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.filepath = str(output / 'internal.png')
    bpy.ops.render.render(write_still=True)
    for obj in [skin, *props]:
        obj.hide_render = False
    for obj in organs:
        obj.hide_render = True
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'WEBP'
    projected = []
    bpy.context.view_layer.update()
    for i, frame in enumerate(frames):
        pos=Vector(frame['contact'])
        lateral=Vector(frame['width'])
        outward=-Vector(frame['beam'])
        probe.matrix_world=Matrix.Translation(pos) @ Matrix((lateral,outward.cross(lateral),outward)).transposed().to_4x4()
        end=pos+outward*60
        points=(end,end+outward*13,end+Vector((-35,13,-24)),end+Vector((-55,-7,-105)))
        for point, co in zip(path.bezier_points,points):
            point.co=co
            point.handle_left_type=point.handle_right_type='AUTO'
        # Project the actual sector boundaries into the pose camera (millimetres to voxels).
        outline = []
        half_angle = SECTOR_HALF_ANGLE_DEG
        for radius, angles in [(LENS_RADIUS_MM, range(-half_angle, half_angle+1, 3)),
                               (LENS_RADIUS_MM + SECTOR_DEPTH_MM, range(half_angle, -half_angle-1, -3))]:
            for degrees in angles:
                a = math.radians(degrees)
                point = pos + (lateral*(radius*math.sin(a))-outward*(radius*math.cos(a)-LENS_RADIUS_MM))/VOXEL_MM
                uv = world_to_camera_view(scene, cam, point)
                outline.append([uv.x*650, (1-uv.y)*455])
        projected.append(outline)
        scene.render.filepath=str(output / 'media' / f'base-{i:02}.webp')
        bpy.ops.render.render(write_still=True)
    (output / 'projected-field.json').write_text(json.dumps(projected))


if __name__ == '__main__':
    main()
