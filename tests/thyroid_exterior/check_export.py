"""Check actual source/candidate reimports and finite-precision surface integrity."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SOURCE = 'models/thyroid_ct_s0189/exports/source-candidate-02/thyroid_ct_s0189_source_frame.glb'
SOURCE_SHA = '4add07e2efed2d67efb1d4ba225a109fe448043c79182e3d2e1a96e671534883'
CENTER = Vector((0, .180, .625))


def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def dot(a,b): return sum(x*y for x,y in zip(a,b))


def contact(a,b):
    ea=[sub(a[(i+1)%3],a[i]) for i in range(3)]
    eb=[sub(b[(i+1)%3],b[i]) for i in range(3)]
    na=cross(ea[0],ea[1]); nb=cross(eb[0],eb[1])
    axes=[na,nb]+[cross(x,y) for x in ea for y in eb]+[cross(na,e) for e in ea]+[cross(nb,e) for e in eb]
    for axis in axes:
        length=dot(axis,axis)**.5
        if length<1e-20: continue
        aa=[dot(p,axis)/length for p in a]; bb=[dot(p,axis)/length for p in b]
        if max(aa)<min(bb)-1e-7 or max(bb)<min(aa)-1e-7: return False
    return True


def inspect(path):
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=False)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    if len(objects)!=1: raise ValueError('Expected single exterior')
    ob=objects[0]; bm=bmesh.new(); bm.from_mesh(ob.data)
    for v in bm.verts: v.co=(ob.matrix_world@v.co-CENTER)*1000
    bm.verts.ensure_lookup_table(); bm.verts.index_update()
    verts=[tuple(v.co) for v in bm.verts]
    faces=[tuple(v.index for v in f.verts) for f in bm.faces]
    if any(len(f)!=3 for f in faces): raise ValueError('Expected exported triangles')
    if not all(math.isfinite(x) for v in verts for x in v): raise ValueError('Nonfinite geometry')
    remaining=set(bm.verts); components=[]
    while remaining:
        stack=[remaining.pop()]; n=0
        while stack:
            v=stack.pop(); n+=1
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in remaining: remaining.remove(other); stack.append(other)
        components.append(n)
    tree=BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=0)
    contacts=[]
    for i,j in tree.overlap(tree):
        if i>=j or set(faces[i])&set(faces[j]): continue
        if contact([verts[k] for k in faces[i]],[verts[k] for k in faces[j]]): contacts.append([i,j])
    report={'vertices':len(verts),'triangles':len(faces),'components':components,
            'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
            'zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),
            'signed_volume_mm3':bm.calc_volume(signed=True),
            'nonadjacent_contacts':len(contacts),'first_contacts':contacts[:10],
            'bounds_local_mm':[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)]}
    bm.free()
    return verts,faces,report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if a.out.exists(): raise FileExistsError('Use a new receipt path')
    source=a.root/SOURCE
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA: raise ValueError('Wrong source')
    if hashlib.sha256(a.candidate.read_bytes()).hexdigest()!=a.expected_sha256: raise ValueError('Wrong candidate')
    sv,sf,s=inspect(source); cv,cf,c=inspect(a.candidate)
    if sf!=cf: raise ValueError('Export changed vertex/triangle index correspondence')
    distances=[math.dist(x,y) for x,y in zip(sv,cv)]
    record={'source_sha256':SOURCE_SHA,'artifact_sha256':a.expected_sha256,'source':s,'candidate':c,
            'triangle_index_correspondence':True,
            'displacement_mm':{'max':max(distances),'rms':math.sqrt(sum(x*x for x in distances)/len(distances)),
                               'p95':sorted(distances)[int(.95*(len(distances)-1))],
                               'central_abs_x_lt5_max':max(d for d,v in zip(distances,sv) if abs(v[0])<5)},
            'relative_volume_change':c['signed_volume_mm3']/s['signed_volume_mm3']-1,
            'scope':'Fresh GLB import; no seam weld or mesh modification. BVH plus nonadjacent triangle SAT at1e-7mm finite-precision gap tolerance; not exhaustive exact arithmetic or anatomical proof.',
            'tracheal_context':'unverified: same-sample context not included','runtime':'unverified'}
    a.out.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
    if c['nonmanifold_edges'] or c['zero_area_faces'] or c['nonadjacent_contacts'] or c['signed_volume_mm3']<=0 or len(c['components'])!=1:
        raise ValueError('Candidate surface integrity failed')


if __name__=='__main__': main()
