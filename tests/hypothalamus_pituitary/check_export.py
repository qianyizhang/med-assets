"""Fresh-export connectivity and finite-precision nonadjacent triangle-contact screen."""
import argparse, hashlib, json, math, struct, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def hit(A,B):
    ea=[sub(A[(i+1)%3],A[i]) for i in range(3)];eb=[sub(B[(i+1)%3],B[i]) for i in range(3)];na=cross(ea[0],ea[1]);nb=cross(eb[0],eb[1])
    axes=[na,nb]+[cross(x,y) for x in ea for y in eb]+[cross(na,e) for e in ea]+[cross(nb,e) for e in eb]
    for axis in axes:
        length=dot(axis,axis)**.5
        if length<1e-20:continue
        aa=[dot(p,axis)/length for p in A];bb=[dot(p,axis)/length for p in B]
        if max(aa)<min(bb)-1e-7 or max(bb)<min(aa)-1e-7:return False
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    raw=a.candidate.read_bytes();assert hashlib.sha256(raw).hexdigest()==a.expected_sha256
    assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,8)[0]==len(raw)
    n=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+n]);assert not any('uri' in b for b in gltf.get('buffers',[]));assert not gltf.get('animations')
    if a.out.exists():raise FileExistsError(a.out)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(a.candidate),merge_vertices=False)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1
    ob=objects[0];bm=bmesh.new();bm.from_mesh(ob.data)
    origin=Vector((-.00065,-.103,1.534))
    for v in bm.verts:v.co=(ob.matrix_world@v.co-origin)*1000
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update()
    verts=[tuple(v.co) for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces]
    assert all(math.isfinite(x) for v in verts for x in v)
    todo=set(bm.verts);components=[]
    while todo:
        stack=[todo.pop()];n=0
        while stack:
            v=stack.pop();n+=1
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in todo:todo.remove(other);stack.append(other)
        components.append(n)
    tree=BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=0);candidates=[];contacts=[]
    for i,j in tree.overlap(tree):
        if i>=j or set(faces[i])&set(faces[j]):continue
        candidates.append((i,j))
        if hit([verts[k] for k in faces[i]],[verts[k] for k in faces[j]]):contacts.append((i,j))
    report={'artifact_sha256':a.expected_sha256,'bytes':len(raw),'vertices_after_seam_weld':len(verts),'triangles':len(faces),'components':components,'edge_incidence_not_two':sum(len(e.link_faces)!=2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume_mm3':bm.calc_volume(signed=True),'self_candidates':len(candidates),'nonadjacent_self_contacts':len(contacts),'first_contacts':contacts[:20],'scope':'Actual GLB reimport; 1e-5mm render-seam weld, connectivity/volume, BVH broadphase and triangle SAT at 1e-7mm gap tolerance. Finite-precision contact screen; not exact-arithmetic, anatomical or clinical proof.'}
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));bm.free()
    assert len(components)==1 and report['edge_incidence_not_two']==0 and report['zero_area_faces']==0 and report['signed_volume_mm3']>0,'Topology/connectivity failed'
    assert not contacts,'Nonadjacent surface contacts remain'

if __name__=='__main__':main()
