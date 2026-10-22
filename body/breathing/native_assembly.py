import bpy,pathlib,json
root=pathlib.Path('/workspace/scratch/57dbce61b79b/anatomy-site/dist/body/3d/assets/motion')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps=30
for f in root.glob('*_breathing.glb'): bpy.ops.import_scene.gltf(filepath=str(f))
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=121;bpy.context.scene.render.fps=30
bpy.context.scene['educational_motion']='Authored inspiration/expiration; not measured physiology. 15 breaths/min, apex restrained, basal descent, modest neighbor displacement.'
bpy.ops.wm.save_as_mainfile(filepath='/workspace/scratch/57dbce61b79b/anatomy-output/body/Breathing_Assembly.blend')
