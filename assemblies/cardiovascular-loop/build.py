"""Build the exploded circulation teaching circuit from Cardiac Atlas ED surfaces."""
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
ATLAS = ROOT / "heart/Cardiac_Atlas/exports"
UNIT = 0.025  # 1 native Atlas BU in metres
PINS = {
    "anatomy_meshes.json": "64b6bd5d48d941ecfe330ac5f929b5ad001efc28e2b51f8b876a7e85f3b1946b",
    "anatomy_details.json": "51891140bf475767ce9842bc83beeea901c7150975d351a6ac7c4eefae2ef871",
}
PALETTE = {
    "venous": (.22, .36, .53), "arterial": (.52, .21, .13),
    "annulus": (.72, .61, .44), "leaflet": (.86, .75, .53),
    "labels": (.17, .22, .27), "pulmonary bed": (.43, .61, .58), "systemic bed": (.65, .42, .21),
}
# Coordinates in diagram BU. Left and right heart retain patient laterality.
CHAMBERS = [
    ("RA", "01 Right atrium", -5.1, "venous"),
    ("RV", "03 Right ventricle", -1.9, "venous"),
    ("LA", "07 Left atrium", 1.9, "arterial"),
    ("LV", "09 Left ventricle", 5.1, "arterial"),
]
# Ring centre and rotation about Y from native superior-facing annuli.
VALVES = [
    ("Tricuspid", "02", (-3.5, 0, 0), -70),
    ("Pulmonary", "04", (-1.9, 0, 1.95), -12),
    ("Mitral", "08", (3.5, 0, 0), -70),
    ("Aortic", "10", (5.1, 0, 1.95), 12),
]


def read_source(file):
    data = (ATLAS / file).read_bytes()
    if hashlib.sha256(data).hexdigest() != PINS[file]:
        raise ValueError(f"Atlas source SHA-256 mismatch for {file}")
    return json.loads(data)["meshes"]


def mesh(name, vertices, triangles, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata([Vector(p) * UNIT for p in vertices], [], triangles)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(bpy.data.materials[mat])
    for face in data.polygons:
        face.use_smooth = True
    return obj


def tube(name, controls, mat, radius=.088):
    """Capped swept polyline with centre vertices at the two named endpoints."""
    points = [Vector(p) for p in controls]
    rings = 16
    vertices = []
    faces = []
    for i, point in enumerate(points):
        tangent = (points[min(i + 1, len(points)-1)] - points[max(0, i-1)]).normalized()
        across = tangent.cross(Vector((0, 1, 0))).normalized()
        normal = tangent.cross(across).normalized()
        for j in range(rings):
            a = math.tau * j / rings
            vertices.append(point + radius * (across * math.cos(a) + normal * math.sin(a)))
            if i:
                n = i * rings + j
                m = i * rings + (j + 1) % rings
                faces.append((n-rings, m-rings, m, n))
    for i, end in ((0, points[0]), (len(points)-1, points[-1])):
        tip = len(vertices)
        vertices.append(end)
        for j in range(rings):
            a = i*rings + j
            b = i*rings + (j+1) % rings
            faces.append((tip,b,a) if i == 0 else (tip,a,b))
    obj = mesh(name, vertices, faces, mat)
    obj["teaching_role"] = "authored schematic path"
    return obj


def arrow(name, start, end, mat):
    a, b = Vector(start), Vector(end)
    direction = (b-a).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=.215*UNIT, radius2=0,
                                    depth=.49*UNIT, location=(a+b)*(.5*UNIT))
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(bpy.data.materials[mat])


