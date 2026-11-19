"""Small Blender modelling operations shared by schematic teaching compositions."""

import hashlib
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]


def material(name, rgb):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*rgb, 1)
    shader.inputs["Roughness"].default_value = 0.74
    return mat


def colorize(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.material_index = 0
    return obj


def load_meshes(path, sha256, select=lambda name: True):
    """Import selected surfaces in Blender world metres, detaching source parents."""
    path = ROOT / path
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != sha256:
            raise ValueError(f"Input identity mismatch for {path.name}")
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    added = set(bpy.context.scene.objects) - before
    kept = sorted(
        (o for o in added if o.type == "MESH" and select(o.name)), key=lambda o: o.name
    )
    if not kept:
        raise ValueError(f"No selected meshes in {path.name}")
    for obj in kept:
        matrix = obj.matrix_world.copy()
        obj.data = obj.data.copy()
        obj.data.transform(matrix)
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
    for obj in added - set(kept):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    return kept


def ellipsoid(name, center, radii, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=36, ring_count=20, location=center)
    obj = bpy.context.object
    obj.name, obj.scale = name, radii
    for face in obj.data.polygons:
        face.use_smooth = True
    return colorize(obj, mat)


def tube(name, points, radius, mat, *, smooth=True):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    curve.use_fill_caps = True
    if smooth:
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(len(points) - 1)
        for p, co in zip(spline.bezier_points, points):
            p.co = co
            p.handle_left_type = p.handle_right_type = "AUTO"
    else:
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for p, co in zip(spline.points, points):
            p.co = (*co, 1)
    curve.materials.append(mat)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def bounds(objects):
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(p) for obj in objects for p in obj.bound_box]
    return (
        Vector([min(p[i] for p in corners) for i in range(3)]),
        Vector([max(p[i] for p in corners) for i in range(3)]),
    )


def place(objects, center, scale=1):
    """Uniform scale around group bounds and translate to a teaching location."""
    lo, hi = bounds(objects)
    offset = Vector(center) - (lo + hi) * (scale / 2)
    for obj in objects:
        obj.location = offset
        obj.scale = (scale,) * 3
    bpy.context.view_layer.update()
    return list(offset)


def export(output, name):
    """Save editable curves in the blend and evaluate them to portable mesh nodes."""
    bpy.ops.wm.save_as_mainfile(filepath=str((output / (name + ".blend")).resolve()))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in list(bpy.context.scene.objects):
        if obj.type == "CURVE":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    if bpy.context.selected_objects:
        bpy.ops.object.convert(target="MESH")
    bpy.ops.export_scene.gltf(
        filepath=str((output / (name + ".glb")).resolve()),
        export_format="GLB",
        export_yup=True,
        export_extras=True,
        export_animations=False,
    )
