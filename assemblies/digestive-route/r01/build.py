"""Build the editable frontal teaching plate; lengths in metres, Blender Z up."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# Cross sections for the uninterrupted food route: X, Z and local radius (mm).
# A station shared by consecutive organs is a single sampled rim.
FOOD = [
    ("01 Oral cavity", [(0, 345, 13), (0, 335, 17), (0, 325, 13)]),
    ("02 Pharynx", [(0, 312, 11), (0, 295, 7)]),
    ("03 Esophagus", [(0, 245, 5), (1, 190, 5), (8, 140, 6)]),
    ("04 Stomach", [(18, 131, 15), (40, 132, 24), (54, 107, 22),
                    (46, 86, 18), (25, 80, 12), (5, 82, 6)]),
    ("05 Duodenum", [(-13, 83, 8), (-23, 75, 8), (-24, 59, 8),
                     (-21, 45, 8), (-8, 40, 8), (7, 47, 7)]),
    ("06 Jejunum and ileum", [(31, 51, 6), (44, 39, 6), (29, 28, 6),
                              (-11, 27, 6), (-25, 16, 6), (-14, 7, 6),
                              (28, 8, 6), (40,-6,6), (25,-18,6), (-25,-16,6),
                              (-38,-28,6), (-47,-34,6)]),
    ("07 Cecum and ascending colon", [(-59,-38,11), (-69,-31,12),
                                      (-69,0,11), (-67,48,10)]),
    ("08 Transverse colon", [(-57,62,10), (-32,69,9), (3,66,9),
                             (41,67,9), (63,77,10)]),
    ("09 Descending and sigmoid colon", [(73,68,10), (75,16,10),
                                         (70,-33,10), (55,-49,10), (33,-47,9),
                                         (20,-54,8), (13,-62,8)]),
    ("10 Rectum and anal canal", [(9,-73,10), (8,-86,9), (8,-102,5)]),
]
PALETTE = {"rose": (.55,.23,.18), "clay": (.65,.36,.22), "sand": (.72,.51,.29),
           "gland": (.65,.42,.21), "bile": (.30,.49,.30), "pancreatic": (.19,.46,.48),
           "saliva": (.22,.36,.53), "liver": (.38,.17,.15)}
ROUTE_X = .162


def paint(obj, tone):
    mat = bpy.data.materials.get(tone)
    if mat is None:
        mat = bpy.data.materials.new(tone)
        mat.diffuse_color = (*PALETTE[tone], 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = mat.diffuse_color
        shader.inputs["Roughness"].default_value = .74
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.material_index = 0
        face.use_smooth = True


def smooth(points):
    # Catmull-Rom spline through the controls, with radius as a fourth coordinate.
    result = []
    for i in range(len(points)-1):
        a,b,c,d = (points[max(i-1,0)], points[i], points[i+1], points[min(i+2,len(points)-1)])
        for step in range(8):
            u = step / 8
            result.append((2*b + (-a+c)*u + (2*a-5*b+4*c-d)*u*u + (-a+3*b-3*c+d)*u**3)/2)
    return result + [points[-1]]


def loft(parts, tones, flattened=False):
    controls = [Vector(p) for _, points in parts for p in points]
    samples = smooth(controls)
    rings = []
    for i, p in enumerate(samples):
        xyz = p.to_3d()
        tangent = (samples[min(len(samples)-1,i+1)].to_3d()-samples[max(0,i-1)].to_3d()).normalized()
        u = tangent.cross(Vector((0,1,0))).normalized()
        v = tangent.cross(u)
        ring = []
        for k in range(32):
            angle = math.tau*k/32
            pos = (xyz + p.w*(math.cos(angle)*u + math.sin(angle)*v*(.84 if flattened else 1))) / 1000
            ring.append(tuple(pos + Vector((ROUTE_X,0,0))))
        rings.append(ring)
    end = 0
    for index,(name,points) in enumerate(parts):
        start = end
        end += (len(points) - (index == 0)) * 8
        vertices = [v for ring in rings[start:end+1] for v in ring]
        faces = [(j*32+k, j*32+(k+1)%32, (j+1)*32+(k+1)%32, (j+1)*32+k)
                 for j in range(end-start) for k in range(32)]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        paint(obj, tones[index])
        obj["derivation"] = "Authored teaching surface"
        obj["start_ring_vertex_count"] = 32


def build(out):
    inputs = json.loads((HERE/'inputs.json').read_text())
    for spec in inputs.values():
        if hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest() != spec['sha256']:
            raise ValueError(f"Input hash mismatch: {spec['path']}")
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name,spec in inputs.items():
        bpy.ops.import_scene.gltf(filepath=str(ROOT/spec['path']))
        imported = list(bpy.context.selected_objects)
        bowel = 'intestine' in name
        for obj in imported:
            if obj.type != 'MESH' or (not bowel and obj.get('view_role') != 'surface'):
                bpy.data.objects.remove(obj,do_unlink=True)
                continue
            obj.name = 'Source '+name
            obj.animation_data_clear()
            if obj.data.shape_keys:
                obj.shape_key_clear()
            # Keep the source groups internally coherent; separate them vertically.
            obj.location += Vector((-.105,0,-.91 if bowel else .335))
            paint(obj, {"stomach":"rose","liver":"liver","pancreas":"gland",
                        "gallbladder":"bile","small-intestine":"clay","large-intestine":"sand"}[name])
            obj["source_sha256"] = spec["sha256"]
    route = []
    for name,points in FOOD:
        # Transverse colon passes anterior to the duodenum/mesentery.
        controls = [(x, -27 if name.startswith("08") else 0, z, radius)
                    for x,z,radius in points]
        route.append(('Food '+name, controls))
    loft(route,['clay','rose','clay','rose','sand','clay','rose','rose','rose','clay'],True)
    # Each insertion crosses its recipient's near wall. Keep the hepatobiliary and
    # pancreatic branches separately selectable until their common channel.
    ducts = [
        ('Saliva - parotid to oral vestibule', 'saliva', [(-37,0,341,7),(-32,-2,343,6),(-27,-3,337,2),(-14,-4,335,2)]),
        ('Bile - hepatic duct', 'bile', [(-63,0,120,4),(-52,-3,109,3),(-41,-10,95,3)]),
        ('Bile - gallbladder and cystic duct', 'bile', [(-72,0,100,7),(-63,-2,101,7),(-57,-5,98,3),(-41,-10,95,3)]),
        ('Bile - common bile duct', 'bile', [(-41,-10,95,3),(-34,-16,84,3),(-30,-19,67,3),(-23,-14,59,3)]),
        ('Pancreatic - main duct', 'pancreatic', [(46,-20,59,3),(19,-20,59,3),(0,-20,57,3),(-23,-14,59,3)]),
        ('Common channel - duodenal entry', 'sand', [(-23,-14,59,3),(-24,-10,59,3),(-24,-5,59,3)]),
    ]
    for name,tone,points in ducts:
        loft([('Accessory '+name,points)],[tone])
    for image in list(bpy.data.images):
        if not image.users:
            bpy.data.images.remove(image)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.export_scene.gltf(filepath=str(out/'digestive-route.glb'),export_extras=True,
                              export_animations=False,export_texcoords=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'digestive-route.blend'),compress=True)


if __name__ == '__main__':
    build(Path(sys.argv[sys.argv.index('--')+1]).resolve())
