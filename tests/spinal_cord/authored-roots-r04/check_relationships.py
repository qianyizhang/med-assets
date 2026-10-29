"""Screen root/trunk contact and dorsal-only swellings on an exact GLB reimport."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser()
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--record',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
record=json.loads(a.record.read_text())
sha=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
if sha!=record['candidate_sha256']: raise ValueError('Artifact/record mismatch')
if a.out.exists(): raise FileExistsError(a.out)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(a.candidate),merge_vertices=True)
meshes={}; groups={}
for ob in bpy.context.scene.objects:
    if ob.type!='MESH' or not ob.name.startswith('Representative'):continue
    verts=[ob.matrix_world@v.co for v in ob.data.vertices]
    faces=[tuple(f.vertices) for f in ob.data.polygons]
    tree=BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=0)
    meshes[ob.name]=(ob,verts,faces,tree)
    groups.setdefault(ob['pair'],{})[ob['role']]=ob.name
records={r['name']:r for r in record['roots']}; checks=[]
for pair,roles in sorted(groups.items()):
    if set(roles)!={'dorsal','ventral','mixed'}:raise ValueError('Missing role in '+pair)
    dorsal,ventral,mixed=(meshes[roles[r]] for r in ('dorsal','ventral','mixed'))
    dr=records[roles['dorsal']];vr=records[roles['ventral']]
    join=(Vector(dr['controls'][-1])+Vector(vr['controls'][-1]))/2
    if not dorsal[0]['ganglion'] or ventral[0]['ganglion']:raise ValueError('Wrong ganglion role')
    contacts={}
    for name,root in [('dorsal',dorsal),('ventral',ventral)]:
        candidates=root[3].overlap(mixed[3])
        # BVH overlap is a finite-precision triangle contact screen, not proof.
        if not candidates:raise ValueError('No '+name+' / mixed contact in '+pair)
        contacts[name]=len(candidates)
    roots_contact=dorsal[3].overlap(ventral[3]); far=[]
    for i,j in roots_contact:
        center=sum((dorsal[1][v] for v in dorsal[2][i]),Vector())/3
        if (center-join).length>.004:far.append(i)
    if far:raise ValueError('Dorsal/ventral contact away from union in '+pair)
    g=Vector(dr['controls'][dr['ganglion_index']]); peak=dr['radii'][dr['ganglion_index']]
    nearest=ventral[3].find_nearest(g)
    if nearest is None or nearest[3]<=peak:raise ValueError('Ganglion/ventral clearance failed in '+pair)
    checks.append({'pair':pair,'root_to_mixed_triangle_candidates':contacts,
                   'dorsal_ventral_contact_triangles_outside_4mm_join_zone':len(far),
                   'ganglion_center_to_ventral_surface_m':nearest[3],
                   'authored_ganglion_radius_m':peak})
if len(checks)!=34:raise ValueError('Expected 34 illustrative groups')
a.out.write_text(json.dumps({'candidate_sha256':sha,'groups':checks,
    'scope':'Exact export reimport; role/count and finite-precision contact/clearance screening. 4 mm join zone is an authored geometry tolerance, not an anatomical normal range.'},indent=2)+'\n')
print('PASS: 34 dorsal-only ganglia, 68 root/trunk contacts, no premature paired-root contacts')
