"""Exact-mesh silhouette SVG comparisons; these are NOT raster screenshots.

Front-facing triangle boundaries produce vector silhouettes. Object depth ordering
is approximate; use the separately reviewed Cycles images for surface/occlusion.
No image embedding, remote fetches, or binary publication occurs.
"""
import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]); a.out.mkdir(exist_ok=False,parents=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene; s.render.resolution_x=900; s.render.resolution_y=1000; s.render.resolution_percentage=100
bpy.ops.object.camera_add(); camera=bpy.context.object; camera.data.type='ORTHO'; s.camera=camera
views=[('whole',(0,.06,.04),(.45,-1,.12),.62),
       ('pair',(.017,.066,.195),(.15,-1,.65),.056),
       ('lower',(0,.054,-.14),(.65,-1,.1),.225)]
rows=[]; panels={}; locators={}; identities={}

def projected(co):
    v=world_to_camera_view(s,camera,co)
    return (v.x*900,(1-v.y)*1000)


def signature(ob):
    coords=[tuple(ob.matrix_world@v.co) for v in ob.data.vertices]
    triangles=sorted(tuple(sorted(coords[i] for i in f.vertices)) for f in ob.data.polygons)
    return hashlib.sha256(repr(triangles).encode()).hexdigest()


for phase,path in [('before',a.baseline),('current',a.candidate)]:
    for ob in list(s.objects):
        if ob.type=='MESH': bpy.data.objects.remove(ob,do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=True)
    meshes=[ob for ob in s.objects if ob.type=='MESH']
    identities[phase]={ob.name:signature(ob) for ob in meshes if ob.name.startswith(('Authored cord','Filum'))}
    for name,t,direction,scale in views:
        target=Vector(t); view=Vector(direction).normalized(); camera.data.ortho_scale=scale
        camera.location=target+view*2; camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update()
        shapes=[]; pair_points=[]
        for ob in meshes:
            verts=[ob.matrix_world@v.co for v in ob.data.vertices]
            # Front-face boundary is a true silhouette of the imported mesh.
            edges={}
            for face in ob.data.polygons:
                indices=list(face.vertices)
                if (verts[indices[1]]-verts[indices[0]]).cross(verts[indices[2]]-verts[indices[0]]).dot(view)<=0: continue
                for i,j in zip(indices,indices[1:]+indices[:1]):
                    if (j,i) in edges: del edges[(j,i)]
                    else: edges[(i,j)]=True
            graph={}
            for i,j in edges: graph.setdefault(i,[]).append(j)
            paths=[]
            while graph:
                start=next(iter(graph)); i=start; loop=[]
                while True:
                    loop.append(projected(verts[i]))
                    if i not in graph: raise ValueError('Open silhouette boundary')
                    nxt=graph[i].pop()
                    if not graph[i]: del graph[i]
                    i=nxt
                    if i==start: break
                paths.append('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in loop)+'Z')
            depth=sum(v.dot(view) for v in verts)/len(verts)
            # One neutral color: shape is the comparison, not a color legend.
            fill='#d8c8a9' if not ob.name.startswith('Filum') else '#b8b7ad'
            shapes.append((depth, f'<path fill="{fill}" d="{"".join(paths)}"/>'))
            if ' upper 4 side1' in ob.name: pair_points.extend(projected(v) for v in verts)
        panels[phase,name]=''.join(x[1] for x in sorted(shapes))
        if name=='whole':
            locators[phase]=[min(p[0] for p in pair_points)-8,min(p[1] for p in pair_points)-12,
                             max(p[0] for p in pair_points)+8,max(p[1] for p in pair_points)+12]
        rows.append({'phase':phase,'view':name,'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'camera':list(camera.location),'target':t,'orthoscale':scale,
                     'projection':'front-facing mesh silhouette, flat fill, object-average depth ordering; not a raster render',
                     'native_viewport':[900,1000]})
if identities['before']!=identities['current']:
    raise ValueError('Retained cord or filum changed')

for name,_,_,_ in views:
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="650" viewBox="0 0 1000 650">',
           '<title>Spinal roots: baseline and r04 geometry projections</title>',
           '<desc>Matched orthographic mesh silhouettes. Not screenshots. Surface and occlusion were reviewed separately in local Cycles raster images.</desc>',
           '<rect width="1000" height="650" fill="#19252c"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#edf0ed}.label{font-size:17px;font-weight:600}.note{font-size:13px;fill:#bdc9cc}</style>',
           '<text class="label" x="24" y="29">Spinal roots · '+{'whole':'whole context','pair':'one representative pair','lower':'descending roots'}[name]+'</text>',
           '<text class="note" x="24" y="51">Matched geometry projections · flat vector silhouettes, not screenshots</text>',
           '<defs><clipPath id="frame"><rect width="900" height="1000"/></clipPath></defs>']
    for x,phase,title in [(25,'before','Before · r03'),(515,'current','Current · r04')]:
        parts.append(f'<text class="label" x="{x}" y="84">{title}</text>')
        parts.append(f'<g transform="translate({x},98) scale(.51)" clip-path="url(#frame)">')
        parts.append('<rect width="900" height="1000" fill="#303b40"/>')
        parts.append(panels[phase,name])
        if name=='whole':
            boxes=list(locators.values()); x0=min(b[0] for b in boxes); y0=min(b[1] for b in boxes); x1=max(b[2] for b in boxes); y1=max(b[3] for b in boxes)
            parts.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}" rx="8" fill="none" stroke="#8bcbd1" stroke-width="3" stroke-dasharray="8 6"/>')
            parts.append(f'<text x="{x1+12:.2f}" y="{(y0+y1)/2:.2f}" fill="#8bcbd1" font-size="24">Detail pair</text>')
        parts.append('</g>')
    footer={'whole':'Cord, conus and non-neural filum retained · detail locator marks the same representative pair.',
            'pair':'Dorsal swelling + separate ventral root → short shared mixed nerve. Dimensions are illustrative.',
            'lower':'17 bilateral samples, not a complete 31-pair map. Some lower roots overlap in this view.'}[name]
    parts.append(f'<text class="note" x="24" y="635">{html.escape(footer)}</text></svg>')
    out=a.out/f'comparison-{name}.svg';out.write_text(''.join(parts)+'\n')
(a.out/'projection-bindings.json').write_text(json.dumps({'views':rows,'preserved_mesh_signatures':identities,
    'files':[{'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(a.out.glob('*.svg'))]},indent=2)+'\n')
