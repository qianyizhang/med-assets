"""Sample reimported skinning, attachment landmarks and ankle contacts at 3 frames."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import kdtree, Matrix, Vector
import math
from mathutils.bvhtree import BVHTree


def snapshot(meshes,frame):
    bpy.context.scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    result = {}
    for obj in meshes:
        e = obj.evaluated_get(deps)
        result[obj.name.split('.')[0]] = [e.matrix_world @ v.co for v in e.data.vertices]
    return result


def tree(coords):
    kd = kdtree.KDTree(len(coords))
    for i,v in enumerate(coords):
        kd.insert(v,i)
    kd.balance()
    return kd


def closest(source,target):
    kd = tree(target)
    distance,source_idx,target_idx = min((d,i,j) for i,v in enumerate(source)
                                        for _,j,d in [kd.find(v)])
    return distance,source_idx,target_idx


def verify(glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
    meshes = [o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    if len(meshes)!=8 or not any(o.type=='ARMATURE' and o.animation_data for o in bpy.context.scene.objects):
        raise ValueError('Expected eight meshes and an animated armature')
    baseline = snapshot(meshes,0)
    heel = 'Calcaneus'
    tendon = 'Calcaneal tendon'
    pairs = [(name,tendon) for name in baseline if 'muscle' in name or 'gastrocnemius' in name]
    pairs.append((tendon,heel))
    witnesses = {}
    for a,b in pairs:
        d,i,j = closest(baseline[a],baseline[b])
        witnesses[a,b] = (i,j)
    stats = []
    for frame in (0,6,12,18,24):
        current = snapshot(meshes,frame)
        shifts = {}
        stretch = {}
        for obj in meshes:
            name = obj.name.split('.')[0]
            before,after = baseline[name],current[name]
            shifts[name] = round(max((p-q).length for p,q in zip(before,after))*1000,4)
            ratios = []
            for edge in obj.data.edges:
                i,j = edge.vertices
                length = (before[i]-before[j]).length
                if length>1e-5:
                    ratios.append((after[i]-after[j]).length/length)
            stretch[name] = [round(min(ratios),5),round(max(ratios),5)]
        separations = {f"{a} / {b}":round((current[a][i]-current[b][j]).length*1000,5)
                       for (a,b),(i,j) in witnesses.items()}
        # Track any new bone/bone surface intersections at the ankle articulation.
        trees = {}
        for obj in meshes:
            n = obj.name.split('.')[0]
            if n in {'Tibia','Fibula','Talus'}:
                trees[n] = BVHTree.FromPolygons(current[n],[tuple(f.vertices) for f in obj.data.polygons])
        collisions = {n:len(trees[n].overlap(trees['Talus'])) for n in ('Tibia','Fibula')}
        stats.append(dict(frame=frame,displacementMm=shifts,edgeLengthRatios=stretch,
                          fixedLandmarkSeparationMm=separations,talusIntersectionPairs=collisions))
    # The qualified input has pre-existing talofibular interpenetration.
    for sample in stats:
        hits = sample['talusIntersectionPairs']
        if hits['Tibia'] or hits['Fibula'] > stats[0]['talusIntersectionPairs']['Fibula']:
            raise ValueError('Hinge introduces additional bone intersections')
    if max(stats[-1]['displacementMm'][x] for x in ('Tibia','Fibula')) > .01:
        raise ValueError('Stationary shank moved')
    if stats[-1]['displacementMm'][heel] < 8:
        raise ValueError('Plantarflexion missing on reimport')
    if min(stats[-1]['displacementMm'][name] for name,_ in pairs) < .1:
        raise ValueError('Soft-tissue deformation missing')
    for s in stats:
        for n,(lo,hi) in s['edgeLengthRatios'].items():
            if lo < .70 or hi > 1.30:
                raise ValueError(f'Excessive edge change: {n}: {lo}, {hi}')
        for k,d in s['fixedLandmarkSeparationMm'].items():
            if abs(d - stats[0]['fixedLandmarkSeparationMm'][k]) > .2:
                raise ValueError(f'Attachment separates: {k}')
    # Compare the full calcaneus with the prescribed rigid transform.
    pivot = Vector((-.080,.051,.065))
    rotation = Matrix.Rotation(math.radians(15),3,'X')
    err = max((pivot + rotation @ (v-pivot) - w).length for v,w in zip(baseline[heel],current[heel]))
    if err > 1e-5:
        raise ValueError('Hindfoot pose differs from the 15 degree target')
    source = Path(__file__).resolve().parents[1]/'2026-10-23'/'achilles-right-context.glb'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    original = snapshot([o for o in bpy.context.scene.objects if o.type=='MESH'],0)
    neutral_errors = {}
    for name,v in original.items():
        a,b = tree(v),tree(baseline[name])
        neutral_errors[name] = 1000*max(max(b.find(p)[2] for p in v),
                                        max(a.find(p)[2] for p in baseline[name]))
    if max(neutral_errors.values()) > .01:
        raise ValueError('Neutral pose changed source surface positions')
    return dict(glb=glb.name,sha256=hashlib.sha256(glb.read_bytes()).hexdigest(),
                neutralVsStaticMaxMm=neutral_errors,heelRigidTransformErrorMm=err*1000,
                sampledPoses=stats,neutralWitnessVertices={f'{a} / {b}':v for (a,b),v in witnesses.items()})


if __name__=='__main__':
    glb,out = map(Path,sys.argv[sys.argv.index('--')+1:])
    result = verify(glb)
    with out.open('x') as f:
        f.write(json.dumps(result,indent=2)+'\n')
