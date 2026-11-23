"""Orthographic Cycles setup shared by the right-arm lesson and plate review."""

import bpy
from mathutils import Vector


def blender_axes(three_point):
    x, y, z = three_point
    return Vector((x, -z, y))


def set_up_scene(scene, width, height):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    scene.cycles.seed = 7
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world = bpy.data.worlds.new('World')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes['Background']
    background.inputs[0].default_value = (.44, .47, .50, 1)
    background.inputs[1].default_value = .38
    scene.view_settings.view_transform = 'AgX'
    camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(camera)
    camera.data.type = 'ORTHO'
    scene.camera = camera
    lights = []
    for index, (offset, energy, radius) in enumerate((
        ((-.5, .6, .8), 75, .65), ((.6, .2, .4), 40, .60), ((0, .2, -.5), 55, .50),
    )):
        data = bpy.data.lights.new(f'Area{index}', 'AREA')
        light = bpy.data.objects.new(f'Area{index}', data)
        scene.collection.objects.link(light)
        data.energy, data.size, data.shape = energy, radius, 'DISK'
        lights.append((light, Vector(offset)))
    return camera, lights
