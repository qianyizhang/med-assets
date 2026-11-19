"""Editable two-pose right tibiofemoral flexion demonstration."""
from pathlib import Path
import hashlib
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "models/joints/exports/z-knee-r01/knee_z_native.glb"
SHA = "6dcc793e4132e62e4962e504bef0d595bb2e7d3a31881137244f31eadbb53aad"
PIVOT = Vector((-.077,.030,.452))
BONES = ("Femur", "Tibia", "Fibula")
COLORS = {"Femur":(.72,.61,.44), "Tibia":(.64,.46,.30), "Fibula":(.48,.37,.28),
          "compression":(.52,.21,.13), "support":(.19,.46,.48), "caption":(.15,.19,.23)}


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color,1)
    shader.inputs["Roughness"].default_value = .74
    return mat


def cropped_bone(obj, top):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    # Truncate the shaft only. All joint-end triangles remain in source coordinates.
    cut = bmesh.ops.bisect_plane(bm, geom=[*bm.verts,*bm.edges,*bm.faces],
        plane_co=(0,0,.55 if top else .318),plane_no=(0,0,1),
        clear_outer=top,clear_inner=not top,dist=1e-8)
    rim = [e for e in cut["geom_cut"] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
    bmesh.ops.holes_fill(bm,edges=rim)
    mesh = bpy.data.meshes.new(obj.name+" shaft section")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def arrow(name, start, end, mat):
    axis = (end-start).normalized()
    base = end-axis*.014
    parts = []
    for primitive, a, b, radii in (
        (bpy.ops.mesh.primitive_cylinder_add,start,base,dict(radius=.0026)),
        (bpy.ops.mesh.primitive_cone_add,base,end,dict(radius1=.007,radius2=0)),
    ):
        primitive(vertices=24,location=(a+b)/2,depth=(b-a).length,**radii)
        obj = bpy.context.object
        obj.rotation_euler = axis.to_track_quat("Z","Y").to_euler()
        parts.append(obj)
    for part in parts:
        part.select_set(True)
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)


def caption(text, location, mat):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.object
    obj.name = "Caption | "+text
    obj.rotation_euler = Vector((-1,0,0)).to_track_quat("Z","Y").to_euler()
    obj.data.align_x = "CENTER"
    obj.data.body = text
    obj.data.size = .011
    obj.data.materials.append(mat)
    bpy.ops.object.convert(target='MESH')


def build(out):
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SHA:
        raise ValueError("Right knee source identity mismatch")
    out.mkdir(parents=True,exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    source = list(bpy.context.scene.objects)
    meshes = {}
    mats = {name:material(name,rgb) for name,rgb in COLORS.items()}
    for bone in BONES:
        obj = next(o for o in source if o.get("source_object_name")==bone+".r")
        mesh = cropped_bone(obj,bone=="Femur")
        mesh.materials.append(mats[bone])
        meshes[bone] = mesh
    for obj in source:
        bpy.data.objects.remove(obj,do_unlink=True)
    for pose, degrees, offset in (("Source",0,0),("Flexion",20,-.175)):
        shift = Vector((0,offset,0))
        pivot = PIVOT+shift
        hinge = bpy.data.objects.new(pose+" | tibial hinge",None)
        bpy.context.collection.objects.link(hinge)
        hinge.location = pivot
        hinge.rotation_euler.x = math.radians(degrees)
        for bone,mesh in meshes.items():
            obj = bpy.data.objects.new(pose+" | "+bone,mesh)
            bpy.context.collection.objects.link(obj)
            if bone == "Femur":
                obj.location = shift
            else:
                obj.parent = hinge
                obj.location = -PIVOT
        arrow(pose+" | Femoral load",Vector((-.12,-.010,.532))+shift,
              Vector((-.12,-.010,.480))+shift,mats["compression"])
        rotation = Matrix.Rotation(math.radians(degrees),3,"X")
        def lower(z):
            return pivot + rotation @ (Vector((-.12,-.010,z))-PIVOT)
        arrow(pose+" | Tibial support",lower(.327),lower(.385),mats["support"])
        caption("Source pose" if degrees==0 else "+20° flexion",
                (-.128,.027+offset,.298),mats["caption"])
    bpy.ops.object.select_all(action='DESELECT')
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_location = Vector((-.08,-.056,.422))
            area.spaces.active.region_3d.view_distance = .53
            area.spaces.active.region_3d.view_rotation = Vector((1,0,0)).to_track_quat("-Z","Y")
            area.spaces.active.region_3d.view_perspective = "ORTHO"
            area.spaces.active.shading.color_type = "MATERIAL"
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"knee-motion.blend"),compress=True)
    bpy.ops.export_scene.gltf(filepath=str(out/"knee-motion.glb"),export_extras=True)


if __name__ == "__main__":
    build(Path(sys.argv[sys.argv.index("--")+1]).resolve())
