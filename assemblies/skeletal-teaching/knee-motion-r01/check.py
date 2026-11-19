"""Independently compare clean exported knee poses to the original bone surfaces."""
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "models/joints/exports/z-knee-r01/knee_z_native.glb"


def read_meshes(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    return {o.name: ([o.matrix_world@v.co for v in o.data.vertices],
                     [list(f.vertices) for f in o.data.polygons])
            for o in bpy.context.scene.objects if o.type=="MESH"}


def check(path):
    poses = read_meshes(path)
    source = read_meshes(SOURCE)
    pivot = Vector((-.077,.030,.452))
    report = {}
    for prefix, angle, y in [("Source",0,0),("Flexion",20,-.175)]:
        shift = Vector((0,y,0))
        rot = Matrix.Rotation(math.radians(angle),3,"X")
        errors = {}
        for bone in ("Femur","Tibia","Fibula"):
            points, _ = poses[prefix+" | "+bone]
            tree = KDTree(len(points))
            for i,v in enumerate(points):
                tree.insert(v,i)
            tree.balance()
            native,_ = source[bone+".r candidate"]
            retained = [v for v in native if .31801 < v.z < .54999]
            expect = [v+shift if bone=="Femur" else pivot+rot@(v-pivot)+shift for v in retained]
            errors[bone] = max(tree.find(v)[2] for v in expect)*1000
            if errors[bone] > .001:
                raise ValueError(f"{prefix} {bone} landmark disagrees with expected rigid placement")
        f, fp = poses[prefix+" | Femur"]
        t, tp = poses[prefix+" | Tibia"]
        femur = BVHTree.FromPolygons(f,fp)
        tibia = BVHTree.FromPolygons(t,tp)
        intersections = len(femur.overlap(tibia))
        if intersections:
            raise ValueError(f"{prefix} femur intersects tibial surface")
        gaps = {}
        for label,lateral in [("lateral",True),("medial",False)]:
            native = [p for p in source["Tibia.r candidate"][0] if p.z>.416 and (p.x<-.077)==lateral]
            points = [pivot+rot@(p-pivot)+shift for p in native]
            gaps[label] = min(femur.find_nearest(p)[3] for p in points)*1000
            if gaps[label]>6:
                raise ValueError(f"{prefix} {label} plateau exceeds 6 mm teaching envelope")
        gaps["fibularHeadToFemur"] = min(femur.find_nearest(p)[3] for p in poses[prefix+" | Fibula"][0])*1000
        for label, vector in [("Femoral load",Vector((0,0,-1))),("Tibial support",rot@Vector((0,0,1)))]:
            points,_ = poses[prefix+" | "+label]
            span = [p.dot(vector) for p in points]
            # Cone tip is the unique leading point; a reversed arrow presents a ring instead.
            tip = {tuple(p) for p,s in zip(points,span) if max(span)-s < 1e-6}
            if len(tip)!=1 or max(span)-min(span)<.05:
                raise ValueError(f"{prefix} {label} direction/length mismatch")
        report[prefix] = dict(maxLandmarkErrorMm=errors, femurTibiaIntersections=intersections,
                              sampledSurfaceDistancesMm=gaps)
    print(json.dumps(dict(glbSha256=hashlib.sha256(path.read_bytes()).hexdigest(),poses=report),indent=2))


if __name__=="__main__":
    check(Path(sys.argv[sys.argv.index("--")+1]))
