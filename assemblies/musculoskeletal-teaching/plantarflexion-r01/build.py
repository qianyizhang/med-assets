"""Skin the eight native Z-Anatomy surfaces for a bounded illustrative ankle motion."""
import math
import sys
from pathlib import Path
import bpy
from mathutils import Quaternion

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/"tools"))
from teaching_scene import load_meshes, colorize, material

SOURCE = "assemblies/musculoskeletal-teaching/2026-10-23/achilles-right-context.glb"
DIGEST = "e38e33c1d0ceb791e4a2ad676dedd7923f53b5ad8d7dc8b195202565609354ea"
PIVOT = (-.080,.051,.065)


def rig():
    arm = bpy.data.armatures.new("Ankle hinge")
    obj = bpy.data.objects.new("Right regional rig",arm)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    shank = arm.edit_bones.new("Shank")
    shank.head, shank.tail = (-.080,.045,.43),(-.080,.050,.43)
    foot = arm.edit_bones.new("Hindfoot")
    foot.head,foot.tail,foot.parent = PIVOT,(-.080,.091,.065),shank
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def foot_weight(name,z):
    if name.startswith(("Calcaneus","Talus")):
        return 1.
    if name.startswith(("Tibia","Fibula")):
        return 0.
    # A common smooth height field preserves source-side relationships.
    t = min(1.,max(0.,(z-.065)/(.28-.065)))
    return 1. - t*t*(3.-2.*t)


def build(out):
    out.mkdir(parents=True,exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts = load_meshes(SOURCE,DIGEST)
    model = rig()
    for obj in parts:
        muscle = "muscle" in obj.name or "gastrocnemius" in obj.name
        tendon = "tendon" in obj.name
        shade = (.54,.20,.16) if muscle else (.72,.61,.44)
        if tendon:
            shade = (.68,.48,.24)
        colorize(obj,material(obj.name.split('.')[0],shade))
        obj.parent = model
        mod = obj.modifiers.new("Regional blend weights","ARMATURE")
        mod.object = model
        hold = obj.vertex_groups.new(name="Shank")
        move = obj.vertex_groups.new(name="Hindfoot")
        for vert in obj.data.vertices:
            w = foot_weight(obj.name,vert.co.z)
            if w < 1.:
                hold.add([vert.index],1.-w,"REPLACE")
            if w > 0.:
                move.add([vert.index],w,"REPLACE")
    foot = model.pose.bones["Hindfoot"]
    scene = bpy.context.scene
    scene.frame_start,scene.frame_end,scene.render.fps = 0,24,24
    for frame,angle in [(0,0),(24,15)]:
        foot.rotation_quaternion = Quaternion((1,0,0),math.radians(angle))
        foot.keyframe_insert(data_path="rotation_quaternion",frame=frame)
    model.animation_data.action.name = "Neutral to 15 degree plantarflexion"
    scene.timeline_markers.new("Neutral",frame=0)
    scene.timeline_markers.new("Plantarflexion 15 degrees",frame=24)
    scene.frame_set(0)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"calf-plantarflexion.blend"))
    bpy.ops.export_scene.gltf(filepath=str(out/"calf-plantarflexion.glb"),export_extras=True,
                              export_animations=True,export_skins=True,export_frame_range=True)


if __name__ == '__main__':
    build(Path(sys.argv[sys.argv.index('--')+1]).resolve())
