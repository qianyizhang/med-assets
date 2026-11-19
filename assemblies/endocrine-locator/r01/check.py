"""Clean-import audit of endocrine signal endpoints, landmarks and collisions."""
import hashlib
import itertools
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def check(glb, placement):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
    objects = {o.name:o for o in bpy.context.scene.objects if o.type == "MESH"}
    vertices = {n:[o.matrix_world @ v.co for v in o.data.vertices] for n,o in objects.items()}
    surfaces = {n:BVHTree.FromPolygons(vertices[n],[list(p.vertices) for p in o.data.polygons])
                for n,o in objects.items()}

    def group(prefix, count):
        names = sorted(n for n in objects if n.startswith(prefix))
        if len(names) != count:
            raise ValueError(f"Expected {count} {prefix} meshes, got {len(names)}")
        return names

    hypothalamus, = group("Hypothalamus-pituitary",1)
    thyroid, = group("Neck - Thyroid",1)
    adrenals = group("Adrenal -",2)
    pancreas = group("Pancreas -",5)
    overlaps = sum(len(surfaces[a].overlap(surfaces[p])) for a,p in itertools.product(adrenals,pancreas))
    if overlaps:
        raise ValueError(f"Adrenal/pancreas locator collision: {overlaps} polygon pairs")
    for prefix,count in [("Pelvic ovary",2),("Alternative testis inset",2),
                         ("Neck - Superior",2),("Neck - Inferior",2),("Islet alpha",3),
                         ("Islet beta",6),("Islet capillary",1),("Head to pelvis outline",1)]:
        group(prefix,count)
    anchors = list(map(Vector, json.loads(placement.read_text())["signalAnchors"]))
    anchor_errors = [surfaces[name].find_nearest(p)[3] for name,p in
                     zip([hypothalamus,hypothalamus,thyroid],anchors,strict=True)]
    directions = {}
    for i,hormone in enumerate(("TRH","TSH")):
        names = group(hormone,2)
        shaft = next(n for n in names if n.endswith(" path"))
        cone = next(n for n in names if n.endswith(" direction"))
        # A cone has one distal apex and a circular ring at its base.
        points = [Vector(p) for p in set(map(tuple,vertices[cone]))]
        center = sum(points,Vector())/len(points)
        tip = max(points,key=lambda p:(p-center).length)
        ring = [p for p in points if p != tip]
        base = sum(ring,Vector())/len(ring)
        errors = [surfaces[shaft].find_nearest(anchors[i])[3],
                  surfaces[shaft].find_nearest(base)[3],(tip-anchors[i+1]).length]
        if max(errors) > .00001:
            raise ValueError(f"{hormone} arrow misses its source, shaft or receptor landmark")
        directions[hormone] = [round(x*1e6,6) for x in errors]
    if max(anchor_errors) > .00001:
        raise ValueError("Signal anchor outside owning organ")
    print(json.dumps({"glbSha256":hashlib.sha256(glb.read_bytes()).hexdigest(),"meshes":len(objects),
          "adrenalPancreasIntersections":overlaps,"glandAnchorErrorsMicrons":[x*1e6 for x in anchor_errors],
          "arrowSourceBaseTipErrorsMicrons":directions},indent=2))


if __name__=="__main__":
    model, anchors = sys.argv[sys.argv.index("--")+1:]
    check(Path(model),Path(anchors))
