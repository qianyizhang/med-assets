"""Author a hollow teaching derivative of the frozen r05 airway display cast.

The shell is NOT segmented wall tissue. Thickness and cut positions are authored.
Blender 4.3.2; all inputs local. Original r05 is left unchanged.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BASELINE_SHA256='af54ca254e47910ded53c6b690b475ab17236ba47d314fbdd5357dc67849bf4d'
THICKNESS=.0006
BAND_SECTION_SETBACK=.00005  # Separate display-overlay caps from the shell cut faces.
TERMINAL_CUTS=[('proximal',(.002,-.0025,.1735),(.28,-.5,1)),
               ('branch_x_positive',(.024,0,0),(1,0,0)),
               ('branch_x_negative',(-.027,0,0),(-1,0,0))]
# The editorial front-half cut follows a fitted depth field of the display cast.
# This is an illustration operator, not a reconstructed anatomical wall boundary.


def mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=.8
    return m


def cap_loops(bm):
    boundary=[e for e in bm.edges if e.is_boundary]
    directed={}
    for e in boundary:
        loop=e.link_loops[0]
        directed[loop.vert]=loop.link_loop_next.vert
    while directed:
        start=next(iter(directed));v=start;loop=[]
        while True:
            loop.append(v)
            if v not in directed:raise ValueError('Unclosed band section')
            v=directed.pop(v)
            if v==start:break
        center=bm.verts.new(sum((v.co for v in loop),Vector())/len(loop))
        for a,b in zip(loop,loop[1:]+loop[:1]):bm.faces.new((b,a,center))


def clip(ob,planes,cap=False):
    bm=bmesh.new();bm.from_mesh(ob.data)
    # Rejoin GLB export seams within 1e-8 m before topological cutting.
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    for _,point,normal in planes:
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                              dist=1e-8,plane_co=point,plane_no=normal,
                              clear_outer=True,clear_inner=False)
    if cap:
        cap_loops(bm)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(ob.data);bm.free();ob.data.update()


def depth_field(host):
    points=[v.co for v in host.data.vertices]
    design=[];values=[]
    for p in points:
        x=p.x/.05;z=(p.z-.12)/.05
        design.append([1,x,z,x*x,x*z,z*z]);values.append(p.y)
    coefficients=np.linalg.lstsq(np.array(design),np.array(values),rcond=None)[0]
    return [float(c) for c in coefficients]


def clip_front_half(ob,coefficients,cap=False):
    def field(p):
        x=p.x/.05;z=(p.z-.12)/.05
        return p.y-sum(c*t for c,t in zip(coefficients,[1,x,z,x*x,x*z,z*z]))
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    verts=[];faces=[]
    for face in bm.faces:
        poly=[v.co.copy() for v in face.verts];cut=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            fa,fb=field(a),field(b)
            if fa>=0:cut.append(a)
            if (fa>=0)!=(fb>=0):cut.append(a+(b-a)*(fa/(fa-fb)))
        if len(cut)>=3:
            ids=list(range(len(verts),len(verts)+len(cut)))
            verts.extend(tuple(p) for p in cut);faces.append(ids)
    bm.free()
    me=bpy.data.meshes.new('Editorial depth-following cut')
    me.from_pydata(verts,[],faces);me.update();ob.data=me
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    if cap:cap_loops(bm)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()


def boundary_loops(edges):
    graph={}
    for a,b in edges:
        graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
    if any(len(v)!=2 for v in graph.values()):raise ValueError('Non-loop cut boundary')
    seen=set();loops=[]
    for start in graph:
        if start in seen:continue
        todo=[start];loop=[]
        while todo:
            v=todo.pop()
            if v in seen:continue
            seen.add(v);loop.append(v);todo.extend(graph[v])
        loops.append(loop)
    return loops


def reference_normals(ob):
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.normal_update()
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    points=[v.co.copy() for v in bm.verts];normals=[v.normal.copy() for v in bm.verts]
    faces=[tuple(v.index for v in f.verts) for f in bm.faces]
    tree=BVHTree.FromPolygons(points,faces,all_triangles=True);bm.free()
    def normal(p):
        _,_,i,_=tree.find_nearest(p);ia,ib,ic=faces[i];a,b,c=points[ia],points[ib],points[ic]
        u,v,w=b-a,c-a,p-a;uu,uv,vv=u.dot(u),u.dot(v),v.dot(v)
        d=uu*vv-uv*uv
        beta=(vv*w.dot(u)-uv*w.dot(v))/d;gamma=(uu*w.dot(v)-uv*w.dot(u))/d
        return ((1-beta-gamma)*normals[ia]+beta*normals[ib]+gamma*normals[ic]).normalized()
    return normal


def shell(ob,materials,normal_at,planes,coefficients,cutaway):
    bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bm.verts.index_update()
    edges=[];oriented=[];curve_boundary=set()
    for edge in bm.edges:
        if not edge.is_boundary:continue
        loop=edge.link_loops[0];a=loop.vert.index;b=loop.link_loop_next.vert.index
        edges.append((a,b));oriented.append((a,b))
        on_terminal=any(all(abs((bm.verts[i].co-Vector(point)).dot(Vector(normal).normalized()))<1e-7 for i in (a,b)) for _,point,normal in planes)
        if cutaway and not on_terminal:curve_boundary.update((a,b))
    loops=boundary_loops(edges);outer=[v.co.copy() for v in bm.verts]
    centers=[list(sum((outer[i] for i in loop),Vector())/len(loop)) for loop in loops]
    inner=[];max_shift=0.0;reduced_offsets=0;min_normal_thickness=THICKNESS
    def field(p):
        x=p.x/.05;z=(p.z-.12)/.05
        return p.y-sum(c*t for c,t in zip(coefficients,[1,x,z,x*x,x*z,z*z]))
    def gradient(p):
        x=p.x/.05;z=(p.z-.12)/.05;c=coefficients
        return Vector((-(c[1]+2*c[3]*x+c[4]*z)/.05,1,-(c[2]+c[4]*x+2*c[5]*z)/.05))
    for i,p in enumerate(outer):
        normal=normal_at(p);constraints=[]
        for _,point,axis in planes:
            axis=Vector(axis).normalized()
            if abs((p-Vector(point)).dot(axis))<1e-7:constraints.append(axis)
        if i in curve_boundary:
            x=p.x/.05;z=(p.z-.12)/.05;c=coefficients
            constraints.append(Vector((-(c[1]+2*c[3]*x+c[4]*z)/.05,1,-(c[2]+c[4]*x+2*c[5]*z)/.05)).normalized())
        basis=[]
        for c in constraints:
            for q in basis:c=c-q*c.dot(q)
            if c.length>1e-7:basis.append(c.normalized())
        direction=normal.copy()
        for c in basis:direction-=c*direction.dot(c)
        cosine=normal.dot(direction)
        if cosine<.05:raise ValueError('Editorial section too tangent to cast surface')
        delta=-THICKNESS*direction/cosine
        ratio=1.0
        for _,point,axis in planes:
            axis=Vector(axis).normalized();distance=(p-Vector(point)).dot(axis);toward=delta.dot(axis)
            if distance < -1e-7 and toward>0:ratio=min(ratio,.85*(-distance)/toward)
        if cutaway and i not in curve_boundary and field(p+delta*ratio)<.15*field(p):
            lo,hi=0.0,ratio
            for _ in range(20):
                mid=(lo+hi)/2
                if field(p+delta*mid)>=.15*field(p):lo=mid
                else:hi=mid
            ratio=lo
        if ratio<.999999:reduced_offsets+=1
        q=p+delta*ratio
        if i in curve_boundary:
            for _ in range(4):
                grad=gradient(q);adjust=grad.copy()
                for _,point,axis in planes:
                    axis=Vector(axis).normalized()
                    if abs((p-Vector(point)).dot(axis))<1e-7:adjust-=axis*adjust.dot(axis)
                denominator=grad.dot(adjust)
                if denominator<1e-8:raise ValueError('Degenerate editorial cut intersection')
                q-=adjust*((field(q)-field(p))/denominator)
        inner.append(q);max_shift=max(max_shift,(q-p).length)
        min_normal_thickness=min(min_normal_thickness,-(q-p).dot(normal))
    n=len(outer);faces=[];indices=[]
    for face in bm.faces:
        ids=[v.index for v in face.verts];faces.append(ids);indices.append(0)
        faces.append([i+n for i in reversed(ids)]);indices.append(1)
    for a,b in oriented:faces.append((b,a,a+n,b+n));indices.append(2)
    bm.free();me=bpy.data.meshes.new('Constrained authored shell')
    me.from_pydata([tuple(v) for v in outer+inner],[],faces);me.update();ob.data=me
    for m in materials:me.materials.append(m)
    for face,idx in zip(me.polygons,indices):face.material_index=idx;face.use_smooth=idx!=2
    return {'surface_boundary_loops_before_shell':len(loops),'boundary_vertex_counts':[len(x) for x in loops],
            'opening_centers':centers,'outer_vertices':n,'nominal_shell_thickness_m':THICKNESS,
            'max_offset_vector_m':max_shift,'locally_reduced_offsets':reduced_offsets,'minimum_normal_thickness_m':min_normal_thickness,'thickness_rule':'Authored source-normal offset constrained to editorial sections; locally reduced to avoid crossing cuts. Not measured tissue.'}


def build(baseline,out):
    if hashlib.sha256(baseline.read_bytes()).hexdigest()!=BASELINE_SHA256:
        raise ValueError('Exact hydrated r05 baseline required')
    out.mkdir(parents=True,exist_ok=False)
    records=[]
    for variant in ('open','cutaway'):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(baseline),merge_vertices=True)
        meshes=[ob for ob in bpy.context.scene.objects if ob.type=='MESH']
        host=next(ob for ob in meshes if ob.name.startswith('Trachea |'))
        bands=[ob for ob in meshes if ob!=host]
        if len(bands)!=18:raise ValueError('Expected existing 18 C-bands')
        for ob in meshes:
            for v in ob.data.vertices:v.co=ob.matrix_world@v.co
            ob.matrix_world.identity()
            ob.data.materials.clear()
        outer=mat('Illustrative external display surface',(.55,.43,.30))
        inner=mat('Illustrative inner shell - not segmented mucosa',(.52,.29,.23))
        rim=mat('Editorial cut face - not anatomical termination',(.82,.65,.42))
        bandmat=mat('Retained illustrative C-bands',(.73,.66,.51))
        planes=list(TERMINAL_CUTS)
        coefficients=depth_field(host)
        normal_at=reference_normals(host)
        clip(host,planes)
        if variant=='cutaway':clip_front_half(host,coefficients)
        qa=shell(host,[outer,inner,rim],normal_at,planes,coefficients,variant=='cutaway')
        if variant=='open' and qa['surface_boundary_loops_before_shell']!=3:
            raise ValueError('Expected exactly three open airway ends')
        band_planes=[(name,tuple(Vector(point)-Vector(normal).normalized()*BAND_SECTION_SETBACK),normal) for name,point,normal in planes]
        for ob in bands:
            clip(ob,band_planes,cap=True)
            if variant=='cutaway':clip_front_half(ob,coefficients,cap=True)
            ob.data.materials.append(bandmat)
        host.name='Trachea | authored '+variant+' teaching shell'
        host['derivation']='Teaching shell from preprocessed source display envelope; not recovered wall tissue'
        host['modifications']=str(host.get('modifications',''))+'; r06 illustrative terminal sections and 0.6 mm inward shell; editorial cutaway in cutaway variant.'
        host['scope']='Airway continuity teaching only. Wall thickness, terminal sections and cutaway authored. No clinical, histology or caliber claim.'
        bpy.context.scene['scope']='Authored teaching derivative of an airway cast; not a hollow specimen reconstruction'
        bpy.context.scene['clinical_status']='Not clinically validated'
        bpy.ops.object.select_all(action='SELECT')
        path=out/f'trachea-{variant}.glb'
        bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_extras=True,export_animations=False)
        records.append({'variant':variant,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'bytes':path.stat().st_size,'section_planes':planes,'band_cap_setback_m':BAND_SECTION_SETBACK,'editorial_depth_field':coefficients if variant=='cutaway' else None,**qa})
    (out/'build-record.json').write_text(json.dumps({'baseline_sha256':BASELINE_SHA256,'variants':records,
        'scope':'Authored hollow teaching derivative of existing display cast. Original source is not validated wall geometry; dimensions and cuts illustrative.'},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);build(a.baseline,a.out)