def build(out):
    from runpy import run_path
    run_path(str(ATLAS.parent / 'geometry_inputs.py'))['ensure_geometry_exports'](ATLAS)
    chambers, details = (read_source(path) for path in PINS)
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, rgb in PALETTE.items():
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*rgb, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*rgb, 1)
        shader.inputs["Roughness"].default_value = .74
    anchors = {}
    transforms = {}
    for key, name, x, mat in CHAMBERS:
        src = next(m for m in chambers if m["anatomy_id"] == f"bloodpool_{key}")
        points = [Vector(p) for p in src["vertices_BU"]]
        center = Vector([(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)])
        shift = Vector((x, 0, 0)) - center
        points = [p + shift for p in points]
        mesh(name, points, src["triangles"], mat)
        transforms[name] = {"translate_BU": list(shift)}
        # Pick actual source vertices facing each neighbour in the exploded view.
        for port, axis, sign in [("left",0,-1),("right",0,1),("top",2,1)]:
            extreme = max(points, key=lambda p: sign*p[axis])
            anchors[key+"."+port] = (name, extreme)
    for key, num, target, angle in VALVES:
        pieces = [m for m in details if m["object"].startswith(key+" valve | ")]
        annulus = next(m for m in pieces if m["object"].endswith("annulus"))
        center = sum(map(Vector, annulus["vertices_BU"]), Vector())/len(annulus["vertices_BU"])
        rot = Matrix.Rotation(math.radians(angle), 3, 'Y')
        for part in pieces:
            suffix = part["object"].split(" | ")[1]
            name = f"{num} {key} valve - {suffix}"
            pts = [rot @ (Vector(p)-center) + Vector(target) for p in part["vertices_BU"]]
            mesh(name, pts, part["triangles"], "annulus" if suffix=="annulus" else "leaflet")
        anchors[key] = (f"{num} {key} valve - annulus", Vector(target))
        transforms[key] = {"atlas_pivot_BU": list(center), "diagram_pivot_BU": target, "rotate_Y_degrees": angle}
    for key, z, name in [("lung",3.65,"05 Lung vascular bed"),("body",-3.3,"11 Systemic vascular bed")]:
        for end, x in [("left",-.84),("right",.84)]:
            anchors[f"{key}.{end}"] = (name+" - central", Vector((x,0,z)))
        for branch, height in [("central",0),("upper",.35),("lower",-.35)]:
            points = [(x,0,z+height*math.sin(math.pi*i/16)) for i,x in enumerate([-.84+1.68*j/16 for j in range(17)])]
            tube(name+" - "+branch, points, "pulmonary bed" if key=="lung" else "systemic bed", .065)
    connections = [
        ("01 to 02","RA.right","Tricuspid",[],"venous"),
        ("02 to 03","Tricuspid","RV.left",[],"venous"),
        ("03 to 04","RV.top","Pulmonary",[],"venous"),
        ("04 to 05 pulmonary outflow","Pulmonary","lung.left",[(-1.9,0,3.1),(-1.65,0,3.5)],"venous"),
        ("05 to 07 pulmonary venous return","lung.right","LA.top",[(1.56,0,3.53),(1.9,0,3.12)],"arterial"),
        ("07 to 08","LA.right","Mitral",[],"arterial"),
        ("08 to 09","Mitral","LV.left",[],"arterial"),
        ("09 to 10","LV.top","Aortic",[],"arterial"),
        ("10 to 11 aorta to systemic arteries","Aortic","body.right",[(5.2,0,2.35),(5.65,0,2.58),(6.19,0,2.49),(6.56,0,2.00),(6.63,0,-2.55),(6.3,0,-3.1),(5.68,0,-3.3)],"arterial"),
        ("11 to 01 systemic veins to vena cava","body.left","RA.left",[(-5.95,0,-3.3),(-6.5,0,-3.04),(-6.68,0,-2.56),(-6.68,0,-.5),(-6.48,0,-.15)],"venous"),
    ]
    checks = []
    for label, start, end, middle, mat in connections:
        node = "Bridge "+label
        points = [anchors[start][1], *middle, anchors[end][1]]
        tube(node,points,mat)
        i = max(range(len(points)-1), key=lambda i: (Vector(points[i+1])-Vector(points[i])).length)
        if (Vector(points[i+1])-Vector(points[i])).length > 1.0:
            arrow("Direction "+label,points[i],points[i+1],mat)
        for port in (start,end):
            host, point = anchors[port]
            checks.append({"bridge":node,"port":port,"host":host,"point_m":list(point*UNIT)})
    captions = [
        ("RA", -5.1, -1.08), ("RV", -1.9, -1.8), ("LA", 1.9, -1.08), ("LV", 5.1, -1.8),
        ("Tricuspid", -3.5, .64), ("Mitral", 3.5, .64),
        ("Pulmonary", -3.06, 2.0), ("Aortic", 4.27, 2.14),
        ("Lung bed", 0, 4.25), ("Body bed", 0, -4.15),
    ]
    for word,x,z in captions:
        bpy.ops.object.text_add(location=(x*UNIT,-.025,z*UNIT),rotation=(math.pi/2,0,0))
        obj = bpy.context.object
        obj.name = "Label " + word
        obj.data.body = word
        obj.data.align_x = "CENTER"
        obj.data.size = .32*UNIT
        obj.data.materials.append(bpy.data.materials["labels"])
        bpy.ops.object.convert(target='MESH')
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"cardiovascular-loop.blend"), compress=True)
    bpy.ops.export_scene.gltf(filepath=str(out/"cardiovascular-loop.glb"),export_extras=True)
    (out/"placement.json").write_text(json.dumps({"inputs":PINS,"transforms":transforms,"joins":checks},indent=2)+"\n")


if __name__ == "__main__":
    build(Path(sys.argv[sys.argv.index("--")+1]).resolve())
