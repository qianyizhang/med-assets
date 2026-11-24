"""Render the authored curvilinear transducer on the same-case abdominal surface in Blender."""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


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
    # Elliptical sections broaden into the convex footprint at the contact face.
    vertices, faces = [], []
    for z, w, d, curvature in rings:
        for i in range(48):
            a = 2 * math.pi * i / 48
            vertices.append((w*math.cos(a), d*math.sin(a), z + curvature*math.cos(a)**2))
    for j in range(len(rings)-1):
        for i in range(48):
            a, b = 48*j+i, 48*j+(i+1)%48
            faces.append((a, b, b+48, a+48))
    faces.extend([tuple(reversed(range(48))), tuple(range(len(vertices)-48, len(vertices)))])
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
    grip('Convex face', [(-.7,14,3,2.5),(1,16,4.4,3),(3,16,4.5,3)],rubber,probe)
    grip('Housing', [(2.6,16,4.5,3),(5,17,5,2.5),(10,15,5.7,1.2),(18,10,5.2,0),
                     (30,7,4.4,0),(45,7.3,4.8,0),(49,5,4,0),(50,3.5,3.1,0)],white,probe)
    grip('Strain relief', [(49,3.5,3.0,0),(55,3.3,2.9,0),(60,2.0,2.0,0)],rubber,probe)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    dot=bpy.context.object
    dot.name='Orientation pip on image-left end'
    dot.parent=probe
    dot.location=(-13.8,0,11)
    dot.scale=(2,2.1,2.7)
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
        for radius, angles in [(38, range(-36, 37, 3)), (171, range(36, -37, -3))]:
            for degrees in angles:
                a = math.radians(degrees)
                point = pos + (lateral*(radius*math.sin(a))-outward*(radius*math.cos(a)-38))/1.5
                uv = world_to_camera_view(scene, cam, point)
                outline.append([uv.x*650, (1-uv.y)*455])
        projected.append(outline)
        scene.render.filepath=str(output / 'media' / f'base-{i:02}.webp')
        bpy.ops.render.render(write_still=True)
    (output / 'projected-field.json').write_text(json.dumps(projected))


if __name__ == '__main__':
    main()
