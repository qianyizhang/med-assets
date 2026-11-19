"""Measure contacts on clean imports. Distances are nearest sampled vertices (mm)."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector, kdtree


def points(name):
    obj = bpy.data.objects[name]
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def distances(a,b):
    tree = kdtree.KDTree(len(b))
    for i,p in enumerate(b):
        tree.insert(p,i)
    tree.balance()
    return min(tree.find(p)[2] for p in a)*1000


def check(folder, sex):
    glb = folder / f"{sex}.glb"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    result = {}
    def join(a,b,tol,point=None):
        p,q = points(a),points(b)
        if point is not None:
            # Check a local junction. Overlap elsewhere cannot satisfy this test.
            target = Vector(point)
            p = [x for x in p if (x-target).length < .007]
            q = [x for x in q if (x-target).length < .007]
        distance = distances(p,q)
        if distance > tol:
            raise ValueError(f"Gap {a}/{b}: {distance:.3f} mm > {tol} mm")
        result[f"{a} / {b}"] = round(distance,5)
    if sex == "female":
        for side,word in [('L','left'),('R','right')]:
            def name(label):
                return f'VH_F_{label}_{side}'
            join('VH_F_'+word+'_ovary',name('fibria_of_uterine_tube'),6)
            chain = [name(x) for x in ['fibria_of_uterine_tube','uterine_tube_infundibulum',
                    'ampulla_of_uterine_tube','isthmus_of_fallopian_tube']]+['VH_F_cornua','VH_F_body_of_uterus']
            for a,b in zip(chain,chain[1:]):
                join(a,b,3)
        join('VH_F_body_of_uterus','VH_F_lower_uterine_segment',3)
        join('VH_F_lower_uterine_segment','VH_F_cervix',3)
        join('VH_F_cervix','VH_F_cervicovaginal_junction',3)
        join('VH_F_cervicovaginal_junction','VH_F_vagina',3)
    else:
        for sign,side in [(-1,'r'),(1,'l')]:
            ep = 'Epididymis.'+side+' native study'
            tail = min(points(ep),key=lambda p:p.z)
            j = (sign*.009,.036,.837)
            join('Testis.'+side+' native study',ep,4)
            join(ep,'Ductus deferens.'+side,2,tail)
            join('Seminal vesicle.'+side,'Vesicular duct.'+side,4,(sign*.018,.040,.843))
            join('Vesicular duct.'+side,'Ejaculatory duct.'+side,2,j)
            join('Ductus deferens.'+side,'Ejaculatory duct.'+side,2,j)
            join('Ejaculatory duct.'+side,'Urethra source display',2,(sign*.001,.013,.821))
        urethra = points("Urethra source display")
        distal = min(urethra,key=lambda p:p.z)
        if distal.z > .747 or distal.y > -.080:
            raise ValueError("Distal urethral surface absent")
    return dict(sha256=hashlib.sha256(glb.read_bytes()).hexdigest(),nodes=len(bpy.context.scene.objects),
                nearestVertexDistancesMm=result)


if __name__ == '__main__':
    source,receipt = map(Path,sys.argv[sys.argv.index('--')+1:])
    result = {s:check(source.resolve(),s) for s in ['female','male']}
    with receipt.open('x') as out:
        out.write(json.dumps(result,indent=2)+'\n')
